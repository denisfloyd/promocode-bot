# PromoCode AI

Public REST API that aggregates promotional codes from Brazilian e-commerce platforms into a single, searchable interface. Codes are collected via automated scraping, validated through crowdsourced feedback, and ranked by a confidence score.

Stop hunting through Facebook groups, Instagram, and chat groups for promo codes. Query one API instead.

## Supported Platforms

| Platform | Status |
|---|---|
| Amazon Brasil | Scraper ready |
| Mercado Livre | Scraper ready |

## Features

- **Automated scraping** — periodic collection of promo codes from platform coupon pages
- **Confidence scoring** — codes ranked by vote ratio, freshness, and source reliability
- **Crowdsourced validation** — users report whether codes worked or not
- **Filtering & sorting** — by platform, discount type, category, confidence, status
- **Pagination** — configurable page size (max 100 per page)
- **Rate limiting** — 60 requests/minute per IP
- **Admin controls** — trigger scrapers on demand, monitor scraping status
- **Auto-generated docs** — Swagger UI at `/docs`
- **Zero cost** — SQLite, in-memory cache, in-process scheduler. No Redis, no Celery, no external services

## Quick Start

### Requirements

- Python 3.12+

### Installation

```bash
git clone https://github.com/your-username/promocode-ai.git
cd promocode-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configuration

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./promocode.db` | Database file path |
| `ADMIN_TOKEN` | `change-me-to-a-secret-token` | Secret token for admin endpoints |
| `DEFAULT_SCRAPE_INTERVAL` | `30` | Scrape interval in minutes |
| `CACHE_TTL` | `300` | Cache TTL in seconds |
| `RATE_LIMIT` | `60/minute` | Global rate limit per IP |
| `LOG_LEVEL` | `INFO` | Logging level |

### Running

```bash
source .venv/bin/activate
python -m app.main
```

The API will be available at `http://localhost:8000`.

Interactive docs at `http://localhost:8000/docs`.

---

## API Reference

**Base URL:** `/api/v1`

### List Promo Codes

```
GET /api/v1/codes
```

Query parameters:

| Param | Type | Description |
|---|---|---|
| `platform` | string | `amazon_br` or `mercado_livre` |
| `discount_type` | string | `percentage`, `fixed_amount`, or `free_shipping` |
| `category` | string | Product category (e.g., `electronics`) |
| `min_confidence` | float | Minimum confidence score (0.0 to 1.0) |
| `status` | string | `active`, `expired`, or `flagged` |
| `sort_by` | string | `confidence_score`, `created_at`, `discount_value`, or `expires_at` |
| `order` | string | `asc` or `desc` (default: `desc`) |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 20, max: 100) |

**Example:**

```bash
# Get high-confidence active codes from Amazon BR
curl "http://localhost:8000/api/v1/codes?platform=amazon_br&status=active&min_confidence=0.7&sort_by=confidence_score&order=desc"
```

**Response:**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "code": "ELETRO10",
      "platform": "amazon_br",
      "description": "10% de desconto em eletrônicos",
      "discount_type": "percentage",
      "discount_value": 10.0,
      "min_purchase": null,
      "category": "Eletrônicos",
      "source_url": "https://www.amazon.com.br/coupons",
      "expires_at": "2026-04-01T00:00:00",
      "confidence_score": 0.87,
      "status": "active",
      "votes_worked": 45,
      "votes_failed": 5,
      "created_at": "2026-03-10T10:30:00",
      "updated_at": "2026-03-15T14:20:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "total_pages": 3
  }
}
```

### Get Single Code

```
GET /api/v1/codes/{id}
```

```bash
curl "http://localhost:8000/api/v1/codes/550e8400-e29b-41d4-a716-446655440000"
```

### Submit Feedback

Report whether a code worked or not. One vote per IP per code per day.

```
POST /api/v1/codes/{id}/feedback
```

```bash
curl -X POST "http://localhost:8000/api/v1/codes/550e8400/feedback" \
  -H "Content-Type: application/json" \
  -d '{"worked": true}'
