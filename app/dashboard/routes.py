import math
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.promo_code import CodeStatus, PromoCode

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/stats")
def stats_partial(request: Request, db: Session = Depends(get_db)):
    total_active = db.query(PromoCode).filter(PromoCode.status == CodeStatus.ACTIVE).count()
    total_expired = db.query(PromoCode).filter(PromoCode.status == CodeStatus.EXPIRED).count()
    amazon_count = (
        db.query(PromoCode)
        .filter(PromoCode.platform == "amazon_br", PromoCode.status == CodeStatus.ACTIVE)
        .count()
    )
    ml_count = (
        db.query(PromoCode)
        .filter(PromoCode.platform == "mercado_livre", PromoCode.status == CodeStatus.ACTIVE)
        .count()
    )
    return templates.TemplateResponse(
        request,
        "partials/stats_cards.html",
        {"active": total_active, "expired": total_expired, "amazon": amazon_count, "ml": ml_count},
    )
