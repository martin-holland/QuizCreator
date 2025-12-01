FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# Tesseract OCR for image text extraction
# Chromium dependencies for Playwright
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
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
    fonts-unifont \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Note: We skip 'playwright install-deps' because:
# 1. We've already installed the critical Chromium dependencies manually above
# 2. Some font packages (ttf-ubuntu-font-family, ttf-unifont) are not available
#    in all Debian versions, but we've installed fonts-unifont as a replacement
# 3. Playwright will work fine with the browser and manually installed dependencies

# Copy application code
COPY . .

# Create upload directory (using temp directory for compatibility)
RUN mkdir -p /tmp/quiz_app_uploads

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2"]