```

**Response:**

```json
{
  "message": "Feedback submitted",
  "votes_worked": 46,
  "votes_failed": 5,
  "confidence_score": 0.88
}
```

### List Platforms

```
GET /api/v1/platforms
```

```json
{
  "data": [
    {"name": "Amazon Brasil", "code": "amazon_br", "active_codes": 28},
    {"name": "Mercado Livre", "code": "mercado_livre", "active_codes": 15}
  ]
}
```

### Get Stats

```
GET /api/v1/stats
```

```json
{
  "total_codes": 156,
  "active_codes": 43,
  "expired_codes": 113,
  "platforms": {
    "amazon_br": 89,
    "mercado_livre": 67
  }
}
```

### Health Check

```
GET /health
```

```json
{"status": "ok"}
```

---

## Admin Endpoints

Protected by the `X-Admin-Token` header. Set the token via the `ADMIN_TOKEN` environment variable.

### Trigger Scraping

```bash
# Scrape all platforms
curl -X POST "http://localhost:8000/api/v1/admin/scrape" \
  -H "X-Admin-Token: your-secret-token"

# Scrape a specific platform
curl -X POST "http://localhost:8000/api/v1/admin/scrape/amazon_br" \
  -H "X-Admin-Token: your-secret-token"
```

### Scraping Status

```bash
curl "http://localhost:8000/api/v1/admin/scrape/status" \
  -H "X-Admin-Token: your-secret-token"
```

```json
{
  "last_run": null,
  "sources": [
    {
      "name": "Amazon BR Coupons",
      "platform": "amazon_br",
      "is_active": true,
      "consecutive_failures": 0,
      "schedule_minutes": 30
    }
  ]
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "not_found",
    "message": "Code 550e8400 not found"
  }
}
```

| HTTP Code | Error Code | Description |
|---|---|---|
| 404 | `not_found` | Resource not found |
| 422 | (FastAPI default) | Validation error |
| 429 | `rate_limit_exceeded` | Too many requests |
| 429 | `duplicate_vote` | Already voted on this code today |
| 403 | `forbidden` | Invalid or missing admin token |

---

## Confidence Score

Every promo code gets a confidence score (0.0 to 1.0) that estimates how likely it is to work.

### Formula

```
confidence = (vote_score × 0.4) + (freshness × 0.3) + (source_reliability × 0.3)
```

| Component | Weight | Calculation |
|---|---|---|
| **Vote score** | 40% | Bayesian smoothed: `(worked + 1) / (worked + failed + 2)`. Defaults to 0.5 with no votes. |
| **Freshness** | 30% | Linear decay: `max(0, 1 - days_since_last_seen / 14)`. Codes unseen for 14+ days score 0. Expired codes forced to 0. |
| **Source reliability** | 30% | Average vote score of all codes from the same source with 3+ total votes. New sources default to 0.5. |

### Score Lifecycle

1. Code scraped → starts at **0.65** (vote=0.5, fresh=1.0, source=0.5)
2. Users vote "worked" → score rises
3. Users vote "didn't work" → score drops
4. Re-seen by scraper → freshness resets
5. Not re-seen for 14 days → freshness decays to 0
6. Past expiry date → auto-expired, score set to 0

### Anti-Gaming

- 1 vote per IP per code per 24 hours
- IP addresses are hashed (SHA-256) before storage — no raw IPs retained

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI App                        │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  /codes   │  │ /platforms│  │  /admin/scrape   │  │
│  │ /feedback │  │  /stats   │  │  (token-gated)   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │             │
│  ┌────▼──────────────▼──────────────────▼─────────┐  │
│  │              SQLAlchemy + SQLite (WAL)          │  │
│  │         PromoCode │ CodeFeedback │ Source       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─────────────────┐    ┌──────────────────────┐    │
│  │   APScheduler    │───▶│     Scrapers          │    │
│  │  (in-process)    │    │  Amazon BR │ ML       │    │
│  └─────────────────┘    └──────────────────────┘    │
│                                                      │
│  ┌─────────────────┐    ┌──────────────────────┐    │
│  │  Rate Limiter    │    │   TTL Cache           │    │
│  │  (slowapi)       │    │   (cachetools)        │    │
│  └─────────────────┘    └──────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
Scrapers (every 30 min)
    → Fetch HTML from platform coupon pages
    → Parse with BeautifulSoup
    → Deduplicate (code + platform unique constraint)
    → Insert/update in SQLite
    → Recalculate confidence scores
    → Clear cache

API Request
    → Rate limit check (60/min per IP)
    → Query SQLite (with filters)
    → Return JSON response
```

