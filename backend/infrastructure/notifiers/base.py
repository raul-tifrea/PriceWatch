from __future__ import annotations
import abc
from backend.domain.events import PriceEvent
class Notifier(abc.ABC):
    @abc.abstractmethod
    def handle(self, event: PriceEvent) -> None: