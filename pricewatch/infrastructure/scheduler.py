"""APScheduler integration for running background price refreshes."""
from __future__ import annotations

import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from pricewatch.application.use_cases import RefreshPrices
from pricewatch.domain.events import PriceEventBus
from pricewatch.infrastructure.db.engine import SessionLocal
from pricewatch.infrastructure.scrapers.factory import ScraperFactory

logger = logging.getLogger(__name__)


def run_refresh_job(factory: ScraperFactory, event_bus: PriceEventBus) -> None:
    """The job function that APScheduler will run periodically."""
    logger.info("Starting scheduled price refresh job...")
    session: Session = SessionLocal()
    try:
        use_case = RefreshPrices(session, factory, event_bus)
        use_case.execute()
    except Exception:
        logger.exception("Error during scheduled price refresh.")
    finally:
        session.close()


class PriceScheduler:
    """Manages the APScheduler instance and job scheduling."""

    def __init__(self, factory: ScraperFactory, event_bus: PriceEventBus) -> None:
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.factory = factory
        self.event_bus = event_bus

    def start(self, interval_minutes: int = 60) -> None:
        """Start the background scheduler."""
        # Add the refresh job
        self.scheduler.add_job(
            run_refresh_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[self.factory, self.event_bus],
            id="refresh_prices",
            name="Refresh product prices",
            replace_existing=True,
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("PriceScheduler started (interval: %d minutes).", interval_minutes)

    def shutdown(self) -> None:
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("PriceScheduler shut down.")
