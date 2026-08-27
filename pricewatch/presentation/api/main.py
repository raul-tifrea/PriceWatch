import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pricewatch.infrastructure.db.engine import SessionLocal
from pricewatch.application.use_cases import AddProduct, RefreshPrices, GetPriceHistory, RemoveProduct
from pricewatch.infrastructure.db.repositories import ProductRepository
from pricewatch.infrastructure.scrapers.factory import ScraperFactory
from pricewatch.domain.events import PriceEventBus

logger = logging.getLogger(__name__)

app = FastAPI(title="PriceWatch API")

# Allow React frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class ProductCreate(BaseModel):
    name: str
    url: str
    target_price: Optional[float] = None

class ProductResponse(BaseModel):
    id: UUID
    name: str
    url: str
    created_at: str

from pricewatch.infrastructure.db.orm_models import AlertORM

@app.get("/api/products")
def list_products(db = Depends(get_db)):
    """Return all products with their price history and alerts."""
    product_repo = ProductRepository(db)
    history_uc = GetPriceHistory(db)
    
    products = product_repo.list_all()
    results = []
    
    for p in products:
        history = history_uc.execute(p.id)
        alert = db.query(AlertORM).filter_by(product_id=p.id).first()
        target_price = float(alert.target_price) if alert else None
        
        # Format history for Recharts
        formatted_history = []
        current_price = None
        initial_price = None
        
        for retailer_id, points in history.items():
            if points:
                current_price = float(points[-1].price)
                if initial_price is None:
                    initial_price = float(points[0].price)
            for pt in points:
                formatted_history.append({
                    "date": pt.recorded_at.strftime("%Y-%m-%d %H:%M"),
                    "price": float(pt.price),
                    "retailer": retailer_id
                })
        
        results.append({
            "id": str(p.id),
            "name": p.name,
            "url": p.url,
            "created_at": p.created_at.strftime("%Y-%m-%d"),
            "current_price": current_price,
            "initial_price": initial_price,
            "target_price": target_price,
            "history": formatted_history
        })
        
    return results

@app.post("/api/products")
def add_product(payload: ProductCreate, db = Depends(get_db)):
    uc = AddProduct(db)
    product = uc.execute(name=payload.name, url=payload.url, target_price=payload.target_price)
    return {"message": "success", "id": str(product.id)}

@app.delete("/api/products/{product_id}")
def remove_product(product_id: UUID, db = Depends(get_db)):
    uc = RemoveProduct(db)
    uc.execute(product_id)
    return {"message": "success"}

@app.post("/api/refresh")
def refresh_prices(db = Depends(get_db)):
    factory = ScraperFactory()
    bus = PriceEventBus()
    uc = RefreshPrices(db, factory, bus)
    uc.execute()
    return {"message": "success"}
