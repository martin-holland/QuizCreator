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
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (system dependencies already installed above)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create upload directory (using temp directory for compatibility)
RUN mkdir -p /tmp/quiz_app_uploads

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2"]

