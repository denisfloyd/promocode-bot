import pytest
from app.scrapers.base import BaseScraper


class ConcreteScraper(BaseScraper):
    platform = "test_platform"

    async def scrape(self):
        return [
            {"code": "TEST10", "description": "10% off", "discount_type": "percentage", "discount_value": 10.0, "source_url": "https://example.com"},
            {"code": "TEST20", "description": "R$20 off", "discount_type": "fixed_amount", "discount_value": 20.0, "source_url": "https://example.com"},
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
