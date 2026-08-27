# PriceWatch

A multi-site price tracker built as a portfolio project demonstrating layered architecture, design patterns, and testability.

## Architecture

```
pricewatch/
├── domain/          # Pure dataclasses — no framework dependencies
├── application/     # Use cases (wiring domain + infrastructure)
├── infrastructure/  # Scrapers, SQLAlchemy repos, scheduler, notifier
└── presentation/    # Streamlit dashboard (next pass)
```

## Design Patterns

| Pattern | Location | Purpose |
|---|---|---|
| **Strategy** | `infrastructure/scrapers/base.py` | `Scraper` ABC — every retailer implements the same interface |
| **Template Method** | `infrastructure/scrapers/base.py` | `BaseScraper.search()` orchestrates fetch→parse→normalize; subclasses override `parse()` |
| **Factory** | `infrastructure/scrapers/factory.py` | `ScraperFactory.get("cel.ro")` — decouples callers from concrete classes |
| **Repository** | `infrastructure/db/repositories.py` | DB access behind a clean interface; application never imports SQLAlchemy |

## Retailers

| Site | Scraper | Method |
|---|---|---|
| `cel.ro` | `CelRoScraper` | httpx + BeautifulSoup (server-rendered HTML) |
| `altex.ro` | `AltexScraper` | Playwright + `__NEXT_DATA__` JSON (Next.js SSR) |

## Setup

### 1. Start Postgres
```bash
docker compose up -d
```

### 2. Install dependencies
```bash
pip install -e ".[dev]"
playwright install chromium
```

### 3. Create DB tables
```bash
python -m pricewatch.infrastructure.db
```

### 4. Run tests
```bash
pytest -v
```

### 5. Capture altex.ro fixture (run once)
```bash
python scripts/capture_altex_fixture.py
```

## Environment

Copy `.env.example` to `.env`:
```
DATABASE_URL=postgresql+psycopg2://pricewatch:0000@localhost:5432/pricewatch
```
