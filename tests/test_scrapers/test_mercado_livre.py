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
