#!/bin/bash
# Startup script for Cloud Run / Render deployment
# Cloud Run and Render set $PORT automatically and it works with shell expansion

set -e

# Use PORT from environment (Cloud Run/Render sets this automatically)
# Default to 8080 (Cloud Run standard) or 5000 (Render standard) if not set
PORT=${PORT:-8080}

echo "Starting gunicorn on port: $PORT"

# Start gunicorn using wsgi.py (explicit entry point)
exec gunicorn wsgi:app \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

