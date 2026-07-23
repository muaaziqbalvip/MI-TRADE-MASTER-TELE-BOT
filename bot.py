"""
MI Trade Master — Telegram Bot
All command / callback handlers live here. Uses pyTelegramBotAPI (telebot).
"""
import logging

import telebot
from telebot import types

import storage
import ui
from config import BOT_TOKEN, ASSETS, CONFIDENCE_THRESHOLD
from engine import generate_signal
from fetcher import fetch_candles

log = logging.getLogger("mi.bot")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# ---------------------------------------------------------------------------
# /start & main menu
# ---------------------------------------------------------------------------
@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name or "Trader"
    storage.add_subscriber(chat_id, message.from_user.username or "")
    subs = storage.active_subscriber_ids()
    bot.send_message(
        chat_id,
        ui.welcome_text(first_name),
        reply_markup=ui.main_menu_keyboard(str(chat_id) in subs),
    )


@bot.message_handler(commands=["menu"])
def handle_menu(message):
    _show_main_menu(message.chat.id)


def _show_main_menu(chat_id, message_id=None):
    subs = storage.active_subscriber_ids()
    is_sub = str(chat_id) in subs
    text = f"🤖 <b>Main Menu</b>\n\nChoose an option below 👇"
    kb = ui.main_menu_keyboard(is_sub)
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)


# ---------------------------------------------------------------------------
# Callback router
# ---------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    try:
        if data == "noop":
            bot.answer_callback_query(call.id)
            return

        if data == "sub:on":
            storage.add_subscriber(chat_id, call.from_user.username or "")
            bot.answer_callback_query(call.id, "🔔 Subscribed! You'll get live signals.")
            _show_main_menu(chat_id, msg_id)

        elif data == "sub:off":
            storage.remove_subscriber(chat_id)
            bot.answer_callback_query(call.id, "🔕 Unsubscribed.")
            _show_main_menu(chat_id, msg_id)

        elif data == "menu:main":
            bot.answer_callback_query(call.id)
            _show_main_menu(chat_id, msg_id)

        elif data == "menu:settings":
            bot.answer_callback_query(call.id)
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                "⚙️ <b>Your Preferences</b>\n\nToggle asset categories and set your "
                "minimum confidence threshold. Only signals matching these will "
                "be sent to you.",
                chat_id, msg_id,
                reply_markup=ui.settings_keyboard(settings),
            )

        elif data.startswith("cat:"):
            category = data.split(":", 1)[1]
            storage.toggle_category(chat_id, category)
            bot.answer_callback_query(call.id, "Updated ✅")
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                "⚙️ <b>Your Preferences</b>\n\nToggle asset categories and set your "
                "minimum confidence threshold.",
                chat_id, msg_id,
                reply_markup=ui.settings_keyboard(settings),
            )

        elif data.startswith("conf:"):
            direction = data.split(":", 1)[1]
            settings = storage.get_user_settings(chat_id)
            conf = settings.get("min_confidence", 82)
            conf = conf + 3 if direction == "up" else conf - 3
            conf = max(60, min(98, conf))
            storage.update_user_settings(chat_id, min_confidence=conf)
            bot.answer_callback_query(call.id, f"Set to {conf}%")
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                "⚙️ <b>Your Preferences</b>\n\nToggle asset categories and set your "
                "minimum confidence threshold.",
                chat_id, msg_id,
                reply_markup=ui.settings_keyboard(settings),
            )

        elif data == "menu:stats":
            bot.answer_callback_query(call.id)
            stats = storage.load_stats()
            sub_count = len(storage.active_subscriber_ids())
            bot.edit_message_text(
                ui.stats_text(stats, sub_count),
                chat_id, msg_id,
                reply_markup=ui.back_keyboard(),
            )

        elif data == "menu:about":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                ui.about_text(), chat_id, msg_id,
                reply_markup=ui.back_keyboard(),
            )

        elif data == "menu:live":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "🎯 <b>Get a Live Signal</b>\n\nPick a category, then an asset, "
                "and I'll analyze it right now.",
                chat_id, msg_id,
                reply_markup=ui.live_menu_keyboard(),
            )

        elif data.startswith("catlive:"):
            category = data.split(":", 1)[1]
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                f"📂 <b>{ui.CATEGORY_LABELS.get(category, category)}</b>\n\nSelect an asset:",
                chat_id, msg_id,
                reply_markup=ui.category_asset_keyboard(category),
            )

        elif data.startswith("pick:"):
            symbol = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, "🔍 Analyzing...")
            bot.send_chat_action(chat_id, "typing")
            bot.edit_message_text(
                f"🔍 <b>Analyzing {symbol}...</b>\n\n⏳ Fetching live market data...",
                chat_id, msg_id,
            )
            _run_live_analysis(chat_id, msg_id, symbol)

        else:
            bot.answer_callback_query(call.id)

    except Exception as e:
        log.error(f"Callback error: {e}")
        try:
            bot.answer_callback_query(call.id, "⚠️ Something went wrong, try again.")
        except Exception:
            pass


def _run_live_analysis(chat_id, msg_id, symbol):
    is_otc = symbol in ASSETS.get("forex_otc", [])
    df = fetch_candles(symbol)

    if df is None:
        bot.edit_message_text(
            f"⚠️ <b>Couldn't fetch data for {symbol}.</b>\n\nTry again in a moment.",
            chat_id, msg_id,
            reply_markup=ui.back_keyboard("menu:live"),
        )
        return

    signal = generate_signal(symbol, df, is_otc=is_otc)

    if not signal:
        bot.edit_message_text(
            f"⚪ <b>{symbol}</b>\n\nNo high-confidence setup right now — "
            f"market conditions are unclear. Check back shortly.",
            chat_id, msg_id,
            reply_markup=ui.back_keyboard("menu:live"),
        )
        return

    storage.record_signal(symbol, signal["direction"])
    bot.edit_message_text(
        ui.format_signal_card(signal, is_otc=is_otc),
        chat_id, msg_id,
        reply_markup=ui.back_keyboard("menu:live"),
    )


# ---------------------------------------------------------------------------
# Fallback text handler
# ---------------------------------------------------------------------------
@bot.message_handler(func=lambda m: True)
def handle_fallback(message):
    _show_main_menu(message.chat.id)
