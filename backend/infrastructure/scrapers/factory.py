"""ScraperFactory — maps site names to scraper classes.

Adding a new retailer requires only:

1. Writing a new :class:`~pricewatch.infrastructure.scrapers.base.BaseScraper`
   subclass.
2. Registering it in :data:`_REGISTRY` below.

No other code needs to change — the application layer calls
:func:`ScraperFactory.get` and is shielded from concrete classes.
"""
from __future__ import annotations

from backend.infrastructure.scrapers.base import Scraper
from backend.infrastructure.scrapers.celro import CelRoScraper

# Registry maps the Retailer.id string to the concrete scraper class.
# Order matters for documentation but not for lookup.
_REGISTRY: dict[str, type[Scraper]] = {
    "cel.ro": CelRoScraper,
}


class ScraperFactory:
    """Factory that resolves a site name to a configured :class:`Scraper`."""

    @staticmethod
    def get(site_name: str, **kwargs: object) -> Scraper:
        """Return a new scraper instance for *site_name*.

        Args:
            site_name: Must match a key in the internal registry
                       (e.g. ``"cel.ro"``).
            **kwargs:  Forwarded to the scraper's constructor
                       (e.g. ``max_pages=5``).

        Raises:
            ValueError: If *site_name* is not registered.
        """
        cls = _REGISTRY.get(site_name)
        if cls is None:
            registered = ", ".join(f'"{k}"' for k in _REGISTRY)
            raise ValueError(
                f"No scraper registered for {site_name!r}. "
                f"Available: {registered}"
            )
        return cls(**kwargs)  # type: ignore[arg-type]

    @staticmethod
    def available() -> list[str]:
        """Return the list of registered site names."""
        return list(_REGISTRY.keys())
