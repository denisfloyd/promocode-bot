from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.amazon_br import AmazonBRScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def scraper():
    return AmazonBRScraper(source_url="https://www.promobit.com.br/cupons/loja/amazon/")


@pytest.fixture
def sample_html():
    return (FIXTURES_DIR / "amazon_br_coupons.html").read_text()


@pytest.mark.asyncio
async def test_scrape_extracts_from_next_data(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        # 5 coupons in fixture: LEVE20, VEMCARNAVAL approved+code,
        # PETLOVE filtered (pet shop), EXPIRED filtered (status), CUPOM NO LINK filtered (no code)
        assert len(results) == 2
        codes = [r["code"] for r in results]
        assert "LEVE20" in codes
        assert "VEMCARNAVAL" in codes


@pytest.mark.asyncio
async def test_scrape_detects_discount_types(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        by_code = {r["code"]: r for r in results}
        assert by_code["LEVE20"]["discount_type"] == "percentage"
        assert by_code["LEVE20"]["discount_value"] == 20.0
        assert by_code["VEMCARNAVAL"]["discount_type"] == "fixed_amount"
        assert by_code["VEMCARNAVAL"]["discount_value"] == 100.0


@pytest.mark.asyncio
async def test_scrape_filters_narrow_categories(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        codes = [r["code"] for r in results]
        assert "PETLOVE" not in codes  # pet shop = narrow


@pytest.mark.asyncio
async def test_scrape_filters_expired(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        codes = [r["code"] for r in results]
        assert "EXPIRED" not in codes


@pytest.mark.asyncio
async def test_scrape_skips_cupom_no_link(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        codes = [r["code"] for r in results]
        assert "CUPOM NO LINK" not in codes


@pytest.mark.asyncio
async def test_scrape_extracts_min_purchase(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        by_code = {r["code"]: r for r in results}
        assert by_code["LEVE20"]["min_purchase"] == 100.0


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
