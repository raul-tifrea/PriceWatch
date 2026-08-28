import uuid
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
            name="Test RTX 5090 GPU",
            url="https://www.altex.ro/rtx-5090",
            created_at=datetime.utcnow() - timedelta(days=20)
        )
        session.add(product)
        listing_id = uuid.uuid4()
        listing = ListingORM(
            id=listing_id,
            product_id=product_id,
            retailer_id="altex.ro",
            url="https://www.altex.ro/rtx-5090",
            title="Test RTX 5090 GPU",
            price=12000.0
        )
        session.add(listing)
        base_price = 8000.0 
        current_time = datetime.utcnow() - timedelta(days=20)
        for i in range(21):
            if i > 10:
                base_price = 12000.0 
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