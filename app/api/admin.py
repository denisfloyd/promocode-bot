from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ScrapingSource
from app.schemas import PlatformEnum

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_admin(token: str | None):
    if not token or token != settings.admin_token:
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "forbidden", "message": "Invalid or missing admin token"}},
        )
    return None


@router.post("/scrape")
def trigger_scrape_all(x_admin_token: str | None = Header(None), db: Session = Depends(get_db)):
    err = _check_admin(x_admin_token)
    if err:
        return err
    from app.services.scheduler import trigger_scrape

    trigger_scrape()
    return {"message": "Scraping triggered for all platforms"}


@router.post("/scrape/{platform}")
def trigger_scrape_platform(
    platform: PlatformEnum, x_admin_token: str | None = Header(None), db: Session = Depends(get_db)
):
    err = _check_admin(x_admin_token)
    if err:
        return err
    from app.services.scheduler import trigger_scrape

    trigger_scrape(platform=platform.value)
    return {"message": f"Scraping triggered for {platform.value}"}


@router.get("/scrape/status")
def scrape_status(x_admin_token: str | None = Header(None), db: Session = Depends(get_db)):
    err = _check_admin(x_admin_token)
    if err:
        return err
    sources = db.query(ScrapingSource).all()
    return {
        "last_run": None,
        "sources": [
            {
                "name": s.name,
                "platform": s.platform,
                "is_active": s.is_active,
                "consecutive_failures": s.consecutive_failures,
                "schedule_minutes": s.schedule_minutes,
            }
            for s in sources
        ],
    }
