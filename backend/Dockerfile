# Backend Dockerfile for ReceiptBank API
FROM python:3.12-slim

WORKDIR /app

# Install system deps if needed (e.g. for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway sets PORT; default for local
ENV PORT=8000
EXPOSE 8000

# Run migrations then start the app (migrations need DATABASE_URL at runtime)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
