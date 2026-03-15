import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import init_db

logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


def _seed_sources(db):
    from app.models import Platform, ScrapingSource

    default_sources = [
        {
            "platform": Platform.AMAZON_BR,
            "name": "Amazon Brasil Coupons",
            "url": "https://www.amazon.com.br/coupons",
            "scraper_type": "amazon_br",
        },
        {
            "platform": Platform.MERCADO_LIVRE,
            "name": "Mercado Livre Cupons",
            "url": "https://www.mercadolivre.com.br/cupons",
            "scraper_type": "mercado_livre",
        },
    ]

    for src in default_sources:
        exists = (
            db.query(ScrapingSource)
            .filter(
                ScrapingSource.platform == src["platform"],
                ScrapingSource.url == src["url"],
            )
            .first()
        )
        if not exists:
            db.add(ScrapingSource(**src))
            logger.info(f"Seeded source: {src['name']}")

    db.commit()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PromoCode AI",
        description="Public API aggregating promo codes from Brazilian e-commerce platforms",
        version="0.1.0",
    )

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": "Rate limit exceeded. Try again later.",
                }
            },
        )

    @app.on_event("startup")
    def startup():
        init_db()
        logger.info("Database initialized")
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            _seed_sources(db)
            from app.services.scheduler import start_scheduler

            start_scheduler(db)
        finally:
            db.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    from app.api.admin import router as admin_router
    from app.api.codes import router as codes_router
    from app.api.platforms import router as platforms_router
    from app.api.stats import router as stats_router

    app.include_router(codes_router, prefix="/api/v1")
    app.include_router(platforms_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
