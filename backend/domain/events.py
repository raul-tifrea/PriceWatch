from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Callable
from uuid import UUID
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class PriceEvent:
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
        return self.old_price is None
    @property
    def is_price_drop(self) -> bool:
        return self.old_price is not None and self.new_price < self.old_price
    @property
    def price_change_pct(self) -> float | None:
        if self.old_price is None or self.old_price == 0:
            return None
        return float((self.new_price - self.old_price) / self.old_price * 100)
EventHandler = Callable[[PriceEvent], None]
class PriceEventBus:
    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []
    def subscribe(self, handler: EventHandler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)
            logger.debug("PriceEventBus: subscribed %s", getattr(handler, "__name__", repr(handler)))
    def unsubscribe(self, handler: EventHandler) -> None:
        try:
            self._handlers.remove(handler)
        except ValueError:
            pass
    def publish(self, event: PriceEvent) -> None:
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
        return len(self._handlers)