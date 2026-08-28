from backend.infrastructure.db.engine import engine
from backend.infrastructure.db.orm_models import Base
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already exist).")
if __name__ == "__main__":
    create_tables()