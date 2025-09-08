"""
Main FastAPI application entry point for Smart Invoice Scheduler
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup - minimal initialization for faster startup
    setup_logging()
    logging.info("🚀 Smart Invoice Scheduler starting up...")

    # Import and include routes after app startup to avoid blocking startup
    try:
        from routes.routes import routes_router  # pylint: disable=import-outside-toplevel
        app.include_router(routes_router)
        logging.info("✅ Routes loaded successfully")
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("❌ Error loading routes: %s", exc)
        # Continue anyway - basic endpoints will still work

    yield
    # Shutdown
    logging.info("🛑 Smart Invoice Scheduler shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Smart Invoice Scheduler",
    description="Intelligent invoice scheduling and processing system",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (React frontend)
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except RuntimeError:
    # Static directory doesn't exist, skip mounting
    logging.warning("Static directory not found, skipping frontend mount")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "smart-invoice-scheduler"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)