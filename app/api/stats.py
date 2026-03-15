from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CodeStatus, PromoCode
from app.schemas import StatsResponse

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(PromoCode.id)).scalar()
    active = db.query(func.count(PromoCode.id)).filter(PromoCode.status == CodeStatus.ACTIVE).scalar()
    expired = db.query(func.count(PromoCode.id)).filter(PromoCode.status == CodeStatus.EXPIRED).scalar()
    platform_counts = (
        db.query(PromoCode.platform, func.count(PromoCode.id))
        .group_by(PromoCode.platform)
        .all()
    )
    return StatsResponse(
        total_codes=total,
        active_codes=active,
        expired_codes=expired,
        platforms={p: c for p, c in platform_counts},
    )
