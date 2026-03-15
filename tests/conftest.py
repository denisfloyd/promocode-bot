import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app
from app.models.promo_code import CodeStatus, DiscountType, Platform, PromoCode


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_code(db_session):
    code = PromoCode(
        code="AMAZON10",
        platform=Platform.AMAZON_BR,
        description="10% off electronics",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        source_url="https://example.com/coupons",
        confidence_score=0.75,
        status=CodeStatus.ACTIVE,
    )
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


@pytest.fixture
def sample_codes(db_session):
    codes = [
        PromoCode(
            code="AMAZON10",
            platform=Platform.AMAZON_BR,
            description="10% off electronics",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10.0,
            source_url="https://example.com/c1",
            confidence_score=0.8,
            status=CodeStatus.ACTIVE,
        ),
        PromoCode(
            code="FRETEGRATIS",
            platform=Platform.MERCADO_LIVRE,
            description="Free shipping",
            discount_type=DiscountType.FREE_SHIPPING,
            discount_value=0.0,
            source_url="https://example.com/c2",
            confidence_score=0.6,
            status=CodeStatus.ACTIVE,
        ),
        PromoCode(
            code="SAVE50",
            platform=Platform.AMAZON_BR,
            description="R$50 off",
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=50.0,
            category="electronics",
            source_url="https://example.com/c3",
            confidence_score=0.3,
            status=CodeStatus.EXPIRED,
        ),
    ]
    db_session.add_all(codes)
    db_session.commit()
    for c in codes:
        db_session.refresh(c)
    return codes
