"""
Chart image renderer — builds a clean, professional-looking synthetic
candlestick chart with a BUY/SELL signal overlay, based on the vision
model's read of the user's uploaded screenshot. This is a fresh
illustrative chart (not a crop of the user's image), branded and
styled consistently with the bot.
"""
import io
import logging
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

log = logging.getLogger("mi.chartgen")

_UP_COLOR = "#26a69a"
_DOWN_COLOR = "#ef5350"
_BG_COLOR = "#0e1117"
_GRID_COLOR = "#2a2e39"
_TEXT_COLOR = "#e0e0e0"


def _synthesize_candles(direction: str, trend: str, n: int = 40, seed: int | None = None):
    """
    Generate a plausible-looking candle sequence that visually matches
    the analyzed trend/direction, purely for illustrative rendering —
    not real market data (the real analysis already happened via vision).

    The overall path is guaranteed to move in the signal's direction so
    the chart never visually contradicts the signal it's illustrating;
    randomness is layered on top only for natural-looking wick/body noise.
    """
    rng = random.Random(seed)
    base = 100.0
    candles = []
    price = base

    if trend == "BULLISH":
        bias = 0.45
    elif trend == "BEARISH":
        bias = -0.45
    else:
        bias = 0.0

    for i in range(n):
        local_bias = bias
        # Stronger, deterministic push in the final stretch so the chart
        # clearly leads into the signal arrow in the right direction.
        if i > n - 8:
            if direction == "BUY":
                local_bias = max(local_bias, 0.55)
            elif direction == "SELL":
                local_bias = min(local_bias, -0.55)

        noise = rng.gauss(0, 0.35)  # small wobble only, bias dominates
        change = local_bias + noise
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.gauss(0.25, 0.15))
        low_p = min(open_p, close_p) - abs(rng.gauss(0.25, 0.15))
        candles.append((open_p, high_p, low_p, close_p))
        price = close_p

    return candles


def render_signal_chart(analysis: dict, symbol_label: str = "Live Chart") -> bytes:
    """
    Render a branded candlestick chart with signal overlay.
    Returns PNG bytes ready to send as a Telegram photo.
    """
    direction = analysis.get("direction", "NEUTRAL")
    confidence = analysis.get("confidence", 0)
    trend = analysis.get("trend", "RANGING")
    timeframe = analysis.get("timeframe", "1m")
    expiry = analysis.get("expiry_minutes", 5)

    candles = _synthesize_candles(direction, trend, n=40)

    fig, ax = plt.subplots(figsize=(9, 6), dpi=160)
    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_BG_COLOR)

    for i, (o, h, l, c) in enumerate(candles):
        color = _UP_COLOR if c >= o else _DOWN_COLOR
        ax.plot([i, i], [l, h], color=color, linewidth=1, zorder=2)
        body_bottom = min(o, c)
        body_height = max(abs(c - o), 0.05)
        ax.add_patch(mpatches.Rectangle(
            (i - 0.3, body_bottom), 0.6, body_height,
            facecolor=color, edgecolor=color, zorder=3,
        ))

    # Signal arrow at the end of the sequence
    last_close = candles[-1][3]
    arrow_x = len(candles) - 1
    if direction == "BUY":
        ax.annotate(
            "", xy=(arrow_x + 2.2, last_close + 2.5), xytext=(arrow_x, last_close),
            arrowprops=dict(arrowstyle="-|>", color=_UP_COLOR, lw=3, mutation_scale=25),
            zorder=5,
        )
        signal_color = _UP_COLOR
        signal_text = "🟢 BUY / CALL"
    elif direction == "SELL":
        ax.annotate(
            "", xy=(arrow_x + 2.2, last_close - 2.5), xytext=(arrow_x, last_close),
            arrowprops=dict(arrowstyle="-|>", color=_DOWN_COLOR, lw=3, mutation_scale=25),
            zorder=5,
        )
        signal_color = _DOWN_COLOR
        signal_text = "🔴 SELL / PUT"
    else:
        signal_color = "#9e9e9e"
        signal_text = "⚪ NEUTRAL"

    ax.axhline(y=last_close, color="#555b66", linestyle="--", linewidth=0.8, zorder=1)

    ax.set_xlim(-1, len(candles) + 3)
    ax.grid(True, color=_GRID_COLOR, linewidth=0.5, alpha=0.6)
    ax.set_xticks([])
    ax.tick_params(colors=_TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_color(_GRID_COLOR)

    ax.set_title(
        f"{symbol_label}  •  {timeframe} chart  •  {expiry}m expiry",
        color=_TEXT_COLOR, fontsize=13, fontweight="bold", loc="left", pad=14,
    )

    # Signal badge box (top-right)
    ax.text(
        0.98, 0.95, f"{signal_text}\nConfidence: {confidence}%",
        transform=ax.transAxes, fontsize=13, fontweight="bold",
        color="white", ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor=signal_color, edgecolor="none", alpha=0.9),
        zorder=10,
    )

    # Watermark / branding footer
    fig.text(
        0.02, 0.02, "MI Trade Master — Vision Signal Engine",
        color="#6b7280", fontsize=9, style="italic",
    )

    fig.tight_layout(rect=[0, 0.03, 1, 1])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=_BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
