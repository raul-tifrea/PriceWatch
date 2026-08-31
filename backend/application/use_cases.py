from __future__ import annotations
import logging
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from backend.domain.events import PriceEvent, PriceEventBus
from backend.domain.models import Product, Listing, PricePoint
from backend.infrastructure.db.repositories import ProductRepository, PriceRepository
from backend.infrastructure.scrapers.factory import ScraperFactory
logger = logging.getLogger(__name__)
class AddProduct:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
    def execute(
        self, name: str, url: str
    ) -> Product:
        product = Product(name=name, url=url)
        self.product_repo.add(product)
        self.session.commit()
        logger.info("Added product: %r (url: %r)", name, url)
        return product
class AddProductFromExtension:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
        self.price_repo = PriceRepository(session)
        self.event_bus = PriceEventBus()
    def execute(
        self,
        name: str,
        url: str,
        retailer_id: str,
        title: str,
        price: Decimal,
        external_id: str,
        image_url: str | None = None,
        currency: str = "RON",
    ) -> Product:
        product = Product(name=name, url=url)
        self.product_repo.add(product)
        existing = self.price_repo.get_listing_by_external_id(retailer_id, external_id)
        if existing:
            listing = existing
        else:
            listing = Listing(
                product_id=product.id,
                retailer_id=retailer_id,
                title=title,
                price=price,
                currency=currency,
                url=url,
                external_id=external_id,
                image_url=image_url,
            )
            self.price_repo.add_listing(listing)
        pt = PricePoint(listing_id=listing.id, price=price)
        self.price_repo.add_price_point(pt)
        event = PriceEvent(
            product_id=product.id,
            listing_id=listing.id,
            retailer_id=retailer_id,
            title=title,
            new_price=price,
            currency=currency,
            url=url,
            old_price=None,
        )
        self.event_bus.publish(event)
        self.session.commit()
        logger.info("Added product from extension: %r (%s)", name, retailer_id)
        return product
class RefreshPrices:
    def __init__(self, session: Session, factory: ScraperFactory, event_bus: PriceEventBus) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
        self.price_repo = PriceRepository(session)
        self.factory = factory
        self.event_bus = event_bus
    def execute(self) -> None:
        products = self.product_repo.list_all()
        if not products:
            logger.info("No products to refresh.")
            return
        retailers = self.factory.available()
        logger.info("Starting price refresh for %d products", len(products))
        import urllib.parse
        for product in products:
            domain = urllib.parse.urlparse(product.url).netloc.replace("www.", "")
            scraper = None
            for r_id in retailers:
                if r_id in domain:
                    scraper = self.factory.get(r_id)
                    break
            if not scraper:
                logger.error("No scraper available for domain %s (product %s)", domain, product.name)
                continue
            logger.info("Scraping %s via %s...", product.name, scraper.retailer_id)
            try:
                listing = scraper.scrape_product(product.url, product.id)
            except Exception:
                logger.exception("Scraping failed for %s", product.name)
                continue
            if not listing:
                logger.debug("No listing found for %s", product.name)
                continue
            assert listing.external_id is not None
            existing_listing = self.price_repo.get_listing_by_external_id(scraper.retailer_id, listing.external_id)
            if not existing_listing:
                self.price_repo.add_listing(listing)
                existing_listing = listing
                old_price = None
            else:
                history = self.price_repo.get_history(existing_listing.id)
                latest_point = history[-1] if history else None
                old_price = latest_point.price if latest_point else None
            pt = PricePoint(listing_id=existing_listing.id, price=listing.price)
            self.price_repo.add_price_point(pt)
            event = PriceEvent(
                product_id=product.id,
                listing_id=existing_listing.id,
                retailer_id=scraper.retailer_id,
                title=listing.title,
                new_price=listing.price,
                currency=listing.currency,
                url=listing.url,
                old_price=old_price,
            )
            self.event_bus.publish(event)
        self.session.commit()
        logger.info("Price refresh complete.")
class RemoveProduct:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
    def execute(self, product_id: UUID) -> None:
        self.product_repo.delete(product_id)
        self.session.commit()
        logger.info("Removed product ID: %s", product_id)

class GetPriceHistory:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.price_repo = PriceRepository(session)
        self.product_repo = ProductRepository(session)
    def execute(self, product_id: UUID) -> dict[str, list[PricePoint]]:
        listings = self.price_repo.get_listings_for_product(product_id)
        history = {}
        for listing in listings:
            points = self.price_repo.get_history(listing.id)
            history[listing.retailer_id] = points
        return history