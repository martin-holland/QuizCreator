# Deployment Guide

This guide covers the best deployment options for your Flask Quiz Application, ranked by ease of use.

**✅ Deployment Status: READY**

All system dependencies are handled via Docker or platform-specific configurations. The application is fully compatible with cloud platforms.

## 🚀 Quick Comparison

| Platform                      | Ease       | Cost                | Best For                    |
| ----------------------------- | ---------- | ------------------- | --------------------------- |
| **Railway**                   | ⭐⭐⭐⭐⭐ | Free tier + usage   | Easiest, modern platform    |
| **Render**                    | ⭐⭐⭐⭐⭐ | Free tier available | Great free tier, simple     |
| **Fly.io**                    | ⭐⭐⭐⭐   | Free tier           | Global edge deployment      |
| **Heroku**                    | ⭐⭐⭐     | Paid only           | Legacy, but reliable        |
| **DigitalOcean App Platform** | ⭐⭐⭐⭐   | $5/month            | Simple, predictable pricing |
| **AWS/GCP/Azure**             | ⭐⭐       | Varies              | Enterprise, more complex    |

---

## 🏆 Recommended: Railway (Easiest)

**Why Railway?**

- ✅ Zero configuration needed
- ✅ Automatic deployments from GitHub
- ✅ Free tier with $5 credit/month
- ✅ Built-in PostgreSQL option
- ✅ Environment variables UI
- ✅ Automatic HTTPS

### Steps to Deploy on Railway:

1. **Prepare your code:**

   ```bash
   # Make sure all changes are committed
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Railway account:**

   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

3. **Deploy:**

   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-detects Flask!

4. **Set Environment Variables:**

   - In Railway dashboard, go to "Variables"
   - Add:
     ```
     OPENAI_API_KEY=your_key_here
     SECRET_KEY=generate-a-random-secret-key-here
     FLASK_ENV=production
     PORT=5000
     ```

5. **Optional: Add PostgreSQL (recommended for production):**

   - Click "New" → "Database" → "PostgreSQL"
   - Railway will provide `DATABASE_URL` automatically
   - Update `config.py` to use PostgreSQL (see below)

6. **Deploy!**
   - Railway will automatically build and deploy
   - Your app will be live at `your-app-name.railway.app`

---

## 🥈 Alternative: Render (Great Free Tier)

**Why Render?**

- ✅ Generous free tier
- ✅ Automatic HTTPS
- ✅ PostgreSQL included
- ✅ Simple configuration

### Steps to Deploy on Render:

1. **Create `render.yaml` in project root:**

   ```yaml
   services:
     - type: web
       name: quiz-app
       env: docker # Use Docker to install system dependencies
       dockerfilePath: ./Dockerfile
       envVars:
         - key: OPENAI_API_KEY
           sync: false
         - key: SECRET_KEY
           generateValue: true
         - key: FLASK_ENV
           value: production
   ```

   **Note:** Render requires Docker for system dependencies like Tesseract. See Docker section below.

2. **Create `Procfile` (alternative to render.yaml):**

   ```
   web: gunicorn app:app --bind 0.0.0.0:$PORT
   ```

3. **Update `requirements.txt` to include gunicorn:**

   ```
   gunicorn==21.2.0
   ```

4. **Deploy:**
   - Go to [render.com](https://render.com)
   - Connect GitHub
   - Create "New Web Service"
   - Select your repo
   - Render will auto-detect settings
   - Add environment variables in dashboard
   - Deploy!

---

## 📝 Environment Variables Setup

### Local Development (.env file)

The app now supports `.env` files for local development. A `.env.example` file is provided as a template.

1. **Copy the example file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**

   ```bash
   # Generate a secret key
   python -c "import secrets; print(secrets.token_hex(32))"

   # Then edit .env and add:
   SECRET_KEY=your-generated-key-here
   OPENAI_API_KEY=your-openai-key-here
   ```

3. **Database Configuration:**
   - Leave `DATABASE_URL` empty for SQLite (local development)
   - Or set it to a PostgreSQL connection string if you want to use PostgreSQL locally
   - Format: `postgresql://user:password@localhost:5432/dbname`

**Note:** The `.env` file is already in `.gitignore` and won't be committed to version control.

### Production Environment Variables

In production (Railway, Render, etc.), set these environment variables in the platform dashboard:

- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - A secure random string (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `DATABASE_URL` - Automatically provided by Railway/Render if you add PostgreSQL
- `FLASK_ENV=production` - Tells Flask to use production config

---

## 🔧 Required Changes for Production

### 1. Update `app.py` for Production

```python
# app.py
import os
from app import create_app

# Use production config in production
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    config_name = 'production'

app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Don't use debug=True in production!
    app.run(host='0.0.0.0', port=port, debug=(config_name != 'production'))
```

### 2. Update `config.py` for Production Database

```python
# config.py - Update ProductionConfig
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use PostgreSQL if DATABASE_URL is set, otherwise SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///quiz_app.db'
    # Remove hardcoded API key - use environment variable only
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
```

### 3. Add `gunicorn` to `requirements.txt`

```
gunicorn==21.2.0
```

### 4. Create `Procfile` (for Heroku/Render)

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 5. Create `.gitignore` (if not exists)

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.db
*.sqlite
uploads/
.DS_Store
.env
.venv
quiz_app.db
```

---

## 🗄️ Database Migration (SQLite → PostgreSQL)

If you want to use PostgreSQL (recommended for production):

### Option 1: Use Railway/Render PostgreSQL (Easiest)

Both platforms provide PostgreSQL automatically. Just:

1. Add PostgreSQL service
2. Use the provided `DATABASE_URL` environment variable
3. Your app will automatically use it!

### Option 2: Manual Migration Script

Create `migrate_to_postgres.py`:

```python
import os
import sqlite3
import psycopg2
from urllib.parse import urlparse

# SQLite connection
sqlite_conn = sqlite3.connect('quiz_app.db')
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL connection (from DATABASE_URL)
database_url = os.environ.get('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

pg_conn = psycopg2.connect(database_url)
pg_cursor = pg_conn.cursor()

# Migrate data (simplified - you'd need to adapt for your schema)
# ... migration logic here ...

pg_conn.commit()
pg_conn.close()
sqlite_conn.close()
```

---

## 🔒 Security Checklist

Before deploying:

- [ ] Remove hardcoded API keys from `config.py`
- [ ] Generate a strong `SECRET_KEY` (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set `DEBUG=False` in production
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (automatic on Railway/Render)
- [ ] Set up CORS properly for your domain
- [ ] Consider rate limiting for API endpoints
- [ ] Review file upload size limits

---

## 📦 Additional Dependencies for Production

Update `requirements.txt`:

```
Flask==3.1.2
flask-cors==5.0.0
Flask-SQLAlchemy==3.1.1
gunicorn==21.2.0  # Production WSGI server
requests==2.31.0
beautifulsoup4==4.12.0
PyPDF2==3.0.1
python-docx==1.1.0
pytesseract==0.3.10
Pillow>=10.0.0
playwright==1.40.0
trafilatura==1.6.3
psycopg2-binary==2.9.9  # For PostgreSQL (if using)
```

---

## 🐳 Docker Deployment (Recommended for Production)

**Docker is the most reliable way to ensure all system dependencies are available.**

A `Dockerfile` is already included in the project root. It:

- ✅ Installs Tesseract OCR for image text extraction
- ✅ Installs Playwright browsers for JavaScript-rendered URLs
- ✅ Sets up all Python dependencies
- ✅ Works on Railway, Render, Fly.io, AWS, GCP, Azure

**To use Docker on Railway:**

1. Railway will auto-detect the Dockerfile
2. No additional configuration needed
3. All system dependencies will be installed automatically

**To use Docker on Render:**

1. Set service type to "Docker" in Render dashboard
2. Render will use the Dockerfile automatically

**Why Docker?**

- ✅ Guarantees Tesseract OCR is available
- ✅ Ensures Playwright browsers work correctly
- ✅ Consistent environment across platforms
- ✅ No need to configure buildpacks or system packages manually

Create `.dockerignore`:

```
venv/
__pycache__/
*.db
*.pyc
.env
.git
```

Then deploy to:

- Railway (supports Docker)
- Fly.io (Docker-native)
- AWS ECS / Google Cloud Run / Azure Container Instances

---

## 🚨 Common Issues & Solutions

### Issue: Tesseract OCR not found

**Error:** `Tesseract OCR is not installed or not in PATH`

**Solutions:**

1. **Use Docker** (Recommended) - Dockerfile includes Tesseract
2. **Railway with Nixpacks** - `nixpacks.toml` includes Tesseract
3. **Manual installation** - Not recommended for cloud platforms

**Note:** Image OCR will gracefully fail with a helpful error message if Tesseract is not available. Other features (PDF, Word, URLs) will continue to work.

### Issue: Playwright browser not found

**Error:** `Playwright browser not found` or `Executable doesn't exist`

**Solution:**

- **Docker:** Already handled in Dockerfile
- **Railway/Render:** Add to build command: `playwright install chromium && playwright install-deps chromium`
- **Manual:** Run `playwright install chromium` in build step

### Issue: Port binding

**Error:** `Address already in use` or app won't start

**Solution:** Use `$PORT` environment variable (set by platform). The app already uses this.

### Issue: Database migrations

**Solution:** SQLAlchemy `db.create_all()` runs automatically, but for schema changes, consider Flask-Migrate

### Issue: Static files not loading

**Solution:** Ensure `static_folder` is set correctly in Flask app initialization (already configured)

### Issue: CORS errors

**Solution:** Update CORS origins in `app/__init__.py` to your production domain

### Issue: File uploads fail

**Solution:** The app now uses system temp directory (`/tmp` on Linux), which is available on all platforms. No action needed.

---

## 📊 Monitoring & Logs

### Railway

- Built-in logs in dashboard
- Metrics included

### Render

- Logs in dashboard
- Can set up external monitoring

### Recommended: Add Sentry for Error Tracking

```python
# In app/__init__.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if not app.config['DEBUG']:
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )
```

---

## 🎯 Quick Start: Railway (5 minutes)

1. Push code to GitHub
2. Sign up at railway.app
3. Connect GitHub repo
4. Add environment variables
5. Deploy!

**That's it!** Railway handles everything else.

---

## 💰 Cost Estimates

- **Railway:** Free tier ($5 credit/month), then ~$5-20/month
- **Render:** Free tier available, then ~$7-25/month
- **Fly.io:** Free tier, then ~$3-15/month
- **DigitalOcean:** $5/month minimum
- **Heroku:** $7/month minimum (no free tier)

---

## 📚 Additional Resources

- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)
- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Gunicorn Docs](https://gunicorn.org/)

---

## ✅ Pre-Deployment Checklist

- [ ] Code is committed and pushed to GitHub
- [ ] `requirements.txt` is up to date
- [ ] Environment variables are documented
- [ ] `SECRET_KEY` is generated and set
- [ ] `OPENAI_API_KEY` is set
- [ ] `DEBUG=False` in production config
- [ ] Database migration plan (if needed)
- [ ] CORS origins updated
- [ ] File upload limits reviewed
- [ ] Error handling tested

---

**Ready to deploy? Start with Railway - it's the easiest!** 🚀
