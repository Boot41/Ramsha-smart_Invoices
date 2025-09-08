"""
Main FastAPI application entry point for Smart Invoice Scheduler
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes.routes import routes_router
from utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    setup_logging()
    logging.info("🚀 Smart Invoice Scheduler starting up...")
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

# Include all routes
app.include_router(routes_router)

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