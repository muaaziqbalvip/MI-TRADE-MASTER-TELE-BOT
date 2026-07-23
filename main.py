"""
MI Trade Master — Main Runner
Runs the Telegram bot's polling loop and the background signal scanner
concurrently. Self-limits its own runtime (MAX_RUNTIME_MINUTES) so the
GitHub Actions workflow can cleanly restart it before hitting the job
time cap — giving effectively infinite 24/7 uptime.
"""
import logging
import sys
import threading
import time

import storage
from bot import bot
from config import BOT_TOKEN, MAX_RUNTIME_MINUTES
from scanner import run_scanner_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("mi.main")


def _polling_thread(stop_event):
    log.info("🤖 Telegram polling started")
    while not stop_event.is_set():
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as e:
            log.error(f"Polling crashed, restarting in 5s: {e}")
            time.sleep(5)
        if stop_event.is_set():
            break


def main():
    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN is not set. Configure it as a GitHub Actions secret.")
        sys.exit(1)

    storage.load_stats()  # ensures stats file + started_at exist

    stop_event = threading.Event()

    poll_thread = threading.Thread(target=_polling_thread, args=(stop_event,), daemon=True)
    scan_thread = threading.Thread(target=run_scanner_loop, args=(stop_event,), daemon=True)

    poll_thread.start()
    scan_thread.start()

    log.info(f"✅ MI Trade Master is LIVE — running for up to {MAX_RUNTIME_MINUTES} minutes this session")

    deadline = time.time() + (MAX_RUNTIME_MINUTES * 60)
    try:
        while time.time() < deadline:
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Interrupted by user")
    finally:
        log.info("⏳ Runtime limit reached — shutting down cleanly for scheduled restart")
        stop_event.set()
        try:
            bot.stop_polling()
        except Exception:
            pass
        time.sleep(2)
        log.info("👋 Session ended. GitHub Actions will restart automatically.")


if __name__ == "__main__":
    main()
