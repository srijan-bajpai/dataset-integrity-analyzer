#!/usr/bin/env bash
set -e

# Function to wait for Postgres if configured
wait_for_db() {
    if [[ "$DIA_DATABASE_URL" == postgres* ]]; then
        echo "==> Detected PostgreSQL database URL. Checking connection..."
        python - << 'EOF'
import sys, time, os
import psycopg2

db_url = os.environ.get("DIA_DATABASE_URL", "")
max_retries = 30
for attempt in range(1, max_retries + 1):
    try:
        clean_url = db_url.replace("postgresql+psycopg2://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")
        conn = psycopg2.connect(clean_url, connect_timeout=3)
        conn.close()
        print(f"==> Database connected successfully on attempt {attempt}.")
        sys.exit(0)
    except Exception as e:
        print(f"==> Waiting for database (attempt {attempt}/{max_retries}): {e}")
        time.sleep(2)
sys.exit(1)
EOF
    fi
}

run_migrations() {
    echo "==> Running database migrations (alembic upgrade head)..."
    alembic upgrade head
}

MODE="${1:-all-in-one}"

case "$MODE" in
    api)
        wait_for_db
        run_migrations
        echo "==> Starting DIA API server on port ${PORT:-8000}..."
        exec uvicorn dia.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
        ;;

    worker)
        wait_for_db
        echo "==> Starting DIA background worker..."
        exec python -m dia.worker
        ;;

    all-in-one|standalone)
        wait_for_db
        run_migrations
        echo "==> Starting DIA worker in background..."
        python -m dia.worker &
        WORKER_PID=$!

        echo "==> Starting DIA API server on port ${PORT:-8000}..."
        uvicorn dia.api.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
        API_PID=$!

        # Graceful shutdown handler
        trap 'echo "==> Shutting down DIA..."; kill -TERM "$API_PID" "$WORKER_PID" 2>/dev/null; wait "$API_PID" "$WORKER_PID"' SIGTERM SIGINT

        # Wait for either process to exit
        wait -n "$API_PID" "$WORKER_PID"
        EXIT_CODE=$?
        echo "==> A DIA sub-process exited with code $EXIT_CODE. Exiting container."
        kill -TERM "$API_PID" "$WORKER_PID" 2>/dev/null || true
        exit $EXIT_CODE
        ;;

    *)
        exec "$@"
        ;;
esac
