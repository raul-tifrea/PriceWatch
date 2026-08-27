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
    # Template Method step: build URL
    # ------------------------------------------------------------------

    def _build_url(self, query: str, page: int) -> str:
        encoded = quote_plus(query.replace(" ", "+"))
        if page == 1:
            return f"{_BASE_URL}/cauta/{encoded}/"
        return f"{_BASE_URL}/cauta/{encoded}/0j-{page}/"

    # ------------------------------------------------------------------
    # Template Method step: parse (the only *required* override)
    # ------------------------------------------------------------------

    def parse(self, html: str, query: str, product_id: UUID) -> list[Listing]:
        """Extract product listings from a cel.ro search results page.

        Args:
            html:       Raw HTML string of a cel.ro ``/cauta/`` page.
            query:      Original search query (unused in parsing, kept for
                        interface consistency).
            product_id: UUID assigned to each returned :class:`Listing`.

        Returns:
            Unvalidated :class:`Listing` objects — validation is applied by
            the inherited :meth:`~BaseScraper._normalize` step.
        """
        soup = BeautifulSoup(html, "lxml")
        cards: list[Tag] = soup.select(_CARD_SEL)
        logger.debug("cel.ro: found %d product cards in HTML", len(cards))

        listings: list[Listing] = []
        for card in cards:
            listing = self._parse_card(card, product_id)
            if listing is not None:
                listings.append(listing)
        return listings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_card(self, card: Tag, product_id: UUID) -> Listing | None:
        """Extract a :class:`Listing` from a single product card ``<div>``.

        Returns ``None`` if any required field is missing so that
        :meth:`parse` can safely skip malformed cards without crashing.
        """
        # --- external_id (retailer's own product ID) --------------------
        external_id: str | None = card.get("data-pid_prod")  # type: ignore[assignment]

        # --- title -------------------------------------------------------
        title_tag = card.select_one(_TITLE_SEL)
        if title_tag is None:
            logger.debug("Skipping card %s: no title element", external_id)
            return None
        title = title_tag.get_text(strip=True)

        # --- URL ---------------------------------------------------------
        link_tag = card.select_one(_LINK_SEL)
        if link_tag is None:
            logger.debug("Skipping card %s: no link element", external_id)
            return None
        url: str = link_tag.get("href", "")  # type: ignore[assignment]
        if not url.startswith("http"):
            url = f"{_BASE_URL}{url}"

        # --- price -------------------------------------------------------
        price_tag = card.select_one(_PRICE_SEL)
        if price_tag is None:
            logger.debug("Skipping card %s: no price element", external_id)
            return None
        # Prefer the machine-readable ``content`` attribute (pure integer, no
        # thousands separator) over the display text which may include "lei".
        price_raw = price_tag.get("content") or price_tag.get_text(strip=True)
        try:
            # Strip any stray whitespace or non-numeric characters
            price = Decimal(str(price_raw).replace(",", ".").strip())
        except InvalidOperation:
            logger.debug("Skipping card %s: unparseable price %r", external_id, price_raw)
            return None

        # --- image -------------------------------------------------------
        img_tag = card.select_one(_IMAGE_SEL)
        image_url: str | None = None
        if img_tag is not None:
            image_url = img_tag.get("src")  # type: ignore[assignment]

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
