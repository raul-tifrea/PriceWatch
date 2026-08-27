import logging
from pricewatch.infrastructure.db.engine import SessionLocal
from pricewatch.application.use_cases import RefreshPrices
from pricewatch.infrastructure.scrapers.factory import ScraperFactory
from pricewatch.domain.events import PriceEventBus

logging.basicConfig(level=logging.DEBUG)

def test_refresh():
    session = SessionLocal()
    factory = ScraperFactory()
    bus = PriceEventBus()
    
    uc = RefreshPrices(session, factory, bus)
    uc.execute()
    
    session.close()

if __name__ == "__main__":
    test_refresh()
