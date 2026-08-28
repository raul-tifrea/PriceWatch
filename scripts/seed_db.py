from datetime import datetime, timedelta
import uuid
import random
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.infrastructure.db.engine import SessionLocal
from backend.infrastructure.db.orm_models import ProductORM, ListingORM, PricePointORM
def seed_database():
    session = SessionLocal()
    try:
        print("Seeding database with a test product...")
        product_id = uuid.uuid4()
        product = ProductORM(
            id=product_id,
            name="Test iPhone 17 Pro",
            url="https://www.cel.ro/iphone-17",
            created_at=datetime.utcnow() - timedelta(days=30) 
        )
        session.add(product)

        listing_id = uuid.uuid4()
        listing = ListingORM(
            id=listing_id,
            product_id=product_id,
            retailer_id="cel.ro",
            url="https://www.cel.ro/iphone-17",
            title="Test iPhone 17 Pro",
            price=6000.0
        )
        session.add(listing)
        base_price = 6000.0
        current_time = datetime.utcnow() - timedelta(days=30)
        for i in range(31):
            if i % 7 == 0:
                base_price -= random.choice([50, 100, 150]) 
            elif i % 5 == 0:
                base_price += random.choice([20, 50]) 
            price_point = PricePointORM(
                id=uuid.uuid4(),
                listing_id=listing_id,
                price=base_price,
                recorded_at=current_time
            )
            session.add(price_point)
            current_time += timedelta(days=1)
        session.commit()
        print("Success! A test product with 30 days of price history has been added.")
    except Exception as e:
        session.rollback()
        print(f"Failed to seed database: {e}")
    finally:
        session.close()
if __name__ == "__main__":
    seed_database()