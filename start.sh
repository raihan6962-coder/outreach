#!/bin/bash
set -e

cd /app/backend

if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" != *"+asyncpg"* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+asyncpg:\/\/}"
fi

if [ -z "$REDIS_URL" ]; then
    export REDIS_URL="redis://localhost:6379/0"
fi
if [ -z "$CELERY_BROKER_URL" ]; then
    export CELERY_BROKER_URL="$REDIS_URL"
fi
if [ -z "$CELERY_RESULT_BACKEND" ]; then
    export CELERY_RESULT_BACKEND="$REDIS_URL"
fi
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY="railway-$(openssl rand -hex 16)"
fi
if [ -z "$FRONTEND_URL" ]; then
    export FRONTEND_URL="https://$RAILWAY_PUBLIC_DOMAIN"
fi
if [ -z "$GOOGLE_REDIRECT_URI" ]; then
    export GOOGLE_REDIRECT_URI="https://$RAILWAY_PUBLIC_DOMAIN/api/v1/gmail/callback"
fi

export ENVIRONMENT="production"
export PYTHONPATH="/app/backend:$PYTHONPATH"

echo "Running database migrations..."
alembic upgrade head || echo "Migrations done"

echo "Starting web server..."
cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
