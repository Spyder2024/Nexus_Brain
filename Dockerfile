# Multi-Stage Production Dockerfile for NexusBrain
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code, schemas, and configurations
COPY src/ /app/src/
COPY data/ /app/data/
COPY .agent/ /app/.agent/
COPY .env.example /app/.env.example

# Expose FastAPI backend (8000) and Streamlit UI (8501)
EXPOSE 8000 8501

# Healthcheck targeting FastAPI ping or auto_seed check
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "from src.graph.loader import FalkorDBLoader; l = FalkorDBLoader(); exit(0 if l.ping() else 1)"

# Default entrypoint: Run auto-seeder to ensure FalkorDB is ready, then run application
ENTRYPOINT ["python", "src/main.py"]
CMD ["--mode", "all"]
