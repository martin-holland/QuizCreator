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

# Get port from environment variable, default to 5000
PORT=${PORT:-5000}

# Validate port is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be a number, got: '$PORT'"
    echo "Setting PORT to default: 5000"
    PORT=5000
fi

# Validate port is in valid range
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "ERROR: PORT must be between 1 and 65535, got: $PORT"
    echo "Setting PORT to default: 5000"
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

