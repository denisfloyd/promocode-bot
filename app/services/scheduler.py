import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.cache import clear_cache
from app.database import SessionLocal
from app.models import CodeStatus, PromoCode

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
_executor = ThreadPoolExecutor(max_workers=2)


def run_telegram_job():
    """Fetch codes from Telegram channels and save them."""
    from app.config import settings

    if not settings.telegram_api_id:
        return

    db = SessionLocal()
    try:
        from app.scrapers.telegram import monitor_telegram_channels

        result = asyncio.run(monitor_telegram_channels())
        active_codes, expired_pairs = result
        if active_codes:
            _save_telegram_codes(db, active_codes)
        if expired_pairs:
            _expire_codes(db, expired_pairs)
        if active_codes or expired_pairs:
            clear_cache()
            logger.info(f"Telegram: {len(active_codes)} active, {len(expired_pairs)} expired")
    except Exception as e:
        logger.error(f"Telegram job failed: {e}")
    finally:
        db.close()


def _save_telegram_codes(db: Session, parsed: list[dict]):
    """Save codes from Telegram."""
    now = datetime.now(timezone.utc)
    count = 0
    for item in parsed:
        existing = (
            db.query(PromoCode)
            .filter(PromoCode.code == item["code"], PromoCode.platform == item["platform"])
            .first()
        )
        if existing:
            existing.updated_at = now
        else:
            code = PromoCode(
                code=item["code"],
                platform=item["platform"],
                description=item.get("description", ""),
                discount_type=item.get("discount_type", "percentage"),
                discount_value=item.get("discount_value", 0.0),
                min_purchase=item.get("min_purchase"),
                category=item.get("category"),
                source_url="telegram",
                confidence_score=0.5,
                status=CodeStatus.ACTIVE,
            )
            db.add(code)
            count += 1
    db.commit()
    logger.info(f"Telegram: {count} new codes saved")


def _expire_codes(db: Session, expired_pairs: list[tuple[str, str]]):
    """Mark codes as expired based on Telegram signals (esgotado, desativado, strikethrough)."""
    count = 0
    for code_text, platform in expired_pairs:
        existing = (
            db.query(PromoCode)
            .filter(
                PromoCode.code == code_text,
                PromoCode.platform == platform,
                PromoCode.status == CodeStatus.ACTIVE,
            )
            .first()
        )
        if existing:
            existing.status = CodeStatus.EXPIRED
            existing.confidence_score = 0.0
            count += 1
    db.commit()
    if count:
        logger.info(f"Expired {count} codes based on Telegram signals")


def cleanup_old_codes():
    """Delete codes older than 24 hours that have no positive votes."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        # Delete codes that are:
        # - created more than 24h ago
        # - have no "worked" votes (no user confirmed them)
        old_codes = (
            db.query(PromoCode)
            .filter(
                PromoCode.created_at < cutoff,
                PromoCode.votes_worked == 0,
            )
            .all()
        )

        count = len(old_codes)
        for code in old_codes:
            db.delete(code)
        db.commit()

        if count > 0:
            clear_cache()
            logger.info(f"Cleanup: deleted {count} codes older than 24h with no positive votes")
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}")
    finally:
        db.close()


def start_scheduler(db: Session):
    from app.config import settings

    # Telegram job
    if settings.telegram_api_id:
        scheduler.add_job(
            run_telegram_job,
            "interval",
            minutes=settings.default_scrape_interval,
            id="telegram_monitor",
            replace_existing=True,
        )
        logger.info("Telegram channel monitoring enabled")

    # Cleanup job — runs every hour
    scheduler.add_job(
        cleanup_old_codes,
        "interval",
        hours=1,
        id="cleanup_old_codes",
        replace_existing=True,
    )
    logger.info("Code cleanup job enabled (every 1h, deletes codes >24h with no positive votes)")

    if not scheduler.running:
        scheduler.start()
