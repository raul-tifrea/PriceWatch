"""Scraper abstraction layer.

Defines the Strategy interface (``Scraper`` ABC) and the Template Method
base class (``BaseScraper``) that concrete site scrapers extend.
"""
from __future__ import annotations

import abc
import logging
import time
from decimal import Decimal, InvalidOperation
from uuid import UUID

import httpx

from backend.domain.models import Listing

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class Scraper(abc.ABC):
    """Strategy interface — every concrete scraper must implement this."""

    @abc.abstractmethod
    def scrape_product(self, url: str, product_id: UUID) -> Listing | None:
        """Fetch and parse a specific product URL.

        Args:
            url:        Exact URL of the product page.
            product_id: UUID of the :class:`~pricewatch.domain.models.Product`
                        this listing belongs to.
        """


# ---------------------------------------------------------------------------
# Template Method base
# ---------------------------------------------------------------------------


class BaseScraper(Scraper):
    """Template Method implementation of :class:`Scraper`.

    Subclasses **must** override :meth:`parse_product_page`.

    Execution order for :meth:`scrape_product`:

        1. ``_fetch(url)``                 →  raw HTML string
        2. ``parse_product_page(html, ...)``→  raw :class:`Listing` object
        3. ``_normalize([listing])``       →  validated / cleaned listing
    """

    #: Retailer identifier — set in each concrete subclass.
    retailer_id: str = ""

    #: Default HTTP headers sent with every request.
    _DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(
        self,
        *,
        max_pages: int = 3,
        request_delay: float = 1.0,
        timeout: float = 15.0,
    ) -> None:
        self.max_pages = max_pages
        self.request_delay = request_delay
        self._client = httpx.Client(
            headers=self._DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # Public Template Method entry-point
    # ------------------------------------------------------------------

    def scrape_product(self, url: str, product_id: UUID) -> Listing | None:
        """Fetch and parse a specific product URL.
        
        Args:
            url: Exact URL of the product page.
            product_id: UUID to assign to the extracted Listing.
            
        Returns:
            A single Listing object, or None if scraping fails.
        """
        logger.info("%s: fetching product %s", self.retailer_id, url)
        try:
            html = self._fetch(url)
            listing = self.parse_product_page(html, url, product_id)
            if listing:
                # Reuse normalize to validate the single listing
                normalized = self._normalize([listing])
                return normalized[0] if normalized else None
            return None
        except httpx.HTTPError as exc:
            logger.error("%s: HTTP error fetching %s: %s", self.retailer_id, url, exc)
            return None

    # ------------------------------------------------------------------
    # Steps that subclasses may / must override
    # ------------------------------------------------------------------

    def _fetch(self, url: str) -> str:
        """Perform an HTTP GET and return the response body as a string."""
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    @abc.abstractmethod
    def parse_product_page(self, html: str, url: str, product_id: UUID) -> Listing | None:
        """Parse the HTML of a specific product page.

        Returns:
            A raw Listing object, or None if parsing fails.
        """

    # ------------------------------------------------------------------
    # Post-processing (shared across all scrapers)
    # ------------------------------------------------------------------

    def _normalize(self, listings: list[Listing]) -> list[Listing]:
        """Validate and clean listings produced by :meth:`parse`.

        Rules applied:

        * ``price`` must be > 0 (drops listings with invalid/zero price).
        * ``title`` is stripped of leading/trailing whitespace.
        * ``url`` must be non-empty.
        """
        valid: list[Listing] = []
        for listing in listings:
            if not listing.title.strip():
                logger.warning("Dropping listing with empty title: %s", listing.url)
                continue
            if not listing.url:
                logger.warning("Dropping listing with empty URL")
                continue
            try:
                price = Decimal(listing.price)
            except InvalidOperation:
                logger.warning("Dropping listing with invalid price: %r", listing.price)
                continue
            if price <= 0:
                logger.warning("Dropping listing with non-positive price: %s", price)
                continue
            valid.append(
                Listing(
                    id=listing.id,
                    product_id=listing.product_id,
                    retailer_id=listing.retailer_id,
                    title=listing.title.strip(),
                    price=price,
                    currency=listing.currency,
                    url=listing.url.strip(),
                    external_id=listing.external_id,
                    image_url=listing.image_url,
                    scraped_at=listing.scraped_at,
                )
            )
        logger.info(
            "%s: %d/%d listings passed validation",
            type(self).__name__,
            len(valid),
            len(listings),
        )
        return valid
