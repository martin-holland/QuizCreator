# Quiz Application

A Flask-based quiz application that uses AI to generate questions from various sources (URLs, PDFs, Word documents, images).

## Features

- **Source Submission**: Submit URLs (including JavaScript-rendered pages), PDFs, Word documents, or images
- **AI Question Generation**: Automatically generates 5 multiple-choice questions per topic using OpenAI GPT-4o-mini
- **Quiz Creation**: Create quizzes from generated questions
- **Interactive Quiz Taking**: Take quizzes with instant scoring
- **Results Review**: View detailed results showing correct/incorrect answers

## Scoring Rules

- Each question has 6 possible answers
- 4 correct answers: +0.25 points each
- 2 incorrect answers: -0.5 points each
- Minimum score per question: 0 (no negative scores)

## Setup

### 1. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Important Notes**:

1. **Tesseract OCR (Required for Image Text Extraction)**

   To extract text from images, you need to install Tesseract OCR separately:

   - **macOS** (using Homebrew):

     ```bash
     brew install tesseract
     ```

     If you don't have Homebrew, install it from [brew.sh](https://brew.sh)

   - **Linux** (Ubuntu/Debian):

     ```bash
     sudo apt-get update
     sudo apt-get install tesseract-ocr
     ```

     For other distributions, see [Tesseract installation guide](https://github.com/tesseract-ocr/tesseract)

   - **Windows**:
     1. Download the installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
     2. Run the installer
     3. Add Tesseract to your PATH, or set it in code:
        ```python
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        ```

   **Verify installation:**

   ```bash
   tesseract --version
   ```

2. **Playwright Browser (Required for JavaScript-rendered URLs)**

   After installing Playwright, you need to install the browser:

   ```bash
   playwright install chromium
   ```

### 2. Configure Environment Variables

The app uses environment variables for configuration. The easiest way is to use a `.env` file:

1. **Copy the example file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your values:**

   ```bash
   # Generate a secret key
   python -c "import secrets; print(secrets.token_hex(32))"

   # Then edit .env and add:
   SECRET_KEY=your-generated-key-here
   OPENAI_API_KEY=your-openai-key-here
   ```

3. **Database Configuration:**
   - Leave `DATABASE_URL` empty to use SQLite (default for local development)
   - Or set it to a PostgreSQL connection string if you want to use PostgreSQL locally
   - Format: `postgresql://user:password@localhost:5432/dbname`

**Note:** The `.env` file is already in `.gitignore` and won't be committed to version control.

**Alternative:** You can also set environment variables directly:

```bash
export OPENAI_API_KEY=your_key_here
export SECRET_KEY=your_secret_key_here
```

### 3. Run the Application

**Option 1: Direct Python (Recommended)**

```bash
source venv/bin/activate
python3 app.py
# OR use the full path:
./venv/bin/python app.py
```

**Option 2: Using Flask CLI with explicit Python**

```bash
source venv/bin/activate
python3 -m flask run --port 5001
# OR use the full path:
./venv/bin/python -m flask run --port 5001
```

**Option 3: Use the helper script**

```bash
./run_flask.sh
```

The app will run on `http://localhost:5001`

**Important:** If you have a shell alias for `python` pointing to system Python, use `python3` instead. The venv Python has all required packages installed.

## Deployment

### Google Cloud Platform (GCP) Deployment

The application is ready to deploy to Google Cloud Build and Cloud Run with minimal configuration.

**Quick Start:**

1. **Set up secrets** (one-time setup):

   ```bash
   ./setup-gcp-secrets.sh
   ```

2. **Build and deploy**:

   ```bash
   # Build container
   gcloud builds submit --config cloudbuild.yaml

   # Deploy to Cloud Run
   gcloud run deploy quiz-app \
     --image gcr.io/$(gcloud config get-value project)/quiz-app:latest \
     --region us-central1 \
     --set-secrets SECRET_KEY=secret-key:latest,OPENAI_API_KEY=openai-api-key:latest
   ```

**Features:**

- ✅ SQLite database runs in the same container (no external database needed)
- ✅ All dependencies (Tesseract, Playwright) included in container
- ✅ Secrets managed via Google Secret Manager
- ✅ Automatic scaling with Cloud Run
- ✅ Zero-downtime deployments

**For detailed instructions, see [GCP_DEPLOYMENT.md](GCP_DEPLOYMENT.md)**

## Usage

### 1. Submit a Source

- Go to **Sources** page
- Choose source type (URL, PDF, Word, Image)
- Submit URL or upload file
- Content will be extracted automatically

### 2. Generate Questions

- Click **"Generate Topic & Questions"** on a source
- Enter a topic title
- AI will generate 5 questions with 6 answers each

### 3. Create a Quiz

- Go to **Quizzes** page
- Select questions to include
- Enter quiz title and description
- Create quiz

### 4. Take a Quiz

- Click **"Take Quiz"** on any quiz
- Select answers (multiple selection allowed)
- Submit to see results

### 5. View Results

- See your score and percentage
- Review which answers were correct/incorrect
- Retake quiz if desired

## Project Structure

```
intern-project-test/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── api.py               # REST API endpoints
│   ├── routes.py            # Web page routes
│   ├── models.py            # Data model functions
│   ├── database.py          # SQLAlchemy database models
│   ├── extractors.py        # Document extraction
│   └── openai_service.py    # OpenAI AI integration
├── templates/               # Jinja2 templates
├── static/                  # CSS and JavaScript
├── quiz_app.db             # SQLite database (auto-created)
├── uploads/                 # Temporary file storage (auto-created)
└── requirements.txt         # Python dependencies
```

## Data Storage

The app uses **SQLite database** (`quiz_app.db`) - SQLite is built into Python, no installation needed!

**Benefits:**

- ✅ Built into Python (no setup required)
- ✅ File-based (easy to backup)
- ✅ Easy to migrate to PostgreSQL/MySQL later (just change connection string)
- ✅ Better performance than JSON
- ✅ ACID transactions
- ✅ Relationships and foreign keys

**Migration:** If you have existing JSON data, run `python migrate_to_sqlite.py` to migrate it.

## API Endpoints

### Sources

- `POST /api/v1/sources` - Submit source
- `GET /api/v1/sources` - List all sources
- `GET /api/v1/sources/{id}` - Get source details
- `DELETE /api/v1/sources/{id}` - Delete source

### Topics & Questions

- `POST /api/v1/sources/{id}/generate-topic` - Generate topic with 5 questions
- `GET /api/v1/sources/{id}/topics` - Get all topics for a source

### Quizzes

- `POST /api/v1/quizzes` - Create quiz
- `GET /api/v1/quizzes` - List all quizzes
- `GET /api/v1/quizzes/{id}` - Get quiz details
- `GET /api/v1/quizzes/{id}/take` - Get quiz for taking
- `POST /api/v1/quizzes/{id}/submit` - Submit quiz answers
- `GET /api/v1/quizzes/{id}/attempts` - Get quiz attempts

### Quiz Attempts

- `GET /api/v1/quiz-attempts/{id}` - Get attempt details

## Technologies Used

- **Flask** - Web framework
- **OpenAI GPT-4o-mini** - Question generation
- **BeautifulSoup** - HTML parsing
- **PyPDF2** - PDF extraction
- **python-docx** - Word document extraction
- **pytesseract** - OCR for images
- **Playwright** - Browser automation for JavaScript-rendered pages
- **Trafilatura** - Advanced web content extraction
- **SQLite** - Built-in Python database (no installation needed!)
- **SQLAlchemy** - ORM for database operations

## Future Enhancements

- Database migration (MongoDB/Supabase/Firebase)
- User authentication
- Question editing
- Export quizzes
- Analytics and statistics
