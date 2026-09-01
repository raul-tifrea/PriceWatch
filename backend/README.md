# PriceWatch Backend

The backend of PriceWatch handles data persistence, web scraping, background task scheduling, and exposes a RESTful API for the frontend and Chrome extension.

## Core Responsibilities

1. **API Server:** Built with FastAPI to handle authentication, product management, and data retrieval.
2. **Database:** Uses PostgreSQL and SQLAlchemy ORM. The architecture follows the Repository Pattern to abstract SQL queries from the application logic.
3. **Web Scraping:** Uses BeautifulSoup4 and httpx. The scrapers are scheduled to run periodically via a background scheduler to keep price history up to date.
4. **Authentication:** Uses JWT and bcrypt for secure user session management.

## Architecture

The backend follows Domain-Driven Design (DDD) principles:
- `domain/`: Contains core entities and business rules.
- `application/`: Contains Use Cases to orchestrate business logic.
- `infrastructure/`: Contains database repositories, authentication logic, and web scrapers.
- `presentation/`: Contains the FastAPI routes.

## Adding a New Scraper

To add support for a new retailer:
1. Create a new scraper class inheriting from `BaseScraper` in `infrastructure/scrapers/`.
2. Implement the `parse_product_page` method.
3. Register the new scraper in `infrastructure/scrapers/factory.py`.

## Running Locally

Activate your virtual environment and start the server:
```bash
python -m scripts.run_api
```

For full setup instructions, see the [Main README](../README.md).
