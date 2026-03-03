"""Indicator helpers using pandas and numpy.

Functions return dictionaries summarizing commonly requested indicators.
"""
import pandas as pd
import numpy as np


def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, adjust=False).mean()
    ma_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int = 14):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    sig = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - sig
    return macd_line, sig, hist


def bollinger(series: pd.Series, window: int = 20, dev: int = 2):
    mid = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = mid + dev * std
    lower = mid - dev * std
    pb = (series - lower) / (upper - lower)
    return upper, mid, lower, pb


def vwap(df: pd.DataFrame):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    v = df["volume"]
    return (tp * v).cumsum() / v.cumsum()


def run_analysis(bars_df: pd.DataFrame):
    if bars_df is None or bars_df.empty:
        return {"error": "no bars"}

    close = bars_df["close"].astype(float)
    high = bars_df["high"].astype(float)
    low = bars_df["low"].astype(float)

    out = {}
    out["ema_20"] = float(ema(close, 20).iloc[-1])
    out["ema_50"] = float(ema(close, 50).iloc[-1])
    out["rsi_14"] = float(rsi(close, 14).iloc[-1])
    out["atr_14"] = float(atr(bars_df, 14).iloc[-1])
    macd_line, sig, hist = macd(close)
    out["macd"] = float(macd_line.iloc[-1])
    out["macd_signal"] = float(sig.iloc[-1])
    out["macd_hist"] = float(hist.iloc[-1])
    upper, mid, lower, pb = bollinger(close)
    out["bb_upper"] = float(upper.iloc[-1])
    out["bb_mid"] = float(mid.iloc[-1])
    out["bb_lower"] = float(lower.iloc[-1])
    out["bb_pct_b"] = float(pb.iloc[-1])
    out["vwap"] = float(vwap(bars_df).iloc[-1])
    out["volatility_score"] = out["atr_14"] / float(close.iloc[-1])

    return out
