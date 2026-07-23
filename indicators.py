"""
Technical indicator calculations — no external TA library dependency
so the bot has zero fragile dependencies. Pure pandas/numpy.
"""
import numpy as np
import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # EMA / SMA
    df["EMA_14"] = df["Close"].ewm(span=14, adjust=False).mean()
    df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()

    # RSI (Wilder's smoothing)
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(50)

    # MACD
    ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    # Bollinger Bands
    sma_20 = df["Close"].rolling(window=20).mean()
    std_20 = df["Close"].rolling(window=20).std()
    df["BB_upper"] = sma_20 + (std_20 * 2)
    df["BB_mid"] = sma_20
    df["BB_lower"] = sma_20 - (std_20 * 2)

    # Stochastic
    low_14 = df["Low"].rolling(window=14).min()
    high_14 = df["High"].rolling(window=14).max()
    rng = (high_14 - low_14).replace(0, np.nan)
    df["Stoch_K"] = ((df["Close"] - low_14) / rng) * 100
    df["Stoch_D"] = df["Stoch_K"].rolling(window=3).mean()

    # Volatility (used to size expiry recommendation)
    df["Volatility"] = df["Close"].pct_change().rolling(window=20).std()

    return df


def find_swing_points(df: pd.DataFrame, swing_length: int = 5):
    """Identify swing highs/lows for market-structure analysis (SMC/ICT)."""
    highs, lows = [], []
    n = len(df)
    for i in range(swing_length, n - swing_length):
        window_hi = df["High"].iloc[i - swing_length: i + swing_length + 1]
        window_lo = df["Low"].iloc[i - swing_length: i + swing_length + 1]

        if df["High"].iloc[i] == window_hi.max() and \
           (window_hi == df["High"].iloc[i]).sum() == 1:
            highs.append({"index": i, "price": df["High"].iloc[i]})

        if df["Low"].iloc[i] == window_lo.min() and \
           (window_lo == df["Low"].iloc[i]).sum() == 1:
            lows.append({"index": i, "price": df["Low"].iloc[i]})

    return highs, lows


def market_structure(df: pd.DataFrame) -> dict:
    """Break of Structure (BOS) detection via swing high/low sequencing."""
    highs, lows = find_swing_points(df)
    structure = {"trend": "NEUTRAL", "bos": False}

    if len(highs) >= 2 and len(lows) >= 2:
        h1, h2 = highs[-2], highs[-1]
        l1, l2 = lows[-2], lows[-1]

        if h2["price"] > h1["price"] and l2["price"] > l1["price"]:
            structure["trend"] = "BULLISH"
            structure["bos"] = True
        elif h2["price"] < h1["price"] and l2["price"] < l1["price"]:
            structure["trend"] = "BEARISH"
            structure["bos"] = True

    return structure
