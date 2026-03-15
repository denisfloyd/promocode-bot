# PromoCode AI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public REST API that aggregates and ranks promotional codes from Amazon BR and Mercado Livre.

**Architecture:** FastAPI monolith with SQLite (WAL mode), in-memory caching, APScheduler for periodic scraping, and crowdsourced feedback for code validation. All zero-cost, open source.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, SQLite, httpx, BeautifulSoup4, APScheduler, Pydantic v2, slowapi, cachetools, pytest

**Spec:** `docs/superpowers/specs/2026-03-15-promocode-ai-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, dependencies |
| `.env.example` | Environment variable template |
| `.gitignore` | Git ignore rules |
| `app/__init__.py` | Package marker |
| `app/main.py` | FastAPI app creation, lifespan (startup/shutdown), router mounting |
| `app/config.py` | Pydantic Settings class, loads env vars with defaults |
| `app/database.py` | SQLAlchemy engine, session factory, WAL mode setup, `create_all()` |
| `app/models/__init__.py` | Re-exports all models |
| `app/models/promo_code.py` | PromoCode and CodeFeedback SQLAlchemy models |
| `app/models/scraping_source.py` | ScrapingSource SQLAlchemy model |
| `app/schemas/__init__.py` | Re-exports all schemas |
| `app/schemas/promo_code.py` | Pydantic schemas for codes (request/response) |
| `app/schemas/feedback.py` | Pydantic schemas for feedback |
| `app/api/__init__.py` | Package marker |
| `app/api/codes.py` | `GET /codes`, `GET /codes/{id}`, `POST /codes/{id}/feedback` |
| `app/api/platforms.py` | `GET /platforms` |
| `app/api/stats.py` | `GET /stats` |
| `app/api/admin.py` | `POST /admin/scrape`, `POST /admin/scrape/{platform}`, `GET /admin/scrape/status` |
| `app/scrapers/__init__.py` | Package marker |
| `app/scrapers/base.py` | BaseScraper abstract class |
| `app/scrapers/amazon_br.py` | Amazon BR scraper implementation |
| `app/scrapers/mercado_livre.py` | Mercado Livre scraper implementation |
| `app/services/__init__.py` | Package marker |
| `app/services/confidence.py` | Confidence score calculation |
| `app/services/scheduler.py` | APScheduler setup, job management |
| `app/cache.py` | TTLCache wrapper with invalidation |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Shared fixtures (test DB, test client, factories) |
| `tests/test_api/__init__.py` | Package marker |
| `tests/test_api/test_codes.py` | Tests for /codes endpoints |
| `tests/test_api/test_feedback.py` | Tests for /codes/{id}/feedback |
| `tests/test_api/test_platforms.py` | Tests for /platforms |
| `tests/test_api/test_stats.py` | Tests for /stats |
| `tests/test_api/test_admin.py` | Tests for /admin endpoints |
| `tests/test_scrapers/__init__.py` | Package marker |
| `tests/test_scrapers/test_base.py` | Tests for BaseScraper |
| `tests/test_scrapers/test_amazon_br.py` | Tests for Amazon BR scraper |
| `tests/test_scrapers/test_mercado_livre.py` | Tests for Mercado Livre scraper |
| `tests/test_services/__init__.py` | Package marker |
| `tests/test_services/test_confidence.py` | Tests for confidence score calculation |

---

## Chunk 1: Project Foundation

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create `pyproject.toml` with all dependencies**

```toml
[project]
name = "promocode-ai"
version = "0.1.0"
description = "Public API aggregating promo codes from Brazilian e-commerce platforms"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "apscheduler>=3.10.0",
    "slowapi>=0.1.9",
    "cachetools>=5.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.5.0",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.env.example`**

```bash
# Database
DATABASE_URL=sqlite:///./promocode.db

# Admin
ADMIN_TOKEN=change-me-to-a-secret-token

# Scraping
DEFAULT_SCRAPE_INTERVAL=30

# Cache
CACHE_TTL=300

# Rate Limiting
RATE_LIMIT=60/minute

# Logging
LOG_LEVEL=INFO
```

- [ ] **Step 3: Create `.gitignore`**

```
__pycache__/
*.py[cod]
*.db
*.db-wal
*.db-shm
.env
.venv/
venv/
dist/
*.egg-info/
.pytest_cache/
.ruff_cache/
```

- [ ] **Step 4: Install dependencies**

Run: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: All packages installed successfully.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example .gitignore
git commit -m "chore: project setup with dependencies"
```

---

### Task 2: Configuration

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_services/__init__.py`

- [ ] **Step 1: Create package markers**

`app/__init__.py` — empty file.
`tests/__init__.py` — empty file.
`tests/test_services/__init__.py` — empty file.

- [ ] **Step 2: Write `app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./promocode.db"
    admin_token: str = "change-me-to-a-secret-token"
    default_scrape_interval: int = 30
    cache_ttl: int = 300
    rate_limit: str = "60/minute"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 3: Commit**

```bash
git add app/__init__.py app/config.py tests/__init__.py tests/test_services/__init__.py
git commit -m "feat: add configuration module with env var support"
```

---

### Task 3: Database Setup

**Files:**
- Create: `app/database.py`

