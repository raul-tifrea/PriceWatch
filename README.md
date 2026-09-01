# PriceWatch

PriceWatch is a full-stack web scraper and price tracking application built to monitor product prices across Romanian retailers (Altex, PCGarage, Cel.ro). It includes a Chrome extension for easy product tracking directly from the retailer's page, and a web dashboard for data visualization.

## Features

- **Chrome Extension Integration:** Track products with a single click from supported retailer websites.
- **Secure Authentication:** JWT-based user authentication using passlib and bcrypt.
- **Data Visualization:** View historical price trends through interactive charts built with Recharts.
- **Automated Price Scraping:** A background task scheduler continuously monitors tracked products and updates prices.
- **Responsive UI:** A clean interface utilizing CSS variables and modern layout techniques.

### Backend
- **Framework:** FastAPI (Python 3)
- **Database:** PostgreSQL & SQLAlchemy ORM
- **Web Scraping:** BeautifulSoup4, Requests
- **Architecture:** Repository Pattern, Use Cases, Event-driven updates

### Frontend
- **Framework:** React & Vite
- **Routing:** React Router DOM
- **Visualization:** Recharts
- **Styling:** CSS

### Extension
- **Platform:** Manifest V3 Chrome Extension
- **Features:** Content scripts, DOM injection, synchronized authentication state via cross-origin messaging.

## Setup Instructions

### 1. Database
Start the PostgreSQL database using Docker:
```bash
docker compose up -d
```

### 2. Backend Server
Activate your Python virtual environment and run the FastAPI server:
```bash
.\.venv\Scripts\activate
python -m scripts.run_api
```
The API will be available at http://localhost:8000.

### 3. Frontend Dashboard
Start the Vite development server:
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at http://localhost:5173.

### 4. Chrome Extension
1. Open Google Chrome and navigate to chrome://extensions/.
2. Enable Developer mode in the top right corner.
3. Click Load unpacked and select the extension/ folder from this repository.
4. Navigate to a supported retailer product page to see the tracking button.
