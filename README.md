# MSignalAI Backend

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat&logo=pydantic&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-000000?style=flat&logo=langchain&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=flat&logo=google&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-2F8C9E?style=flat&logo=uvicorn&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

This directory contains the backend for the MSignalAI application, a high-performance API built with FastAPI. It serves as the data and intelligence hub, providing stock market data, technical analysis, fundamental data, news, and AI-powered insights to the frontend.

## Overview

The backend is responsible for:

*   **Exposing a RESTful API:** Providing endpoints for the frontend to fetch all necessary data.
*   **Integrating with External Services:** Fetching data from various financial data providers, including:
    *   **Twelve Data:** For historical price data.
    *   **Financial Modeling Prep (FMP):** For fundamental company data.
    *   **Tavily:** For real-time news articles.
*   **AI and Machine Learning:** Leveraging the Google Gemini API and LangChain to provide:
    *   **AI Stock Analysis:** Generating comprehensive reports on stock performance, fundamentals, and risks.
    *   **AI Chat:** Powering an interactive chat agent that can answer user questions and perform stock-related tasks.
*   **Caching:** Using Redis to cache responses from external APIs, improving performance and reducing redundant calls.
*   **Database:** Utilizing a local SQLite database for storing and retrieving data like stock prices (though much of the data is fetched and cached on-the-fly).

## Technologies

*   **FastAPI:** A modern, fast web framework for building APIs.
*   **Python 3.10:** The core programming language.
*   **Pydantic:** For data validation and settings management.
*   **SQLAlchemy (aiosqlite):** For asynchronous database interactions.
*   **Redis:** For in-memory caching.
*   **LangChain & Google Gemini:** For building AI-powered features.
*   **Uvicorn:** An ASGI server for running the FastAPI application.

## Getting Started

### Prerequisites

*   Python 3.9+
*   A running Redis server.

### Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in this directory and add the necessary API keys and settings. See the main project `README.md` for the required variables.

    ```
    FMP_API_KEY="YOUR_FMP_API_KEY"
    TWELVE_DATA_API_KEY="YOUR_TWELVE_DATA_API_KEY"
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    REDIS_URL="redis://localhost:6379"
    CORS_ORIGINS='["http://localhost:3000"]'
    ```

### Running the Server

Start the development server with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` and the interactive documentation can be accessed at `http://localhost:8000/docs`.

## Project Structure

```
app/
├── api/              # FastAPI endpoints and router configuration
│   ├── endpoints/    # Individual endpoint files (stock, market, agent, chat)
│   └── routers.py    # Main API router
├── cache/            # Redis caching logic
├── config/           # Application settings and environment variable loading
├── database/         # Database connection and table creation
├── schemas/          # Pydantic models for data validation and serialization
├── services/         # Core business logic and integration with external APIs
└── main.py           # FastAPI application entry point
```
