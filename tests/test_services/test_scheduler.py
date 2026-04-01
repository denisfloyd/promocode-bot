from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import CodeStatus, DiscountType, Platform, PromoCode
from app.services.scheduler import _save_telegram_codes, cleanup_old_codes


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


def test_save_telegram_codes_inserts_new(scheduler_db):
    parsed = [
        {
            "code": "LEVE20",
            "platform": "amazon_br",
            "description": "20% off",
            "discount_type": "percentage",
            "discount_value": 20.0,
        }
    ]
    _save_telegram_codes(scheduler_db, parsed)
    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 1
    assert codes[0].code == "LEVE20"
    assert codes[0].source_url == "telegram"


def test_save_telegram_codes_deduplicates(scheduler_db):
    parsed = [
        {
            "code": "LEVE20",
            "platform": "amazon_br",
            "description": "20% off",
            "discount_type": "percentage",
            "discount_value": 20.0,
        }
    ]
    _save_telegram_codes(scheduler_db, parsed)
    _save_telegram_codes(scheduler_db, parsed)
    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 1


def test_save_telegram_codes_updates_existing(scheduler_db):
    parsed = [
        {
            "code": "LEVE20",
            "platform": "amazon_br",
            "description": "20% off",
            "discount_type": "percentage",
            "discount_value": 20.0,
        }
    ]
    _save_telegram_codes(scheduler_db, parsed)
    first_update = scheduler_db.query(PromoCode).first().updated_at
    _save_telegram_codes(scheduler_db, parsed)
    scheduler_db.expire_all()
    second_update = scheduler_db.query(PromoCode).first().updated_at
    assert second_update >= first_update


def test_cleanup_deletes_old_codes_no_votes(scheduler_db, monkeypatch):
    """Codes older than 24h with 0 worked votes get deleted."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=25)
    code = PromoCode(
        code="OLDCODE",
        platform=Platform.AMAZON_BR,
        description="Old code",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        source_url="telegram",
        votes_worked=0,
        votes_failed=0,
        created_at=old_time,
    )
    scheduler_db.add(code)
    scheduler_db.commit()

    # Monkeypatch SessionLocal to return our test session
    monkeypatch.setattr("app.services.scheduler.SessionLocal", lambda: scheduler_db)
    # Prevent close from actually closing (we still need the session)
    monkeypatch.setattr(scheduler_db, "close", lambda: None)

    cleanup_old_codes()

    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 0


def test_cleanup_keeps_recent_codes(scheduler_db, monkeypatch):
    """Codes less than 24h old are kept."""
    code = PromoCode(
        code="NEWCODE",
        platform=Platform.AMAZON_BR,
        description="New code",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        source_url="telegram",
        votes_worked=0,
        votes_failed=0,
    )
    scheduler_db.add(code)
    scheduler_db.commit()

    monkeypatch.setattr("app.services.scheduler.SessionLocal", lambda: scheduler_db)
    monkeypatch.setattr(scheduler_db, "close", lambda: None)

    cleanup_old_codes()

    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 1


def test_cleanup_keeps_old_codes_with_votes(scheduler_db, monkeypatch):
    """Codes older than 24h but with positive votes are kept."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=48)
    code = PromoCode(
        code="VOTED",
        platform=Platform.AMAZON_BR,
        description="Voted code",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        source_url="telegram",
        votes_worked=3,
        votes_failed=1,
        created_at=old_time,
    )
    scheduler_db.add(code)
    scheduler_db.commit()

    monkeypatch.setattr("app.services.scheduler.SessionLocal", lambda: scheduler_db)
    monkeypatch.setattr(scheduler_db, "close", lambda: None)

    cleanup_old_codes()

    codes = scheduler_db.query(PromoCode).all()
    assert len(codes) == 1
    assert codes[0].code == "VOTED"
