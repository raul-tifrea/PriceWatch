"""Repository implementations for the database layer.

Each repository wraps all SQLAlchemy access for one aggregate, exposing a
clean, framework-free interface to the application layer.

Design notes
------------
* Repositories accept a ``Session`` in ``__init__`` — callers (use-cases)
  control the transaction boundary and inject the session.  This makes the
  repositories straightforward to test with an in-memory or mock session.
* Conversion between ORM rows and domain dataclasses happens here and only
  here.  The domain layer has zero awareness of SQLAlchemy.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from pricewatch.domain.models import Alert, Listing, PricePoint, Product
from pricewatch.infrastructure.db.orm_models import (
    AlertORM,
    ListingORM,
    PricePointORM,
    ProductORM,
)


# ---------------------------------------------------------------------------
# Helpers: ORM ↔ domain conversion
# ---------------------------------------------------------------------------


def _product_to_orm(product: Product) -> ProductORM:
    return ProductORM(
        id=product.id,
        name=product.name,
        url=product.url,
        created_at=product.created_at,
    )


def _orm_to_product(row: ProductORM) -> Product:
    return Product(
        id=row.id,
        name=row.name,
        url=row.url,
        created_at=row.created_at,
    )


def _listing_to_orm(listing: Listing) -> ListingORM:
    return ListingORM(
        id=listing.id,
        product_id=listing.product_id,
        retailer_id=listing.retailer_id,
        external_id=listing.external_id,
        title=listing.title,
        price=listing.price,
        currency=listing.currency,
        url=listing.url,
        image_url=listing.image_url,
        scraped_at=listing.scraped_at,
    )


def _orm_to_listing(row: ListingORM) -> Listing:
    return Listing(
        id=row.id,
        product_id=row.product_id,
        retailer_id=row.retailer_id,
        external_id=row.external_id,
        title=row.title,
        price=Decimal(str(row.price)),
        currency=row.currency,
        url=row.url,
        image_url=row.image_url,
        scraped_at=row.scraped_at,
    )


def _price_point_to_orm(pp: PricePoint) -> PricePointORM:
    return PricePointORM(
        id=pp.id,
        listing_id=pp.listing_id,
        price=pp.price,
        recorded_at=pp.recorded_at,
    )


def _orm_to_price_point(row: PricePointORM) -> PricePoint:
    return PricePoint(
        id=row.id,
        listing_id=row.listing_id,
        price=Decimal(str(row.price)),
        recorded_at=row.recorded_at,
    )


# ---------------------------------------------------------------------------
# ProductRepository
# ---------------------------------------------------------------------------


class ProductRepository:
    """All database access for :class:`~pricewatch.domain.models.Product`.

    Args:
        session: An active SQLAlchemy :class:`~sqlalchemy.orm.Session`.
                 The caller owns the transaction (``commit`` / ``rollback``).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, product: Product) -> Product:
        """Persist *product* and return it (with any DB-generated fields)."""
        orm_row = _product_to_orm(product)
        self._session.add(orm_row)
        self._session.flush()  # assigns DB defaults without committing
        return _orm_to_product(orm_row)

    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        """Return the product with *product_id*, or ``None`` if not found."""
        row = self._session.get(ProductORM, product_id)
        return _orm_to_product(row) if row else None

    def list_all(self) -> list[Product]:
        """Return every tracked product."""
        rows = self._session.query(ProductORM).order_by(ProductORM.created_at).all()
        return [_orm_to_product(r) for r in rows]

    def delete(self, product_id: uuid.UUID) -> None:
        """Delete product and its cascaded data."""
        row = self._session.get(ProductORM, product_id)
        if row:
            self._session.delete(row)
            self._session.flush()


# ---------------------------------------------------------------------------
# PriceRepository
# ---------------------------------------------------------------------------


class PriceRepository:
    """All database access for :class:`~pricewatch.domain.models.Listing`
    and :class:`~pricewatch.domain.models.PricePoint`.

    Args:
        session: An active SQLAlchemy :class:`~sqlalchemy.orm.Session`.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # --- listings -----------------------------------------------------------

    def add_listing(self, listing: Listing) -> Listing:
        """Persist *listing* and return it."""
        orm_row = _listing_to_orm(listing)
        self._session.add(orm_row)
        self._session.flush()
        return _orm_to_listing(orm_row)

    def get_listing_by_external_id(
        self, retailer_id: str, external_id: str
    ) -> Listing | None:
        """Look up an existing listing by retailer + retailer-assigned ID.

        Used for deduplication: if a listing already exists, callers can
        update it rather than inserting a duplicate row.
        """
        row = (
            self._session.query(ListingORM)
            .filter_by(retailer_id=retailer_id, external_id=external_id)
            .one_or_none()
        )
        return _orm_to_listing(row) if row else None

    def get_listings_for_product(self, product_id: uuid.UUID) -> list[Listing]:
        """Return all listings ever scraped for *product_id*."""
        rows = (
            self._session.query(ListingORM)
            .filter_by(product_id=product_id)
            .order_by(ListingORM.scraped_at.desc())
            .all()
        )
        return [_orm_to_listing(r) for r in rows]

    # --- price points -------------------------------------------------------

    def add_price_point(self, price_point: PricePoint) -> PricePoint:
        """Persist *price_point* and return it."""
        orm_row = _price_point_to_orm(price_point)
        self._session.add(orm_row)
        self._session.flush()
        return _orm_to_price_point(orm_row)

    def get_history(self, listing_id: uuid.UUID) -> list[PricePoint]:
        """Return all price points for *listing_id*, oldest first."""
        rows = (
            self._session.query(PricePointORM)
            .filter_by(listing_id=listing_id)
            .order_by(PricePointORM.recorded_at)
            .all()
        )
        return [_orm_to_price_point(r) for r in rows]


# ---------------------------------------------------------------------------
# Alert Repository
# ---------------------------------------------------------------------------

def _orm_to_alert(orm_obj: AlertORM) -> Alert:
    return Alert(
        id=orm_obj.id,
        product_id=orm_obj.product_id,
        target_price=orm_obj.target_price,
        channel=orm_obj.channel,
        triggered_at=orm_obj.triggered_at,
    )

def _alert_to_orm(domain_obj: Alert) -> AlertORM:
    return AlertORM(
        id=domain_obj.id,
        product_id=domain_obj.product_id,
        target_price=domain_obj.target_price,
        channel=domain_obj.channel,
        triggered_at=domain_obj.triggered_at,
    )

class AlertRepository:
    """Manages persistence for user-configured :class:`~pricewatch.domain.models.Alert`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, alert: Alert) -> None:
        """Save a new alert to the database."""
        orm_obj = _alert_to_orm(alert)
        self._session.add(orm_obj)

    def list_active(self) -> list[Alert]:
        """Return all alerts that have not yet been triggered."""
        rows = self._session.query(AlertORM).filter_by(triggered_at=None).all()
        return [_orm_to_alert(r) for r in rows]

    def update(self, alert: Alert) -> None:
        """Update an existing alert (e.g. mark it as triggered)."""
        orm_obj = self._session.get(AlertORM, alert.id)
        if orm_obj:
            orm_obj.target_price = alert.target_price
            orm_obj.channel = alert.channel
            orm_obj.triggered_at = alert.triggered_at
