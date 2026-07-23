"""
Lightweight JSON-file persistence — no database server needed.
Files live in data/ and get committed back to the repo by the
GitHub Actions workflow, so state survives across job restarts.
"""
import json
import logging
import os
import threading
from datetime import datetime, timezone

from config import SUBSCRIBERS_FILE, STATS_FILE, SETTINGS_FILE, DATA_DIR

log = logging.getLogger("mi.storage")
_lock = threading.Lock()


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load(path: str, default):
    _ensure_dir()
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Failed to load {path}: {e}")
        return default


def _save(path: str, data):
    _ensure_dir()
    with _lock:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------
def load_subscribers() -> dict:
    return _load(SUBSCRIBERS_FILE, {})


def add_subscriber(chat_id: str, username: str = ""):
    subs = load_subscribers()
    chat_id = str(chat_id)
    if chat_id not in subs:
        subs[chat_id] = {
            "username": username,
            "joined_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }
    else:
        subs[chat_id]["active"] = True
    _save(SUBSCRIBERS_FILE, subs)


def remove_subscriber(chat_id: str):
    subs = load_subscribers()
    chat_id = str(chat_id)
    if chat_id in subs:
        subs[chat_id]["active"] = False
        _save(SUBSCRIBERS_FILE, subs)


def active_subscriber_ids() -> list:
    subs = load_subscribers()
    return [cid for cid, meta in subs.items() if meta.get("active")]


# ---------------------------------------------------------------------------
# Per-user settings (category filters, min confidence, market type)
# ---------------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "categories": ["forex_otc", "crypto"],
    "min_confidence": 82,
    "chart_timeframe": "1m",
    "expiry_minutes": 5,
}


def load_settings() -> dict:
    return _load(SETTINGS_FILE, {})


def get_user_settings(chat_id: str) -> dict:
    settings = load_settings()
    stored = settings.get(str(chat_id), {})
    merged = dict(DEFAULT_SETTINGS)
    merged.update(stored)
    return merged


def update_user_settings(chat_id: str, **kwargs):
    settings = load_settings()
    chat_id = str(chat_id)
    current = dict(DEFAULT_SETTINGS)
    current.update(settings.get(chat_id, {}))
    current.update(kwargs)
    settings[chat_id] = current
    _save(SETTINGS_FILE, settings)


def toggle_category(chat_id: str, category: str):
    settings = load_settings()
    chat_id = str(chat_id)
    current = dict(DEFAULT_SETTINGS)
    current.update(settings.get(chat_id, {}))
    cats = set(current.get("categories", []))
    if category in cats:
        cats.discard(category)
    else:
        cats.add(category)
    current["categories"] = sorted(cats)
    settings[chat_id] = current
    _save(SETTINGS_FILE, settings)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
DEFAULT_STATS = {
    "total_signals": 0,
    "by_direction": {"BUY": 0, "SELL": 0},
    "by_symbol": {},
    "started_at": None,
    "last_signal_at": None,
}


def load_stats() -> dict:
    stats = _load(STATS_FILE, dict(DEFAULT_STATS))
    if stats.get("started_at") is None:
        stats["started_at"] = datetime.now(timezone.utc).isoformat()
        _save(STATS_FILE, stats)
    return stats


def record_signal(symbol: str, direction: str):
    stats = load_stats()
    stats["total_signals"] += 1
    stats["by_direction"][direction] = stats["by_direction"].get(direction, 0) + 1
    stats["by_symbol"][symbol] = stats["by_symbol"].get(symbol, 0) + 1
    stats["last_signal_at"] = datetime.now(timezone.utc).isoformat()
    _save(STATS_FILE, stats)
