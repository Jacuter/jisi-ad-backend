# Dockerfile — Jisi Ad Creative Backend
# Uses Python SDK instead of CLI for faster builds

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (fast)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Apify Python SDK (lightweight, no Node.js needed)
RUN pip install --no-cache-dir apify-client

# Copy application code
COPY modules/ ./modules/
COPY main.py ./

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
