"""
agent.py — Natural language router for the alpaca-trading OpenClaw skill.
Parses user requests and dispatches to alpaca_client.py or indicators.py.

Usage:
  python3 agent.py "buy 5 shares of AAPL"
  python3 agent.py "positions"
  python3 agent.py "analyse SPY 1h"
  python3 agent.py "quote TSLA"
"""

import sys
import re
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

IS_PAPER = os.getenv("ALPACA_PAPER", "true").lower() != "false"
MODE_TAG = "⚠️  PAPER MODE" if IS_PAPER else "🔴 LIVE MODE"
MAX_NOTIONAL = 50_000

# ── Safety gates ───────────────────────────────────────────────────────────────
def require_live_confirm(raw: str) -> bool:
    """Live trades require the word 'confirm' in the message."""
    if IS_PAPER:
        return True
    if "confirm" in raw.lower():
        return True
    print(
        f"\n🔴 LIVE MODE — This will use REAL MONEY.\n"
        f"   Resend your message with the word 'confirm' to proceed.\n"
        f"   Example: 'confirm buy 5 shares of AAPL'\n"
    )
    return False

def check_large_order(notional: float | None, raw: str) -> bool:
    if notional and notional > MAX_NOTIONAL:
        if "confirm large order" not in raw.lower():
            print(
                f"⚠️  Order notional ${notional:,.0f} exceeds ${MAX_NOTIONAL:,} limit.\n"
                f"   Add 'confirm large order' to proceed.\n"
            )
            return False
    return True

# ── Symbol helpers ─────────────────────────────────────────────────────────────
CRYPTO_SUFFIXES = {"/USD", "/USDT", "/BTC"}
COMMON_CRYPTO   = {"BTC", "ETH", "SOL", "DOGE", "AVAX", "MATIC", "LTC", "XRP"}

def extract_symbol(text: str) -> str | None:
    # Match crypto pairs first e.g. BTC/USD
    crypto = re.search(r'\b([A-Z]{2,6}/(?:USD|USDT|BTC))\b', text.upper())
    if crypto:
        return crypto.group(1)
    # Match ticker: 1-5 uppercase letters, not common English words
    tickers = re.findall(r'\b([A-Z]{1,5})\b', text.upper())
    skip = {"BUY","SELL","LIMIT","STOP","AT","OF","FOR","GTC","DAY","FOK",
            "IOC","THE","AND","OR","IN","ON","A","AN","ME","MY","USD"}
    for t in tickers:
        if t not in skip:
            return t
    return None

def parse_price(text: str, keyword: str) -> float | None:
    m = re.search(rf'{keyword}\s+(?:at\s+)?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    return float(m.group(1)) if m else None

def parse_qty(text: str) -> float | None:
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:shares?|coins?|units?)?', text, re.IGNORECASE)
    return float(m.group(1)) if m else None

def parse_notional(text: str) -> float | None:
    m = re.search(r'\$(\d+(?:\.\d+)?)', text)
    return float(m.group(1)) if m else None

# ── Dispatch helpers ───────────────────────────────────────────────────────────
def fmt_money(v) -> str:
    try: return f"${float(v):,.2f}"
    except: return str(v)

def print_account():
    from alpaca_client import get_account, get_market_status
    a   = get_account()
    mkt = get_market_status()
    pdt = max(0, 3 - a["daytrade_count"])
    print(f"""
📊 Alpaca Account [{MODE_TAG}]
   Status:          {a['status']}
   Portfolio Value: {fmt_money(a['portfolio_value'])}
   Buying Power:    {fmt_money(a['buying_power'])}
   Cash:            {fmt_money(a['cash'])}
   Day Trades Left: {pdt}/3 (PDT rolling 5-day)
   Market:          {'OPEN' if mkt['is_open'] else 'CLOSED'} — {'closes' if mkt['is_open'] else 'opens'} {mkt['next_close'] if mkt['is_open'] else mkt['next_open']}
""")

