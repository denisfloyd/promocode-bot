from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CodeStatus, Platform, PromoCode
from app.schemas import PlatformInfo, PlatformListResponse

router = APIRouter(tags=["platforms"])

PLATFORM_NAMES = {
    Platform.AMAZON_BR: "Amazon Brasil",
    Platform.MERCADO_LIVRE: "Mercado Livre",
}


@router.get("/platforms", response_model=PlatformListResponse)
def list_platforms(db: Session = Depends(get_db)):
    counts = (
        db.query(PromoCode.platform, func.count(PromoCode.id))
        .filter(PromoCode.status == CodeStatus.ACTIVE)
        .group_by(PromoCode.platform)
        .all()
    )
    count_map = dict(counts)
    platforms = [
        PlatformInfo(
            name=PLATFORM_NAMES[p],
            code=p.value,
            active_codes=count_map.get(p, 0),
        )
        for p in Platform
    ]
    return PlatformListResponse(data=platforms)
