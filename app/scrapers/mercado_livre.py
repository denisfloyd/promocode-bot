import json
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

# Narrow categories to skip (wide-use filtering)
NARROW_CATEGORIES = {
    "supermercado", "supermarket", "despensa", "alimento", "food",
    "pet shop", "pet", "bebida", "drink", "farmácia", "pharmacy",
}


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
        coupons = self._extract_coupons_from_next_data(html)
        return [c for c in coupons if not self._is_narrow(c)]

    def _extract_coupons_from_next_data(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return []

        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            return []

        coupons_data = (
            data.get("props", {})
            .get("pageProps", {})
            .get("serverCoupons", {})
            .get("coupons", [])
        )

        results = []
        for c in coupons_data:
            if c.get("couponStatusName") != "APPROVED":
                continue

            code = c.get("couponCode", "")
            # Mercado Livre uses "CUPOM NO LINK" for most codes — still include them
            # since they're valid coupons accessed through a redirect link
            if not code:
                continue

            discount_text = c.get("couponDiscountShort", "")
            discount_type, discount_value = self._parse_discount(discount_text)

            min_purchase = self._extract_min_purchase(c.get("couponInstructions", ""))

            item = {
                "code": code,
                "description": c.get("couponTitle", ""),
                "discount_type": discount_type,
                "discount_value": discount_value,
                "source_url": self.source_url,
            }
            if min_purchase:
                item["min_purchase"] = min_purchase

            results.append(item)

        return results

    def _is_narrow(self, coupon: dict) -> bool:
        """Filter out store-specific, food, pet, and other narrow department codes."""
        desc = coupon.get("description", "").lower()
        for keyword in NARROW_CATEGORIES:
            if keyword in desc:
                return True
        return False

    def _extract_min_purchase(self, instructions: str) -> float | None:
        if not instructions:
            return None
        match = re.search(r"[Cc]ompra m[ií]nima[:\s]*R?\$?\s*(\d+(?:[.,]\d+)?)", instructions)
        if match:
            return float(match.group(1).replace(",", "."))
        match = re.search(r"m[ií]nimo[:\s]*R?\$?\s*(\d+(?:[.,]\d+)?)", instructions)
        if match:
            return float(match.group(1).replace(",", "."))
        return None

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
