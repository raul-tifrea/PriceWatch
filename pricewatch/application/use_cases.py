"""Application use cases.

These classes orchestrate the domain models and infrastructure components.
They represent the "verbs" or primary actions of the system.
"""
from __future__ import annotations

import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from pricewatch.domain.events import PriceEvent, PriceEventBus
from pricewatch.domain.models import Product, Listing, PricePoint, Alert
from pricewatch.infrastructure.db.repositories import ProductRepository, PriceRepository, AlertRepository
from pricewatch.infrastructure.scrapers.factory import ScraperFactory

logger = logging.getLogger(__name__)


class AddProduct:
    """Adds a new product to be tracked."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
        self.alert_repo = AlertRepository(session)

    def execute(
        self, name: str, url: str, target_price: float | None = None, channel: str = "console"
    ) -> Product:
        """Create a product and optionally a price-drop alert.

        Args:
            name: Human-readable name.
            url: Exact product URL on a supported retailer.
            target_price: If set, create an alert for this price.
            channel: The notification channel for the alert.

        Returns:
            The created Product.
        """
        product = Product(name=name, url=url)
        self.product_repo.add(product)
        
        if target_price is not None:
            from decimal import Decimal
            alert = Alert(
                product_id=product.id,
                target_price=Decimal(str(target_price)),
                channel=channel
            )
            self.alert_repo.add(alert)
            
        self.session.commit()
        logger.info("Added product: %r (url: %r)", name, url)
        return product


class RefreshPrices:
    """Runs scrapers for all tracked products and records new price points."""

    def __init__(self, session: Session, factory: ScraperFactory, event_bus: PriceEventBus) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
        self.price_repo = PriceRepository(session)
        self.factory = factory
        self.event_bus = event_bus

    def execute(self) -> None:
        """Scrape all active retailers for all products."""
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

            # Check if we already have this listing
            assert listing.external_id is not None
            existing_listing = self.price_repo.get_listing_by_external_id(scraper.retailer_id, listing.external_id)
            
            if not existing_listing:
                # Brand new listing
                self.price_repo.add_listing(listing)
                existing_listing = listing
                old_price = None
            else:
                history = self.price_repo.get_history(existing_listing.id)
                latest_point = history[-1] if history else None
                old_price = latest_point.price if latest_point else None

            # Always add a new PricePoint for today's scrape
            pt = PricePoint(listing_id=existing_listing.id, price=listing.price)
            self.price_repo.add_price_point(pt)
            
            # Emit an event for the UI or alerts to consume
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
    """Removes a product and all its cascaded history/alerts."""
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self.product_repo = ProductRepository(session)
        
    def execute(self, product_id: UUID) -> None:
        self.product_repo.delete(product_id)
        self.session.commit()
        logger.info("Removed product ID: %s", product_id)


class AlertChecker:
    """An observer that listens for PriceEvents and triggers configured alerts."""
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self.alert_repo = AlertRepository(session)
        
    def handle(self, event: PriceEvent) -> None:
        if not event.is_price_drop and not event.is_new_listing:
            return
            
        alerts = self.alert_repo.list_active()
        for alert in alerts:
            if alert.product_id == event.product_id and event.new_price <= alert.target_price:
                logger.info("Alert triggered for product %s at %s! Target: %s, Current: %s", 
                            alert.product_id, event.retailer_id, alert.target_price, event.new_price)
                
                # Mark as triggered
                alert.triggered_at = datetime.utcnow()
                self.alert_repo.update(alert)
                
                # In a real system, we might publish an AlertFiredEvent here.
                # For now, we just update the triggered state.
        
        self.session.commit()


class GetPriceHistory:
    """Fetches price history for a product."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.price_repo = PriceRepository(session)
        self.product_repo = ProductRepository(session)

    def execute(self, product_id: UUID) -> dict[str, list[PricePoint]]:
        """Return a dict mapping retailer_id -> list of PricePoints, sorted by date."""
        # Get all listings for the product
        listings = self.price_repo.get_listings_for_product(product_id)
        
        history = {}
        for listing in listings:
            points = self.price_repo.get_history(listing.id)
            history[listing.retailer_id] = points
            
        return history
