import logging
import re
from datetime import datetime, timedelta, timezone

from app.config import settings

logger = logging.getLogger(__name__)

# Common promo code patterns in Brazilian Telegram messages
CODE_PATTERNS = [
    # Codes in backticks (very common in these channels): `VAIBRASIL`
    re.compile(r"`([A-Z0-9_]{4,30})`"),
    # "cupom: CODIGO" or "código: CODIGO" or "cupom CODIGO"
    re.compile(r"(?:cupom|código|code|cupão)[:\s]+([A-Z0-9_]{4,30})", re.IGNORECASE),
    # "Use o cupom CODIGO" or "Usem o cupom: CODIGO" (with optional markdown **)
    re.compile(r"use[m]?\s+(?:o\s+)?(?:cupom|código|code)[:\s*]+([A-Z0-9_]{4,30})", re.IGNORECASE),
    # "Use o cupom:** CODIGO" — markdown bold variant
    re.compile(r"cupom[:\s*]+\s*([A-Z][A-Z0-9_]{3,29})\b", re.IGNORECASE),
    # Codes in quotes
    re.compile(r"[\"']([A-Z0-9_]{4,30})[\"']"),
]

# Words that look like codes but aren't
FALSE_POSITIVES = {
    "CUPOM", "LINK", "SITE", "LOJA", "AMAZON", "MERCADO", "LIVRE",
    "DESCONTO", "FRETE", "GRATIS", "GRÁTIS", "PROMO", "OFERTA",
    "HTTP", "HTTPS", "WWW", "COM", "BRASIL", "FREE",
    "HOJE", "AQUI", "TUDO", "MAIS", "TODOS", "TODO", "ESSA", "ESSE",
    "COMO", "PARA", "PEGA", "VALE", "SUPER", "MEGA", "MELHOR",
    "SHOPEE", "NOVO", "NOVA", "CADA", "ACABA", "ATENÇÃO",
    "NOITE", "MELI", "BAIXOU", "PREÇO", "ULTIMO",
    "SECRETO", "ATIVE", "ATIVOU", "VOLTOU", "CORRE",
}

PLATFORM_KEYWORDS = {
    "amazon_br": ["amazon", "amz", "amazon.com.br", "achado amazon", "amzn.to"],
    "mercado_livre": [
        "mercado livre", "mercadolivre", "mercadolivre.com",
        "achado mercado livr", "vamosmeli", "mercado livr",
    ],
}

DISCOUNT_PATTERNS = [
    # "R$50 OFF" or "R$ 350 OFF" (check fixed amount first — more specific)
    (re.compile(r"R\$\s*(\d+(?:[.,]\d+)?)\s*(?:off|de desconto|desconto|reais)", re.IGNORECASE), "fixed_amount"),
    # "50% OFF" or "50% de desconto"
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:off|desconto|de desconto)?", re.IGNORECASE), "percentage"),
    # "Frete grátis"
    (re.compile(r"frete\s+(?:grátis|gratuito|free|gr[aá]tis)", re.IGNORECASE), "free_shipping"),
]

# Keywords that indicate a code is no longer valid
INVALIDATION_KEYWORDS = re.compile(
    r"esgotou|esgotado|desativou|desativado|expirou|expirad[oa]|acabou|encerrad[oa]|finalizad[oa]",
    re.IGNORECASE,
)


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


def is_invalidated(text: str) -> bool:
    """Check if the message indicates the code is no longer valid."""
    return bool(INVALIDATION_KEYWORDS.search(text))


def get_struck_codes(text: str, entities: list | None) -> set[str]:
    """Find codes that appear inside strikethrough text regions."""
    if not entities:
        return set()

    try:
        from telethon.tl.types import MessageEntityStrike
    except ImportError:
        return set()

    struck_codes = set()
    for entity in entities:
        if isinstance(entity, MessageEntityStrike):
            struck_text = text[entity.offset:entity.offset + entity.length]
            # Extract any codes from the struck-through region
            for pattern in CODE_PATTERNS:
                for match in pattern.finditer(struck_text):
                    struck_codes.add(match.group(1).upper())

    return struck_codes


def parse_telegram_message(text: str, entities: list | None = None) -> list[dict]:
    """Parse a Telegram message and extract promo code data.

    Returns list of dicts with an 'expired' key indicating if the code
    was marked as invalid in the message.
    """
    if not text:
        return []

    codes = extract_codes_from_message(text)
    if not codes:
        return []

    platform = detect_platform(text)
    if not platform:
        return []

    discount_type, discount_value = parse_discount(text)

    # Check if the whole message says "esgotado" etc
    message_invalidated = is_invalidated(text)

    # Check which codes are inside strikethrough
    struck_codes = get_struck_codes(text, entities)

    # Clean description
    clean = re.sub(r"[*_`~]", "", text)
    clean = re.sub(r"https?://\S+", "", clean)
    lines = [l.strip() for l in clean.split("\n") if l.strip() and len(l.strip()) > 5]
    description = lines[0][:120] if lines else text[:120]

    results = []
    for code in codes:
        # A code is expired if:
        # 1. The message has invalidation keywords (esgotado, desativou, etc.)
        # 2. The code appears inside strikethrough text
        expired = message_invalidated or code in struck_codes

        results.append({
            "code": code,
            "platform": platform,
            "description": description,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "source_url": "telegram",
            "expired": expired,
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
        expired_codes = set()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

        for channel_name in channels:
            try:
                channel = await client.get_entity(channel_name)
                channel_codes = []
                async for message in client.iter_messages(channel, limit=50):
                    if message.date and message.date < cutoff:
                        break
                    if message.text:
                        parsed = parse_telegram_message(message.text, message.entities)
                        for item in parsed:
                            if item.get("expired"):
                                expired_codes.add((item["code"], item["platform"]))
                            else:
                                channel_codes.append(item)
                all_codes.extend(channel_codes)
                logger.info(f"@{channel_name}: found {len(channel_codes)} active codes")
            except Exception as e:
                logger.error(f"Failed to fetch from @{channel_name}: {e}")

        await client.disconnect()

        # Remove codes that were marked as expired in any channel
        active = [c for c in all_codes if (c["code"], c["platform"]) not in expired_codes]

        # Deduplicate by code+platform
        seen = set()
        unique = []
        for c in active:
            key = (c["code"], c["platform"])
            if key not in seen:
                seen.add(key)
                # Remove the 'expired' key before returning
                c.pop("expired", None)
                unique.append(c)

        if expired_codes:
            logger.info(f"Telegram: {len(expired_codes)} codes marked as expired (esgotado/desativado/struck)")

        logger.info(f"Telegram total: {len(unique)} active unique codes from {len(channels)} channels")
        return unique, list(expired_codes)

    except Exception as e:
        logger.error(f"Telegram connection failed: {e}")
        return [], []
