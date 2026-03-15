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
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value="<html><body></body></html>"):
        results = await scraper.scrape()
        assert results == []
