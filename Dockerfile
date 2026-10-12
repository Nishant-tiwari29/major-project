# ==============================================================================
# Multi-Stage Dockerfile for Intelligent Logistics & Vehicle Routing Optimizer 2.0
# ==============================================================================

# STAGE 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# STAGE 2: Python Backend Runtime
FROM python:3.11-slim AS backend-runtime
WORKDIR /app

# Prevent Python from writing .pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=backend \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy source code and data
COPY backend/ ./backend/
COPY data/ ./data/

# Copy pre-built frontend static assets from STAGE 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Seed database and pre-train ML traffic model
RUN python backend/app/core/seed_data.py && \
    python backend/app/ml/model_trainer.py

EXPOSE 8000

# Start FastAPI serving both API and frontend SPA
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