- [ ] **Step 1: Write `app/database.py`**

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def set_sqlite_wal(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: Commit**

```bash
git add app/database.py
git commit -m "feat: database setup with SQLite WAL mode"
```

---

### Task 4: SQLAlchemy Models

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/promo_code.py`
- Create: `app/models/scraping_source.py`

- [ ] **Step 1: Write `app/models/promo_code.py`**

```python
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String, Boolean, ForeignKey, UniqueConstraint
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
```

- [ ] **Step 2: Write `app/models/scraping_source.py`**

```python
import uuid
from sqlalchemy import Boolean, Float, Integer, String, Enum
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
```

- [ ] **Step 3: Write `app/models/__init__.py`**

```python
from app.models.promo_code import PromoCode, CodeFeedback, Platform, DiscountType, CodeStatus
from app.models.scraping_source import ScrapingSource

__all__ = [
    "PromoCode",
    "CodeFeedback",
    "ScrapingSource",
    "Platform",
    "DiscountType",
    "CodeStatus",
]
```

- [ ] **Step 4: Commit**

```bash
git add app/models/
git commit -m "feat: SQLAlchemy models for PromoCode, CodeFeedback, ScrapingSource"
```

---

### Task 5: Pydantic Schemas

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/promo_code.py`
- Create: `app/schemas/feedback.py`

- [ ] **Step 1: Write `app/schemas/promo_code.py`**

```python
import enum
from datetime import datetime

from pydantic import BaseModel, Field


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
```

- [ ] **Step 2: Write `app/schemas/feedback.py`**

```python
from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    worked: bool


class FeedbackResponse(BaseModel):
    message: str
    votes_worked: int
    votes_failed: int
    confidence_score: float
```

- [ ] **Step 3: Write `app/schemas/__init__.py`**

```python
from app.schemas.promo_code import (
    PromoCodeResponse,
    PromoCodeListResponse,
    PaginationResponse,
    PlatformInfo,
    PlatformListResponse,
    StatsResponse,
    ErrorResponse,
    ErrorDetail,
    PlatformEnum,
    DiscountTypeEnum,
    CodeStatusEnum,
    SortByEnum,
    OrderEnum,
)
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

__all__ = [
    "PromoCodeResponse",
    "PromoCodeListResponse",
    "PaginationResponse",
    "PlatformInfo",
    "PlatformListResponse",
    "StatsResponse",
    "ErrorResponse",
    "ErrorDetail",
    "PlatformEnum",
    "DiscountTypeEnum",
    "CodeStatusEnum",
    "SortByEnum",
    "OrderEnum",
    "FeedbackRequest",
    "FeedbackResponse",
]
```

- [ ] **Step 4: Commit**

```bash
git add app/schemas/
git commit -m "feat: Pydantic schemas for API request/response models"
```

---

### Task 6: Test Fixtures

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_api/__init__.py`
- Create: `tests/test_scrapers/__init__.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import create_app
from app.models.promo_code import PromoCode, CodeFeedback, Platform, DiscountType, CodeStatus


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_wal(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

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
```

- [ ] **Step 2: Create package markers**

`tests/test_api/__init__.py` — empty file.
`tests/test_scrapers/__init__.py` — empty file.

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "feat: test fixtures with in-memory DB and sample data factories"
```

---

### Task 7: Minimal FastAPI App

**Files:**
- Create: `app/main.py`
- Create: `app/cache.py`
- Create: `app/api/__init__.py`
- Create: `app/api/codes.py` (stub)
- Create: `app/api/platforms.py` (stub)
- Create: `app/api/stats.py` (stub)
- Create: `app/api/admin.py` (stub)

- [ ] **Step 1: Write `app/cache.py`**

```python
from cachetools import TTLCache

from app.config import settings

cache = TTLCache(maxsize=256, ttl=settings.cache_ttl)


def clear_cache():
    cache.clear()
```

- [ ] **Step 2: Write `app/main.py`**

```python
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import init_db

logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


def create_app() -> FastAPI:
    app = FastAPI(
        title="PromoCode AI",
        description="Public API aggregating promo codes from Brazilian e-commerce platforms",
        version="0.1.0",
    )

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Try again later.",
                }
            },
        )

    @app.on_event("startup")
    def startup():
        init_db()
        logger.info("Database initialized")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Import and mount routers here as they are created
    from app.api.codes import router as codes_router
    from app.api.platforms import router as platforms_router
    from app.api.stats import router as stats_router
    from app.api.admin import router as admin_router

    app.include_router(codes_router, prefix="/api/v1")
    app.include_router(platforms_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 3: Create stub routers** (so `main.py` can import them and the app is in a working state)

`app/api/__init__.py` — empty file.

`app/api/codes.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["codes"])
```

`app/api/platforms.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["platforms"])
```

`app/api/stats.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["stats"])
```

`app/api/admin.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["admin"])
```

- [ ] **Step 4: Verify the app is importable**

Run: `python -c "from app.main import create_app; app = create_app(); print('OK')"`
Expected: "OK"

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/cache.py app/api/
git commit -m "feat: FastAPI app factory with rate limiting, cache, and stub routers"
```

---

## Chunk 2: API Endpoints

### Task 8: GET /codes and GET /codes/{id}

**Files:**
- Modify: `app/api/codes.py`
- Create: `tests/test_api/test_codes.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_api/test_codes.py`:

