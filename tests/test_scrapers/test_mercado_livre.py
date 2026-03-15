from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.scrapers.mercado_livre import MercadoLivreScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def scraper():
    return MercadoLivreScraper(source_url="https://www.promobit.com.br/cupons/loja/mercado-livre/")


@pytest.fixture
def sample_html():
    return (FIXTURES_DIR / "mercado_livre_coupons.html").read_text()


@pytest.mark.asyncio
async def test_scrape_extracts_from_next_data(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        # 5 coupons: 3 CUPOM NO LINK (approved), 1 FRETEML (approved), 1 VELHO (expired)
        # Supermercado one is filtered (narrow), VELHO filtered (expired)
        # ML keeps CUPOM NO LINK codes (unlike Amazon) — so: 2 CUPOM NO LINK + FRETEML = 3
        assert len(results) == 3


@pytest.mark.asyncio
async def test_scrape_detects_discount_types(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        types = {r["discount_type"] for r in results}
        assert "percentage" in types
        assert "fixed_amount" in types or "free_shipping" in types


@pytest.mark.asyncio
async def test_scrape_filters_narrow_categories(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        descriptions = [r["description"].lower() for r in results]
        for desc in descriptions:
            assert "supermercado" not in desc


@pytest.mark.asyncio
async def test_scrape_filters_expired(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        codes = [r["code"] for r in results]
        assert "VELHO" not in codes


@pytest.mark.asyncio
async def test_scrape_extracts_min_purchase(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        # The first coupon (R$200 OFF Informática) has min purchase R$1199
        has_min = [r for r in results if r.get("min_purchase")]
        assert len(has_min) > 0


@pytest.mark.asyncio
async def test_scrape_keeps_cupom_no_link(scraper, sample_html):
    """ML scraper keeps CUPOM NO LINK codes since most ML coupons use this pattern."""
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        results = await scraper.scrape()
        cupom_no_link = [r for r in results if r["code"] == "CUPOM NO LINK"]
        assert len(cupom_no_link) >= 1


@pytest.mark.asyncio
async def test_parse_adds_platform(scraper, sample_html):
    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value=sample_html):
        raw = await scraper.scrape()
        parsed = scraper.parse(raw)
        for item in parsed:
            assert item["platform"] == "mercado_livre"


@pytest.mark.asyncio
async def test_scrape_handles_empty_page(scraper):
    with patch.object(
        scraper, "_fetch_html", new_callable=AsyncMock, return_value="<html><body></body></html>"
    ):
        results = await scraper.scrape()
        assert results == []
