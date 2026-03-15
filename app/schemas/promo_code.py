import enum
from datetime import datetime

from pydantic import BaseModel


class PlatformEnum(str, enum.Enum):
    AMAZON_BR = "amazon_br"
    MERCADO_LIVRE = "mercado_livre"


class DiscountTypeEnum(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"


class CodeStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FLAGGED = "flagged"


class SortByEnum(str, enum.Enum):
    CONFIDENCE_SCORE = "confidence_score"
    CREATED_AT = "created_at"
    DISCOUNT_VALUE = "discount_value"
    EXPIRES_AT = "expires_at"


class OrderEnum(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    platform: PlatformEnum
    description: str
    discount_type: DiscountTypeEnum
    discount_value: float
    min_purchase: float | None
    category: str | None
    source_url: str
    expires_at: datetime | None
    confidence_score: float
    status: CodeStatusEnum
    votes_worked: int
    votes_failed: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginationResponse(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class PromoCodeListResponse(BaseModel):
    data: list[PromoCodeResponse]
    pagination: PaginationResponse


class PlatformInfo(BaseModel):
    name: str
    code: str
    active_codes: int


class PlatformListResponse(BaseModel):
    data: list[PlatformInfo]


class StatsResponse(BaseModel):
    total_codes: int
    active_codes: int
    expired_codes: int
    platforms: dict[str, int]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