```python
def test_list_codes_empty(client):
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 0


def test_list_codes_returns_data(client, sample_codes):
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["pagination"]["total"] == 3


def test_list_codes_filter_by_platform(client, sample_codes):
    response = client.get("/api/v1/codes?platform=amazon_br")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    for code in data["data"]:
        assert code["platform"] == "amazon_br"


def test_list_codes_filter_by_status(client, sample_codes):
    response = client.get("/api/v1/codes?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_list_codes_filter_by_min_confidence(client, sample_codes):
    response = client.get("/api/v1/codes?min_confidence=0.7")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "AMAZON10"


def test_list_codes_filter_by_category(client, sample_codes):
    response = client.get("/api/v1/codes?category=electronics")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "SAVE50"


def test_list_codes_sort_by_confidence_desc(client, sample_codes):
    response = client.get("/api/v1/codes?sort_by=confidence_score&order=desc")
    assert response.status_code == 200
    data = response.json()
    scores = [c["confidence_score"] for c in data["data"]]
    assert scores == sorted(scores, reverse=True)


def test_list_codes_pagination(client, sample_codes):
    response = client.get("/api/v1/codes?page=1&per_page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["total_pages"] == 2


def test_list_codes_per_page_max_100(client, sample_codes):
    response = client.get("/api/v1/codes?per_page=200")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["per_page"] == 100


def test_list_codes_filter_by_discount_type(client, sample_codes):
    response = client.get("/api/v1/codes?discount_type=free_shipping")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "FRETEGRATIS"


def test_list_codes_sort_ascending(client, sample_codes):
    response = client.get("/api/v1/codes?sort_by=confidence_score&order=asc")
    assert response.status_code == 200
    data = response.json()
    scores = [c["confidence_score"] for c in data["data"]]
    assert scores == sorted(scores)


def test_list_codes_page_beyond_total(client, sample_codes):
    response = client.get("/api/v1/codes?page=999")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 3


def test_get_code_by_id(client, sample_code):
    response = client.get(f"/api/v1/codes/{sample_code.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "AMAZON10"
    assert data["id"] == sample_code.id


def test_get_code_not_found(client):
    response = client.get("/api/v1/codes/nonexistent-id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api/test_codes.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write `app/api/__init__.py`** — empty file.

- [ ] **Step 4: Write `app/api/codes.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api/test_codes.py -v`
Expected: All 15 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/api/codes.py tests/test_api/test_codes.py
git commit -m "feat: GET /codes and GET /codes/{id} with filtering and pagination"
```

---

### Task 9: Confidence Score Service

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/confidence.py`
- Create: `tests/test_services/test_confidence.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_services/test_confidence.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest

from app.services.confidence import (
    calculate_vote_score,
    calculate_freshness,
    calculate_confidence,
)


def _now():
    return datetime.now(timezone.utc)


class TestVoteScore:
    def test_no_votes_returns_0_5(self):
        assert calculate_vote_score(0, 0) == pytest.approx(0.5)

    def test_all_positive_votes(self):
        assert calculate_vote_score(10, 0) == pytest.approx(11 / 12)

    def test_all_negative_votes(self):
        assert calculate_vote_score(0, 10) == pytest.approx(1 / 12)

    def test_equal_votes(self):
        assert calculate_vote_score(5, 5) == pytest.approx(0.5)

    def test_bayesian_smoothing(self):
        # (3+1)/(3+2+2) = 4/7
        assert calculate_vote_score(3, 2) == pytest.approx(4 / 7)


class TestFreshness:
    def test_just_scraped(self):
        now = _now()
        assert calculate_freshness(now) == pytest.approx(1.0, abs=0.01)

    def test_7_days_old(self):
        seven_days_ago = _now() - timedelta(days=7)
        assert calculate_freshness(seven_days_ago) == pytest.approx(0.5, abs=0.01)

    def test_14_days_old(self):
        fourteen_days_ago = _now() - timedelta(days=14)
        assert calculate_freshness(fourteen_days_ago) == pytest.approx(0.0, abs=0.01)

    def test_older_than_14_days(self):
        old = _now() - timedelta(days=30)
        assert calculate_freshness(old) == pytest.approx(0.0)

    def test_expired_code(self):
        yesterday = _now() - timedelta(days=1)
        last_seen = _now()
        assert calculate_freshness(last_seen, expires_at=yesterday) == pytest.approx(0.0)

    def test_not_yet_expired(self):
        tomorrow = _now() + timedelta(days=1)
        last_seen = _now()
        result = calculate_freshness(last_seen, expires_at=tomorrow)
        assert result == pytest.approx(1.0, abs=0.01)


class TestConfidence:
    def test_new_code_default(self):
        score = calculate_confidence(
            votes_worked=0,
            votes_failed=0,
            updated_at=_now(),
            source_reliability=0.5,
        )
        assert score == pytest.approx(0.5, abs=0.01)

    def test_high_confidence_code(self):
        score = calculate_confidence(
            votes_worked=20,
            votes_failed=2,
            updated_at=_now(),
            source_reliability=0.9,
        )
        assert score > 0.8

    def test_low_confidence_old_code(self):
        score = calculate_confidence(
            votes_worked=1,
            votes_failed=10,
            updated_at=_now() - timedelta(days=14),
            source_reliability=0.3,
        )
        assert score < 0.2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_services/test_confidence.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `app/services/__init__.py`** — empty file.

- [ ] **Step 4: Write `app/services/confidence.py`**

