"""
Configuration file - similar to React's .env or config files
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This allows local development with .env file, while production uses actual env vars
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = True
    
    # API Configuration
    API_PREFIX = '/api/v1'
    
    # OpenAI Configuration
    # Load from environment variable (from .env file locally, or platform env vars in production)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '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')
    
    # Database Configuration
    # Uses DATABASE_URL if provided (PostgreSQL/MySQL), otherwise SQLite for local development
    # For local: Leave DATABASE_URL empty in .env to use SQLite (no setup needed)
    # For production: Set DATABASE_URL environment variable (e.g., from Railway/Render)
    # Example PostgreSQL URL: postgresql://user:password@localhost:5432/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///quiz_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Static files and templates (Flask auto-discovers these)
    # Similar to React's public/ and src/ folders

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Override in production - require environment variables
    # These will be validated when the config is instantiated
    @property
    def OPENAI_API_KEY(self):
        key = os.environ.get('OPENAI_API_KEY')
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable is required in production")
        return key
    
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key or key == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set to a secure random value in production")
        return key

# Config dictionary - similar to environment-based config in React
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

