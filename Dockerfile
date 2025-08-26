FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir fastapi uvicorn requests pyyaml flask
EXPOSE 8080
CMD ["uvicorn", "agent.app:app", "--host", "0.0.0.0", "--port", "8080"]
