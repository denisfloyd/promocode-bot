from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import PromoCode, ScrapingSource, CodeStatus, Platform, DiscountType
from app.services.scheduler import _save_codes, _update_source_reliability
from app.services.confidence import calculate_vote_score


@pytest.fixture
def scheduler_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_wal(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def source(scheduler_db):
    s = ScrapingSource(
        platform="amazon_br",
        name="Test Source",
        url="https://example.com",
        scraper_type="amazon_br",
        reliability_score=0.5,
    )
    scheduler_db.add(s)
    scheduler_db.commit()
    scheduler_db.refresh(s)
    return s


def test_save_codes_inserts_new(scheduler_db, source):
    parsed = [
        {
            "code": "TEST10",
            "platform": "amazon_br",
            "description": "10% off",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "source_url": "https://example.com",
        }
    ]
    _save_codes(scheduler_db, parsed, source)
    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 1
    assert codes[0].code == "TEST10"


def test_save_codes_deduplicates(scheduler_db, source):
    parsed = [
        {
            "code": "TEST10",
            "platform": "amazon_br",
            "description": "10% off",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "source_url": "https://example.com",
        }
    ]
    _save_codes(scheduler_db, parsed, source)
    _save_codes(scheduler_db, parsed, source)
    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 1


def test_save_codes_expires_old_codes(scheduler_db, source):
    code = PromoCode(
        code="OLD",
        platform=Platform.AMAZON_BR,
        description="Old code",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        source_url="https://example.com",
        expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        status=CodeStatus.ACTIVE,
    )
    scheduler_db.add(code)
    scheduler_db.commit()
    _save_codes(scheduler_db, [], source)
    scheduler_db.refresh(code)
    assert code.status == CodeStatus.EXPIRED


def test_update_source_reliability(scheduler_db, source):
    for i in range(4):
        code = PromoCode(
            code=f"CODE{i}",
            platform=Platform.AMAZON_BR,
            description=f"Code {i}",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10.0,
            source_url=source.url,
            votes_worked=8,
            votes_failed=2,
        )
        scheduler_db.add(code)
    scheduler_db.commit()
    _update_source_reliability(scheduler_db, source)
    scheduler_db.refresh(source)
    assert source.reliability_score > 0.5
