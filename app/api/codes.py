import hashlib
import math
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CodeFeedback, PromoCode
from app.schemas import (
    CodeStatusEnum,
    DiscountTypeEnum,
    ErrorResponse,
    FeedbackRequest,
    FeedbackResponse,
    OrderEnum,
    PaginationResponse,
    PlatformEnum,
    PromoCodeListResponse,
    PromoCodeResponse,
    SortByEnum,
)
from app.services.confidence import recalculate_confidence

router = APIRouter(tags=["codes"])

SORT_COLUMN_MAP = {
    SortByEnum.CONFIDENCE_SCORE: PromoCode.confidence_score,
    SortByEnum.CREATED_AT: PromoCode.created_at,
    SortByEnum.DISCOUNT_VALUE: PromoCode.discount_value,
    SortByEnum.EXPIRES_AT: PromoCode.expires_at,
}


@router.get("/codes", response_model=PromoCodeListResponse)
def list_codes(
    platform: PlatformEnum | None = None,
    discount_type: DiscountTypeEnum | None = None,
    category: str | None = None,
    min_confidence: float | None = Query(None, ge=0, le=1),
    status: CodeStatusEnum | None = None,
    sort_by: SortByEnum = SortByEnum.CONFIDENCE_SCORE,
    order: OrderEnum = OrderEnum.DESC,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1),
    db: Session = Depends(get_db),
):
    per_page = min(per_page, 100)
    query = db.query(PromoCode)

    if platform:
        query = query.filter(PromoCode.platform == platform.value)
    if discount_type:
        query = query.filter(PromoCode.discount_type == discount_type.value)
    if category:
        query = query.filter(PromoCode.category == category)
    if min_confidence is not None:
        query = query.filter(PromoCode.confidence_score >= min_confidence)
    if status:
        query = query.filter(PromoCode.status == status.value)

    sort_column = SORT_COLUMN_MAP[sort_by]
    if order == OrderEnum.DESC:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    offset = (page - 1) * per_page
    codes = query.offset(offset).limit(per_page).all()

    return PromoCodeListResponse(
        data=[PromoCodeResponse.model_validate(c) for c in codes],
        pagination=PaginationResponse(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/codes/{code_id}",
    response_model=PromoCodeResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_code(code_id: str, db: Session = Depends(get_db)):
    code = db.query(PromoCode).filter(PromoCode.id == code_id).first()
    if not code:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"Code {code_id} not found"}},
        )
    return PromoCodeResponse.model_validate(code)


@router.post(
    "/codes/{code_id}/feedback",
    response_model=FeedbackResponse,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
def submit_feedback(
    code_id: str,
    feedback: FeedbackRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    code = db.query(PromoCode).filter(PromoCode.id == code_id).first()
    if not code:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"Code {code_id} not found"}},
        )

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
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "duplicate_vote",
                    "message": "You have already voted on this code today",
                }
            },
        )

    fb = CodeFeedback(code_id=code_id, worked=feedback.worked, ip_hash=ip_hash)
    db.add(fb)

    if feedback.worked:
        code.votes_worked += 1
    else:
        code.votes_failed += 1

    code.confidence_score = recalculate_confidence(code)
    db.commit()
    db.refresh(code)

    return FeedbackResponse(
        message="Feedback submitted",
        votes_worked=code.votes_worked,
        votes_failed=code.votes_failed,
        confidence_score=code.confidence_score,
    )
