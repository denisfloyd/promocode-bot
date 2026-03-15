import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Platform(str, enum.Enum):
    AMAZON_BR = "amazon_br"
    MERCADO_LIVRE = "mercado_livre"


class DiscountType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"


class CodeStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FLAGGED = "flagged"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(Enum(Platform), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    discount_type: Mapped[str] = mapped_column(Enum(DiscountType), nullable=False)
    discount_value: Mapped[float] = mapped_column(Float, nullable=False)
    min_purchase: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(Enum(CodeStatus), nullable=False, default=CodeStatus.ACTIVE)
    votes_worked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    votes_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    feedbacks: Mapped[list["CodeFeedback"]] = relationship(back_populates="promo_code")

    __table_args__ = (
        UniqueConstraint("code", "platform", name="uq_code_platform"),
    )


class CodeFeedback(Base):
    __tablename__ = "code_feedbacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code_id: Mapped[str] = mapped_column(String, ForeignKey("promo_codes.id"), nullable=False)
    worked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    promo_code: Mapped["PromoCode"] = relationship(back_populates="feedbacks")
