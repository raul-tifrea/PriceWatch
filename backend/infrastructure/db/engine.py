from __future__ import annotations
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
load_dotenv()  
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://pricewatch:0000@localhost:5432/pricewatch",
)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)