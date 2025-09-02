FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install system packages including Docker CLI and psutil deps
RUN apt-get update && apt-get install -y \
    docker.io \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn requests pyyaml flask psutil

EXPOSE 8080

CMD ["uvicorn", "agent.app:app", "--host", "0.0.0.0", "--port", "8080"]
