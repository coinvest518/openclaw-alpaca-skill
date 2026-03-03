---
name: alpaca-trading
version: 1.0.0
description: >
  Commission-free US stock and crypto trading via the official Alpaca API.
  Executes market, limit, stop, bracket, and trailing-stop orders. Checks
  portfolio positions, account balance, buying power, and live quotes.
  Defaults to paper trading ($100k virtual cash, no real money) — live
  trading requires ALPACA_PAPER=false and user confirmation. Also runs
  technical indicator analysis (EMA, RSI, ATR, MACD, Bollinger Bands, VWAP)
  on fetched OHLCV bars. Use when user asks to buy or sell stocks or crypto,
  check portfolio, analyse a symbol technically, view open orders, cancel
  orders, or get a live quote. Requires ALPACA_API_KEY and ALPACA_SECRET_KEY.
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["python3"]
      env:
        - ALPACA_API_KEY
        - ALPACA_SECRET_KEY
    install:
      - id: pip
        kind: shell
        command: "pip install -r ~/clawd/skills/alpaca-trading/requirements.txt"
        label: "Install Python dependencies"
---

# Alpaca Trading Skill

Commission-free stock and crypto trading via Alpaca's official Python SDK
(alpaca-py). Paper trading is on by default — $100,000 virtual cash, zero
real-money risk until you explicitly switch to live mode.

⚠️  PAPER MODE is the default and is always active unless the user has
set ALPACA_PAPER=false in .env AND types the word "confirm" in their message.
Never execute a live trade without that confirmation in the same message.

---

## Prerequisites

### 1. Create a free Alpaca account
- Go to alpaca.markets → sign up free
- Navigate to: Paper Trading → API Keys → Generate New Key
- Copy your API Key ID and Secret Key
- For live trading later: fund your account and generate separate live keys

### 2. Copy .env.example → .env and fill in your keys
```
ALPACA_API_KEY="PKXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
ALPACA_SECRET_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
ALPACA_PAPER=true
ALPACA_FEED=iex
```

### 3. Install dependencies (run once)
```bash
pip install -r ~/clawd/skills/alpaca-trading/requirements.txt
```

---

## When to Activate This Skill

Activate when the user says any of:

**Trading**
- "Buy [qty/dollar amount] of [SYMBOL]"
- "Sell [qty] shares of [SYMBOL]"
- "Place a limit order for [SYMBOL] at [price]"
- "Set a stop loss on [SYMBOL] at [price]"
- "Buy [SYMBOL] bracket take-profit [price] stop-loss [price]"
- "Close my position in [SYMBOL]"
- "Cancel order for [SYMBOL]" / "Cancel all orders"

**Portfolio & Account**
- "What's in my portfolio?" / "Show my positions"
- "Check my account balance" / "How much buying power do I have?"
- "What open orders do I have?"
- "Get a quote for [SYMBOL]"

**Analysis**
- "Run technical analysis on [SYMBOL]"
- "Show me RSI and MACD for [SYMBOL]"
- "What are the indicators for [SYMBOL]?"
- "Analyse [SYMBOL] with Bollinger Bands"

Do NOT activate for:
- Options trading → not supported
- Withdrawing funds → must be done manually at alpaca.markets
- Tax reports → manual export from Alpaca dashboard
- Crypto wallet transfers → use /agent-wallet skill instead

---

## Exact Commands

### Account
```bash
cd ~/clawd/skills/alpaca-trading && python3 agent.py "account"
```

### Portfolio positions
```bash
python3 agent.py "positions"
```

### Live quote
```bash
python3 agent.py "quote AAPL"
python3 agent.py "quote BTC/USD"
```

### Market order
```bash
python3 agent.py "buy 5 shares of AAPL"
python3 agent.py "buy $500 of SPY"
python3 agent.py "sell 10 TSLA"
```

### Limit order
```bash
python3 agent.py "buy 10 NVDA limit at 800"
python3 agent.py "sell 5 MSFT limit at 420 GTC"
```

### Bracket order (entry + take-profit + stop-loss in one)
```bash
python3 agent.py "buy 3 SPY bracket take-profit 510 stop-loss 490"
```

### Trailing stop
```bash
python3 agent.py "trailing stop 5% on TSLA sell 10 shares"
```

### Technical analysis
```bash
python3 agent.py "analyse AAPL"
python3 agent.py "technical analysis SPY 1h"
python3 agent.py "show RSI MACD AAPL"
```

### Cancel orders
```bash
python3 agent.py "cancel all orders"
python3 agent.py "cancel order for AAPL"
```

### Close a position
```bash
python3 agent.py "close position TSLA"
```

---

## Order Types Reference

