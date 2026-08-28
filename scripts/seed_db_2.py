import uuid
import random
import os
import sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.infrastructure.db.engine import SessionLocal
from backend.infrastructure.db.orm_models import ProductORM, ListingORM, PricePointORM
def seed_database():
    session = SessionLocal()
    try:
        product_id = uuid.uuid4()
        product = ProductORM(
            id=product_id,
            name="Test Samsung Galaxy S25",
            url="https://www.altex.ro/samsung-s25",
            created_at=datetime.utcnow() - timedelta(days=15)
        )
        session.add(product)
        listing_id = uuid.uuid4()
        listing = ListingORM(
            id=listing_id,
            product_id=product_id,
            retailer_id="altex.ro",
            url="https://www.altex.ro/samsung-s25",
            title="Test Samsung Galaxy S25",
            price=3000.0
        )
        session.add(listing)
        base_price = 5000.0 
        current_time = datetime.utcnow() - timedelta(days=15)
        for i in range(16):
            if i > 5:
                base_price = 3000.0 
            price_point = PricePointORM(
                id=uuid.uuid4(),
                listing_id=listing_id,
                price=base_price,
                recorded_at=current_time
            )
            session.add(price_point)
            current_time += timedelta(days=1)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Failed to seed database: {e}")
    finally:
        session.close()
if __name__ == "__main__":
    seed_database()