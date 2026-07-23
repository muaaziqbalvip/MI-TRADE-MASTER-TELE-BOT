"""
MI Trade Master — Telegram Bot
All command / callback handlers live here. Uses pyTelegramBotAPI (telebot).
"""
import logging

import telebot
from telebot import types

import storage
import ui
import diagnostics
from config import BOT_TOKEN, ASSETS, CONFIDENCE_THRESHOLD, ADMIN_CHAT_IDS
from engine import generate_signal
from fetcher import fetch_candles
from vision import analyze_chart_image
from chartgen import render_signal_chart

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


@bot.message_handler(commands=["logs"])
def handle_logs(message):
    chat_id = message.chat.id
    if ADMIN_CHAT_IDS and str(chat_id) not in ADMIN_CHAT_IDS:
        bot.send_message(chat_id, "🔒 This command is restricted to bot admins.")
        return
    bot.send_message(chat_id, diagnostics.format_logs_text(30))


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

        elif data == "menu:vision_help":
            bot.answer_callback_query(call.id)
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                ui.vision_help_text(settings),
                chat_id, msg_id,
                reply_markup=ui.back_keyboard(),
            )

        elif data == "menu:vision_settings":
            bot.answer_callback_query(call.id)
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                "📸 <b>Screenshot Analysis Settings</b>\n\n"
                "Set the chart timeframe you'll typically screenshot, and "
                "your preferred trade expiry duration. These apply to every "
                "screenshot you send.",
                chat_id, msg_id,
                reply_markup=ui.vision_settings_keyboard(settings),
            )

        elif data.startswith("vtf:"):
            timeframe = data.split(":", 1)[1]
            storage.update_user_settings(chat_id, chart_timeframe=timeframe)
            bot.answer_callback_query(call.id, f"Chart timeframe set to {timeframe}")
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                "📸 <b>Screenshot Analysis Settings</b>\n\n"
                "Set the chart timeframe you'll typically screenshot, and "
                "your preferred trade expiry duration.",
                chat_id, msg_id,
                reply_markup=ui.vision_settings_keyboard(settings),
            )

        elif data.startswith("vexp:"):
            expiry = int(data.split(":", 1)[1])
            storage.update_user_settings(chat_id, expiry_minutes=expiry)
            bot.answer_callback_query(call.id, f"Expiry set to {expiry} min")
            settings = storage.get_user_settings(chat_id)
            bot.edit_message_text(
                "📸 <b>Screenshot Analysis Settings</b>\n\n"
                "Set the chart timeframe you'll typically screenshot, and "
                "your preferred trade expiry duration.",
                chat_id, msg_id,
                reply_markup=ui.vision_settings_keyboard(settings),
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
            kb = ui.back_keyboard()
            kb.add(types.InlineKeyboardButton("🩺 System Health", callback_data="menu:health"))
            bot.edit_message_text(
                ui.about_text(), chat_id, msg_id,
                reply_markup=kb,
            )

        elif data == "menu:health":
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                ui.system_health_text(), chat_id, msg_id,
                reply_markup=ui.back_keyboard("menu:about"),
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
        name = symbol
        bot.edit_message_text(
            f"⚠️ <b>{name} data unavailable right now</b>\n\n"
            f"This can happen when the market is closed/thinly traded "
            f"(common for commodities, indices, and some OTC pairs off-hours) "
            f"or Yahoo Finance is briefly rate-limiting.\n\n"
            f"👉 Try a Forex or Crypto pair instead, or retry in a minute.",
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
# Screenshot chart analysis (photo upload)
# ---------------------------------------------------------------------------
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name or "unknown"
    settings = storage.get_user_settings(chat_id)
    timeframe = settings.get("chart_timeframe", "1m")
    expiry = settings.get("expiry_minutes", 5)

    log.info(f"📸 [{chat_id}/{username}] Screenshot received — tf={timeframe} expiry={expiry}m")

    status_msg = bot.send_message(chat_id, ui.vision_analyzing_text())
    bot.send_chat_action(chat_id, "upload_photo")

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        image_bytes = bot.download_file(file_info.file_path)
        log.info(f"📥 [{chat_id}] Image downloaded — {len(image_bytes)} bytes")
    except Exception as e:
        log.error(f"❌ [{chat_id}] Failed to download photo from Telegram: {e}")
        bot.edit_message_text(
            "⚠️ <b>Couldn't download that image from Telegram.</b>\n\nPlease try sending it again.",
            chat_id, status_msg.message_id,
            reply_markup=ui.back_keyboard(),
        )
        return

    analysis, error_code, error_detail = analyze_chart_image(image_bytes, timeframe, expiry)

    if error_code:
        log.error(f"❌ [{chat_id}] Vision analysis failed — code={error_code} detail={error_detail}")
        if error_code in ("no_api_key", "auth_failed"):
            diagnostics.record(
                "ERROR",
                f"Vision analysis blocked: {error_code} — {error_detail}",
                notify_admin=True,
            )
        bot.edit_message_text(
            ui.vision_error_text(error_code, error_detail),
            chat_id, status_msg.message_id,
            reply_markup=ui.back_keyboard(),
            disable_web_page_preview=True,
        )
        return

    log.info(
        f"✅ [{chat_id}] Vision analysis OK — direction={analysis['direction']} "
        f"confidence={analysis['confidence']}% trend={analysis['trend']}"
    )

    try:
        chart_png = render_signal_chart(analysis, symbol_label=analysis.get("asset_guess") or "Your Chart")
        log.info(f"🖼️ [{chat_id}] Chart image rendered — {len(chart_png)} bytes")
    except Exception as e:
        log.error(f"❌ [{chat_id}] Chart rendering failed: {e}")
        # Analysis succeeded even though rendering failed — still give the user the text result
        bot.edit_message_text(
            ui.format_vision_signal_caption(analysis) +
            "\n\n⚠️ <i>(Chart image rendering failed — showing text result only)</i>",
            chat_id, status_msg.message_id,
            reply_markup=ui.back_keyboard(),
        )
        return

    try:
        bot.delete_message(chat_id, status_msg.message_id)
        bot.send_photo(
            chat_id,
            chart_png,
            caption=ui.format_vision_signal_caption(analysis),
            reply_markup=ui.back_keyboard(),
        )
        log.info(f"📤 [{chat_id}] Signal chart sent successfully")
    except Exception as e:
        log.error(f"❌ [{chat_id}] Failed to send result photo: {e}")
        bot.send_message(
            chat_id,
            ui.format_vision_signal_caption(analysis),
            reply_markup=ui.back_keyboard(),
        )


# ---------------------------------------------------------------------------
# Fallback text handler
# ---------------------------------------------------------------------------
@bot.message_handler(func=lambda m: True)
def handle_fallback(message):
    _show_main_menu(message.chat.id)
