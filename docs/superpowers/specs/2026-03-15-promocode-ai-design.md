# PromoCode AI — Design Spec

## Overview

A public, open-source REST API that aggregates promotional codes from Brazilian e-commerce platforms (Amazon BR, Mercado Livre) into a single searchable interface. Codes are collected via automated scraping, validated through crowdsourced feedback, and ranked by a confidence score.

**Target audience:** Brazilian consumers.
**Approach:** API-first monolith. No frontend in MVP — any client (web app, Telegram bot, browser extension) can consume the API later.
**Cost:** Zero. All tools and infrastructure are free/open source.
**License:** MIT.

---

## Data Model

### PromoCode

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique identifier |
| `code` | string | The actual promo code (e.g., `AMAZON10OFF`) |
| `platform` | enum | `amazon_br`, `mercado_livre` |
| `description` | string | What the code does ("10% off electronics") |
| `discount_type` | enum | `percentage`, `fixed_amount`, `free_shipping` |
| `discount_value` | decimal | The discount amount (10 for 10%, 50 for R$50) |
| `min_purchase` | decimal (nullable) | Minimum purchase required |
| `category` | string (nullable) | Product category if applicable |
| `source_url` | string | Where the code was scraped from |
| `expires_at` | datetime (nullable) | Expiration date if known |
| `confidence_score` | float (0-1) | Calculated from votes + age + source reliability |
| `status` | enum | `active`, `expired`, `flagged` |
| `votes_worked` | int | Count of "worked" feedback |
| `votes_failed` | int | Count of "didn't work" feedback |
| `created_at` | datetime | When we first found it |
| `updated_at` | datetime | Last update |

### ScrapingSource

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique identifier |
| `platform` | enum | Which platform this source covers |
| `name` | string | Human-readable name |
| `url` | string | URL to scrape |
| `scraper_type` | string | Which scraper class handles this |
| `schedule_minutes` | int | How often to scrape (in minutes) |
| `is_active` | boolean | Enable/disable this source |
| `reliability_score` | float | Historical accuracy of codes from this source |

### CodeFeedback

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique identifier |
| `code_id` | UUID (FK) | Which promo code |
| `worked` | boolean | Did it work? |
| `ip_hash` | string | Hashed IP for anti-gaming |
| `created_at` | datetime | When submitted |

---

## API Design

Public REST API. No authentication. Global rate limiting at 60 requests/minute per IP. When deployed behind a reverse proxy (Render, Railway, etc.), the app must be configured to trust `X-Forwarded-For` headers so rate limiting applies per real client IP, not per proxy IP.

**Base URL:** `/api/v1`

### Public Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/codes` | List promo codes with filters |
| `GET` | `/codes/{id}` | Get a single code with full details |
| `POST` | `/codes/{id}/feedback` | Submit "worked" / "didn't work" |
| `GET` | `/platforms` | List supported platforms |
| `GET` | `/stats` | Basic stats (total codes, active codes, per platform) |

### Admin Endpoints (protected by `X-Admin-Token` header)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/admin/scrape` | Trigger all scrapers immediately |
| `POST` | `/admin/scrape/{platform}` | Trigger a specific platform scraper |
| `GET` | `/admin/scrape/status` | Check last run status, next scheduled run, errors |

Admin token is set via environment variable `ADMIN_TOKEN`.

### Filtering & Pagination on `GET /codes`

| Param | Type | Example |
|---|---|---|
| `platform` | string | `?platform=amazon_br` |
| `discount_type` | string | `?discount_type=percentage` |
| `category` | string | `?category=electronics` |
| `min_confidence` | float | `?min_confidence=0.7` |
| `status` | string | `?status=active` |
| `sort_by` | string | `?sort_by=confidence_score` |
| `order` | string | `?order=desc` |
| `page` | int | `?page=1` |
| `per_page` | int | `?per_page=20` (max 100) |

**Allowed `sort_by` values:** `confidence_score`, `created_at`, `discount_value`, `expires_at`.

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

**Error response format:**

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit of 60 requests/minute exceeded. Try again in 45 seconds."
  }
}
```

Standard HTTP codes: 404 (not found), 422 (validation error), 429 (rate limited), 500 (server error).

FastAPI auto-generates Swagger docs at `/docs`.

---

## Scraping Architecture

### Structure

```
BaseScraper (abstract)
  ├── AmazonBRScraper
  └── MercadoLivreScraper
