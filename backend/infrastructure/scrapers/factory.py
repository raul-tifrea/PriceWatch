from __future__ import annotations
from backend.infrastructure.scrapers.base import Scraper
from backend.infrastructure.scrapers.celro import CelRoScraper
from backend.infrastructure.scrapers.pcgarage import PcGarageScraper
from backend.infrastructure.scrapers.altex import AltexScraper
_REGISTRY: dict[str, type[Scraper]] = {
    "cel.ro": CelRoScraper,
    "pcgarage.ro": PcGarageScraper,
    "altex.ro": AltexScraper,
}
class ScraperFactory:
    @staticmethod
    def get(site_name: str, **kwargs: object) -> Scraper:
        cls = _REGISTRY.get(site_name)
        if cls is None:
            registered = ", ".join(f'"{k}"' for k in _REGISTRY)
            raise ValueError(
                f"No scraper registered for {site_name!r}. "
                f"Available: {registered}"
            )
        return cls(**kwargs)  
    @staticmethod
    def available() -> list[str]:
        return list(_REGISTRY.keys())