"""Unit tests for the CelRoScraper.parse() method.

All tests run against a saved HTML fixture — no network access required.
The fixture is a real snapshot of https://www.cel.ro/cauta/laptop/ captured
on 2026-08-27 and committed to the repository.

Test strategy
-------------
* ``parse()`` is tested in isolation: we bypass the Template Method
  orchestration and call ``parse()`` directly so the test stays focused on
  HTML extraction logic.
* We assert structural invariants (non-empty list, required fields present,
  types correct) rather than exact values, so the test remains valid even
  when prices change.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from backend.infrastructure.scrapers.celro import CelRoScraper

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "celro_search.html"


@pytest.fixture(scope="module")
def cel_ro_html() -> str:
    """Load the saved cel.ro search-results page from disk."""
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cel_ro_listings(cel_ro_html: str):
    """Parse the fixture HTML once and return the listing objects."""
    scraper = CelRoScraper()
    product_id = uuid4()
    return scraper.parse(cel_ro_html, query="laptop", product_id=product_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCelRoScraperParse:
    """Verify that CelRoScraper.parse() extracts well-formed Listing objects."""

    def test_returns_at_least_one_listing(self, cel_ro_listings):
        assert len(cel_ro_listings) > 0, "Expected at least one listing from fixture"

    def test_returns_expected_number_of_listings(self, cel_ro_listings):
        # The fixture page contains 60 cards; allow minor variation
        assert len(cel_ro_listings) >= 50, (
            f"Expected ~60 listings, got {len(cel_ro_listings)}"
        )

    def test_title_is_non_empty_string(self, cel_ro_listings):
        for listing in cel_ro_listings:
            assert isinstance(listing.title, str)
            assert listing.title.strip() != "", f"Empty title for {listing.url}"

    def test_price_is_positive_decimal(self, cel_ro_listings):
        for listing in cel_ro_listings:
            assert isinstance(listing.price, Decimal), (
                f"price should be Decimal, got {type(listing.price)}"
            )
            assert listing.price > 0, f"Non-positive price {listing.price} for {listing.url}"

    def test_url_starts_with_celro_domain(self, cel_ro_listings):
        for listing in cel_ro_listings:
            assert listing.url.startswith("https://www.cel.ro/"), (
                f"Unexpected URL: {listing.url}"
            )

    def test_retailer_id_is_celro(self, cel_ro_listings):
        for listing in cel_ro_listings:
            assert listing.retailer_id == "cel.ro", (
                f"Expected retailer_id='cel.ro', got {listing.retailer_id!r}"
            )

    def test_currency_is_ron(self, cel_ro_listings):
        for listing in cel_ro_listings:
            assert listing.currency == "RON"

    def test_external_id_is_present_and_numeric(self, cel_ro_listings):
        for listing in cel_ro_listings:
            assert listing.external_id is not None, (
                f"Missing external_id for listing {listing.url}"
            )
            assert listing.external_id.isdigit(), (
                f"external_id {listing.external_id!r} should be numeric (data-pid_prod)"
            )

    def test_image_url_is_present(self, cel_ro_listings):
        # Expect the vast majority of cards to have an image
        with_image = [l for l in cel_ro_listings if l.image_url]
        ratio = len(with_image) / len(cel_ro_listings)
        assert ratio >= 0.9, f"Only {ratio:.0%} of listings have an image_url"

    def test_product_id_is_consistent(self, cel_ro_html):
        """All listings from a single parse() call share the same product_id."""
        scraper = CelRoScraper()
        pid = uuid4()
        listings = scraper.parse(cel_ro_html, query="laptop", product_id=pid)
        assert all(l.product_id == pid for l in listings)

    def test_parse_is_idempotent(self, cel_ro_html):
        """Calling parse() twice on the same HTML produces the same count."""
        scraper = CelRoScraper()
        pid = uuid4()
        first = scraper.parse(cel_ro_html, query="laptop", product_id=pid)
        second = scraper.parse(cel_ro_html, query="laptop", product_id=pid)
        assert len(first) == len(second)