def print_positions():
    from alpaca_client import get_positions
    positions = get_positions()
    if not positions:
        print(f"📭 No open positions [{MODE_TAG}]")
        return
    total_pl = sum(p["unrealized_pl"] for p in positions)
    print(f"📈 Open Positions [{MODE_TAG}]")
    for p in positions:
        arrow = "▲" if p["unrealized_pl"] >= 0 else "▼"
        pct   = p["unrealized_plpc"] * 100
        print(f"   {p['symbol']:<6} | {p['qty']} shares | "
              f"Avg {fmt_money(p['avg_entry'])} | "
              f"Now {fmt_money(p['current_price'])} | "
              f"{arrow} {fmt_money(p['unrealized_pl'])} ({pct:+.1f}%)")
    arrow = "▲" if total_pl >= 0 else "▼"
    print(f"\n   Total Unrealized P&L: {arrow} {fmt_money(total_pl)}\n")

def print_quote(symbol: str):
    from alpaca_client import get_latest_quote
    q = get_latest_quote(symbol)
    print(f"""
💹 Quote: {q['symbol']} [{MODE_TAG}]
   Bid:      {fmt_money(q['bid'])} (size {q['bid_size']})
   Ask:      {fmt_money(q['ask'])} (size {q['ask_size']})
   Mid:      {fmt_money(q['mid'])}
   Spread:   {fmt_money(q['spread'])} ({q['spread_pct']}%)
   Feed:     {q['feed'].upper()}
   Time:     {q['timestamp']}
""")

def print_orders(symbol: str | None = None):
    from alpaca_client import get_open_orders
    orders = get_open_orders(symbol)
    if not orders:
        label = f"for {symbol}" if symbol else ""
        print(f"📭 No open orders {label} [{MODE_TAG}]")
        return
    print(f"📋 Open Orders [{MODE_TAG}]")
    for o in orders:
        lp = f" lim {fmt_money(o['limit_price'])}" if o['limit_price'] else ""
        sp = f" stop {fmt_money(o['stop_price'])}" if o['stop_price'] else ""
        print(f"   {o['symbol']:<6} | {o['side'].upper()} {o['qty']}{lp}{sp} | "
              f"{o['type']} | {o['status']} | {o['id'][:8]}...")

def do_cancel(symbol: str | None, raw: str):
    if not require_live_confirm(raw): return
    from alpaca_client import get_open_orders
    from alpaca.trading.client import TradingClient
    import os
    tc = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"),
                       paper=IS_PAPER)
    if symbol:
        orders = get_open_orders(symbol)
        for o in orders:
            tc.cancel_order_by_id(o["id"])
        print(f"✅ Cancelled {len(orders)} order(s) for {symbol} [{MODE_TAG}]")
    else:
        tc.cancel_orders()
        print(f"✅ All open orders cancelled [{MODE_TAG}]")

def do_close_position(symbol: str, raw: str):
    if not require_live_confirm(raw): return
    from alpaca.trading.client import TradingClient
    import os
    tc = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"),
                       paper=IS_PAPER)
    tc.close_position(symbol)
    print(f"✅ Position closed: {symbol} [{MODE_TAG}]")

