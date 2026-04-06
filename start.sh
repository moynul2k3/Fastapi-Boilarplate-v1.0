#!/bin/sh
set -e

# Wait for MySQL to be ready
echo "Waiting for MySQL at $DB_HOST:$DB_PORT..."
until nc -z "$DB_HOST" "$DB_PORT"; do
    echo "MySQL not ready, sleeping 3s..."
    sleep 3
done
echo "MySQL is ready!"

# Run schema migrations (production-safe)
echo "Applying Aerich migrations..."
# Do not run `aerich migrate` in production startup.
# `migrate` generates new migration files and needs writable source tree.
if aerich upgrade; then
    echo "Aerich upgrade completed."
else
    echo "Aerich upgrade failed; trying first-time init-db..."
    aerich init-db
fi

# Start FastAPI
echo "Starting FastAPI..."
PORT="${PORT:-8000}"
WORKERS="${WEB_CONCURRENCY:-3}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