```

- **BaseScraper** defines the interface: `scrape()` returns raw data, `parse()` normalizes into our data model, `deduplicate()` avoids inserting codes we already have.
- Each platform gets its own scraper class that knows where to look and how to parse that platform's HTML.

### Sources

| Platform | What to scrape |
|---|---|
| Amazon BR | Coupon landing pages, deal pages, promotional banners |
| Mercado Livre | Cupons section, promotional campaigns, seller coupons |

**Alternative sources (fallback):** If direct platform scraping is blocked by anti-bot measures, scrape third-party coupon aggregator sites and community forums that list codes for these platforms instead.

### Anti-Bot Mitigation

Both Amazon BR and Mercado Livre employ anti-scraping protections (CAPTCHAs, IP blocking, rate limiting, dynamic rendering). Strategies to handle this:

- **Respectful scraping** — rate limit requests, use delays between requests, respect `robots.txt`
- **User-Agent rotation** — rotate realistic browser user-agents
- **Playwright fallback** — use headless browser for JavaScript-rendered pages
- **Fallback sources** — if a platform blocks direct scraping, pivot to scraping third-party coupon sites that aggregate codes for that platform
- **Source auto-disable** — after 5 consecutive failures, disable the source and log a warning for manual review

**Legal note:** This project scrapes publicly available promotional information. Codes are public-facing marketing tools intended for consumer use. The project does not access private data, bypass authentication, or violate LGPD (Brazilian data protection law). However, users deploying this should review platform ToS in their jurisdiction.

### Tools

- **httpx** — async HTTP client for simple pages
- **BeautifulSoup4** — HTML parsing and extraction
- **Playwright** — only if needed for JavaScript-rendered pages

### Scheduling

- **APScheduler** runs in-process alongside the API
- Each scraping source has its own configurable schedule
- Default: every 30 minutes for both platforms
- On each run: scrape → parse → deduplicate → insert new codes → recalculate confidence scores

### Manual Trigger

Admin endpoints allow triggering scrapers on demand via HTTP (protected by `X-Admin-Token`).

### Deduplication

- Match on `code` + `platform` combination
- If a code already exists, update its `updated_at` timestamp
- Codes not re-seen for configurable number of days get their confidence decayed

### Error Handling

- Failed scrapes are logged; retry happens on next scheduled run
- Scrapers run in background threads — they cannot crash the API
- Auto-disable a source after 5 consecutive failures, log a warning

---

## Confidence Score System

### Formula

```
confidence = (vote_score * 0.4) + (freshness * 0.3) + (source_reliability * 0.3)
```

### Components

| Factor | Weight | Calculation |
|---|---|---|
| `vote_score` | 40% | Bayesian smoothed: `(votes_worked + 1) / (votes_worked + votes_failed + 2)` — naturally defaults to 0.5 with no votes, stabilizes with more data |
| `freshness` | 30% | Linear decay: `max(0, 1 - (days_since_last_seen / 14))` — 1.0 when just scraped, reaches 0 after 14 days unseen. If `expires_at` is set and past, freshness is forced to 0 |
| `source_reliability` | 30% | Average vote_score of all codes from this source that have >= 3 total votes. Starts at 0.5 for new sources. Recalculated after each scraper run |

### Score Lifecycle

1. New code scraped → starts at 0.5 (neutral, unverified)
2. "Worked" votes → score rises
3. "Didn't work" votes → score drops
4. Re-seen by scraper → freshness resets
5. Not re-seen for days → freshness decays
6. Past expiry date → auto-set to `expired` status

### Anti-Gaming

- 1 vote per hashed IP per code per 24 hours (enforced via `ip_hash` + `code_id` + date unique constraint)
- Bayesian smoothing naturally handles low vote counts — no artificial threshold needed
- Burst detection: ignore >10 votes on same code from same hashed IP in 1 minute

### Recalculation Triggers

- When new feedback is submitted (single code)
- After each scraper run (batch recalculation for freshness decay)

---

## Project Structure

```
promocode-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, startup, scheduler init
│   ├── config.py             # Settings (env vars, defaults)
│   ├── database.py           # SQLite connection, session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── promo_code.py     # PromoCode, CodeFeedback models
│   │   └── scraping_source.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── promo_code.py     # Pydantic request/response schemas
│   │   └── feedback.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── codes.py          # /codes endpoints
│   │   ├── platforms.py      # /platforms endpoint
│   │   ├── stats.py          # /stats endpoint
│   │   └── admin.py          # /admin/scrape endpoints
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py           # BaseScraper abstract class
│   │   ├── amazon_br.py      # Amazon BR scraper
│   │   └── mercado_livre.py  # Mercado Livre scraper
│   ├── services/
│   │   ├── __init__.py
│   │   ├── confidence.py     # Score calculation logic
│   │   └── scheduler.py      # APScheduler setup
│   └── cache.py              # In-memory cache layer
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_scrapers/
│   └── test_services/
├── .env.example              # Template for env vars
├── .gitignore
├── LICENSE                   # MIT
├── pyproject.toml            # Dependencies, project metadata
└── README.md
```

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| **Framework** | FastAPI | Async, auto-docs, type-safe |
| **Database** | SQLite (WAL mode) + SQLAlchemy | Zero cost, no server, file-based |
| **Cache** | cachetools (in-memory) | No Redis needed |
| **Scheduler** | APScheduler | Runs in-process, no Celery/Redis |
| **HTTP scraping** | httpx | Async, modern |
| **HTML parsing** | BeautifulSoup4 | Battle-tested, simple |
| **JS rendering** | Playwright (only if needed) | Headless browser for dynamic pages |
| **Rate limiting** | slowapi | Lightweight, no Redis |
| **Validation** | Pydantic v2 | Comes with FastAPI |
| **Testing** | pytest + httpx | FastAPI test client |
| **Linting** | Ruff | Fast, all-in-one |
| **Python** | 3.12+ | Latest stable |
| **License** | MIT | Permissive open source |

### Deployment (free tier options)

- Render / Railway / Fly.io
- Or `python -m app.main` on any machine

---

## Database Configuration

- SQLite in **WAL (Write-Ahead Logging) mode** (`PRAGMA journal_mode=WAL`) — enables concurrent reads while a write is in progress, preventing `database is locked` errors when scrapers write while the API serves reads.
- SQLAlchemy with `connect_args={"check_same_thread": False}` for FastAPI's async context.
- Tables created via `SQLAlchemy.create_all()` on startup for the MVP. Alembic migration support should be added before any production deployment with real data.

## Configuration (Environment Variables)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./promocode.db` | Database file path |
| `ADMIN_TOKEN` | (required) | Secret token for admin endpoints |
| `DEFAULT_SCRAPE_INTERVAL` | `30` | Default scrape interval in minutes |
| `CACHE_TTL` | `300` | In-memory cache TTL in seconds |
| `RATE_LIMIT` | `60/minute` | Global rate limit per IP |
| `LOG_LEVEL` | `INFO` | Logging level |

