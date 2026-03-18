from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_admin(token: str | None):
    if not token or token != settings.admin_token:
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "forbidden", "message": "Invalid or missing admin token"}},
        )
    return None


@router.post("/scrape")
def trigger_scrape_all(x_admin_token: str | None = Header(None)):
    err = _check_admin(x_admin_token)
    if err:
        return err
    from app.services.scheduler import run_telegram_job, _executor

    _executor.submit(run_telegram_job)
    return {"message": "Scraping triggered (Telegram)"}


@router.post("/scrape/telegram")
def trigger_scrape_telegram(x_admin_token: str | None = Header(None)):
    err = _check_admin(x_admin_token)
    if err:
        return err
    from app.services.scheduler import run_telegram_job, _executor

    _executor.submit(run_telegram_job)
    return {"message": "Telegram scraping triggered"}


@router.get("/scrape/status")
def scrape_status(x_admin_token: str | None = Header(None)):
    err = _check_admin(x_admin_token)
    if err:
        return err
    from app.config import settings as app_settings

    channels = [c.strip() for c in app_settings.telegram_channels.split(",") if c.strip()]
    return {
        "telegram_enabled": bool(app_settings.telegram_api_id),
        "channels": channels,
        "scrape_interval_minutes": app_settings.default_scrape_interval,
    }
