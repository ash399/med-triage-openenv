# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# Dockerfile for MedTriage Environment - Optimized for Hugging Face

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl is required for health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-install core dependencies to speed up build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH="/app"
ENV PORT=7860
ENV HOST=0.0.0.0

# Expose the app port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start the server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
