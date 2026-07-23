"""
Chart image renderer — takes the user's ACTUAL uploaded chart screenshot
and draws a clean signal overlay directly on top of it (arrow, confidence
badge, entry marker). This is the real image the user sent, not a
synthetic/fake chart — only annotation layers are added.
"""
import io
import logging

from PIL import Image, ImageDraw, ImageFont, ImageOps

log = logging.getLogger("mi.chartgen")

_UP_COLOR = (38, 166, 154, 255)     # teal green
_DOWN_COLOR = (239, 83, 80, 255)    # red
_NEUTRAL_COLOR = (158, 158, 158, 255)
_WHITE = (255, 255, 255, 255)
_SHADOW = (0, 0, 0, 160)


def _load_font(size: int, bold: bool = False):
    """Try a few common system font paths; fall back to PIL's default bitmap font."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_text_with_shadow(draw, xy, text, font, fill):
    x, y = xy
    draw.text((x + 2, y + 2), text, font=font, fill=_SHADOW)
    draw.text((x, y), text, font=font, fill=fill)


def render_signal_chart(analysis: dict, image_bytes: bytes) -> bytes:
    """
    Take the user's real screenshot and overlay a clean signal annotation
    on top of it — a directional arrow, a confidence badge, and a thin
    branded footer strip. Returns PNG bytes ready to send as a photo.
    """
    direction = analysis.get("direction", "NEUTRAL")
    confidence = analysis.get("confidence", 0)
    trend = analysis.get("trend", "RANGING")
    timeframe = analysis.get("timeframe", "1m")
    expiry = analysis.get("expiry_minutes", 5)

    base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    base = ImageOps.exif_transpose(base)  # respect phone camera orientation
    w, h = base.size

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if direction == "BUY":
        signal_color = _UP_COLOR
        signal_text = "🟢 BUY / CALL"
        arrow_up = True
    elif direction == "SELL":
        signal_color = _DOWN_COLOR
        signal_text = "🔴 SELL / PUT"
        arrow_up = False
    else:
        signal_color = _NEUTRAL_COLOR
        signal_text = "⚪ NO CLEAR SIGNAL"
        arrow_up = None

    # --- Scale UI elements relative to image size so it looks right on any resolution ---
    scale = max(w, h) / 1200.0
    scale = max(0.6, min(scale, 2.2))

    badge_font = _load_font(int(26 * scale), bold=True)
    sub_font = _load_font(int(18 * scale), bold=False)
    footer_font = _load_font(int(15 * scale), bold=False)

    # --- Top banner strip (direction + confidence) ---
    banner_h = int(70 * scale)
    draw.rectangle([0, 0, w, banner_h], fill=(*signal_color[:3], 235))
    _draw_text_with_shadow(
        draw, (int(16 * scale), int(10 * scale)),
        signal_text, badge_font, _WHITE,
    )
    _draw_text_with_shadow(
        draw, (int(16 * scale), int(10 * scale) + badge_font.size + 2),
        f"Confidence: {confidence}%  •  {timeframe} chart  •  {expiry}m expiry",
        sub_font, _WHITE,
    )

    # --- Large directional arrow, bottom-right area (doesn't obscure candles at top) ---
    if arrow_up is not None:
        arrow_size = int(90 * scale)
        margin = int(24 * scale)
        cx = w - margin - arrow_size // 2
        cy = h - margin - arrow_size // 2 - int(60 * scale)  # lift above footer

        if arrow_up:
            pts = [
                (cx, cy - arrow_size // 2),
                (cx - arrow_size // 2, cy + arrow_size // 4),
                (cx - arrow_size // 5, cy + arrow_size // 4),
                (cx - arrow_size // 5, cy + arrow_size // 2),
                (cx + arrow_size // 5, cy + arrow_size // 2),
                (cx + arrow_size // 5, cy + arrow_size // 4),
                (cx + arrow_size // 2, cy + arrow_size // 4),
            ]
        else:
            pts = [
                (cx, cy + arrow_size // 2),
                (cx - arrow_size // 2, cy - arrow_size // 4),
                (cx - arrow_size // 5, cy - arrow_size // 4),
                (cx - arrow_size // 5, cy - arrow_size // 2),
                (cx + arrow_size // 5, cy - arrow_size // 2),
                (cx + arrow_size // 5, cy - arrow_size // 4),
                (cx + arrow_size // 2, cy - arrow_size // 4),
            ]

        # Soft glow/shadow behind the arrow for visibility on any chart background
        shadow_pts = [(x + 3, y + 3) for x, y in pts]
        draw.polygon(shadow_pts, fill=(0, 0, 0, 140))
        draw.polygon(pts, fill=(*signal_color[:3], 235), outline=_WHITE)

    # --- Bottom branding footer strip ---
    footer_h = int(34 * scale)
    draw.rectangle([0, h - footer_h, w, h], fill=(0, 0, 0, 190))
    _draw_text_with_shadow(
        draw, (int(12 * scale), h - footer_h + int(6 * scale)),
        "MI Trade Master — Vision Signal Engine  •  Analyzed from your screenshot",
        footer_font, _WHITE,
    )

    composed = Image.alpha_composite(base, overlay).convert("RGB")

    buf = io.BytesIO()
    composed.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()
