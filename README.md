# PriceWatch

PriceWatch is a full-stack web scraper and tracking application. It automatically scrapes retail websites to monitor product prices over time.

## Features
- **Web Scraping:** Automatically fetch the latest prices directly from supported retailers (e.g. cel.ro) by providing a product URL.
- **Price Tracking:** View the historical scraped price data on an interactive chart.

## Tech Stack
- Backend: Python, FastAPI, SQLAlchemy, PostgreSQL, BeautifulSoup.
- Frontend: React, Vite, Vanilla CSS.

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
