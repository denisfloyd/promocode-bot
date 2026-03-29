import hashlib
import math
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.promo_code import CodeFeedback, CodeStatus, PromoCode
from app.services.confidence import recalculate_confidence

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


@router.post("/codes/{code_id}/vote")
def vote_partial(
    code_id: str,
    worked: bool,
    request: Request,
    db: Session = Depends(get_db),
):
    code = db.query(PromoCode).filter(PromoCode.id == code_id).first()
    if not code:
        return HTMLResponse("<small>Code not found</small>", status_code=200)

    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    today = date.today()

    existing = (
        db.query(CodeFeedback)
        .filter(
            CodeFeedback.code_id == code_id,
            CodeFeedback.ip_hash == ip_hash,
            CodeFeedback.created_at >= datetime.combine(today, datetime.min.time()),
        )
        .first()
    )
    if existing:
        return HTMLResponse("<small>Already voted today</small>", status_code=200)

    fb = CodeFeedback(code_id=code_id, worked=worked, ip_hash=ip_hash)
    db.add(fb)

    if worked:
        code.votes_worked += 1
    else:
        code.votes_failed += 1

    code.confidence_score = recalculate_confidence(code)
    db.commit()
    db.refresh(code)

    now = datetime.utcnow()  # Use naive datetime to match SQLite naive timestamps
    return templates.TemplateResponse(
        request,
        "partials/code_row.html",
        {"code": code, "now": now},
    )


@router.post("/scrape")
def scrape_trigger(request: Request):
    # Read token from header (HTMX sends it) or cookie
    token = request.headers.get("X-Admin-Token") or request.cookies.get("admin_token")
    if not token or token != settings.admin_token:
        return HTMLResponse("<small>Invalid or missing admin token. Set cookie first.</small>")

    from app.services.scheduler import run_telegram_job, _executor

    _executor.submit(run_telegram_job)
    return HTMLResponse("<small>Scrape triggered!</small>")


@router.post("/set-token")
def set_admin_token(admin_token: str = Form(...)):
    response = HTMLResponse("<small>Token saved!</small>")
    response.set_cookie(key="admin_token", value=admin_token, httponly=False, samesite="strict")
    return response
