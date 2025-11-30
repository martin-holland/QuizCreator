"""
Main application entry point - similar to React's index.js or main.tsx
This creates and runs the Flask application
"""
import os
from app import create_app

# Determine config based on environment
# In production, set FLASK_ENV=production
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    config_name = 'production'
else:
    config_name = 'development'

# Create app instance using factory pattern
# Similar to: ReactDOM.render(<App />, document.getElementById('root'))
app = create_app(config_name)

if __name__ == '__main__':
    # Run the app - similar to starting a development server
    # Use port from environment variable or default to 5001 (5000 often used by macOS AirPlay)
    port = int(os.environ.get('PORT', 5001))
    # Only enable debug in development
    debug_mode = (config_name != 'production')
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

