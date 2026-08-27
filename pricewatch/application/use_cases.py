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
        self, name: str, search_query: str, target_price: float | None = None, channel: str = "console"
    ) -> Product:
        """Create a product and optionally a price-drop alert.

        Args:
            name: Human-readable name.
            search_query: String to search on retailers.
            target_price: If set, create an alert for this price.
            channel: The notification channel for the alert.

        Returns:
            The created Product.
        """
        product = Product(name=name, search_query=search_query)
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
        logger.info("Added product: %r (query: %r)", name, search_query)
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
        logger.info("Starting price refresh for %d products across %d retailers", len(products), len(retailers))

        for product in products:
            for retailer_id in retailers:
                scraper = self.factory.get(retailer_id)
                logger.info("Scraping %s on %s...", product.name, retailer_id)
                try:
                    listings = scraper.search(product.search_query, product.id)
                except Exception:
                    logger.exception("Scraping failed for %s on %s", product.name, retailer_id)
                    continue

                if not listings:
                    logger.debug("No listings found for %s on %s", product.name, retailer_id)
                    continue

                # Filter out obvious accessories unless the user explicitly searched for them
                query_lower = product.search_query.lower()
                
                # Split query into words to ensure they all exist in the title
                query_words = query_lower.split()
                
                filtered_listings = []
                banned_words = {"husa", "folie", "cablu", "incarcator", "sticla", "glass", "protectie", "case", "cover", "adaptor", "suport"}
                
                for l in listings:
                    title_lower = l.title.lower()
                    
                    # 1. Must contain all words from the search query
                    if not all(word in title_lower for word in query_words):
                        continue
                        
                    # 2. Filter out banned accessory words UNLESS the user actually searched for them
                    is_banned = False
                    for banned in banned_words:
                        # If the banned word is in the title, but NOT in the search query, exclude it
                        if banned in title_lower and banned not in query_lower:
                            is_banned = True
                            break
                    
                    if is_banned:
                        continue
                        
                    filtered_listings.append(l)

                if not filtered_listings:
                    logger.debug("No valid matching listings found for %s on %s after filtering", product.name, retailer_id)
                    continue
                    
                # Take the cheapest matching listing from the FILTERED list
                best_listing = min(filtered_listings, key=lambda l: l.price)
                
                # Check if we already have this listing
                assert best_listing.external_id is not None
                existing_listing = self.price_repo.get_listing_by_external_id(retailer_id, best_listing.external_id)
                
                if not existing_listing:
                    # Brand new listing
                    self.price_repo.add_listing(best_listing)
                    existing_listing = best_listing
                    old_price = None
                else:
                    # We have seen this before. Get the latest price point to check for changes
                    history = self.price_repo.get_history(existing_listing.id)
                    latest_point = history[-1] if history else None
                    old_price = latest_point.price if latest_point else None

                # Record the new price point
                new_point = PricePoint(
                    listing_id=existing_listing.id,
                    price=best_listing.price,
                )
                self.price_repo.add_price_point(new_point)
                
                # Commit the transaction so far (or maybe at the very end, but doing it here ensures it's saved)
                # We'll just flush to get IDs, commit at the very end of the use case.
                self.session.flush()

                # Determine if we should emit an event
                if old_price != best_listing.price:
                    event = PriceEvent(
                        product_id=product.id,
                        listing_id=existing_listing.id,
                        retailer_id=retailer_id,
                        title=best_listing.title,
                        new_price=best_listing.price,
                        currency=best_listing.currency,
                        url=best_listing.url,
                        old_price=old_price,
                    )
                    self.event_bus.publish(event)
                    
        self.session.commit()
        logger.info("Price refresh complete.")


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
