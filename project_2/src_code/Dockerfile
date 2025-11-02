# Amazon Review Analysis Pipeline - Docker Image
# ================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command (run full pipeline)
CMD ["python", "scripts/pipeline.py", "--all"]

# Usage examples:
# Build: docker build -t review-analysis .
# Run:   docker run --env-file .env review-analysis
# Extract only: docker run --env-file .env review-analysis python scripts/pipeline.py --step extract
# Process only: docker run --env-file .env review-analysis python scripts/pipeline.py --step process
# Dry-run: docker run --env-file .env review-analysis python scripts/pipeline.py --all --dry-run
