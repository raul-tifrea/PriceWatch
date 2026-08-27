"""Console notifier — prints price events to stdout.

Useful for development, debugging, and demos.  Replace (or supplement) with
``EmailNotifier`` or ``DiscordNotifier`` in production.
"""
from __future__ import annotations

import logging

from pricewatch.domain.events import PriceEvent
from pricewatch.infrastructure.notifiers.base import Notifier

logger = logging.getLogger(__name__)


class ConsoleNotifier(Notifier):
    """Prints :class:`PriceEvent` details to stdout.

    Only logs events that are actual price drops (not new listings, unless
    ``notify_new`` is ``True``).

    Args:
        notify_new:   Also print notifications for brand-new listings.
        min_drop_pct: Minimum percentage drop to notify about (e.g. ``5.0``
                      means only notify if price dropped by ≥ 5 %).
                      Set to ``0.0`` to notify on any drop.
    """

    def __init__(
        self,
        *,
        notify_new: bool = False,
        min_drop_pct: float = 0.0,
    ) -> None:
        self.notify_new = notify_new
        self.min_drop_pct = min_drop_pct

    def handle(self, event: PriceEvent) -> None:
        if event.is_new_listing:
            if self.notify_new:
                print(
                    f"[NEW LISTING] {event.retailer_id}: "
                    f"{event.title[:60]} — {event.new_price} {event.currency}\n"
                    f"  {event.url}"
                )
            return

        if not event.is_price_drop:
            return  # price increase or unchanged — skip

        pct = event.price_change_pct or 0.0
        if abs(pct) < self.min_drop_pct:
            return

        print(
            f"\n🔔 PRICE DROP [{event.retailer_id}]\n"
            f"   {event.title[:70]}\n"
            f"   {event.old_price} → {event.new_price} {event.currency}  "
            f"({pct:+.1f}%)\n"
            f"   {event.url}"
        )
        logger.info(
            "Price drop: %s %.2f -> %.2f %s (%.1f%%)",
            event.title[:40],
            event.old_price,
            event.new_price,
            event.currency,
            pct,
        )