def do_order(raw: str):
    from alpaca_client import get_market_status
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest, LimitOrderRequest, StopOrderRequest,
        StopLimitOrderRequest, TrailingStopOrderRequest,
        TakeProfitRequest, StopLossRequest,
    )
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
    import os

    low = raw.lower()
    side = OrderSide.BUY if "buy" in low else OrderSide.SELL

    symbol = extract_symbol(raw)
    if not symbol:
        print("❌ Could not parse symbol. Example: 'buy 5 shares of AAPL'")
        return

    notional    = parse_notional(raw)
    qty         = parse_qty(raw) if not notional else None
    limit_price = parse_price(raw, r'limit|at')
    stop_price  = parse_price(raw, r'stop(?:-loss)?')
    take_profit = parse_price(raw, r'take.?profit|tp')
    trail_pct   = None
    trail_match = re.search(r'trail(?:ing)?\s+(?:stop\s+)?(\d+(?:\.\d+)?)\s*%', low)
    if trail_match:
        trail_pct = float(trail_match.group(1))

    tif = TimeInForce.GTC if "gtc" in low else TimeInForce.DAY

    # Safety
    if not require_live_confirm(raw): return
    if not check_large_order(notional, raw): return

    # Market advisory
    mkt = get_market_status()
    if not mkt["is_open"] and "/" not in symbol:
        print(f"ℹ️  Market is closed. Order queues for next session ({tif.value}).")

    tc = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"),
                       paper=IS_PAPER)
    try:
        if take_profit and stop_price:
            req = MarketOrderRequest(
                symbol=symbol, qty=qty, side=side, time_in_force=tif,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=take_profit),
                stop_loss=StopLossRequest(stop_price=stop_price),
            )
        elif trail_pct:
            req = TrailingStopOrderRequest(
                symbol=symbol, qty=qty, side=side, time_in_force=tif,
                trail_percent=trail_pct,
            )
        elif limit_price and stop_price:
            req = StopLimitOrderRequest(
                symbol=symbol, qty=qty, side=side, time_in_force=tif,
                limit_price=limit_price, stop_price=stop_price,
            )
        elif limit_price:
            req = LimitOrderRequest(
                symbol=symbol, qty=qty, notional=notional,
                side=side, time_in_force=tif, limit_price=limit_price,
            )
        elif stop_price:
            req = StopOrderRequest(
                symbol=symbol, qty=qty, side=side,
                time_in_force=tif, stop_price=stop_price,
            )
        else:
            req = MarketOrderRequest(
                symbol=symbol, qty=qty, notional=notional,
                side=side, time_in_force=tif,
            )

        order = tc.submit_order(order_data=req)
        fill  = fmt_money(order.filled_avg_price) if order.filled_avg_price else "pending"
        total = (fmt_money(float(order.filled_avg_price or 0) * float(order.qty or 0))
                 if order.filled_avg_price and order.qty else "—")
        otype = req.__class__.__name__.replace("OrderRequest","").replace("Market","Market ")
        print(f"""
✅ Order Submitted [{MODE_TAG}]
   Type:    {otype.strip()} {side.value.upper()}
   Symbol:  {symbol}
   Qty:     {order.qty}{f' (${notional:,.0f} notional)' if notional else ''}
   Status:  {order.status.value}
   Fill Px: {fill}
   Total:   {total}
   OrderID: {str(order.id)[:12]}...
""")
    except Exception as e:
        print(f"❌ Order failed: {e}")

def do_analysis(symbol: str, timeframe: str = "5min", hours: int = 2):
    from alpaca_client import get_bars
    from indicators import calculate_indicators
    import pandas as pd

    print(f"🔍 Fetching {hours}h of {timeframe} bars for {symbol}...")
    try:
        df = get_bars(symbol, timeframe=timeframe, hours_back=hours, adjustment="split")
    except ValueError as e:
        print(f"❌ Data error: {e}")
        return

    print(f"📊 Calculating indicators on {len(df)} bars...")
    try:
        df = calculate_indicators(df, include=["ema","rsi","atr","macd","bbands","vwap","volatility_score"])
    except ValueError as e:
        print(f"❌ Indicator error: {e}")
        return

    last = df.iloc[-1]
    rsi  = last.get("rsi_14", float("nan"))
    rsi_signal = "🔴 Overbought" if rsi > 70 else ("🟢 Oversold" if rsi < 30 else "⚪ Neutral")
    price = last.get("c", float("nan"))
    ema20 = last.get("ema_20", float("nan"))
    trend = "▲ Above EMA20" if price > ema20 else "▼ Below EMA20"

    print(f"""
📈 Technical Analysis: {symbol} [{timeframe}, last {hours}h]
   Price:           {fmt_money(price)}
   EMA 20:          {fmt_money(ema20)}  {trend}
   EMA 50:          {fmt_money(last.get('ema_50', float('nan')))}
   RSI 14:          {rsi:.1f}  {rsi_signal}
   ATR 14:          {fmt_money(last.get('atr_14', float('nan')))}
   MACD:            {last.get('macd', float('nan')):.4f}
   MACD Signal:     {last.get('signal', float('nan')):.4f}
   MACD Hist:       {last.get('histogram', float('nan')):.4f}
   BB Upper:        {fmt_money(last.get('upper', float('nan')))}
   BB Middle:       {fmt_money(last.get('middle', float('nan')))}
   BB Lower:        {fmt_money(last.get('lower', float('nan')))}
   BB %B:           {last.get('pct_b', float('nan')):.2f}
   VWAP:            {fmt_money(last.get('vwap', float('nan')))}
   Volatility:      {last.get('volatility_score', float('nan')):.2f}% of price
   Bars analysed:   {len(df)}
   Data range:      {df.index[0].strftime('%H:%M')} – {df.index[-1].strftime('%H:%M UTC')}
""")

