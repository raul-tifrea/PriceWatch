import logging
from typing import Optional
from uuid import UUID
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.infrastructure.db.engine import SessionLocal
from backend.infrastructure.db.orm_models import UserORM
from backend.application.use_cases import AddProduct, AddProductFromExtension, RefreshPrices, GetPriceHistory, RemoveProduct
from backend.infrastructure.db.repositories import ProductRepository
from backend.infrastructure.scrapers.factory import ScraperFactory
from backend.domain.events import PriceEventBus
from backend.infrastructure.scheduler import PriceScheduler
from backend.infrastructure.auth import (
    hash_password, verify_password, create_access_token, get_current_user
)
logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    factory = ScraperFactory()
    event_bus = PriceEventBus()
    scheduler = PriceScheduler(factory, event_bus)
    scheduler.start(interval_minutes=60)
    yield
    scheduler.shutdown()
app = FastAPI(title="PriceWatch API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
class RegisterRequest(BaseModel):
    email: str
    password: str
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    email: str
@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(UserORM).filter(UserORM.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = UserORM(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "email": user.email}
@app.post("/api/auth/login")
def login(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "email": user.email}
@app.get("/api/auth/me")
def me(current_user: UserORM = Depends(get_current_user)):
    return {"id": str(current_user.id), "email": current_user.email}
@app.get("/api/products")
def list_products(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    product_repo = ProductRepository(db)
    history_uc = GetPriceHistory(db)
    products = product_repo.list_for_user(current_user.id)
    results = []
    for p in products:
        history = history_uc.execute(p.id)
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
                    "date": pt.recorded_at.isoformat(),
                    "price": float(pt.price),
                    "retailer": retailer_id
                })
        results.append({
            "id": str(p.id),
            "name": p.name,
            "url": p.url,
            "created_at": p.created_at.isoformat(),
            "current_price": current_price,
            "initial_price": initial_price,
            "history": formatted_history
        })
    return results
class ProductCreate(BaseModel):
    name: str
    url: str
@app.post("/api/products")
def add_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    uc = AddProduct(db)
    product = uc.execute(name=payload.name, url=payload.url, user_id=current_user.id)
    return {"message": "success", "id": str(product.id)}
class ProductFromExtension(BaseModel):
    name: str
    url: str
    retailer_id: str
    title: str
    price: float
    external_id: str
    image_url: Optional[str] = None
    currency: str = "RON"
@app.post("/api/products/from-extension")
def add_product_from_extension(
    payload: ProductFromExtension,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    from decimal import Decimal
    import hashlib
    product_repo = ProductRepository(db)
    existing_product = product_repo.get_by_url_for_user(payload.url, current_user.id)
    if existing_product:
        raise HTTPException(status_code=409, detail="You are already tracking this product.")
    uc = AddProductFromExtension(db)
    ext_id = payload.external_id
    if len(ext_id) > 128:
        ext_id = hashlib.sha256(ext_id.encode('utf-8')).hexdigest()
    product = uc.execute(
        name=payload.name,
        url=payload.url,
        retailer_id=payload.retailer_id,
        title=payload.title,
        price=Decimal(str(payload.price)),
        external_id=ext_id,
        image_url=payload.image_url,
        currency=payload.currency,
        user_id=current_user.id,
    )
    return {"message": "success", "id": str(product.id)}
@app.delete("/api/products/{product_id}")
def remove_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    uc = RemoveProduct(db)
    uc.execute(product_id)
    return {"message": "success"}
@app.post("/api/refresh")
def refresh_prices(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    factory = ScraperFactory()
    bus = PriceEventBus()
    uc = RefreshPrices(db, factory, bus)
    uc.execute()
    return {"message": "success"}