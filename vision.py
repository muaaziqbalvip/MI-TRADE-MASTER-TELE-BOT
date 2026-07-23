"""
Vision analysis — sends a user-uploaded chart screenshot to Groq's
multimodal model and gets back a structured trading read (direction,
confidence, key levels, reasoning) grounded in what's visible in the image.
"""
import base64
import json
import logging
import re

import requests

from config import GROQ_API_KEY, GROQ_VISION_MODEL

log = logging.getLogger("mi.vision")

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = """You are an expert price-action / SMC-ICT chart analyst reading a screenshot of a trading platform chart (e.g. Quotex, TradingView, MetaTrader).

Look ONLY at what is visibly present in the image: candle colors and shapes, visible trend direction, higher-highs/higher-lows or lower-highs/lower-lows structure, obvious support/resistance levels, candle wicks vs bodies, and any visible indicators overlaid on the chart (moving averages, RSI panel, etc. — only if actually drawn on the chart).

Respond with STRICT JSON only, no markdown fences, no commentary outside the JSON, matching exactly this schema:
{
  "asset_guess": "string or null — the traded pair/asset name if visible as text on the chart, else null",
  "direction": "BUY" or "SELL" or "NEUTRAL",
  "confidence": integer 0-100,
  "trend": "BULLISH" or "BEARISH" or "RANGING",
  "key_observation": "one short sentence, max 20 words, on the strongest visible pattern",
  "reasons": ["short bullet 1", "short bullet 2", "short bullet 3"] (max 4 items, each under 12 words),
  "risk_note": "one short sentence flagging any visible reason for caution, or null"
}

If the image does not show a readable price chart, set "direction" to "NEUTRAL", "confidence" to 0, and explain in "key_observation" that no valid chart was detected. Never invent price values or indicator readings that are not visibly present."""


def _extract_json(text: str) -> dict | None:
    """Groq sometimes wraps JSON in markdown fences despite instructions — strip them."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        # Last resort: find the first {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
        return None


def analyze_chart_image(image_bytes: bytes, timeframe: str, expiry_minutes: int) -> dict | None:
    """
    Send a chart screenshot to the Groq vision model and return a
    structured analysis dict, or None on failure.
    """
    if not GROQ_API_KEY:
        log.error("GROQ_API_KEY not configured")
        return None

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    user_text = (
        f"This chart is set to a {timeframe} timeframe. The trader intends to "
        f"enter a trade with a {expiry_minutes}-minute expiry. Analyze the visible "
        f"price action and structure, and return your JSON assessment."
    )

    payload = {
        "model": GROQ_VISION_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                ],
            },
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(_GROQ_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        result = r.json()
        content = result["choices"][0]["message"]["content"]
        parsed = _extract_json(content)

        if not parsed:
            log.error(f"Could not parse vision response as JSON: {content[:200]}")
            return None

        # Normalize / validate fields
        direction = str(parsed.get("direction", "NEUTRAL")).upper()
        if direction not in ("BUY", "SELL", "NEUTRAL"):
            direction = "NEUTRAL"

        confidence = parsed.get("confidence", 0)
        try:
            confidence = max(0, min(100, int(confidence)))
        except (ValueError, TypeError):
            confidence = 0

        reasons = parsed.get("reasons", [])
        if not isinstance(reasons, list):
            reasons = []
        reasons = [str(r) for r in reasons][:4]

        return {
            "asset_guess": parsed.get("asset_guess"),
            "direction": direction,
            "confidence": confidence,
            "trend": parsed.get("trend", "RANGING"),
            "key_observation": parsed.get("key_observation", ""),
            "reasons": reasons,
            "risk_note": parsed.get("risk_note"),
            "timeframe": timeframe,
            "expiry_minutes": expiry_minutes,
        }

    except requests.exceptions.RequestException as e:
        log.error(f"Groq vision request failed: {e}")
        return None
    except (KeyError, IndexError) as e:
        log.error(f"Unexpected Groq response shape: {e}")
        return None
