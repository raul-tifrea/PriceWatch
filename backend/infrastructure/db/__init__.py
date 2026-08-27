"""DB infrastructure package.

Run ``python -m pricewatch.infrastructure.db`` to create all tables.
"""
from backend.infrastructure.db.engine import engine
from backend.infrastructure.db.orm_models import Base


def create_tables() -> None:
    """Create all ORM-defined tables that don't already exist."""
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already exist).")


if __name__ == "__main__":
    create_tables()