```python
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


def calculate_vote_score(votes_worked: int, votes_failed: int) -> float:
    return (votes_worked + 1) / (votes_worked + votes_failed + 2)


def calculate_freshness(
    updated_at: datetime,
    expires_at: datetime | None = None,
) -> float:
    now = _now()
    # Make updated_at timezone-aware if it isn't
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            return 0.0
    days_since = (now - updated_at).total_seconds() / 86400
    return max(0.0, 1.0 - (days_since / 14.0))


def calculate_confidence(
    votes_worked: int,
    votes_failed: int,
    updated_at: datetime,
    source_reliability: float = 0.5,
    expires_at: datetime | None = None,
) -> float:
    vote_score = calculate_vote_score(votes_worked, votes_failed)
    freshness = calculate_freshness(updated_at, expires_at)
    return (vote_score * 0.4) + (freshness * 0.3) + (source_reliability * 0.3)


def recalculate_confidence(code, source_reliability: float = 0.5) -> float:
    return calculate_confidence(
        votes_worked=code.votes_worked,
        votes_failed=code.votes_failed,
        updated_at=code.updated_at,
        source_reliability=source_reliability,
        expires_at=code.expires_at,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_services/test_confidence.py -v`
Expected: All 11 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/services/ tests/test_services/test_confidence.py
git commit -m "feat: confidence score calculation with Bayesian smoothing and freshness decay"
```

---

### Task 10: POST /codes/{id}/feedback

**Files:**
- Create: `tests/test_api/test_feedback.py`
- Modify: `app/api/codes.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_api/test_feedback.py`:

```python
def test_submit_feedback_worked(client, sample_code):
    response = client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["votes_worked"] == 1
    assert data["votes_failed"] == 0
    assert data["message"] == "Feedback submitted"
    assert "confidence_score" in data


def test_submit_feedback_did_not_work(client, sample_code):
    response = client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["votes_worked"] == 0
    assert data["votes_failed"] == 1


def test_submit_feedback_code_not_found(client):
    response = client.post(
        "/api/v1/codes/nonexistent/feedback",
        json={"worked": True},
    )
    assert response.status_code == 404


