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


def extract_items(page_text: str, query: str) -> dict:
    """Витягує список елементів з тексту сторінки за запитом користувача.

    Повертає {results, summary, source, count}.
    За будь-якої помилки повертає порожній результат з source="error" — ніколи не кидає.
    """
    prompt = f"""You are a web data extraction assistant. Extract items from the page text below that match the user's query.

User query: {query}

Return ONLY a JSON object in this exact format, no explanation:
{{"results": [{{"<field>": "<value>"}}], "summary": "<one sentence describing what was found>"}}

Rules:
- Maximum 40 items in results.
- Fields must be consistent across all items (same keys).
- Keep values short and factual.
- If nothing matches, return empty results array with a summary saying so.

Page text:
{page_text[:15000]}"""

    try:
        client = _get_client()
        model = resolve_model(DEFAULT_MODEL_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048,
        )
        text = response.choices[0].message.content or ""
        data = _extract_json_object(text)
        results = data.get("results", [])
        if not isinstance(results, list):
            results = []
        return {
            "results": results,
            "summary": data.get("summary", ""),
            "source": "ai",
        }
    except Exception as e:
        logger.info("extract_items AI unavailable (%s) — returning empty result.", e)
        return {"results": [], "summary": "", "source": "error", "error": str(e)}


def extract_product_price(page_text: str, target_name: str | None = None) -> dict:
    """Витягує назву та поточну ціну товару зі сторінки через AI.

    Якщо задано target_name — шукає ціну саме цього товару. Інакше визначає
    головний товар сторінки та його назву й ціну.

    Повертає {"name": str, "price": number, "currency": str}.
    На БУДЬ-ЯКІЙ помилці (немає ключа, кривий JSON, нема ціни) кидає ValueError —
    виклик обробляє це сам.
    """
    if target_name:
        task = (
            f'Find the CURRENT price of the item named "{target_name}" on this page.'
        )
    else:
        task = "Identify the MAIN product on this page and its name and current price."

    prompt = f"""You are a price extraction assistant. {task}

Return ONLY a JSON object in this exact format, no explanation:
{{"name": "<product name>", "price": <number>, "currency": "<GBP|USD|EUR>"}}

Rules:
- price must be a numeric value (no currency symbols).
- currency is an ISO code like GBP, USD, EUR. Use "USD" if unknown.

Page text:
{page_text[:15000]}"""

    try:
        client = _get_client()
        model = resolve_model(DEFAULT_MODEL_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1024,
        )
        text = response.choices[0].message.content or ""
        data = _extract_json_object(text)
    except Exception as e:
        raise ValueError(f"AI price extraction failed: {e}") from e

    if data.get("price") is None:
        raise ValueError("AI returned no price")

    return {
        "name": data.get("name") or (target_name or ""),
        "price": data["price"],
        "currency": data.get("currency") or "USD",
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
