"""
UI layer — rich HTML-formatted messages and inline keyboards.
Keeps all visual/branding logic in one place so the bot stays
consistent and easy to re-skin.
"""
from telebot import types

from config import BOT_NAME, BOT_TAGLINE, ASSETS, DISPLAY_NAMES, CHART_TIMEFRAMES, EXPIRY_OPTIONS

DIRECTION_EMOJI = {"BUY": "🟢📈", "SELL": "🔴📉"}
CATEGORY_LABELS = {
    "forex_otc": "💱 Forex OTC",
    "forex_real": "💵 Forex Real",
    "crypto": "🪙 Crypto",
    "commodities": "🥇 Commodities",
    "indices": "📊 Indices",
}


def _bar(confidence: float, direction: str = None) -> str:
    """Render a colored visual confidence bar using direction-tinted blocks."""
    filled = round(confidence / 10)
    filled = max(0, min(10, filled))
    fill_emoji = "🟩" if direction == "BUY" else "🟥" if direction == "SELL" else "🟦"
    return fill_emoji * filled + "⬜" * (10 - filled)


def welcome_text(first_name: str) -> str:
    return (
        f"🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢\n"
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"🤖 <b>{BOT_NAME}</b>\n"
        f"<i>{BOT_TAGLINE}</i>\n"
        f"🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢🔵🟢\n\n"
        f"🧠 Smart Money Concepts + Multi-Indicator Confluence Engine\n"
        f"📸 Send any chart screenshot for instant AI vision analysis\n"
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
        types.InlineKeyboardButton("📸 Analyze Screenshot", callback_data="menu:vision_help"),
    )
    kb.add(
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
    kb.add(types.InlineKeyboardButton(
        "📸 Screenshot Analysis Settings", callback_data="menu:vision_settings"
    ))
    kb.add(types.InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:main"))
    return kb


def vision_settings_keyboard(user_settings: dict) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=3)
    tf = user_settings.get("chart_timeframe", "1m")
    exp = user_settings.get("expiry_minutes", 5)

    tf_buttons = [
        types.InlineKeyboardButton(
            f"✅ {t}" if t == tf else t, callback_data=f"vtf:{t}"
        )
        for t in CHART_TIMEFRAMES
    ]
    for i in range(0, len(tf_buttons), 3):
        kb.row(*tf_buttons[i:i + 3])

    exp_buttons = [
        types.InlineKeyboardButton(
            f"✅ {e}m" if e == exp else f"{e}m", callback_data=f"vexp:{e}"
        )
        for e in EXPIRY_OPTIONS
    ]
    for i in range(0, len(exp_buttons), 4):
        kb.row(*exp_buttons[i:i + 4])

    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu:settings"))
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
    conf = signal["confidence"]
    reasons = "\n".join(f"   ▫️ {r}" for r in signal["reasons"])
    otc_tag = " (OTC)" if is_otc else ""

    if direction == "BUY":
        top_strip = "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"
        direction_line = "🟢 <b>BUY / CALL</b> ⬆️"
    else:
        top_strip = "🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥"
        direction_line = "🔴 <b>SELL / PUT</b> ⬇️"

    return (
        f"{top_strip}\n"
        f"💎 <b>{name}{otc_tag}</b>\n"
        f"{top_strip}\n\n"
        f"📍 <b>Signal:</b> {direction_line}\n"
        f"💰 <b>Entry:</b> <code>{signal['entry_price']}</code>\n"
        f"⏱ <b>Expiry:</b> {signal['expiry_minutes']} min\n"
        f"📐 <b>Trend:</b> {signal['trend']}\n\n"
        f"🎯 <b>Confidence: {conf}%</b>\n"
        f"{_bar(conf, direction)}\n\n"
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


def vision_help_text(user_settings: dict) -> str:
    tf = user_settings.get("chart_timeframe", "1m")
    exp = user_settings.get("expiry_minutes", 5)
    return (
        f"📸 <b>Screenshot Chart Analysis</b>\n\n"
        f"Send me a screenshot of any trading chart (Quotex, TradingView, "
        f"MetaTrader — any platform) and I'll analyze the visible price "
        f"action and structure to generate a signal.\n\n"
        f"⚙️ <b>Your current settings:</b>\n"
        f"   📈 Chart timeframe: <b>{tf}</b>\n"
        f"   ⏱ Trade expiry: <b>{exp} min</b>\n\n"
        f"You can change these anytime in ⚙️ Preferences → Screenshot "
        f"Analysis Settings.\n\n"
        f"👉 <b>Just send the photo now to get your signal.</b>"
    )


def vision_analyzing_text() -> str:
    return "🔍 <b>Analyzing your chart...</b>\n\n⏳ Reading price action and structure..."


def format_vision_signal_caption(analysis: dict) -> str:
    direction = analysis.get("direction", "NEUTRAL")
    confidence = analysis.get("confidence", 0)
    trend = analysis.get("trend", "RANGING")
    asset_guess = analysis.get("asset_guess")
    key_obs = analysis.get("key_observation", "")
    reasons = analysis.get("reasons", [])
    risk_note = analysis.get("risk_note")
    tf = analysis.get("timeframe", "1m")
    exp = analysis.get("expiry_minutes", 5)

    if direction == "BUY":
        top_strip = "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"
        direction_line = "🟢 <b>BUY / CALL</b> ⬆️"
    elif direction == "SELL":
        top_strip = "🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥"
        direction_line = "🔴 <b>SELL / PUT</b> ⬇️"
    else:
        top_strip = "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜"
        direction_line = "⚪ <b>NO CLEAR SIGNAL</b>"

    asset_line = f"💎 <b>{asset_guess}</b>\n" if asset_guess else ""
    reasons_block = "\n".join(f"   ▫️ {r}" for r in reasons) if reasons else "   ▫️ No strong confluence detected"
    risk_block = f"\n\n⚠️ <i>{risk_note}</i>" if risk_note else ""

    return (
        f"{top_strip}\n"
        f"{asset_line}"
        f"📸 <b>Screenshot Analysis</b>\n"
        f"{top_strip}\n\n"
        f"📍 <b>Signal:</b> {direction_line}\n"
        f"📈 <b>Chart:</b> {tf}   ⏱ <b>Expiry:</b> {exp}m\n"
        f"📐 <b>Trend:</b> {trend}\n\n"
        f"🎯 <b>Confidence: {confidence}%</b>\n"
        f"{_bar(confidence, direction if direction != 'NEUTRAL' else None)}\n\n"
        f"👁 <b>Key Observation:</b>\n   {key_obs}\n\n"
        f"🧠 <b>Why:</b>\n{reasons_block}"
        f"{risk_block}\n\n"
        f"🤖 <i>{BOT_NAME}</i> · Vision Signal Engine"
    )


def about_text() -> str:
    return (
        f"ℹ️ <b>About {BOT_NAME}</b>\n\n"
        f"🧠 <b>Engine:</b> Smart Money Concepts (BOS/market structure) "
        f"fused with a multi-indicator confluence scorer — RSI, EMA stack, "
        f"MACD, Bollinger Bands, and Stochastic.\n\n"
        f"📡 <b>Coverage:</b> Forex (OTC + Real), Crypto, Commodities, Indices\n"
        f"📸 <b>Vision:</b> Send any chart screenshot for an instant AI-powered "
        f"read of the visible price action — no login or account access needed\n"
        f"⚡ <b>Uptime:</b> 24/7 via self-restarting automation\n"
        f"🎯 <b>Filter:</b> Only signals above your chosen confidence threshold "
        f"are ever sent to you\n\n"
        f"⚠️ <i>Trading involves risk. Signals are for educational purposes — "
        f"always manage your risk responsibly.</i>"
    )
