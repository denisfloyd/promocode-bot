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
            discount_text = discount_el.get_text(strip=True) if discount_el else ""
            discount_type, discount_value = self._parse_discount(discount_text)
            item = {
                "code": code_el.get_text(strip=True),
                "description": desc_el.get_text(strip=True),
                "discount_type": discount_type,
                "discount_value": discount_value,
                "source_url": self.source_url,
            }
            if category_el:
                item["category"] = category_el.get_text(strip=True)
            if expiry_el:
                item["expires_at"] = expiry_el.get_text(strip=True)
            results.append(item)
        return results

    def _parse_discount(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        if "frete" in text_lower or "shipping" in text_lower:
            return "free_shipping", 0.0
        pct_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
        if pct_match:
            return "percentage", float(pct_match.group(1).replace(",", "."))
        val_match = re.search(r"R?\$?\s*(\d+(?:[.,]\d+)?)", text)
        if val_match:
            return "fixed_amount", float(val_match.group(1).replace(",", "."))
        return "percentage", 0.0
