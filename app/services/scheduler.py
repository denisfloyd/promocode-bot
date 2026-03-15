import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.cache import clear_cache
from app.database import SessionLocal
from app.models import CodeStatus, PromoCode, ScrapingSource
from app.services.confidence import calculate_confidence, calculate_vote_score

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
_executor = ThreadPoolExecutor(max_workers=2)
SCRAPER_MAP = {}


def register_scrapers():
    from app.scrapers.amazon_br import AmazonBRScraper
    from app.scrapers.mercado_livre import MercadoLivreScraper

    SCRAPER_MAP["amazon_br"] = AmazonBRScraper
    SCRAPER_MAP["mercado_livre"] = MercadoLivreScraper


def run_scraper_job(source_id: str):
    db = SessionLocal()
    try:
        source = db.query(ScrapingSource).filter(ScrapingSource.id == source_id).first()
        if not source or not source.is_active:
            return
        scraper_cls = SCRAPER_MAP.get(source.scraper_type)
        if not scraper_cls:
            logger.error(f"No scraper found for type: {source.scraper_type}")
            return
        scraper = scraper_cls(source_url=source.url)
        raw_data = asyncio.run(scraper.scrape())
        parsed = scraper.parse(raw_data)
        _save_codes(db, parsed, source)
        _update_source_reliability(db, source)
        source.consecutive_failures = 0
        db.commit()
        clear_cache()
        logger.info(f"Scraped {len(parsed)} codes from {source.name}")
    except Exception as e:
        logger.error(f"Scraper failed for {source_id}: {e}")
        source = db.query(ScrapingSource).filter(ScrapingSource.id == source_id).first()
        if source:
            source.consecutive_failures += 1
            if source.consecutive_failures >= 5:
                source.is_active = False
                logger.warning(f"Disabled source {source.name} after 5 consecutive failures")
            db.commit()
    finally:
        db.close()


def _save_codes(db: Session, parsed: list[dict], source: ScrapingSource):
    now = datetime.now(timezone.utc)
    for item in parsed:
        existing = (
            db.query(PromoCode)
            .filter(PromoCode.code == item["code"], PromoCode.platform == item["platform"])
            .first()
        )
        if existing:
            existing.updated_at = now
            existing.confidence_score = calculate_confidence(
                votes_worked=existing.votes_worked,
                votes_failed=existing.votes_failed,
                updated_at=existing.updated_at,
                source_reliability=source.reliability_score,
                expires_at=existing.expires_at,
            )
        else:
            expires_at = None
            if item.get("expires_at"):
                try:
                    expires_at = datetime.fromisoformat(item["expires_at"])
                except (ValueError, TypeError):
                    pass
            code = PromoCode(
                code=item["code"],
                platform=item["platform"],
                description=item.get("description", ""),
                discount_type=item.get("discount_type", "percentage"),
                discount_value=item.get("discount_value", 0.0),
                min_purchase=item.get("min_purchase"),
                category=item.get("category"),
                source_url=item.get("source_url", source.url),
                expires_at=expires_at,
                confidence_score=0.5,
                status=CodeStatus.ACTIVE,
            )
            db.add(code)
    # Expire old codes
    active_codes = db.query(PromoCode).filter(PromoCode.status == CodeStatus.ACTIVE).all()
    for code in active_codes:
        if code.expires_at:
            exp = code.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                code.status = CodeStatus.EXPIRED
                code.confidence_score = 0.0
    db.commit()


def _update_source_reliability(db: Session, source: ScrapingSource):
    codes = db.query(PromoCode).filter(
        PromoCode.source_url.contains(source.url),
        (PromoCode.votes_worked + PromoCode.votes_failed) >= 3,
    ).all()
    if codes:
        scores = [calculate_vote_score(c.votes_worked, c.votes_failed) for c in codes]
        source.reliability_score = sum(scores) / len(scores)
        db.commit()


def start_scheduler(db: Session):
    register_scrapers()
    sources = db.query(ScrapingSource).filter(ScrapingSource.is_active == True).all()  # noqa: E712
    for source in sources:
        scheduler.add_job(
            run_scraper_job,
            "interval",
            minutes=source.schedule_minutes,
            args=[source.id],
            id=f"scrape_{source.id}",
            replace_existing=True,
        )
    if not scheduler.running:
        scheduler.start()
    logger.info(f"Scheduler started with {len(sources)} sources")


def trigger_scrape(platform: str | None = None):
    db = SessionLocal()
    try:
        query = db.query(ScrapingSource).filter(ScrapingSource.is_active == True)  # noqa: E712
        if platform:
            query = query.filter(ScrapingSource.platform == platform)
        sources = query.all()
        for source in sources:
            _executor.submit(run_scraper_job, source.id)
    finally:
        db.close()
