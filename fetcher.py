"""
Market data fetcher — unifies Binance (crypto, live klines) and
Yahoo Finance (forex / commodities / indices) into one clean OHLC DataFrame.
"""
import logging
import time

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from config import SYMBOL_MAP, TIMEFRAME, CANDLE_LIMIT

log = logging.getLogger("mi.fetcher")

_YF_INTERVAL_MAP = {"1m": "1m", "3m": "5m", "5m": "5m", "15m": "15m"}


def _fetch_binance(symbol: str, interval: str, limit: int) -> pd.DataFrame | None:
    """Pull recent klines straight from Binance's public REST API."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        raw = r.json()
        if not raw:
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


def _fetch_yahoo(symbol: str, limit: int) -> pd.DataFrame | None:
    """Pull recent intraday candles from Yahoo Finance."""
    try:
        interval = _YF_INTERVAL_MAP.get(TIMEFRAME, "1m")
        period = "2d" if interval == "1m" else "5d"
        data = yf.download(symbol, period=period, interval=interval,
                            progress=False, auto_adjust=False)
        if data is None or len(data) == 0:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.tail(limit)
        if "Volume" not in data.columns:
            data["Volume"] = 0.0
        return data[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        log.warning(f"Yahoo fetch failed for {symbol}: {e}")
        return None


def fetch_candles(internal_symbol: str, retries: int = 2) -> pd.DataFrame | None:
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
            df = _fetch_binance(meta["symbol"], TIMEFRAME, CANDLE_LIMIT)
        else:
            df = _fetch_yahoo(meta["symbol"], CANDLE_LIMIT)

        if df is not None and len(df) >= 50:
            df = df.dropna()
            return df

        if attempt < retries:
            time.sleep(1.5)

    return None
