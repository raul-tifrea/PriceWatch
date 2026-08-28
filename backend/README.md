# PriceWatch Backend

Welcome to the backend of **PriceWatch**, a web scraping and price tracking service!

This component is responsible for orchestrating the web scraping processes, storing historical price data, and serving it to the frontend via a REST API.

## Core Responsibilities

1. **Web Scraping:** Uses `BeautifulSoup` and `httpx` to periodically scrape supported retail websites (such as `cel.ro`).
2. **Database:** Stores product definitions, listings, and price points using `SQLAlchemy` and `PostgreSQL`.
3. **API server:** Serves endpoints built with `FastAPI` to retrieve and manage scraped data.

## Adding a New Scraper

To add support for a new retailer:
1. Create a new scraper class inheriting from `BaseScraper` in `backend/infrastructure/scrapers/`.
2. Implement the `parse_product_page` method to extract price, title, and image from the raw HTML.
3. Register the new scraper in `backend/infrastructure/scrapers/factory.py`.

## Running the API

```bash
python -m scripts.run_api
```

For full setup instructions, see the [Main README](../README.md).
