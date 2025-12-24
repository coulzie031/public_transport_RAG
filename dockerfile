# 1. Use Python 3.14 (Slim version)
FROM python:3.14-slim

WORKDIR /app

# 2. Install build tools
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Upgrade pip
RUN pip install --upgrade pip

# 4. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code
COPY . .

# 6. Set environment variable for Gradio
# This ensures Gradio accepts connections from outside the container
ENV GRADIO_SERVER_NAME="0.0.0.0"

# 7. Expose the Gradio port
EXPOSE 7860

# 8. Run the agent script
# We don't need tail -f /dev/null because the Gradio server keeps the process alive.
CMD ["python", "agent.py"]