# ── Main router ────────────────────────────────────────────────────────────────
def route(user_input: str):
    raw = user_input.strip()
    low = raw.lower()

    # Account
    if any(w in low for w in ["account", "balance", "buying power", "cash"]):
        return print_account()

    # Positions
    if any(w in low for w in ["position", "portfolio", "holdings", "p&l", "pnl"]):
        return print_positions()

    # Open orders list
    if low in ("orders", "open orders") or ("open" in low and "order" in low and
       not any(w in low for w in ["buy","sell","place","cancel"])):
        sym = extract_symbol(raw)
        return print_orders(sym if sym and sym != raw.upper() else None)

    # Cancel
    if "cancel" in low:
        sym = extract_symbol(raw) if "all" not in low else None
        return do_cancel(sym, raw)

    # Quote
    if any(low.startswith(w) for w in ["quote","price","get quote","what is"]):
        sym = extract_symbol(raw)
        if sym: return print_quote(sym)

    # Close position
    if "close" in low and "position" in low:
        sym = extract_symbol(raw)
        if sym: return do_close_position(sym, raw)

    # Analysis
    if any(w in low for w in ["analys", "indicator", "rsi", "macd", "bollinger",
                               "technical", "chart", "ema", "atr", "vwap"]):
        sym = extract_symbol(raw)
        if not sym:
            print("❌ Specify a symbol: e.g. 'analyse AAPL'")
            return
        # parse optional timeframe e.g. "analyse SPY 1h"
        tf_match = re.search(r'\b(1min|5min|15min|30min|1h|4h|1d)\b', low)
        tf   = tf_match.group(1) if tf_match else "5min"
        hrs_match = re.search(r'(\d+)\s*h(?:ours?)?', low)
        hrs  = int(hrs_match.group(1)) if hrs_match else 2
        return do_analysis(sym, tf, hrs)

    # Buy / Sell order
    if "buy" in low or "sell" in low:
        return do_order(raw)

    # Fallback help
    print(
        f"❓ Not sure what to do with: '{raw}'\n\n"
        f"   Try:\n"
        f"   'account'                      → account balance\n"
        f"   'positions'                    → open positions\n"
        f"   'quote AAPL'                   → live quote\n"
        f"   'buy 5 shares of AAPL'         → market order\n"
        f"   'sell 10 SPY limit at 508'     → limit order\n"
        f"   'analyse TSLA 1h'              → technical analysis\n"
        f"   'cancel all orders'            → cancel everything\n"
    )

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.getenv("ALPACA_API_KEY") or not os.getenv("ALPACA_SECRET_KEY"):
        print("❌ Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env before running.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 agent.py '<request>'\n"
              "Example: python3 agent.py 'buy 5 shares of AAPL'")
        sys.exit(1)

    route(" ".join(sys.argv[1:]))