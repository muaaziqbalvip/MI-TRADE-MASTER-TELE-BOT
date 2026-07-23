"""
MI Trade Master — Signal Engine
Combines Smart Money Concepts (market structure / BOS) with a
multi-indicator confluence scorer to produce high-confidence signals.
"""
import logging
from datetime import datetime, timezone

from indicators import add_indicators, market_structure

log = logging.getLogger("mi.engine")


def _score_confluence(latest, structure) -> tuple[str | None, float, list[str]]:
    """Score BUY vs SELL using indicator confluence. Returns (direction, score, reasons)."""
    buy_score = 0.0
    sell_score = 0.0
    buy_reasons = []
    sell_reasons = []

    # --- Market structure (SMC/ICT) — heaviest weight ---
    if structure["trend"] == "BULLISH":
        buy_score += 30
        buy_reasons.append("Bullish market structure (HH/HL)")
        if structure["bos"]:
            buy_score += 10
            buy_reasons.append("Break of Structure confirmed")
    elif structure["trend"] == "BEARISH":
        sell_score += 30
        sell_reasons.append("Bearish market structure (LH/LL)")
        if structure["bos"]:
            sell_score += 10
            sell_reasons.append("Break of Structure confirmed")

    # --- RSI ---
    rsi = latest["RSI"]
    if rsi < 30:
        buy_score += 15
        buy_reasons.append(f"RSI oversold ({rsi:.1f})")
    elif rsi > 70:
        sell_score += 15
        sell_reasons.append(f"RSI overbought ({rsi:.1f})")
    elif rsi < 45:
        buy_score += 5
    elif rsi > 55:
        sell_score += 5

    # --- EMA trend alignment ---
    if latest["Close"] > latest["EMA_21"] > latest["EMA_50"]:
        buy_score += 12
        buy_reasons.append("Price above EMA21/EMA50 stack")
    elif latest["Close"] < latest["EMA_21"] < latest["EMA_50"]:
        sell_score += 12
        sell_reasons.append("Price below EMA21/EMA50 stack")

    # --- MACD ---
    if latest["MACD"] > latest["MACD_signal"] and latest["MACD_hist"] > 0:
        buy_score += 12
        buy_reasons.append("MACD bullish crossover")
    elif latest["MACD"] < latest["MACD_signal"] and latest["MACD_hist"] < 0:
        sell_score += 12
        sell_reasons.append("MACD bearish crossover")

    # --- Bollinger Bands (mean reversion at extremes) ---
    if latest["Close"] <= latest["BB_lower"]:
        buy_score += 10
        buy_reasons.append("Price at lower Bollinger Band")
    elif latest["Close"] >= latest["BB_upper"]:
        sell_score += 10
        sell_reasons.append("Price at upper Bollinger Band")

    # --- Stochastic ---
    if latest["Stoch_K"] < 20 and latest["Stoch_K"] > latest["Stoch_D"]:
        buy_score += 8
        buy_reasons.append("Stochastic bullish cross (oversold)")
    elif latest["Stoch_K"] > 80 and latest["Stoch_K"] < latest["Stoch_D"]:
        sell_score += 8
        sell_reasons.append("Stochastic bearish cross (overbought)")

    total = buy_score + sell_score
    if total == 0:
        return None, 0.0, []

    if buy_score > sell_score:
        confidence = 50 + min((buy_score / (buy_score + sell_score + 1e-9)) * 50, 49.9)
        return "BUY", round(min(confidence, 98.5), 1), buy_reasons
    elif sell_score > buy_score:
        confidence = 50 + min((sell_score / (buy_score + sell_score + 1e-9)) * 50, 49.9)
        return "SELL", round(min(confidence, 98.5), 1), sell_reasons

    return None, 0.0, []


def determine_expiry(volatility: float, is_otc: bool) -> int:
    """Suggest an expiry (minutes) based on recent volatility."""
    if volatility is None or volatility != volatility:  # NaN check
        volatility = 0.01

    if is_otc:
        options = [1, 2, 3, 5]
    else:
        options = [5, 10, 15]

    if volatility > 0.004:
        return options[0]
    elif volatility > 0.002:
        return options[min(1, len(options) - 1)]
    else:
        return options[-1]


def generate_signal(internal_symbol: str, df, is_otc: bool = False) -> dict | None:
    """
    Run the full pipeline on a raw OHLCV DataFrame and return a signal dict,
    or None if no high-confidence setup is present.
    """
    if df is None or len(df) < 60:
        return None

    try:
        df = add_indicators(df)
        latest = df.iloc[-1]
        if latest[["RSI", "EMA_21", "MACD", "BB_upper"]].isna().any():
            return None

        structure = market_structure(df)
        direction, confidence, reasons = _score_confluence(latest, structure)

        if not direction:
            return None

        volatility = float(latest["Volatility"]) if latest["Volatility"] == latest["Volatility"] else 0.01
        expiry = determine_expiry(volatility, is_otc)

        return {
            "symbol": internal_symbol,
            "direction": direction,
            "confidence": confidence,
            "entry_price": round(float(latest["Close"]), 6),
            "expiry_minutes": expiry,
            "reasons": reasons[:4],
            "trend": structure["trend"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        log.error(f"Signal generation failed for {internal_symbol}: {e}")
        return None
