"""Notifier base class (Observer interface).

Every notification channel implements this ABC.  The concrete implementations
live in sub-modules alongside this file:

* ``console.py``  — prints to stdout (useful for development and testing)
* ``discord.py``  — sends a Discord webhook message  (future pass)
* ``email.py``    — sends an SMTP email              (future pass)
"""
from __future__ import annotations

import abc

from pricewatch.domain.events import PriceEvent


class Notifier(abc.ABC):
    """Observer interface — receives :class:`~pricewatch.domain.events.PriceEvent` objects."""

    @abc.abstractmethod
    def handle(self, event: PriceEvent) -> None:
        """React to a price event.

        Implementations should not raise exceptions — log errors instead.

        Args:
            event: The price change event to act on.
        """
