"""SQLAlchemy engine and session factory.

Reads ``DATABASE_URL`` from the environment (via ``.env`` if present).
All other modules import ``engine`` and ``SessionLocal`` from here — they
never call ``create_engine`` themselves.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()  # loads .env into os.environ (no-op if file absent)

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://pricewatch:0000@localhost:5432/pricewatch",
)

engine = create_engine(
    DATABASE_URL,
    # Connection pool tuned for a single-process scraper / small dashboard.
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # discard stale connections silently
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
