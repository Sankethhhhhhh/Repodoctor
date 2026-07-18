#!/bin/sh
set -e

cd /app

echo "Running database migrations..."
alembic upgrade head

if [ "$APP_ENVIRONMENT" = "production" ]; then
    echo "Starting server (production)..."
    WORKERS=${APP_WORKERS:-2}
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers "$WORKERS" \
        --no-access-log \
        --proxy-headers \
        --forwarded-allow-ips='*'
else
    echo "Starting server (development)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
