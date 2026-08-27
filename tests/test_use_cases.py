"""Tests for application use cases with an in-memory SQLite DB."""
import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.application.use_cases import RefreshPrices, AddProduct, AlertChecker
from backend.domain.events import PriceEventBus
from backend.domain.models import Product, Listing
from backend.infrastructure.db.orm_models import Base
from backend.infrastructure.scrapers.base import Scraper
from backend.infrastructure.scrapers.factory import ScraperFactory


class MockScraper(Scraper):
    retailer_id = "mock.retailer"
    
    def __init__(self, listings: list[Listing] | None = None):
        self._listings = listings or []

    def search(self, query: str, product_id: UUID) -> list[Listing]:
        import copy
        out = []
        for l in self._listings:
            new_l = copy.deepcopy(l)
            new_l.product_id = product_id
            new_l.external_id = f"{l.external_id}-{product_id}"
            from uuid import uuid4 as generate_uuid
            new_l.id = generate_uuid()
            out.append(new_l)
        return out


@pytest.fixture
def session():
    """Provides a fresh in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_add_product_creates_product_and_alert(session):
    use_case = AddProduct(session)
    product = use_case.execute("Laptop", "laptop i7", 3000.0)
    
    assert product.name == "Laptop"
    assert product.search_query == "laptop i7"
    assert product.id is not None
    
    # Check that alert was created
    from backend.infrastructure.db.repositories import AlertRepository
    repo = AlertRepository(session)
    active_alerts = repo.list_active()
    assert len(active_alerts) == 1
    assert active_alerts[0].product_id == product.id
    assert active_alerts[0].target_price == Decimal("3000.0")


def test_refresh_prices_emits_event_on_price_drop(session):
    # Setup bus and factory
    event_bus = PriceEventBus()
    events = []
    event_bus.subscribe(events.append)
    
    factory = ScraperFactory()
    
    # 1. Add a product
    add_product_uc = AddProduct(session)
    product = add_product_uc.execute("Laptop", "laptop i7")
    
    # 2. Setup mock scraper returning a listing
    listing1 = Listing(
        product_id=product.id,
        retailer_id="mock.retailer",
        title="Test Laptop i7",
        price=Decimal("4000.00"),
        currency="RON",
        url="http://mock/1",
        external_id="ext123"
    )
    mock_scraper = MockScraper([listing1])
    
    # Mock factory methods
    factory.available = lambda: ["mock.retailer"]
    factory.get = lambda x: mock_scraper
    
    # 3. First refresh (new listing)
    refresh_uc = RefreshPrices(session, factory, event_bus)
    refresh_uc.execute()
    
    assert len(events) == 1
    assert events[0].is_new_listing
    assert events[0].new_price == Decimal("4000.00")
    events.clear()
    
    # 4. Second refresh (price drop)
    listing1.price = Decimal("3500.00")
    refresh_uc.execute()
    
    assert len(events) == 1
    assert events[0].is_price_drop
    assert events[0].old_price == Decimal("4000.00")
    assert events[0].new_price == Decimal("3500.00")
    
    # 5. Check alerts trigger
    add_product_uc.execute("Laptop2", "laptop", target_price=3600.0)
    # the second product will also trigger the scraper and get a listing at 3500.00
    # Wait, the alertchecker should see this!
    alert_checker = AlertChecker(session)
    event_bus.subscribe(alert_checker.handle)
    
    refresh_uc.execute() # Will fetch 3500 again for Laptop and Laptop2
    
    # The alert should be triggered for Laptop2
    from backend.infrastructure.db.repositories import AlertRepository
    repo = AlertRepository(session)
    active_alerts = repo.list_active()
    assert len(active_alerts) == 0 # Alert was triggered and is no longer active
