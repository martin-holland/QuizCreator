FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# Tesseract OCR for image text extraction
# Chromium dependencies for Playwright (comprehensive list)
RUN apt-get update && apt-get install -y \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # Chromium/Playwright core dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libpangocairo-1.0-0 \
    # Additional X11 and system libraries
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxext6 \
    libxi6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    # System libraries
    libc6 \
    libcairo2 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libglib2.0-0 \
    libstdc++6 \
    # Utilities
    ca-certificates \
    libappindicator3-1 \
    lsb-release \
    wget \
    xdg-utils \
    # Fonts
    fonts-unifont \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Install Playwright system dependencies
# This ensures all required libraries are present for Chromium to run
RUN playwright install-deps chromium || true
# Note: We use || true because some optional packages might fail, but critical ones should install

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

