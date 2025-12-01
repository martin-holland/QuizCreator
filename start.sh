#!/bin/bash
# Startup script for production deployment
# Handles PORT environment variable with debugging

set -e  # Exit on error

# Debug: Print environment information
echo "=== Deployment Debug Information ==="
echo "PORT environment variable: ${PORT:-NOT SET}"
echo "FLASK_ENV: ${FLASK_ENV:-NOT SET}"
echo "DATABASE_URL: ${DATABASE_URL:+SET (hidden)}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET (hidden)}"
echo "===================================="

# Get port from environment variable
# Railway automatically sets PORT, but we default to 5000 for safety
# Railway will handle port mapping automatically
if [ -n "$PORT" ] && [[ "$PORT" =~ ^[0-9]+$ ]] && [ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ]; then
    # PORT is set and valid, use it
    PORT=$PORT
else
    # PORT is not set or invalid, use static 5000
    if [ -n "$PORT" ]; then
        echo "WARNING: PORT is invalid ('$PORT'), using default: 5000"
    else
        echo "INFO: PORT not set, using default: 5000"
    fi
    PORT=5000
fi

echo "Starting gunicorn on port: $PORT"

# Start gunicorn with the determined port
exec gunicorn app:app \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

