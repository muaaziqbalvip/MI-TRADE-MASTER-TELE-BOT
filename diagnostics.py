"""
Live diagnostics — keeps a rolling buffer of recent log events (info/warn/error)
in memory so admins can inspect what's happening without needing GitHub Actions
log access. Also pushes critical errors straight to ADMIN_CHAT_IDS in real time.
"""
import logging
import threading
from collections import deque
from datetime import datetime, timezone

from config import ADMIN_CHAT_IDS

_BUFFER_SIZE = 200
_buffer = deque(maxlen=_BUFFER_SIZE)
_lock = threading.Lock()

_bot_ref = None  # set by main.py to avoid circular import at module load time


def bind_bot(bot_instance):
    global _bot_ref
    _bot_ref = bot_instance


def record(level: str, message: str, notify_admin: bool = False):
    """Add an entry to the rolling log buffer, and optionally alert admins live."""
    entry = {
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    }
    with _lock:
        _buffer.append(entry)

    if notify_admin and _bot_ref and ADMIN_CHAT_IDS:
        icon = {"ERROR": "🔴", "WARN": "🟡", "INFO": "🔵"}.get(level, "⚪")
        text = f"{icon} <b>MI Trade Master Alert</b>\n\n{message}"
        for admin_id in ADMIN_CHAT_IDS:
            try:
                _bot_ref.send_message(admin_id, text)
            except Exception:
                pass  # never let admin notification failures cascade


def recent_logs(count: int = 20) -> list:
    with _lock:
        return list(_buffer)[-count:]


def format_logs_text(count: int = 20) -> str:
    entries = recent_logs(count)
    if not entries:
        return "📋 <b>Live Logs</b>\n\nNo events recorded yet this session."

    icon_map = {"ERROR": "🔴", "WARN": "🟡", "INFO": "🔵"}
    lines = []
    for e in entries:
        icon = icon_map.get(e["level"], "⚪")
        lines.append(f"{icon} <code>{e['time']}</code> {e['message']}")

    return (
        f"📋 <b>Live Logs</b> (last {len(entries)} events)\n\n"
        + "\n".join(lines)
    )


class BufferLogHandler(logging.Handler):
    """A logging.Handler that mirrors mi.* logger output into the rolling buffer."""

    def emit(self, record_obj: logging.LogRecord):
        try:
            level = record_obj.levelname
            if level == "WARNING":
                level = "WARN"
            msg = record_obj.getMessage()
            with _lock:
                _buffer.append({
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "level": level,
                    "message": msg,
                })
        except Exception:
            pass  # logging handlers must never raise
