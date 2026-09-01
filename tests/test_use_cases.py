import pytest
import uuid
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.application.use_cases import RefreshPrices, AddProduct
from backend.domain.events import PriceEventBus
from backend.domain.models import Product, Listing
from backend.infrastructure.db.orm_models import Base
from backend.infrastructure.scrapers.base import Scraper
from backend.infrastructure.scrapers.factory import ScraperFactory
class MockScraper(Scraper):
    retailer_id = "mock.retailer"
    def __init__(self, listings: list[Listing] | None = None):
        self._listings = listings or []
    def scrape_product(self, url: str, product_id: UUID) -> Listing | None:
        import copy
        for l in self._listings:
            new_l = copy.deepcopy(l)
            new_l.product_id = product_id
            new_l.url = url
            new_l.external_id = f"{l.external_id}-{product_id}"
            from uuid import uuid4
            new_l.id = uuid4()
            return new_l
        return None
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
def test_add_product_creates_product(session):
    use_case = AddProduct(session)
    product = use_case.execute("Laptop", "http://mock.retailer/laptop-i7", uuid.uuid4())
    assert product.name == "Laptop"
    assert product.url == "http://mock.retailer/laptop-i7"
    assert product.id is not None
def test_refresh_prices_emits_event_on_price_drop(session):
    event_bus = PriceEventBus()
    events = []
    event_bus.subscribe(events.append)
    factory = ScraperFactory()
    add_product_uc = AddProduct(session)
    product = add_product_uc.execute("Laptop", "http://mock.retailer/1", uuid.uuid4())
    listing1 = Listing(
        product_id=product.id,
        retailer_id="mock.retailer",
        title="Test Laptop i7",
        price=Decimal("4000.00"),
        currency="RON",
        url="http://mock.retailer/1",
        external_id="ext123"
    )
    mock_scraper = MockScraper([listing1])
    factory.available = lambda: ["mock.retailer"]
    factory.get = lambda x: mock_scraper
    refresh_uc = RefreshPrices(session, factory, event_bus)
    refresh_uc.execute()
    assert len(events) == 1
    assert events[0].is_new_listing
    assert events[0].new_price == Decimal("4000.00")
    events.clear()
    listing1.price = Decimal("3500.00")
    refresh_uc.execute()
    assert len(events) == 1
    assert events[0].is_price_drop
    assert events[0].old_price == Decimal("4000.00")
    assert events[0].new_price == Decimal("3500.00")
    add_product_uc.execute("Laptop2", "http://mock.retailer/2", uuid.uuid4())
    refresh_uc.execute() 