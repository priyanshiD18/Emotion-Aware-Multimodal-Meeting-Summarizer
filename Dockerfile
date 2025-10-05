# Multi-stage build for Meeting Intelligence Platform

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config.env.example ./config.env

# Create necessary directories
RUN mkdir -p data/uploads data/outputs data/chroma_db models/cache

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# API service image
FROM base as api
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Frontend service image
FROM base as frontend
CMD ["streamlit", "run", "src/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