## Caching Strategy

- **What is cached:** `GET /codes` query results and `GET /stats` response.
- **TTL:** 5 minutes (300 seconds) by default, configurable via `CACHE_TTL`.
- **Invalidation:** Cache is cleared after each scraper run completes (new data available).
- **Implementation:** `cachetools.TTLCache` with key based on query parameters hash.

---

## Key Design Decisions

1. **API-first, no frontend** — decouples data from presentation; any client can be built later
2. **Monolith architecture** — simplest for MVP with 2 platforms; scrapers run in background threads via APScheduler
3. **Zero cost stack** — SQLite, in-memory cache, in-process scheduler; no external services required
4. **Hybrid validation** — automated scraping as primary, crowdsourced feedback as secondary signal
5. **Confidence scoring** — combines vote ratio, freshness, and source reliability to rank codes
6. **Manual scrape trigger** — admin endpoints for on-demand scraping, protected by token
7. **Public API, no auth** — simplest for MVP; global rate limiting per IP for abuse prevention

---

## Future Expansion (out of MVP scope)

- More platforms (Americanas, Magazine Luiza, Shopee, iFood)
- Telegram/WhatsApp bot consuming the API
- Web frontend
- Browser extension (auto-apply codes at checkout)
- API key authentication for usage tracking
- PostgreSQL + Redis migration for scale
- Community code submissions with moderation
