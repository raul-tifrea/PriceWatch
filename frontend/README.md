# PriceWatch Frontend

The frontend of PriceWatch is a single-page application (SPA) built with React and Vite. It serves as the primary dashboard for users to view and manage their tracked products.

## Overview

The application connects to the FastAPI backend and provides the following capabilities:
- User authentication (Login/Registration) via JWT.
- A dashboard displaying all tracked products for the authenticated user.
- Interactive data visualization of historical price trends using Recharts.
- A responsive, component-based UI styled with vanilla CSS and CSS variables.

## Key Components

- **AuthContext:** Manages global authentication state and synchronizes token data across tabs and the Chrome extension via `window.postMessage`.
- **ProductModal:** Handles the detailed view of a product, including the Recharts line chart for price history.
- **api.js:** Configures the Axios HTTP client, including global interceptors for the Authorization header.

## Setup Instructions

Ensure Node.js is installed on your system.

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

For full instructions, refer to the [Main README](../README.md).
