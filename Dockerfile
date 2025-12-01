FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# Tesseract OCR for image text extraction
# Basic Chromium dependencies (playwright install-deps will handle the rest)
RUN apt-get update && apt-get install -y \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # Basic Chromium/Playwright dependencies (minimal set)
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # Fonts
    fonts-unifont \
    fonts-liberation \
    fonts-noto-color-emoji \
    # Utilities
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Install Playwright system dependencies
# This installs all required Chromium dependencies for the current Debian version
# We allow it to continue even if some optional packages fail
RUN set +e && playwright install-deps chromium; exit_code=$?; \
    if [ $exit_code -ne 0 ]; then \
    echo "Warning: Some Playwright dependencies may have failed, but continuing..."; \
    fi; \
    set -e

# Copy application code
COPY . .

# Create upload directory (using temp directory for compatibility)
RUN mkdir -p /tmp/quiz_app_uploads

# Expose port (Render sets PORT env var automatically)
EXPOSE 5000

# Copy and make startup script executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Use startup script to handle PORT (Render sets $PORT automatically)
# Render handles $PORT correctly with shell expansion
CMD ["/bin/bash", "/app/start.sh"]

