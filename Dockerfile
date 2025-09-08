# Multi-stage Docker build for Smart Invoice Scheduler
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/client

# Copy package files
COPY client/package*.json ./

# Install dependencies
RUN npm ci

# Copy client source
COPY client/ ./

# Build frontend (skip TypeScript type checking)
ENV NODE_ENV=production
RUN npx vite build --mode production

# Python backend stage
FROM python:3.11-slim AS backend

# Install system dependencies including WeasyPrint requirements
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    curl \
    # WeasyPrint dependencies
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    shared-mime-info \
    libxml2-dev \
    libxslt-dev \
    libglib2.0-dev \
    libgirepository1.0-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy pyproject.toml first for better caching
COPY server/pyproject.toml ./

# Install dependencies with uv
RUN uv pip install --system --no-cache -e .

# Copy the rest of the backend files
COPY server/ ./

# Copy built frontend
COPY --from=frontend-builder /app/client/dist ./static

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start the application
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT}"