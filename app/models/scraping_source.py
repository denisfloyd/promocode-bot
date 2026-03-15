import uuid

from sqlalchemy import Boolean, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.promo_code import Platform


class ScrapingSource(Base):
    __tablename__ = "scraping_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform: Mapped[str] = mapped_column(Enum(Platform), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    scraper_type: Mapped[str] = mapped_column(String, nullable=False)
    schedule_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
