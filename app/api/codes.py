import math

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PromoCode
from app.schemas import (
    PromoCodeResponse,
    PromoCodeListResponse,
    PaginationResponse,
    ErrorResponse,
    PlatformEnum,
    DiscountTypeEnum,
    CodeStatusEnum,
    SortByEnum,
    OrderEnum,
)

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
