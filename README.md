# PriceWatch 🛍️

PriceWatch is a modern, full-stack application designed to help you track product prices across major retailers, visualize price history, and receive alerts when prices drop below your target threshold.

## Features

- **Price Tracking**: Add a product URL (e.g., from `cel.ro`) and the system will automatically scrape and track its current price.
- **Price History Graphs**: View a beautiful, interactive chart showing how the price has changed over time (1D, 1W, 1M, 6M, Max).
- **Target Alerts**: Set a target price. The system calculates your overall savings and alerts you if the price drops below your target.
- **Clean Architecture**: Built with a decoupled FastAPI backend and a responsive React frontend.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL, BeautifulSoup (for scraping).
- **Frontend**: React, Vite, React Router, Recharts, Vanilla CSS (Glassmorphism design).

## How to Run

To run the application locally, you will need to start the database, the backend API, and the frontend server.

### 1. Start the Database (PostgreSQL)
Ensure Docker is running on your machine, then start the database container:
```powershell
docker compose up -d
```

### 2. Start the Backend API (FastAPI)
Open a terminal in the root `PriceWatch/` directory and run the server:
```powershell
python -m scripts.run_api
```
*(The API will start on `http://localhost:8000`)*

### 3. Start the Frontend (React)
Open a **second** terminal, navigate to the `frontend/` directory, and start the Vite dev server:
```powershell
cd frontend
npm run dev
```
*(The UI will start on `http://localhost:5173` — open this URL in your browser!)*
