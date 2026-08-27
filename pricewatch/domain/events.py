"""Domain events — the Observer pattern's event types and event bus.

Design
------
``PriceEventBus`` is the *Subject* in the Observer pattern.
``Notifier`` implementations (Console, Email, Discord) are *Observers* that
subscribe to it.  Crucially, the event bus lives in the **domain layer** —
it knows nothing about databases, scrapers, or scheduling frameworks.

This means adding a new notification channel (e.g. Telegram) requires:
1. Implementing ``Notifier`` in the infrastructure layer.
2. Subscribing it to the bus at startup.
No scraping or scheduling code changes at all.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Callable
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PriceEvent:
    """Emitted every time a scrape produces a price change for a listing.

    ``old_price`` is ``None`` the first time a listing is seen (new product
    on a retailer).  Subscribers can use this to distinguish "new listing"
    from "price changed".
    """

    product_id: UUID
    listing_id: UUID
    retailer_id: str
    title: str
    new_price: Decimal
    currency: str
    url: str
    old_price: Decimal | None = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_new_listing(self) -> bool:
        """True if this is the first price observation for this listing."""
        return self.old_price is None

    @property
    def is_price_drop(self) -> bool:
        """True if the price decreased compared to the previous observation."""
        return self.old_price is not None and self.new_price < self.old_price

    @property
    def price_change_pct(self) -> float | None:
        """Percentage price change, or ``None`` for new listings."""
        if self.old_price is None or self.old_price == 0:
            return None
        return float((self.new_price - self.old_price) / self.old_price * 100)


# ---------------------------------------------------------------------------
# Event bus (Observer Subject)
# ---------------------------------------------------------------------------

#: Type alias for event handler callables.
EventHandler = Callable[[PriceEvent], None]


class PriceEventBus:
    """Simple synchronous event bus for :class:`PriceEvent` objects.

    Usage::

        bus = PriceEventBus()
        bus.subscribe(my_handler)
        bus.publish(PriceEvent(...))   # my_handler is called immediately

    The bus is intentionally synchronous and in-process.  If you later need
    async fanout or durable queues, replace this with an async version or a
    message broker — the ``subscribe`` / ``publish`` interface stays the same.
    """

    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        """Register *handler* to be called for every published event.

        Args:
            handler: A callable that accepts a single :class:`PriceEvent`.
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            logger.debug("PriceEventBus: subscribed %s", getattr(handler, "__name__", repr(handler)))

    def unsubscribe(self, handler: EventHandler) -> None:
        """Remove a previously registered handler (idempotent)."""
        try:
            self._handlers.remove(handler)
        except ValueError:
            pass

    def publish(self, event: PriceEvent) -> None:
        """Dispatch *event* to all registered handlers.

        Errors in individual handlers are logged but do not prevent other
        handlers from receiving the event.
        """
        logger.debug(
            "PriceEventBus: publishing PriceEvent for %s @ %s %s",
            event.title[:40],
            event.new_price,
            event.currency,
        )
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "PriceEventBus: handler %s raised an exception",
                    getattr(handler, "__name__", repr(handler)),
                )

    def handler_count(self) -> int:
        """Return the number of currently registered handlers."""
        return len(self._handlers)
