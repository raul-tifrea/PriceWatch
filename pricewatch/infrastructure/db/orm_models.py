"""SQLAlchemy ORM models (mapped classes).

These are **infrastructure** concerns — they mirror the schema but are NOT
the same as the domain dataclasses in ``pricewatch.domain.models``.

The repositories are responsible for converting between ORM rows and domain
objects so the application/domain layers never import from here.

Schema overview
---------------
products        — one row per tracked product
listings        — one row per (product, retailer, scrape_run)
price_points    — append-only price history, one row per new price observation
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class ProductORM(Base):
    """Persisted representation of :class:`~pricewatch.domain.models.Product`."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    search_query: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    listings: Mapped[list[ListingORM]] = relationship(
        "ListingORM", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProductORM id={self.id} name={self.name!r}>"


class ListingORM(Base):
    """Persisted representation of :class:`~pricewatch.domain.models.Listing`.

    ``external_id`` is the retailer-assigned product identifier (e.g.
    ``data-pid_prod`` on cel.ro).  The composite unique constraint on
    ``(retailer_id, external_id)`` enables efficient deduplication when
    the scheduler runs.
    """

    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("retailer_id", "external_id", name="uq_listing_retailer_external"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    retailer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RON")
    url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    product: Mapped[ProductORM] = relationship("ProductORM", back_populates="listings")
    price_points: Mapped[list[PricePointORM]] = relationship(
        "PricePointORM", back_populates="listing", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ListingORM id={self.id} title={self.title[:40]!r} price={self.price}>"


class PricePointORM(Base):
    """Append-only price history for a :class:`ListingORM`.

    A new row is inserted whenever the scheduler detects a price change for
    a given ``listing_id``.
    """

    __tablename__ = "price_points"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    listing: Mapped[ListingORM] = relationship("ListingORM", back_populates="price_points")

    def __repr__(self) -> str:
        return f"<PricePointORM id={self.id} price={self.price} at={self.recorded_at}>"


class AlertORM(Base):
    """Persisted representation of :class:`~pricewatch.domain.models.Alert`.

    When the scheduler detects ``listing.price <= target_price`` for a tracked
    product, it fires the alert and sets ``triggered_at``.
    """

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False, default="console")
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AlertORM id={self.id} product={self.product_id} "
            f"target={self.target_price} channel={self.channel!r}>"
        )
