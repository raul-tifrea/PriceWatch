from __future__ import annotations
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from uuid import UUID
from bs4 import BeautifulSoup
from backend.domain.models import Listing
from backend.infrastructure.scrapers.base import BaseScraper
logger = logging.getLogger(__name__)
_RETAILER_ID = "pcgarage.ro"
_BASE_URL = "https://www.pcgarage.ro"
def _extract_external_id(url: str) -> str | None:
    cleaned = url.rstrip("/")
    match = re.search(r"-p(\d+)(?:[./]|$)", cleaned)
    if match:
        return match.group(1)
    match = re.search(r"/(\d{4,})(?:[/.]|$)", cleaned)
    if match:
        return match.group(1)
    return None
class PcGarageScraper(BaseScraper):
    retailer_id = _RETAILER_ID
    def parse_product_page(self, html: str, url: str, product_id: UUID) -> Listing | None:
        soup = BeautifulSoup(html, "lxml")
        h1 = soup.select_one("h1")
        if h1 is None:
            logger.debug("pcgarage.ro: No h1 found on %s", url)
            return None
        title = h1.get_text(strip=True)
        price: Decimal | None = None
        image_url: str | None = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict) or item.get("@type") != "Product":
                        continue
                    offers = item.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0]
                    raw_price = offers.get("price")
                    if raw_price is not None and price is None:
                        try:
                            price = Decimal(str(raw_price).replace(",", ".").strip())
                        except InvalidOperation:
                            pass
                    img = item.get("image")
                    if img and image_url is None:
                        image_url = img[0] if isinstance(img, list) else img
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
        if price is None:
            for sel in [
                "[itemprop='price']",
                ".price-wrap .price",
                ".product-price",
                "span.price",
            ]:
                el = soup.select_one(sel)
                if el:
                    raw = el.get("content") or el.get_text(strip=True)
                    cleaned = re.sub(r"[^\d.,]", "", raw).replace(",", ".")
                    try:
                        price = Decimal(cleaned)
                        break
                    except InvalidOperation:
                        continue
        if price is None:
            logger.debug("pcgarage.ro: Could not extract price from %s", url)
            return None
        external_id = _extract_external_id(url) or url
        return Listing(
            product_id=product_id,
            retailer_id=_RETAILER_ID,
            title=title,
            price=price,
            currency="RON",
            url=url,
            external_id=external_id,
            image_url=image_url,
        )