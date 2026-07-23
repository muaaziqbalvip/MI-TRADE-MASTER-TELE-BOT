"""
MI Trade Master — Branding Setup
Programmatically applies the bot's profile photo, description, and
short description using Telegram's Bot API (setMyProfilePhoto,
setMyDescription, setMyShortDescription). Runs once automatically at
startup (main.py calls this) and is safe to re-run — Telegram simply
overwrites with the same values if nothing changed.
"""
import logging
import os

import requests

from config import BOT_TOKEN, BOT_NAME, BOT_TAGLINE

log = logging.getLogger("mi.branding")

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_ICON_PATH = os.path.join(_ASSETS_DIR, "bot_icon.jpg")

_API_BASE = "https://api.telegram.org/bot{token}/{method}"

_DESCRIPTION = (
    "🤖 MI Trade Master — Smart Money Signal Engine\n\n"
    "📡 Forex OTC/Real, Crypto, Commodities & Indices\n"
    "🧠 SMC/ICT market structure + multi-indicator confluence scoring\n"
    "📸 Send a chart screenshot for instant AI vision analysis\n"
    "⚡ Live 24/7 automated scanning\n"
    "🎯 Only high-confidence setups reach you\n\n"
    "⚠️ Educational tool — not financial advice. Trade responsibly."
)

_SHORT_DESCRIPTION = "🎯 Pro-level SMC/ICT trading signals — Forex, Crypto, Commodities. Live 24/7."


def _call(method: str, data: dict):
    url = _API_BASE.format(token=BOT_TOKEN, method=method)
    try:
        r = requests.post(url, json=data, timeout=15)
        result = r.json()
        if not result.get("ok"):
            log.warning(f"{method} failed: {result.get('description')}")
        return result
    except Exception as e:
        log.warning(f"{method} request failed: {e}")
        return None


def apply_branding():
    """Set profile photo + descriptions. Safe to call on every startup."""
    if not BOT_TOKEN:
        return

    # --- Profile photo ---
    # Telegram's InputProfilePhotoStatic expects: {"type":"static","photo":"attach://<field_name>"}
    # where <field_name> is the multipart field carrying the actual file bytes.
    if os.path.exists(_ICON_PATH):
        try:
            url = _API_BASE.format(token=BOT_TOKEN, method="setMyProfilePhoto")
            with open(_ICON_PATH, "rb") as f:
                files = {"bot_icon": ("bot_icon.jpg", f, "image/jpeg")}
                data = {"photo": '{"type":"static","photo":"attach://bot_icon"}'}
                r = requests.post(url, data=data, files=files, timeout=15)
            result = r.json()
            if result.get("ok"):
                log.info("✅ Bot profile photo set")
            else:
                log.warning(f"setMyProfilePhoto failed: {result.get('description')}")
        except Exception as e:
            log.warning(f"Could not set profile photo: {e}")
    else:
        log.info("ℹ️ No bot_icon.jpg found in assets/ — skipping profile photo setup")

    # --- Descriptions ---
    _call("setMyName", {"name": BOT_NAME})
    _call("setMyDescription", {"description": _DESCRIPTION})
    _call("setMyShortDescription", {"short_description": _SHORT_DESCRIPTION})
    log.info("✅ Bot name/description synced")
