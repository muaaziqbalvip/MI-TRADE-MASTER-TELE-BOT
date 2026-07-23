"""
Background signal scanner — runs on its own thread, continuously scans
all configured assets, and pushes high-confidence signals to subscribers
whose preferences match.
"""
import logging
import time
from datetime import datetime, timezone

import storage
import ui
from bot import bot
from config import (
    ASSETS, MAX_SIGNALS_PER_CYCLE, SIGNAL_SCAN_INTERVAL,
)
from engine import generate_signal
from fetcher import fetch_candles

log = logging.getLogger("mi.scanner")

_ALL_SYMBOLS = []
for _cat, _syms in ASSETS.items():
    for _s in _syms:
        if (_cat, _s) not in _ALL_SYMBOLS:
            _ALL_SYMBOLS.append((_cat, _s))

_last_sent = {}  # symbol -> timestamp, to avoid duplicate spam on the same setup
_COOLDOWN_SECONDS = 240


def _symbol_category(symbol: str) -> str:
    for cat, syms in ASSETS.items():
        if symbol in syms:
            return cat
    return "forex_real"


def scan_once():
    """Run a single scan cycle across all assets, broadcast qualifying signals."""
    sent_this_cycle = 0
    now = time.time()

    for category, symbol in _ALL_SYMBOLS:
        if sent_this_cycle >= MAX_SIGNALS_PER_CYCLE:
            break

        if now - _last_sent.get(symbol, 0) < _COOLDOWN_SECONDS:
            continue

        try:
            is_otc = category == "forex_otc"
            df = fetch_candles(symbol)
            if df is None:
                continue

            signal = generate_signal(symbol, df, is_otc=is_otc)
            if not signal:
                continue

            _broadcast(signal, category, is_otc)
            _last_sent[symbol] = now
            sent_this_cycle += 1

        except Exception as e:
            log.error(f"Scan error for {symbol}: {e}")

    return sent_this_cycle


def _broadcast(signal: dict, category: str, is_otc: bool):
    confidence = signal["confidence"]
    card = ui.format_signal_card(signal, is_otc=is_otc)
    subscriber_ids = storage.active_subscriber_ids()

    sent_count = 0
    for chat_id in subscriber_ids:
        settings = storage.get_user_settings(chat_id)
        if category not in settings.get("categories", []):
            continue
        if confidence < settings.get("min_confidence", 82):
            continue
        try:
            bot.send_message(chat_id, card)
            sent_count += 1
        except Exception as e:
            log.warning(f"Failed to send to {chat_id}: {e}")

    if sent_count > 0:
        storage.record_signal(signal["symbol"], signal["direction"])
        log.info(
            f"📡 Broadcast {signal['symbol']} {signal['direction']} "
            f"({confidence}%) to {sent_count} subscribers"
        )


def run_scanner_loop(stop_event):
    """Continuously scan until stop_event is set (used by the runtime guard)."""
    log.info("🔍 Signal scanner started")
    while not stop_event.is_set():
        cycle_start = time.time()
        try:
            sent = scan_once()
            if sent:
                log.info(f"Cycle complete — {sent} signal(s) broadcast")
        except Exception as e:
            log.error(f"Scanner cycle failed: {e}")

        elapsed = time.time() - cycle_start
        sleep_for = max(5, SIGNAL_SCAN_INTERVAL - elapsed)
        stop_event.wait(sleep_for)

    log.info("🛑 Signal scanner stopped")
