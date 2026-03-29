# Dockerfile — Jisi Ad Creative Backend
FROM python:3.11-slim

WORKDIR /app

# Install Node.js for Apify CLI
RUN apt-get update && apt-get install -y \
    curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Apify CLI
RUN npm install -g apify-cli

# Copy requirements first
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application modules
COPY modules/ ./modules/

# Copy FastAPI entrypoint (main.py)
COPY main.py ./

# Note: Apify CLI login happens at runtime via `apify login` command
# The token is injected via the APIFY_TOKEN environment variable at runtime
# We DON'T pre-login here to avoid build failures due to invalid tokens

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
