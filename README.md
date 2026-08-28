# PriceWatch

PriceWatch is a full-stack application for tracking product prices.

## Features
- Track product prices by adding a product URL.
- View price history on an interactive chart.

## Tech Stack
- Backend: Python, FastAPI, SQLAlchemy, PostgreSQL, BeautifulSoup.
- Frontend: React, Vite, Recharts, Vanilla CSS.

## How to Run

### 1. Database
Start the PostgreSQL container:
```
docker compose up -d
```

### 2. Backend
Run the FastAPI server from the root directory:
```
python -m scripts.run_api
```

### 3. Frontend
Start the Vite dev server:
```
cd frontend
npm run dev
```
