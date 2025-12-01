"""
WSGI entry point for production servers (gunicorn, uwsgi, etc.)
This file is used by gunicorn to find the Flask app instance
"""
import os
from app import create_app

# Determine config based on environment
config_name = os.environ.get('FLASK_ENV', 'production')
if config_name == 'production':
    config_name = 'production'
else:
    config_name = 'development'

# Create app instance - this is what gunicorn will use
app = create_app(config_name)

if __name__ == '__main__':
    # This allows running: python wsgi.py (for testing)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

