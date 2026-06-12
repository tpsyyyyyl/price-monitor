"""AI-інсайти по динаміці ціни товару через Groq.

price_insight завжди повертає словник {trend, recommendation, summary, source}.
За БУДЬ-ЯКОЇ помилки AI (немає ключа, 429, кривий JSON) — детермінований
евристичний fallback, порахований із самих точок ціни (source="heuristic").
"""

import json
import logging
import os

from groq import Groq

logger = logging.getLogger("price_monitor.ai")

_client: Groq | None = None

MODELS = {
    "gpt-oss": "openai/gpt-oss-120b",
    "scout": "meta-llama/llama-4-scout-17b-16e-instruct",
}
DEFAULT_MODEL_KEY = os.getenv("GROQ_MODEL", "gpt-oss")

# Скільки останніх точок ціни передаємо в промпт.
MAX_POINTS = 30


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _client = Groq(api_key=api_key)
    return _client


def resolve_model(model_key: str) -> str:
    return MODELS.get(model_key or DEFAULT_MODEL_KEY, MODELS["gpt-oss"])


def _extract_json_object(text: str) -> dict:
    """Дістає JSON-об'єкт з відповіді AI, навіть якщо він у ```-блоці."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("AI returned no JSON object")
    result = json.loads(text[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError("AI returned non-object JSON")
    return result


def _build_prompt(product, points) -> str:
    recent = points[-MAX_POINTS:]
    prices = [p.price for p in recent]
    lines = "\n".join(
        f"{p.scraped_at.date().isoformat()}: {p.price:.2f}" for p in recent
    )
    return f"""You are a price-tracking analyst. Below is the recent price history for a product.

Product: {product.name}
Currency: {product.currency}
Min: {min(prices):.2f}  Max: {max(prices):.2f}  Current: {prices[-1]:.2f}

Price history (date: price):
{lines}

Analyse the trend and give a short buying recommendation.
Return ONLY a JSON object, no explanation, in this exact format:
{{"trend": "up|down|stable", "recommendation": "...", "summary": "..."}}"""


def _heuristic_insight(product, points) -> dict:
    """Детермінований fallback: порівнюємо середнє першої й останньої третини."""
    prices = [p.price for p in points]
    n = len(prices)
    third = max(1, n // 3)
    first_avg = sum(prices[:third]) / third
    last_avg = sum(prices[-third:]) / third
    change = (last_avg - first_avg) / first_avg * 100 if first_avg else 0.0
    current = prices[-1]
    lowest = min(prices)

    if change <= -3:
        trend = "down"
        recommendation = "Price is falling — a good moment to buy."
        summary = (
            f"The price dropped about {abs(change):.0f}% over the tracked period, "
            f"now at {current:.2f} {product.currency}."
        )
    elif change >= 3:
        trend = "up"
        recommendation = "Price is rising — consider waiting or buying soon."
        summary = (
            f"The price rose about {change:.0f}% over the tracked period, "
            f"now at {current:.2f} {product.currency}."
        )
    else:
        trend = "stable"
        near_low = current <= lowest * 1.02
        recommendation = (
            "Price is near its low — reasonable to buy now."
            if near_low
            else "Price is stable — no urgency to buy."
        )
        summary = (
            f"The price stayed roughly flat, currently {current:.2f} "
            f"{product.currency} (low {lowest:.2f})."
        )

    return {
        "trend": trend,
        "recommendation": recommendation,
        "summary": summary,
        "source": "heuristic",
    }


def price_insight(product, points) -> dict:
    """Повертає {trend, recommendation, summary, source}.

    Пробує Groq; за будь-якої помилки падає на евристику.
    """
    if not points:
        return {
            "trend": "stable",
            "recommendation": "Not enough data yet — keep tracking.",
            "summary": "No price history collected for this product yet.",
            "source": "heuristic",
        }

    try:
        client = _get_client()
        model = resolve_model("")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _build_prompt(product, points)}],
            temperature=0.3,
            max_tokens=512,
        )
        text = response.choices[0].message.content or ""
        data = _extract_json_object(text)
        return {
            "trend": data.get("trend", "stable"),
            "recommendation": data.get("recommendation", ""),
            "summary": data.get("summary", ""),
            "source": "ai",
        }
    except Exception as e:
        logger.info("AI insight unavailable (%s) — using heuristic fallback.", e)
        return _heuristic_insight(product, points)