| Type | Example Phrase | Notes |
|---|---|---|
| Market | "buy 5 AAPL" | Fills at best available price |
| Market (dollar) | "buy $500 of SPY" | Fractional shares if supported |
| Limit | "buy 10 NVDA at 800" | Fills only at limit price or better |
| Stop | "stop loss TSLA at 200" | Triggers market order at stop price |
| Stop-Limit | "stop limit AAPL at 185 stop 183" | Stop triggers limit, not market |
| Bracket | "buy 3 SPY bracket tp 510 sl 490" | Entry + take-profit + stop in one |
| Trailing Stop | "trailing stop 5% TSLA" | Stop moves up with price |

Default time-in-force is DAY unless user says "GTC".

---

## Technical Indicators Available

When user asks for analysis, run `agent.py "analyse [SYMBOL]"`.
Default fetches 2h of 5-min bars, calculates:

| Indicator | Column | Notes |
|---|---|---|
| EMA 20 | ema_20 | Trend direction |
| EMA 50 | ema_50 | Medium-term trend |
| RSI 14 | rsi_14 | Momentum (>70 overbought, <30 oversold) |
| ATR 14 | atr_14 | Volatility in price units |
| MACD | macd, signal, histogram | Trend + momentum crossover |
| Bollinger Bands | upper, middle, lower, pct_b | Volatility channel |
| VWAP | vwap | Intraday institutional benchmark |
| Volatility Score | volatility_score | ATR % of price — position sizing guide |

All indicators use Wilder smoothing to match TradingView and Bloomberg output.
Data fetched with split adjustment by default to avoid false signals on splits.

---

## Safety Rules

1. **Paper mode default** — active unless ALPACA_PAPER=false in .env
2. **Live confirmation required** — agent prints warning and requires the
   word "confirm" in the same message before any live trade executes
3. **Large order block** — refuses orders over $50,000 notional without
   "confirm large order" in the message
4. **PDT warning** — warns when fewer than 3 day trades remain in the
   rolling 5-day window (only applies to accounts under $25,000)
5. **Market hours advisory** — tells user if market is closed and how
   the queued order will behave (DAY expires at close, GTC persists)
6. **Rate limit handling** — automatic retry with exponential backoff
   on Alpaca 429 responses (3 retries, 2–4–8 second waits)

---

## Output Format

**Account:**
```
📊 Alpaca Account [⚠️ PAPER MODE]
   Status:          ACTIVE
   Portfolio Value: $102,150.00
   Buying Power:    $98,432.11
   Cash:            $52,432.11
   Day Trades Left: 2/3 PDT rolling 5-day
   Market: OPEN — closes 4:00 PM ET
```

**Order submitted:**
```
✅ Order Submitted [⚠️ PAPER MODE]
   Type:    Market Buy
   Symbol:  AAPL
   Qty:     5 shares
   Status:  filled
   Fill Px: $189.42
   Total:   $947.10
   OrderID: abc12345...
```

**Positions:**
```
📈 Open Positions [⚠️ PAPER MODE]
   AAPL  | 5 shares | Avg $185.20 | Now $189.42 | ▲ +$21.10 (+2.3%)
   SPY   | 2 shares | Avg $501.00 | Now $508.33 | ▲ +$14.66 (+1.5%)
   Total Unrealized P&L: ▲ +$35.76
```

---

## Error Reference

| Error | Cause | Fix |
|---|---|---|
| `403 forbidden` | Paper/live key mismatch | Ensure ALPACA_PAPER matches key type |
| `insufficient_balance` | Low buying power | Check account balance |
| `asset_not_tradable` | Symbol halted/unsupported | Verify on alpaca.markets |
| `market_closed` | Outside trading hours | DAY orders queue; GTC persists |
| `pattern_day_trader` | PDT limit hit | Max 3 day trades/5 days under $25k |
| `ALPACA_API_KEY not found` | Missing .env | Copy .env.example → .env and fill keys |
| `429 rate limited` | Too many requests | Auto-retried with backoff — wait and retry |

---

## Market Hours (US Eastern)

| Session | Hours | Notes |
|---|---|---|
| Pre-market | 4:00 AM – 9:30 AM | Limited liquidity |
| Regular | 9:30 AM – 4:00 PM | Full liquidity |
| After-hours | 4:00 PM – 8:00 PM | Limited liquidity |
| Crypto | 24 / 7 | Always open on Alpaca |

---

## Disclaimer

This skill executes real trades when ALPACA_PAPER=false.
Alpaca Securities LLC is a registered broker-dealer and FINRA/SIPC member.
Paper trading carries no financial risk. Live trading involves real capital.
This skill is not financial advice. Always review order details before confirming.