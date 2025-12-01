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
# Try playwright install-deps first (it knows what's needed for the current OS)
# If it fails, install common Chromium dependencies manually
RUN apt-get update && \
    (playwright install-deps chromium 2>&1 || \
    (echo "playwright install-deps failed, installing dependencies manually..." && \
    apt-get install -y \
    libxshmfence1 \
    libxss1 \
    libxi6 \
    libxtst6 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    || true)) && \
    rm -rf /var/lib/apt/lists/*

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