def test_submit_feedback_duplicate_vote_same_day(client, sample_code, db_session):
    # First vote
    client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": True},
    )
    # Duplicate vote same day
    response = client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": True},
    )
    assert response.status_code == 429
    data = response.json()
    assert "already voted" in data["error"]["message"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api/test_feedback.py -v`
Expected: FAIL — endpoint not implemented.

- [ ] **Step 3: Add feedback endpoint to `app/api/codes.py`**

Add these imports at the top of `app/api/codes.py`:
```python
import hashlib
from datetime import datetime, date

from fastapi import APIRouter, Depends, Query, Request

from app.models import CodeFeedback
from app.schemas import FeedbackRequest, FeedbackResponse
from app.services.confidence import recalculate_confidence
```

Add this endpoint after the `get_code` function:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api/test_feedback.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/codes.py tests/test_api/test_feedback.py
git commit -m "feat: POST /codes/{id}/feedback with duplicate vote prevention"
```

---

### Task 11: GET /platforms and GET /stats

**Files:**
- Modify: `app/api/platforms.py`
- Modify: `app/api/stats.py`
- Create: `tests/test_api/test_platforms.py`
- Create: `tests/test_api/test_stats.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_api/test_platforms.py`:

```python
def test_list_platforms(client):
    response = client.get("/api/v1/platforms")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    codes = [p["code"] for p in data["data"]]
    assert "amazon_br" in codes
    assert "mercado_livre" in codes


def test_platforms_include_active_counts(client, sample_codes):
    response = client.get("/api/v1/platforms")
    assert response.status_code == 200
    data = response.json()
    for p in data["data"]:
        if p["code"] == "amazon_br":
            assert p["active_codes"] == 1  # SAVE50 is expired
        elif p["code"] == "mercado_livre":
            assert p["active_codes"] == 1
```

`tests/test_api/test_stats.py`:

```python
def test_stats_empty(client):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_codes"] == 0
    assert data["active_codes"] == 0


def test_stats_with_data(client, sample_codes):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_codes"] == 3
    assert data["active_codes"] == 2
    assert data["expired_codes"] == 1
    assert data["platforms"]["amazon_br"] == 2
    assert data["platforms"]["mercado_livre"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api/test_platforms.py tests/test_api/test_stats.py -v`
Expected: FAIL — no endpoints defined.

- [ ] **Step 3: Implement `app/api/platforms.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import PromoCode, Platform, CodeStatus
from app.schemas import PlatformListResponse, PlatformInfo

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
```

- [ ] **Step 4: Implement `app/api/stats.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import PromoCode, CodeStatus
from app.schemas import StatsResponse

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(PromoCode.id)).scalar()
    active = (
        db.query(func.count(PromoCode.id))
        .filter(PromoCode.status == CodeStatus.ACTIVE)
        .scalar()
    )
    expired = (
        db.query(func.count(PromoCode.id))
        .filter(PromoCode.status == CodeStatus.EXPIRED)
        .scalar()
    )
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api/test_platforms.py tests/test_api/test_stats.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/api/platforms.py app/api/stats.py tests/test_api/test_platforms.py tests/test_api/test_stats.py
git commit -m "feat: GET /platforms and GET /stats endpoints"
```

---

### Task 12: Admin Endpoints

**Files:**
- Modify: `app/api/admin.py`
- Create: `tests/test_api/test_admin.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_api/test_admin.py`:

```python
from app.config import settings


def test_admin_scrape_requires_token(client):
    response = client.post("/api/v1/admin/scrape")
    assert response.status_code == 403


def test_admin_scrape_wrong_token(client):
    response = client.post(
        "/api/v1/admin/scrape",
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert response.status_code == 403


def test_admin_scrape_valid_token(client):
    response = client.post(
        "/api/v1/admin/scrape",
        headers={"X-Admin-Token": settings.admin_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_admin_scrape_platform(client):
    response = client.post(
        "/api/v1/admin/scrape/amazon_br",
        headers={"X-Admin-Token": settings.admin_token},
    )
    assert response.status_code == 200


def test_admin_scrape_invalid_platform(client):
    response = client.post(
        "/api/v1/admin/scrape/invalid_platform",
        headers={"X-Admin-Token": settings.admin_token},
    )
    assert response.status_code == 422


def test_admin_scrape_status(client):
    response = client.get(
        "/api/v1/admin/scrape/status",
        headers={"X-Admin-Token": settings.admin_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "last_run" in data
    assert "sources" in data


def test_admin_scrape_status_requires_token(client):
    response = client.get("/api/v1/admin/scrape/status")
    assert response.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api/test_admin.py -v`
Expected: FAIL — no endpoints defined.

- [ ] **Step 3: Implement `app/api/admin.py`**

```python
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ScrapingSource
from app.schemas import PlatformEnum, ErrorResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_admin(token: str | None):
    if not token or token != settings.admin_token:
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "forbidden", "message": "Invalid or missing admin token"}},
        )
    return None


@router.post("/scrape")
def trigger_scrape_all(
    x_admin_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    err = _check_admin(x_admin_token)
    if err:
        return err
    return {"message": "Scraping triggered for all platforms"}


@router.post("/scrape/{platform}")
def trigger_scrape_platform(
    platform: PlatformEnum,
    x_admin_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    err = _check_admin(x_admin_token)
    if err:
        return err
    return {"message": f"Scraping triggered for {platform.value}"}


@router.get("/scrape/status")
def scrape_status(
    x_admin_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    err = _check_admin(x_admin_token)
    if err:
        return err
    sources = db.query(ScrapingSource).all()
    return {
        "last_run": None,
        "sources": [
            {
                "name": s.name,
                "platform": s.platform,
                "is_active": s.is_active,
                "consecutive_failures": s.consecutive_failures,
                "schedule_minutes": s.schedule_minutes,
            }
            for s in sources
        ],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api/test_admin.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/admin.py tests/test_api/test_admin.py
git commit -m "feat: admin endpoints for manual scrape triggering"
```

- [ ] **Step 6: Run all tests to verify nothing is broken**

Run: `pytest -v`
Expected: All tests PASS.

- [ ] **Step 7: Commit if any fixes were needed**

---

## Chunk 3: Scraping System

### Task 13: Base Scraper

**Files:**
- Create: `app/scrapers/__init__.py`
- Create: `app/scrapers/base.py`
- Create: `tests/test_scrapers/test_base.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_scrapers/test_base.py`:

```python
import pytest

from app.scrapers.base import BaseScraper


class ConcreteScraper(BaseScraper):
    platform = "test_platform"

    async def scrape(self):
        return [
            {
                "code": "TEST10",
                "description": "10% off",
                "discount_type": "percentage",
                "discount_value": 10.0,
                "source_url": "https://example.com",
            },
            {
                "code": "TEST20",
                "description": "R$20 off",
                "discount_type": "fixed_amount",
                "discount_value": 20.0,
                "source_url": "https://example.com",
            },
        ]


class FailingScraper(BaseScraper):
    platform = "test_platform"

    async def scrape(self):
        raise ConnectionError("Network error")


def test_scraper_is_abstract():
    with pytest.raises(TypeError):
        BaseScraper(source_url="https://example.com")


def test_concrete_scraper_instantiates():
    scraper = ConcreteScraper(source_url="https://example.com")
    assert scraper.source_url == "https://example.com"


@pytest.mark.asyncio
async def test_scrape_returns_raw_data():
    scraper = ConcreteScraper(source_url="https://example.com")
    results = await scraper.scrape()
    assert len(results) == 2
    assert results[0]["code"] == "TEST10"


@pytest.mark.asyncio
async def test_parse_normalizes_data():
    scraper = ConcreteScraper(source_url="https://example.com")
    raw = await scraper.scrape()
    parsed = scraper.parse(raw)
    assert len(parsed) == 2
    assert parsed[0]["platform"] == "test_platform"
    assert parsed[0]["source_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_failing_scraper_raises():
    scraper = FailingScraper(source_url="https://example.com")
    with pytest.raises(ConnectionError):
        await scraper.scrape()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scrapers/test_base.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `app/scrapers/__init__.py`** — empty file.

- [ ] **Step 4: Write `app/scrapers/base.py`**

```python
import random
from abc import ABC, abstractmethod

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class BaseScraper(ABC):
    platform: str = ""

    def __init__(self, source_url: str):
        self.source_url = source_url

    def get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }

    @abstractmethod
    async def scrape(self) -> list[dict]:
        """Fetch raw data from the source. Returns list of raw code dicts."""
        ...

    def parse(self, raw_data: list[dict]) -> list[dict]:
        """Normalize raw data into our standard format. Returns new dicts (no mutation)."""
        parsed = []
        for item in raw_data:
            entry = {**item, "platform": self.platform}
            if "source_url" not in entry:
                entry["source_url"] = self.source_url
            parsed.append(entry)
        return parsed
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_scrapers/test_base.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/scrapers/ tests/test_scrapers/test_base.py
git commit -m "feat: BaseScraper abstract class with user-agent rotation"
```

---

### Task 14: Amazon BR Scraper

**Files:**
- Create: `app/scrapers/amazon_br.py`
- Create: `tests/test_scrapers/test_amazon_br.py`
- Create: `tests/test_scrapers/fixtures/` (HTML fixtures)

- [ ] **Step 1: Create a sample HTML fixture**

`tests/test_scrapers/fixtures/amazon_br_coupons.html`:

```html
<html>
<body>
<div class="coupon-card">
    <span class="coupon-code">ELETRO10</span>
    <span class="coupon-description">10% de desconto em eletrônicos</span>
    <span class="coupon-discount">10%</span>
    <span class="coupon-category">Eletrônicos</span>
    <span class="coupon-expiry">2026-04-01</span>
