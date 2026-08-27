"""Script to create all database tables based on ORM models."""
from backend.infrastructure.db.orm_models import Base
from backend.infrastructure.db.engine import engine

def main():
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Done!")

if __name__ == "__main__":
    main()
