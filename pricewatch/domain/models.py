"""PriceWatch — domain layer.

Pure Python dataclasses with zero framework dependencies.
All business entities live here; no SQLAlchemy, no httpx, no Streamlit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass
class Retailer:
    """A retailer/marketplace that the system can scrape.

    Uses a human-readable string ID (e.g. ``"cel.ro"``) because the set of
    retailers is small and fixed — string IDs are self-documenting in logs,
    foreign-key columns, and config files.
    """

    id: str          # e.g. "cel.ro", "altex.ro"
    name: str        # e.g. "CEL.ro"
    base_url: str    # e.g. "https://www.cel.ro"


@dataclass
class Product:
    """A product the user wants to track.

    ``search_query`` is the free-text string sent to each retailer's search
    endpoint.  The same product may produce multiple :class:`Listing` rows —
    one per retailer per scrape run.
    """

    name: str
    search_query: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Listing:
    """A single product result returned by a scraper for one retailer.

    ``external_id`` is the retailer's own product identifier (e.g.
    ``data-pid_prod`` on cel.ro).  It is used to deduplicate results across
    scrape runs and to detect price changes for the same SKU.
    """

    product_id: UUID
    retailer_id: str          # FK to Retailer.id
    title: str
    price: Decimal
    currency: str
    url: str
    external_id: str | None = None   # retailer-assigned product ID
    image_url: str | None = None
    id: UUID = field(default_factory=uuid4)
    scraped_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PricePoint:
    """A timestamped price observation derived from a :class:`Listing`.

    A new ``PricePoint`` is recorded every time the scraper sees a price for
    a given ``external_id``, enabling historical trend analysis.
    """

    listing_id: UUID
    price: Decimal
    id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    """A price-drop alert configured by the user.

    When ``price <= target_price`` the alert fires via the configured
    ``channel`` (e.g. ``"email"``, ``"discord"``).
    ``triggered_at`` is ``None`` until the alert has fired at least once.
    """

    product_id: UUID
    target_price: Decimal
    channel: str                      # e.g. "email", "discord"
    id: UUID = field(default_factory=uuid4)
    triggered_at: datetime | None = None
