#!/bin/bash
# Startup script for Render deployment
# Render sets $PORT automatically and it works with shell expansion

set -e

# Use PORT from environment (Render sets this automatically)
# Default to 5000 if not set (shouldn't happen on Render)
PORT=${PORT:-5000}

echo "Starting gunicorn on port: $PORT"

# Start gunicorn
exec gunicorn app:app \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

