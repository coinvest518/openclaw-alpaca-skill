"""Lightweight Alpaca REST wrapper using `requests`.

This client implements a small subset of endpoints used by the skill:
- account
- positions
- submit market order
- fetch bars (data API)
"""
import os
import time
import requests
from typing import Optional


class AlpacaClient:
    def __init__(self, key: str, secret: str, paper: bool = True):
        self.key = key
        self.secret = secret
        self.paper = paper
        self.base = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.data_base = "https://data.alpaca.markets/v2"
        self.auth_headers = {
            "APCA-API-KEY-ID": self.key,
            "APCA-API-SECRET-KEY": self.secret,
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls):
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_SECRET_KEY")
        paper = os.getenv("ALPACA_PAPER", "true").lower() != "false"
        if not (key and secret):
            raise RuntimeError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment")
        return cls(key, secret, paper=paper)

    def _request(self, method, url, headers=None, **kwargs):
        h = dict(self.auth_headers)
        if headers:
            h.update(headers)
        resp = requests.request(method, url, headers=h, timeout=15, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"Alpaca error {resp.status_code}: {resp.text}")
        return resp.json()

    def get_account(self):
        return self._request("GET", f"{self.base}/v2/account")

    def list_positions(self):
        return self._request("GET", f"{self.base}/v2/positions")

    def submit_market_order(self, symbol: str, qty: int, side: str = "buy", time_in_force: str = "day"):
        body = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": time_in_force,
        }
        return self._request("POST", f"{self.base}/v2/orders", json=body)

    def get_quote(self, symbol: str):
        # Fallback to fetching latest bar as a quick quote
        bars = self.get_bars(symbol, timeframe="1Min", limit=1)
        if bars is None or bars.empty:
            return {"symbol": symbol, "note": "no bars"}
        last = bars.iloc[-1]
        return {"symbol": symbol, "t": str(last.name), "open": float(last.open), "high": float(last.high), "low": float(last.low), "close": float(last.close), "v": int(last.volume)}

    def get_bars(self, symbol: str, timeframe: str = "5Min", limit: int = 500):
        # Uses the Data API v2 bars endpoint
        url = f"{self.data_base}/stocks/{symbol}/bars"
        params = {"timeframe": timeframe, "limit": limit}
        # data API expects same auth headers
        resp = requests.get(url, headers=self.auth_headers, params=params, timeout=15)
        if resp.status_code == 204:
            return None
        if resp.status_code >= 400:
            raise RuntimeError(f"Data API error {resp.status_code}: {resp.text}")
        data = resp.json()
        # convert to pandas DataFrame if available
        try:
            import pandas as pd
            bars = data.get("bars", [])
            if not bars:
                return pd.DataFrame()
            df = pd.DataFrame(bars)
            df = df.set_index(pd.to_datetime(df["t"]))
            df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
            return df[["open", "high", "low", "close", "volume"]]
        except Exception:
            return data
