"""CEL.ro concrete scraper.

Extends :class:`~pricewatch.infrastructure.scrapers.base.BaseScraper` and
overrides only the parts specific to cel.ro:

* ``_build_url`` — constructs the search URL with cel.ro's pagination scheme.
* ``parse``       — extracts product cards from cel.ro's HTML.

Everything else (HTTP, normalization, multi-page looping) is inherited.
"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import quote_plus
from uuid import UUID

from bs4 import BeautifulSoup, Tag

from pricewatch.domain.models import Listing
from pricewatch.infrastructure.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.cel.ro"
_RETAILER_ID = "cel.ro"

# Verified against live HTML on 2026-08-27
# Card:    <div class="product_data productListing-tot" data-pid_prod="…">
# Title:   <a class="… product_name" href="…"><span>…</span></a>
# Price:   <span class="price" content="1549">
# Image:   .productListing-poza img[src]
_CARD_SEL = "div.product_data"
_TITLE_SEL = "a.product_name span"
_LINK_SEL = "a.product_name"
_PRICE_SEL = "span.price"
_IMAGE_SEL = ".productListing-poza img"


class CelRoScraper(BaseScraper):
    """Scraper for `cel.ro <https://www.cel.ro>`_.

    Pagination pattern: ``/cauta/{query}/0j-{page}/``
    (page 1 has no suffix, pages 2+ append ``/0j-{page}/``).
    """

    retailer_id = _RETAILER_ID

    # ------------------------------------------------------------------
    # Template Method step: parse_product_page
    # ------------------------------------------------------------------

    def parse_product_page(self, html: str, url: str, product_id: UUID) -> Listing | None:
        """Extract a Listing from a cel.ro product page.

        Args:
            html:       Raw HTML string of the product page.
            url:        The product URL.
            product_id: UUID assigned to the returned Listing.
        """
        soup = BeautifulSoup(html, "lxml")
        
        # --- title -------------------------------------------------------
        title_tag = soup.select_one("h1")
        if title_tag is None:
            logger.debug("cel.ro: No h1 title found on %s", url)
            return None
        title = title_tag.get_text(strip=True)

        # --- Parse JSON-LD for Price and Image -----------------------------
        import json
        price = None
        image_url = None
        
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "offers" in item and "price" in item["offers"]:
                            price = Decimal(str(item["offers"]["price"]))
                        if isinstance(item, dict) and "image" in item:
                            if isinstance(item["image"], list):
                                image_url = item["image"][0]
                            else:
                                image_url = item["image"]
                elif isinstance(data, dict):
                    if "offers" in data and "price" in data["offers"]:
                        price = Decimal(str(data["offers"]["price"]))
                    if "image" in data:
                        if isinstance(data["image"], list):
                            image_url = data["image"][0]
                        else:
                            image_url = data["image"]
            except (json.JSONDecodeError, InvalidOperation, KeyError, TypeError):
                continue
                
        # Fallback for price if JSON-LD fails
        if price is None:
            price_tag = soup.select_one("span.price") or soup.select_one("[itemprop='price']")
            if price_tag is None:
                logger.debug("cel.ro: No price element found on %s", url)
                return None
                
            price_raw = price_tag.get("content") or price_tag.get_text(strip=True)
            try:
                price = Decimal(str(price_raw).replace(",", ".").strip())
            except InvalidOperation:
                logger.debug("cel.ro: Unparseable price %r on %s", price_raw, url)
                return None

        # --- external_id -------------------------------------------------
        form_tag = soup.select_one("form[name='buy']")
        external_id = None
        if form_tag:
            pid_input = form_tag.select_one("input[name='products_id']")
            if pid_input:
                external_id = pid_input.get("value")
        
        if not external_id:
            parts = url.strip("/").split("-")
            if len(parts) > 1 and parts[-1] == "l" and parts[-2].startswith("p"):
                external_id = parts[-2][1:]
            else:
                external_id = url
                
        return Listing(
            product_id=product_id,
            retailer_id=_RETAILER_ID,
            title=title,
            price=price,
            currency="RON",
            url=url,
            external_id=str(external_id),
            image_url=image_url,
        )