</div>
<div class="coupon-card">
    <span class="coupon-code">FRETEGRATIS</span>
    <span class="coupon-description">Frete grátis para todo o Brasil</span>
    <span class="coupon-discount">Frete Grátis</span>
    <span class="coupon-expiry">2026-03-30</span>
</div>
</body>
</html>
```

- [ ] **Step 2: Write the failing tests**

`tests/test_scrapers/test_amazon_br.py`:

```python
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.amazon_br import AmazonBRScraper


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def scraper():
    return AmazonBRScraper(source_url="https://www.amazon.com.br/coupons")


@pytest.fixture
def sample_html():
    return (FIXTURES_DIR / "amazon_br_coupons.html").read_text()


@pytest.mark.asyncio
async def test_scrape_parses_coupon_cards(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        assert len(results) == 2
        assert results[0]["code"] == "ELETRO10"
        assert results[0]["description"] == "10% de desconto em eletrônicos"


@pytest.mark.asyncio
async def test_scrape_detects_discount_type(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        assert results[0]["discount_type"] == "percentage"
        assert results[0]["discount_value"] == 10.0
        assert results[1]["discount_type"] == "free_shipping"
        assert results[1]["discount_value"] == 0.0


@pytest.mark.asyncio
async def test_parse_adds_platform(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        raw = await scraper.scrape()
        parsed = scraper.parse(raw)
        for item in parsed:
            assert item["platform"] == "amazon_br"


@pytest.mark.asyncio
async def test_scrape_handles_empty_page(scraper):
    with patch.object(
        scraper, "_fetch_html", new_callable=AsyncMock, return_value="<html><body></body></html>"
    ):
        results = await scraper.scrape()
        assert results == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_scrapers/test_amazon_br.py -v`
Expected: FAIL — module not found.

- [ ] **Step 4: Write `app/scrapers/amazon_br.py`**

```python
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper


class AmazonBRScraper(BaseScraper):
    platform = "amazon_br"

    async def _fetch_html(self, url: str | None = None) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url or self.source_url,
                headers=self.get_headers(),
                follow_redirects=True,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.text

    async def scrape(self) -> list[dict]:
        html = await self._fetch_html()
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for card in soup.select(".coupon-card"):
            code_el = card.select_one(".coupon-code")
            desc_el = card.select_one(".coupon-description")
            discount_el = card.select_one(".coupon-discount")
            category_el = card.select_one(".coupon-category")
            expiry_el = card.select_one(".coupon-expiry")

            if not code_el or not desc_el:
                continue

            code = code_el.get_text(strip=True)
            description = desc_el.get_text(strip=True)
            discount_text = discount_el.get_text(strip=True) if discount_el else ""
            category = category_el.get_text(strip=True) if category_el else None
            expiry = expiry_el.get_text(strip=True) if expiry_el else None

            discount_type, discount_value = self._parse_discount(discount_text)

            item = {
                "code": code,
                "description": description,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "source_url": self.source_url,
            }
            if category:
                item["category"] = category
            if expiry:
                item["expires_at"] = expiry

            results.append(item)

        return results

    def _parse_discount(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        if "frete" in text_lower or "shipping" in text_lower:
            return "free_shipping", 0.0

        pct_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
        if pct_match:
            value = float(pct_match.group(1).replace(",", "."))
            return "percentage", value

        val_match = re.search(r"R?\$?\s*(\d+(?:[.,]\d+)?)", text)
        if val_match:
            value = float(val_match.group(1).replace(",", "."))
            return "fixed_amount", value

        return "percentage", 0.0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_scrapers/test_amazon_br.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/scrapers/amazon_br.py tests/test_scrapers/test_amazon_br.py tests/test_scrapers/fixtures/
git commit -m "feat: Amazon BR scraper with HTML parsing and discount detection"
```

---

### Task 15: Mercado Livre Scraper

**Files:**
- Create: `app/scrapers/mercado_livre.py`
- Create: `tests/test_scrapers/test_mercado_livre.py`
- Create: `tests/test_scrapers/fixtures/mercado_livre_coupons.html`

- [ ] **Step 1: Create a sample HTML fixture**

`tests/test_scrapers/fixtures/mercado_livre_coupons.html`:

```html
<html>
<body>
<div class="coupon-item">
    <span class="coupon-code">ML15OFF</span>
    <span class="coupon-desc">15% de desconto em moda</span>
    <span class="coupon-value">15%</span>
    <span class="coupon-category">Moda</span>
    <span class="coupon-expires">2026-04-15</span>
</div>
<div class="coupon-item">
    <span class="coupon-code">DESCONTO30</span>
    <span class="coupon-desc">R$30 de desconto acima de R$100</span>
    <span class="coupon-value">R$30</span>
    <span class="coupon-min-purchase">100</span>
</div>
</body>
</html>
```

- [ ] **Step 2: Write the failing tests**

`tests/test_scrapers/test_mercado_livre.py`:

```python
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.mercado_livre import MercadoLivreScraper


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def scraper():
    return MercadoLivreScraper(source_url="https://www.mercadolivre.com.br/cupons")


@pytest.fixture
def sample_html():
    return (FIXTURES_DIR / "mercado_livre_coupons.html").read_text()


@pytest.mark.asyncio
async def test_scrape_parses_coupon_items(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        assert len(results) == 2
        assert results[0]["code"] == "ML15OFF"


@pytest.mark.asyncio
async def test_scrape_detects_discount_types(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        assert results[0]["discount_type"] == "percentage"
        assert results[0]["discount_value"] == 15.0
        assert results[1]["discount_type"] == "fixed_amount"
        assert results[1]["discount_value"] == 30.0


@pytest.mark.asyncio
async def test_scrape_parses_min_purchase(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        assert results[1].get("min_purchase") == 100.0


@pytest.mark.asyncio
async def test_parse_adds_platform(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        raw = await scraper.scrape()
        parsed = scraper.parse(raw)
        for item in parsed:
            assert item["platform"] == "mercado_livre"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_scrapers/test_mercado_livre.py -v`
Expected: FAIL — module not found.

- [ ] **Step 4: Write `app/scrapers/mercado_livre.py`**

```python
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper


class MercadoLivreScraper(BaseScraper):
    platform = "mercado_livre"

    async def _fetch_html(self, url: str | None = None) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url or self.source_url,
                headers=self.get_headers(),
                follow_redirects=True,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.text

    async def scrape(self) -> list[dict]:
        html = await self._fetch_html()
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for card in soup.select(".coupon-item"):
            code_el = card.select_one(".coupon-code")
            desc_el = card.select_one(".coupon-desc")
            value_el = card.select_one(".coupon-value")
            category_el = card.select_one(".coupon-category")
            expiry_el = card.select_one(".coupon-expires")
            min_purchase_el = card.select_one(".coupon-min-purchase")

            if not code_el or not desc_el:
                continue

            code = code_el.get_text(strip=True)
            description = desc_el.get_text(strip=True)
            value_text = value_el.get_text(strip=True) if value_el else ""
            category = category_el.get_text(strip=True) if category_el else None
            expiry = expiry_el.get_text(strip=True) if expiry_el else None

            discount_type, discount_value = self._parse_discount(value_text)

            item = {
                "code": code,
                "description": description,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "source_url": self.source_url,
            }
            if category:
                item["category"] = category
            if expiry:
                item["expires_at"] = expiry
            if min_purchase_el:
                try:
                    item["min_purchase"] = float(min_purchase_el.get_text(strip=True))
                except ValueError:
                    pass

            results.append(item)

        return results

    def _parse_discount(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        if "frete" in text_lower or "shipping" in text_lower:
            return "free_shipping", 0.0

        pct_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
        if pct_match:
            value = float(pct_match.group(1).replace(",", "."))
            return "percentage", value

        val_match = re.search(r"R?\$?\s*(\d+(?:[.,]\d+)?)", text)
        if val_match:
            value = float(val_match.group(1).replace(",", "."))
            return "fixed_amount", value

        return "percentage", 0.0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_scrapers/test_mercado_livre.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/scrapers/mercado_livre.py tests/test_scrapers/test_mercado_livre.py tests/test_scrapers/fixtures/mercado_livre_coupons.html
git commit -m "feat: Mercado Livre scraper with HTML parsing"
```

---

## Chunk 4: Scheduler & Integration

### Task 16: Scheduler Service

**Files:**
- Create: `app/services/scheduler.py`
- Create: `tests/test_services/test_scheduler.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_services/test_scheduler.py`:

```python
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import PromoCode, ScrapingSource, CodeStatus, Platform, DiscountType
from app.services.scheduler import _save_codes, _update_source_reliability


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
    assert len(codes) == 1  # Not duplicated


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
    # Add codes with enough votes
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
    assert source.reliability_score > 0.5  # Should improve with positive votes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_services/test_scheduler.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `app/services/scheduler.py`**

```python
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.cache import clear_cache
from app.database import SessionLocal
from app.models import PromoCode, ScrapingSource, CodeStatus
from app.services.confidence import calculate_confidence, calculate_vote_score

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_executor = ThreadPoolExecutor(max_workers=2)

SCRAPER_MAP = {}


def register_scrapers():
    from app.scrapers.amazon_br import AmazonBRScraper
    from app.scrapers.mercado_livre import MercadoLivreScraper

    SCRAPER_MAP["amazon_br"] = AmazonBRScraper
    SCRAPER_MAP["mercado_livre"] = MercadoLivreScraper


def run_scraper_job(source_id: str):
    db = SessionLocal()
    try:
        source = db.query(ScrapingSource).filter(ScrapingSource.id == source_id).first()
        if not source or not source.is_active:
            return

        scraper_cls = SCRAPER_MAP.get(source.scraper_type)
        if not scraper_cls:
            logger.error(f"No scraper found for type: {source.scraper_type}")
            return

        scraper = scraper_cls(source_url=source.url)
        raw_data = asyncio.run(scraper.scrape())
        parsed = scraper.parse(raw_data)
        _save_codes(db, parsed, source)
        _update_source_reliability(db, source)

        source.consecutive_failures = 0
        db.commit()
        clear_cache()
        logger.info(f"Scraped {len(parsed)} codes from {source.name}")

    except Exception as e:
        logger.error(f"Scraper failed for {source_id}: {e}")
        source = db.query(ScrapingSource).filter(ScrapingSource.id == source_id).first()
        if source:
            source.consecutive_failures += 1
            if source.consecutive_failures >= 5:
                source.is_active = False
                logger.warning(f"Disabled source {source.name} after 5 consecutive failures")
            db.commit()
    finally:
        db.close()


def _save_codes(db: Session, parsed: list[dict], source: ScrapingSource):
    now = datetime.now(timezone.utc)

    for item in parsed:
        existing = (
            db.query(PromoCode)
            .filter(
                PromoCode.code == item["code"],
                PromoCode.platform == item["platform"],
            )
            .first()
        )

        if existing:
            existing.updated_at = now
            existing.confidence_score = calculate_confidence(
                votes_worked=existing.votes_worked,
                votes_failed=existing.votes_failed,
                updated_at=existing.updated_at,
                source_reliability=source.reliability_score,
                expires_at=existing.expires_at,
            )
        else:
            expires_at = None
            if item.get("expires_at"):
                try:
                    expires_at = datetime.fromisoformat(item["expires_at"])
                except (ValueError, TypeError):
                    pass

            code = PromoCode(
                code=item["code"],
                platform=item["platform"],
                description=item.get("description", ""),
                discount_type=item.get("discount_type", "percentage"),
                discount_value=item.get("discount_value", 0.0),
                min_purchase=item.get("min_purchase"),
                category=item.get("category"),
                source_url=item.get("source_url", source.url),
                expires_at=expires_at,
                confidence_score=0.5,
                status=CodeStatus.ACTIVE,
            )
            db.add(code)

    # Batch: expire old codes and recalculate freshness decay
    active_codes = db.query(PromoCode).filter(PromoCode.status == CodeStatus.ACTIVE).all()
    for code in active_codes:
        if code.expires_at and code.expires_at.replace(tzinfo=timezone.utc) < now:
            code.status = CodeStatus.EXPIRED
            code.confidence_score = 0.0

    db.commit()


def _update_source_reliability(db: Session, source: ScrapingSource):
    """Recalculate source reliability as avg vote_score of codes with >= 3 votes."""
    codes = (
        db.query(PromoCode)
        .filter(
            PromoCode.source_url.contains(source.url),
            (PromoCode.votes_worked + PromoCode.votes_failed) >= 3,
        )
        .all()
    )
    if codes:
        scores = [calculate_vote_score(c.votes_worked, c.votes_failed) for c in codes]
        source.reliability_score = sum(scores) / len(scores)
    # If no codes with enough votes, keep existing reliability_score


def start_scheduler(db: Session):
    register_scrapers()
    sources = db.query(ScrapingSource).filter(ScrapingSource.is_active == True).all()

    for source in sources:
        scheduler.add_job(
            run_scraper_job,
            "interval",
            minutes=source.schedule_minutes,
            args=[source.id],
            id=f"scrape_{source.id}",
            replace_existing=True,
        )

    if not scheduler.running:
        scheduler.start()
    logger.info(f"Scheduler started with {len(sources)} sources")


def trigger_scrape(platform: str | None = None):
    """Trigger scraping in background threads (non-blocking)."""
    db = SessionLocal()
    try:
        query = db.query(ScrapingSource).filter(ScrapingSource.is_active == True)
        if platform:
            query = query.filter(ScrapingSource.platform == platform)
        sources = query.all()
        for source in sources:
            _executor.submit(run_scraper_job, source.id)
    finally:
        db.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_services/test_scheduler.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/scheduler.py tests/test_services/test_scheduler.py
git commit -m "feat: APScheduler service with scraper jobs and source reliability"
```

---

### Task 17: Wire Everything Together

**Files:**
- Modify: `app/main.py` — add scheduler startup
- Modify: `app/api/admin.py` — wire admin endpoints to scheduler

- [ ] **Step 1: Update `app/main.py` to start the scheduler**

Add to the `startup` function inside `create_app()`:

```python
    @app.on_event("startup")
    def startup():
        init_db()
        logger.info("Database initialized")
        from app.services.scheduler import start_scheduler
        db = SessionLocal()
        try:
            start_scheduler(db)
        finally:
            db.close()
```

Add import at top:
```python
from app.database import init_db, SessionLocal
```

- [ ] **Step 2: Update `app/api/admin.py` to trigger scrapers**

In `trigger_scrape_all`, replace the return with:
```python
    from app.services.scheduler import trigger_scrape
    trigger_scrape()  # Non-blocking: runs in background thread
    return {"message": "Scraping triggered for all platforms"}
```

In `trigger_scrape_platform`, replace the return with:
```python
    from app.services.scheduler import trigger_scrape
    trigger_scrape(platform=platform.value)  # Non-blocking
    return {"message": f"Scraping triggered for {platform.value}"}
```

- [ ] **Step 3: Run all tests**

Run: `pytest -v`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add app/main.py app/api/admin.py
git commit -m "feat: wire scheduler startup and admin scrape triggers"
```

---

### Task 18: Final Integration Test

**Files:**
- No new files — just verify everything works end-to-end.

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v --tb=short`
Expected: All tests PASS.

- [ ] **Step 2: Run linting**

Run: `ruff check app/ tests/`
Expected: No errors (or fix any that appear).

- [ ] **Step 3: Test the app starts**

Run: `python -c "from app.main import create_app; app = create_app(); print('App created successfully')"`
Expected: "App created successfully"

- [ ] **Step 4: Commit any final fixes**

```bash
git add -A
git commit -m "chore: final integration verification"
```

- [ ] **Step 5: Run `pytest` one final time to confirm green**

Run: `pytest -v`
Expected: All tests PASS.
