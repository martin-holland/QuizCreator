"""
Main Flask application factory - similar to React's index.js or App.js
This is where we initialize and configure the Flask app
"""
import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv
from config import config
from app.database import db

# Load environment variables from .env file if it exists
# This is done here as well to ensure env vars are loaded before config is accessed
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def create_app(config_name='default'):
    """
    Application factory pattern - similar to React's component composition
    This allows us to create multiple app instances (useful for testing)
    """
    # Get the base directory (project root)
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Initialize Flask with explicit paths for templates and static files
    # Similar to how React knows where src/ and public/ folders are
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static')
    )
    
    # Load configuration - similar to React's environment variables
    app.config.from_object(config[config_name])
    
    # Normalize database URL if needed (some platforms provide postgres:// but SQLAlchemy needs postgresql://)
    # Read fresh from environment to handle cases where DATABASE_URL is set after config class definition
    database_url = os.environ.get('DATABASE_URL') or app.config.get('SQLALCHEMY_DATABASE_URI')
    if database_url:
        if database_url.startswith('postgres://'):
            # SQLAlchemy requires postgresql://, not postgres://
            # Some platforms (like Heroku) provide postgres://, so we normalize it
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite if no DATABASE_URL is set
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_app.db'
    
    # Initialize database (SQLite - built into Python!)
    db.init_app(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Enable CORS for React frontend integration
    # Install: pip install flask-cors
    # This allows React (running on :3000) to call Flask API (on :5001)
    try:
        from flask_cors import CORS
        CORS(app, resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
    except ImportError:
        # CORS not installed - templates will still work, but React integration needs it
        pass
    
    # Register blueprints - similar to React Router
    from app.routes import main_bp
    from app.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix=app.config['API_PREFIX'])
    
    return app

