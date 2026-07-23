"""
Market data fetcher — unifies Binance (crypto, live klines) and
Yahoo Finance (forex / commodities / indices) into one clean OHLC DataFrame.

Yahoo Finance intraday data (especially for futures like XAUUSD/XAGUSD/USOIL
and off-hours forex) is frequently sparse or briefly unavailable at 1m
resolution. To keep signals flowing reliably, we automatically fall back
to progressively larger intervals/periods rather than just failing.
"""
import logging
import time

import pandas as pd
import requests
import yfinance as yf

from config import SYMBOL_MAP, CANDLE_LIMIT

log = logging.getLogger("mi.fetcher")

# Ordered fallback chain: (yfinance interval, yfinance period)
# Tried in order until one returns enough candles.
_YF_FALLBACK_CHAIN = [
    ("1m", "1d"),
    ("1m", "5d"),
    ("2m", "5d"),
    ("5m", "5d"),
    ("15m", "1mo"),
]

_MIN_CANDLES = 50


def _fetch_binance(symbol: str, interval: str, limit: int) -> pd.DataFrame | None:
    """Pull recent klines straight from Binance's public REST API."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        raw = r.json()
        if not raw or isinstance(raw, dict):  # Binance returns a dict on error
            log.warning(f"Binance returned no/invalid data for {symbol}: {raw if isinstance(raw, dict) else 'empty'}")
            return None
        df = pd.DataFrame(raw, columns=[
            "open_time", "o", "h", "l", "c", "v", "close_time",
            "qav", "trades", "tb_base", "tb_quote", "ignore",
        ])
        df["Open"] = df["o"].astype(float)
        df["High"] = df["h"].astype(float)
        df["Low"] = df["l"].astype(float)
        df["Close"] = df["c"].astype(float)
        df["Volume"] = df["v"].astype(float)
        df.index = pd.to_datetime(df["open_time"], unit="ms")
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        log.warning(f"Binance fetch failed for {symbol}: {e}")
        return None


def _fetch_yahoo(yf_symbol: str, limit: int) -> pd.DataFrame | None:
    """
    Pull recent intraday candles from Yahoo Finance, automatically
    stepping through a fallback chain of (interval, period) combos
    when the tightest resolution has no/insufficient data — this is
    what fixes symbols like XAGUSD/XAUUSD/USOIL that often come back
    empty at strict 1m/1-2d requests.
    """
    last_error = None
    for interval, period in _YF_FALLBACK_CHAIN:
        try:
            data = yf.download(
                yf_symbol, period=period, interval=interval,
                progress=False, auto_adjust=False, threads=False,
            )
            if data is None or len(data) == 0:
                continue
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            data = data.dropna(subset=["Open", "High", "Low", "Close"])
            if len(data) < _MIN_CANDLES:
                continue
            data = data.tail(limit)
            if "Volume" not in data.columns:
                data["Volume"] = 0.0
            return data[["Open", "High", "Low", "Close", "Volume"]]
        except Exception as e:
            last_error = e
            continue

    if last_error:
        log.warning(f"Yahoo fetch exhausted fallback chain for {yf_symbol}: {last_error}")
    else:
        log.warning(f"Yahoo fetch exhausted fallback chain for {yf_symbol}: no interval returned enough candles")
    return None


def fetch_candles(internal_symbol: str, retries: int = 1) -> pd.DataFrame | None:
    """
    Fetch OHLCV candles for an internal symbol (e.g. 'EURUSD', 'BTCUSDT').
    Returns a DataFrame with columns [Open, High, Low, Close, Volume] or None.
    """
    meta = SYMBOL_MAP.get(internal_symbol)
    if not meta:
        log.error(f"Unknown symbol: {internal_symbol}")
        return None

    for attempt in range(retries + 1):
        if meta["source"] == "binance":
            df = _fetch_binance(meta["symbol"], "1m", CANDLE_LIMIT)
        else:
            df = _fetch_yahoo(meta["symbol"], CANDLE_LIMIT)

        if df is not None and len(df) >= _MIN_CANDLES:
            df = df.dropna()
            return df

        if attempt < retries:
            time.sleep(2)

    log.error(f"❌ All fetch attempts failed for {internal_symbol} ({meta['source']}:{meta['symbol']})")
    return None
