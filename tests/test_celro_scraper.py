from __future__ import annotations
from decimal import Decimal
from uuid import uuid4
import pytest
from backend.infrastructure.scrapers.celro import CelRoScraper

MOCK_HTML = """
<!DOCTYPE html>
<html lang="ro">
<head><title>Test Product</title></head>
<body>
    <h1>Test Product</h1>
    <script type="application/ld+json">
        {"offers": {"price": "3500.50"}, "image": "http://img.cel.ro/test.jpg"}
    </script>
    <form name="buy"><input name="products_id" value="12345"></form>
</body>
</html>
"""

def test_parse_product_page():
    scraper = CelRoScraper()
    pid = uuid4()
    url = "https://www.cel.ro/laptop-test"
    
    listing = scraper.parse_product_page(MOCK_HTML, url, pid)
    
    assert listing is not None
    assert listing.product_id == pid
    assert listing.retailer_id == "cel.ro"
    assert listing.title == "Test Product"
    assert listing.price == Decimal("3500.50")
    assert listing.currency == "RON"
    assert listing.url == url
    assert listing.external_id == "12345"
    assert listing.image_url == "http://img.cel.ro/test.jpg"

def test_parse_product_page_no_title():
    scraper = CelRoScraper()
    pid = uuid4()
    url = "https://www.cel.ro/laptop-test"
    html = "<html><body></body></html>"
    
    listing = scraper.parse_product_page(html, url, pid)
    assert listing is None