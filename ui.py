"""
UI layer — rich HTML-formatted messages and inline keyboards.
Keeps all visual/branding logic in one place so the bot stays
consistent and easy to re-skin.
"""
from telebot import types

from config import BOT_NAME, BOT_TAGLINE, ASSETS, DISPLAY_NAMES

DIRECTION_EMOJI = {"BUY": "🟢📈", "SELL": "🔴📉"}
CATEGORY_LABELS = {
    "forex_otc": "💱 Forex OTC",
    "forex_real": "💵 Forex Real",
    "crypto": "🪙 Crypto",
    "commodities": "🥇 Commodities",
    "indices": "📊 Indices",
}


def _bar(confidence: float) -> str:
    """Render a small visual confidence bar, e.g. ▰▰▰▰▰▰▰▰▱▱ 84%"""
    filled = round(confidence / 10)
    filled = max(0, min(10, filled))
    return "▰" * filled + "▱" * (10 - filled)


def welcome_text(first_name: str) -> str:
    return (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"🤖 <b>{BOT_NAME}</b>\n"
        f"<i>{BOT_TAGLINE}</i>\n\n"
        f"🔵🟢 Smart Money Concepts + Multi-Indicator Confluence Engine\n"
        f"⚡ Live signals scanned every minute, 24/7\n"
        f"🎯 Only high-confidence setups get broadcast\n\n"
        f"Use the buttons below to get started 👇"
    )


def main_menu_keyboard(is_subscribed: bool) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    if is_subscribed:
        kb.add(
            types.InlineKeyboardButton("🔕 Unsubscribe", callback_data="sub:off"),
        )
    else:
        kb.add(
            types.InlineKeyboardButton("🔔 Subscribe to Signals", callback_data="sub:on"),
        )
    kb.add(
        types.InlineKeyboardButton("⚙️ Preferences", callback_data="menu:settings"),
        types.InlineKeyboardButton("📊 Stats", callback_data="menu:stats"),
    )
    kb.add(
        types.InlineKeyboardButton("🎯 Get Signal Now", callback_data="menu:live"),
        types.InlineKeyboardButton("ℹ️ About", callback_data="menu:about"),
    )
    return kb


def settings_keyboard(user_settings: dict) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    active = set(user_settings.get("categories", []))
    for key, label in CATEGORY_LABELS.items():
        mark = "✅" if key in active else "▫️"
        kb.add(types.InlineKeyboardButton(f"{mark} {label}", callback_data=f"cat:{key}"))

    conf = user_settings.get("min_confidence", 82)
    kb.add(
        types.InlineKeyboardButton("➖", callback_data="conf:down"),
        types.InlineKeyboardButton(f"🎯 Min Confidence: {conf}%", callback_data="noop"),
        types.InlineKeyboardButton("➕", callback_data="conf:up"),
    )
    kb.add(types.InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:main"))
    return kb


def category_asset_keyboard(category: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=3)
    symbols = ASSETS.get(category, [])
    buttons = [
        types.InlineKeyboardButton(DISPLAY_NAMES.get(s, s), callback_data=f"pick:{s}")
        for s in symbols
    ]
    for i in range(0, len(buttons), 3):
        kb.row(*buttons[i:i + 3])
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu:live"))
    return kb


def live_menu_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(label, callback_data=f"catlive:{key}")
        for key, label in CATEGORY_LABELS.items()
    ]
    for i in range(0, len(buttons), 2):
        kb.row(*buttons[i:i + 2])
    kb.add(types.InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:main"))
    return kb


def back_keyboard(target: str = "menu:main") -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=target))
    return kb


def format_signal_card(signal: dict, is_otc: bool = False) -> str:
    symbol = signal["symbol"]
    name = DISPLAY_NAMES.get(symbol, symbol)
    direction = signal["direction"]
    emoji = DIRECTION_EMOJI.get(direction, "⚪")
    conf = signal["confidence"]
    reasons = "\n".join(f"   ▫️ {r}" for r in signal["reasons"])
    otc_tag = " (OTC)" if is_otc else ""

    return (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{emoji} <b>{name}{otc_tag}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 <b>Signal:</b> {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}\n"
        f"💰 <b>Entry:</b> <code>{signal['entry_price']}</code>\n"
        f"⏱ <b>Expiry:</b> {signal['expiry_minutes']} min\n"
        f"📐 <b>Trend:</b> {signal['trend']}\n\n"
        f"🎯 <b>Confidence: {conf}%</b>\n"
        f"{_bar(conf)}\n\n"
        f"🧠 <b>Why:</b>\n{reasons}\n\n"
        f"🤖 <i>{BOT_NAME}</i> · #{symbol}"
    )


def stats_text(stats: dict, subscriber_count: int) -> str:
    total = stats.get("total_signals", 0)
    buys = stats.get("by_direction", {}).get("BUY", 0)
    sells = stats.get("by_direction", {}).get("SELL", 0)
    top_symbols = sorted(
        stats.get("by_symbol", {}).items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_lines = "\n".join(
        f"   {i+1}. {DISPLAY_NAMES.get(sym, sym)} — {count} signals"
        for i, (sym, count) in enumerate(top_symbols)
    ) or "   No signals yet"

    return (
        f"📊 <b>{BOT_NAME} — Live Stats</b>\n\n"
        f"📡 Total signals sent: <b>{total}</b>\n"
        f"🟢 BUY: <b>{buys}</b>   🔴 SELL: <b>{sells}</b>\n"
        f"👥 Active subscribers: <b>{subscriber_count}</b>\n\n"
        f"🏆 <b>Top Assets:</b>\n{top_lines}\n\n"
        f"🕐 Since: {stats.get('started_at', 'N/A')[:16].replace('T', ' ')} UTC"
    )


def about_text() -> str:
    return (
        f"ℹ️ <b>About {BOT_NAME}</b>\n\n"
        f"🧠 <b>Engine:</b> Smart Money Concepts (BOS/market structure) "
        f"fused with a multi-indicator confluence scorer — RSI, EMA stack, "
        f"MACD, Bollinger Bands, and Stochastic.\n\n"
        f"📡 <b>Coverage:</b> Forex (OTC + Real), Crypto, Commodities, Indices\n"
        f"⚡ <b>Uptime:</b> 24/7 via self-restarting automation\n"
        f"🎯 <b>Filter:</b> Only signals above your chosen confidence threshold "
        f"are ever sent to you\n\n"
        f"⚠️ <i>Trading involves risk. Signals are for educational purposes — "
        f"always manage your risk responsibly.</i>"
    )
