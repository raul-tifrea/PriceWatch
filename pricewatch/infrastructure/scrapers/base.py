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

from pricewatch.domain.models import Listing

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class Scraper(abc.ABC):
    """Strategy interface — every concrete scraper must implement this."""

    @abc.abstractmethod
    def search(self, query: str, product_id: UUID) -> list[Listing]:
        """Search for *query* and return normalised :class:`Listing` objects.

        Args:
            query:      Free-text search string sent to the retailer.
            product_id: UUID of the :class:`~pricewatch.domain.models.Product`
                        these listings belong to.
        """


# ---------------------------------------------------------------------------
# Template Method base
# ---------------------------------------------------------------------------


class BaseScraper(Scraper):
    """Template Method implementation of :class:`Scraper`.

    Subclasses **must** override :meth:`parse`.  They may optionally override
    :meth:`_build_url` or :meth:`_fetch`.

    Execution order for :meth:`search`:

        1. ``_build_url(query, page)``  →  URL string
        2. ``_fetch(url)``              →  raw HTML string
        3. ``parse(html, query)``       →  list of raw :class:`Listing` objects
        4. ``_normalize(listings)``     →  validated / cleaned listings

    Multi-page scraping is handled by iterating pages up to ``max_pages``.
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

    def search(self, query: str, product_id: UUID) -> list[Listing]:
        """Orchestrate fetch → parse → normalize across up to *max_pages*."""
        all_listings: list[Listing] = []
        for page in range(1, self.max_pages + 1):
            url = self._build_url(query, page)
            logger.debug("Fetching %s (page %d)", url, page)
            html = self._fetch(url)
            page_listings = self.parse(html, query, product_id)
            if not page_listings:
                logger.debug("No listings on page %d — stopping pagination", page)
                break
            all_listings.extend(page_listings)
            if page < self.max_pages:
                time.sleep(self.request_delay)
        return self._normalize(all_listings)

    # ------------------------------------------------------------------
    # Steps that subclasses may / must override
    # ------------------------------------------------------------------

    def _build_url(self, query: str, page: int) -> str:
        """Return the URL for *query* on *page*.  Subclasses must override."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _build_url()"
        )

    def _fetch(self, url: str) -> str:
        """Perform an HTTP GET and return the response body as a string."""
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    @abc.abstractmethod
    def parse(self, html: str, query: str, product_id: UUID) -> list[Listing]:
        """Parse *html* and return a list of raw :class:`Listing` objects.

        This is the only method subclasses **must** implement.  The returned
        listings will be passed through :meth:`_normalize` before being
        returned to callers.

        Args:
            html:       Raw HTML of the search-results page.
            query:      Original search query (may be used for tagging).
            product_id: UUID to assign to each listing.
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
