# 1. Use the latest stable Python 3.14 (Slim version for smaller image size)
FROM python:3.14-slim

WORKDIR /app

# 2. Install build tools needed for Kafka and Elasticsearch clients
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Upgrade pip to the latest 2025 version (25.3+)
RUN pip install --upgrade pip

# 4. Install your project dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keep container alive
CMD ["tail", "-f", "/dev/null"]
