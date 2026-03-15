import logging
import re
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)

# Common promo code patterns in Brazilian Telegram messages
CODE_PATTERNS = [
    # "Cupom: CODIGO" or "Código: CODIGO"
    re.compile(r"(?:cupom|código|code|cupão)[:\s]+([A-Z0-9_]{4,30})", re.IGNORECASE),
    # "Use o código CODIGO"
    re.compile(r"use\s+(?:o\s+)?(?:cupom|código|code)\s+([A-Z0-9_]{4,30})", re.IGNORECASE),
    # "CODIGO para ganhar X% OFF"
    re.compile(r"\b([A-Z0-9_]{4,30})\s+(?:para|pra)\s+(?:ganhar|ter|conseguir)", re.IGNORECASE),
    # Codes in quotes or brackets
    re.compile(r"[\"']([A-Z0-9_]{4,30})[\"']"),
    re.compile(r"\[([A-Z0-9_]{4,30})\]"),
]

# Words that look like codes but aren't
FALSE_POSITIVES = {
    "CUPOM", "LINK", "SITE", "LOJA", "AMAZON", "MERCADO", "LIVRE",
    "DESCONTO", "FRETE", "GRATIS", "GRÁTIS", "PROMO", "OFERTA",
    "HTTP", "HTTPS", "WWW", "COM", "BRASIL", "FREE",
    "HOJE", "AQUI", "TUDO", "MAIS", "TODOS", "TODO", "ESSA", "ESSE",
    "COMO", "PARA", "PEGA", "VALE", "SUPER", "MEGA", "MELHOR",
}

PLATFORM_KEYWORDS = {
    "amazon_br": ["amazon", "amz", "amazon.com.br"],
    "mercado_livre": ["mercado livre", "mercadolivre", "meli", "ml"],
}

DISCOUNT_PATTERNS = [
    # "50% OFF" or "50% de desconto"
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:off|desconto|de desconto)", re.IGNORECASE), "percentage"),
    # "R$50 OFF" or "R$ 50 de desconto"
    (re.compile(r"R?\$\s*(\d+(?:[.,]\d+)?)\s*(?:off|desconto|de desconto|reais)", re.IGNORECASE), "fixed_amount"),
    # "Frete grátis"
    (re.compile(r"frete\s+(?:grátis|gratuito|free|gr[aá]tis)", re.IGNORECASE), "free_shipping"),
]


def extract_codes_from_message(text: str) -> list[str]:
    """Extract potential promo codes from a message."""
    codes = set()
    for pattern in CODE_PATTERNS:
        for match in pattern.finditer(text):
            code = match.group(1).upper()
            if code not in FALSE_POSITIVES and len(code) >= 4:
                codes.add(code)
    return list(codes)


def detect_platform(text: str) -> str | None:
    """Detect which platform a message is about."""
    text_lower = text.lower()
    for platform, keywords in PLATFORM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return platform
    return None


def parse_discount(text: str) -> tuple[str, float]:
    """Extract discount type and value from message text."""
    for pattern, dtype in DISCOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            if dtype == "free_shipping":
                return "free_shipping", 0.0
            value = float(match.group(1).replace(",", "."))
            return dtype, value
    return "percentage", 0.0


def parse_telegram_message(text: str) -> list[dict]:
    """Parse a Telegram message and extract promo code data."""
    if not text:
        return []

    codes = extract_codes_from_message(text)
    if not codes:
        return []

    platform = detect_platform(text)
    if not platform:
        return []

    discount_type, discount_value = parse_discount(text)

    # Use first ~100 chars as description
    description = text[:100].strip()
    if len(text) > 100:
        description += "..."

    results = []
    for code in codes:
        results.append({
            "code": code,
            "platform": platform,
            "description": description,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "source_url": "telegram",
        })

    return results


async def monitor_telegram_channels():
    """Connect to Telegram and fetch recent messages from configured channels."""
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        logger.warning("Telegram API credentials not configured, skipping")
        return []

    channels = [c.strip() for c in settings.telegram_channels.split(",") if c.strip()]
    if not channels:
        logger.warning("No Telegram channels configured, skipping")
        return []

    try:
        from telethon import TelegramClient

        client = TelegramClient("promocode_bot", settings.telegram_api_id, settings.telegram_api_hash)
        await client.start()

        all_codes = []
        for channel_name in channels:
            try:
                channel = await client.get_entity(channel_name)
                # Get last 50 messages
                async for message in client.iter_messages(channel, limit=50):
                    if message.text:
                        parsed = parse_telegram_message(message.text)
                        all_codes.extend(parsed)
                logger.info(f"Fetched messages from @{channel_name}, found {len(all_codes)} codes")
            except Exception as e:
                logger.error(f"Failed to fetch from @{channel_name}: {e}")

        await client.disconnect()
        return all_codes

    except Exception as e:
        logger.error(f"Telegram connection failed: {e}")
        return []
