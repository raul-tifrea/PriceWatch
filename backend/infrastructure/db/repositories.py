from __future__ import annotations
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.domain.models import Listing, PricePoint, Product
from backend.infrastructure.db.orm_models import (
    ListingORM,
    PricePointORM,
    ProductORM,
)
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
class ProductRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
    def add(self, product: Product) -> Product:
        orm_row = _product_to_orm(product)
        self._session.add(orm_row)
        self._session.flush()  
        return _orm_to_product(orm_row)
    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        row = self._session.get(ProductORM, product_id)
        return _orm_to_product(row) if row else None
    def list_all(self) -> list[Product]:
        rows = self._session.query(ProductORM).order_by(ProductORM.created_at).all()
        return [_orm_to_product(r) for r in rows]
    def delete(self, product_id: uuid.UUID) -> None:
        row = self._session.get(ProductORM, product_id)
        if row:
            self._session.delete(row)
            self._session.flush()
class PriceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
    def add_listing(self, listing: Listing) -> Listing:
        orm_row = _listing_to_orm(listing)
        self._session.add(orm_row)
        self._session.flush()
        return _orm_to_listing(orm_row)
    def get_listing_by_external_id(
        self, retailer_id: str, external_id: str
    ) -> Listing | None:
        row = (
            self._session.query(ListingORM)
            .filter_by(retailer_id=retailer_id, external_id=external_id)
            .one_or_none()
        )
        return _orm_to_listing(row) if row else None
    def get_listings_for_product(self, product_id: uuid.UUID) -> list[Listing]:
        rows = (
            self._session.query(ListingORM)
            .filter_by(product_id=product_id)
            .order_by(ListingORM.scraped_at.desc())
            .all()
        )
        return [_orm_to_listing(r) for r in rows]
    def add_price_point(self, price_point: PricePoint) -> PricePoint:
        orm_row = _price_point_to_orm(price_point)
        self._session.add(orm_row)
        self._session.flush()
        return _orm_to_price_point(orm_row)
    def get_history(self, listing_id: uuid.UUID) -> list[PricePoint]:
        rows = (
            self._session.query(PricePointORM)
            .filter_by(listing_id=listing_id)
            .order_by(PricePointORM.recorded_at)
            .all()
        )
        return [_orm_to_price_point(r) for r in rows]