### Tech Stack

| Component | Choice | Why |
|---|---|---|
| Framework | FastAPI | Async, auto-docs, type-safe |
| Database | SQLite (WAL mode) | Zero cost, no server needed |
| Cache | cachetools | In-memory TTL cache, no Redis |
| Scheduler | APScheduler | In-process, no Celery/Redis |
| HTTP Client | httpx | Async, modern |
| HTML Parser | BeautifulSoup4 | Battle-tested |
| Rate Limiter | slowapi | Lightweight |
| Validation | Pydantic v2 | Comes with FastAPI |
| Testing | pytest | Standard |
| Linting | Ruff | Fast, all-in-one |

---

## Project Structure

```
promocode-ai/
├── app/
│   ├── main.py              # FastAPI app, startup, router mounting
│   ├── config.py             # Settings from env vars
│   ├── database.py           # SQLite engine, WAL mode, sessions
│   ├── cache.py              # TTLCache wrapper
│   ├── models/
│   │   ├── promo_code.py     # PromoCode, CodeFeedback
│   │   └── scraping_source.py
│   ├── schemas/
│   │   ├── promo_code.py     # Response/request models
│   │   └── feedback.py
│   ├── api/
│   │   ├── codes.py          # /codes, /codes/{id}, /codes/{id}/feedback
│   │   ├── platforms.py      # /platforms
│   │   ├── stats.py          # /stats
│   │   └── admin.py          # /admin/scrape/*
│   ├── scrapers/
│   │   ├── base.py           # BaseScraper (abstract)
│   │   ├── amazon_br.py      # Amazon BR implementation
│   │   └── mercado_livre.py  # Mercado Livre implementation
│   └── services/
│       ├── confidence.py     # Score calculation
│       └── scheduler.py      # APScheduler jobs
├── tests/                    # 60 tests
│   ├── conftest.py           # Shared fixtures
│   ├── test_api/             # API endpoint tests
│   ├── test_scrapers/        # Scraper tests (with HTML fixtures)
│   └── test_services/        # Service tests
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api/test_codes.py

# Run with coverage (install pytest-cov first)
pytest --cov=app
```

**Current test count: 60 tests**

| Test Suite | Tests | What's Tested |
|---|---|---|
| `test_codes` | 14 | Filtering, pagination, sorting, per_page cap, 404 |
| `test_feedback` | 4 | Vote submission, duplicate prevention, 404 |
| `test_platforms` | 2 | Platform listing, active code counts |
| `test_stats` | 2 | Empty stats, stats with data |
| `test_admin` | 7 | Token auth, scrape triggers, status, invalid platform |
| `test_base` | 5 | Abstract enforcement, parse, headers |
| `test_amazon_br` | 4 | HTML parsing, discount detection, empty page |
| `test_mercado_livre` | 4 | HTML parsing, min_purchase, discount types |
| `test_confidence` | 11 | Bayesian scoring, freshness decay, full formula |
| `test_scheduler` | 4 | Code saving, dedup, expiry, source reliability |

---

## Deployment

### Free Tier Options

The zero-cost stack means you can deploy anywhere Python runs:

- **Render** — free tier web service
- **Railway** — free starter plan
- **Fly.io** — free allowance
- **Any VPS** — just run `python -m app.main`

### Behind a Reverse Proxy

When deployed behind a load balancer or reverse proxy, configure your proxy to pass `X-Forwarded-For` headers so rate limiting works per real client IP, not per proxy IP.

---

## Roadmap

- [ ] Adapt scrapers to real Amazon BR and Mercado Livre page layouts
- [ ] Add wide-use code filtering (skip store-specific and narrow department codes)
- [ ] More platforms (Americanas, Magazine Luiza, Shopee, iFood)
- [ ] Telegram/WhatsApp bot consuming the API
- [ ] Web frontend
- [ ] Browser extension (auto-apply codes at checkout)
- [ ] API key authentication for usage tracking
- [ ] PostgreSQL + Redis migration for scale

---

## License

MIT
