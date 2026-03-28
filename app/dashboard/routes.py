import math
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
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


@router.get("/codes")
def codes_partial(
    request: Request,
    platform: str = "",
    sort_by: str = "confidence_score",
    min_confidence: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(PromoCode)

    if platform:
        query = query.filter(PromoCode.platform == platform)
    if min_confidence:
        query = query.filter(PromoCode.confidence_score >= float(min_confidence))

    sort_map = {
        "confidence_score": PromoCode.confidence_score.desc(),
        "created_at": PromoCode.created_at.desc(),
        "discount_value": PromoCode.discount_value.desc(),
    }
    query = query.order_by(sort_map.get(sort_by, PromoCode.confidence_score.desc()))

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    codes = query.offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse(
        request,
        "partials/codes_table.html",
        {
            "codes": codes,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "platform": platform,
            "sort_by": sort_by,
            "min_confidence": min_confidence,
            "now": datetime.utcnow(),
        },
    )
