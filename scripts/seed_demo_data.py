import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.infrastructure.db.engine import SessionLocal
from backend.infrastructure.db.orm_models import UserORM
from backend.domain.models import Product, Listing, PricePoint
from backend.infrastructure.db.repositories import ProductRepository, PriceRepository

def seed_demo_data():
    db = SessionLocal()
    try:
        user = db.query(UserORM).first()
        if not user:
            print("No user found in the database. Please register an account in the app first!")
            return

        product_repo = ProductRepository(db)
        price_repo = PriceRepository(db)

        demo_product = Product(
            id=uuid.uuid4(),
            name="Apple iPhone 15 Pro Max, 256GB, Titanium",
            url="https://altex.ro/cpd/SMPIPH15PM256NT-DEMO",
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        
        from backend.infrastructure.db.orm_models import ProductORM
        product_orm = ProductORM(
            id=demo_product.id,
            name=demo_product.name,
            url=demo_product.url,
            user_id=user.id,
            created_at=demo_product.created_at
        )
        db.add(product_orm)

        from backend.infrastructure.db.orm_models import ListingORM
        listing_id = uuid.uuid4()
        listing_orm = ListingORM(
            id=listing_id,
            product_id=demo_product.id,
            retailer_id="altex.ro",
            title="Telefon Apple iPhone 15 Pro Max, 256GB, 5G, Natural Titanium",
            url="https://altex.ro/cpd/SMPIPH15PM256NT-DEMO",
            external_id="SMPIPH15PM256NT-DEMO",
            image_url="https://lcdn.altex.ro/resize/media/catalog/product/i/p/2bd48d28d1c32adea0e55139a4e6434a/iphone_15_pro_max_natural_titanium_pdp_image_position-1__en-us_22bb33f7.jpg",
            price=Decimal("6800.00")
        )
        db.add(listing_orm)
        db.commit()

        base_price = 6800.00
        current_date = datetime.utcnow() - timedelta(days=30)
        
        print("Generating 30 days of price history...")
        for i in range(31):
            if i == 5:
                base_price = 6650.00
            elif i == 12:
                base_price = 6999.99
            elif i == 15:
                base_price = 6500.00
            elif i == 25:
                base_price = 6550.00

            daily_noise = random.uniform(-10.0, 10.0)
            final_price = round(base_price + daily_noise, 2)

            price_point = PricePoint(
                id=uuid.uuid4(),
                listing_id=listing_id,
                price=Decimal(str(final_price)),
                recorded_at=current_date
            )
            price_repo.add_price_point(price_point)
            
            current_date += timedelta(days=1)
            
        db.commit()
        print(f"Successfully added Demo Product to user {user.email}!")
        print("Go check your dashboard to see the interactive chart.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
