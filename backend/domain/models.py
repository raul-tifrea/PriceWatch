from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
@dataclass
class Retailer:
    id: str          
    name: str        
    base_url: str    
@dataclass
class Product:
    name: str
    url: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
@dataclass
class Listing:
    product_id: UUID
    retailer_id: str          
    title: str
    price: Decimal
    currency: str
    url: str
    external_id: str | None = None   
    image_url: str | None = None
    id: UUID = field(default_factory=uuid4)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
@dataclass
class PricePoint:
    listing_id: UUID
    price: Decimal
    id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=datetime.utcnow)