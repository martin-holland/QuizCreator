"""
Main routes for Quiz Application UI
"""
from flask import Blueprint, render_template, jsonify
from datetime import datetime
from app.database import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html', title='Quiz App')

@main_bp.route('/sources')
def sources_page():
    """Sources management page"""
    return render_template('sources.html', title='Sources')

@main_bp.route('/quizzes')
def quizzes_page():
    """Quizzes list page"""
    return render_template('quizzes.html', title='Quizzes')

@main_bp.route('/quizzes/<int:quiz_id>/take')
def take_quiz_page(quiz_id):
    """Take quiz page"""
    return render_template('take_quiz.html', quiz_id=quiz_id, title='Take Quiz')

@main_bp.route('/quiz-attempts/<int:attempt_id>')
def quiz_results_page(attempt_id):
    """Quiz results page"""
    return render_template('quiz_results.html', attempt_id=attempt_id, title='Quiz Results')

@main_bp.route('/health')
def health_check():
    """Health check endpoint - verifies database connection"""
    try:
        from sqlalchemy import text
        # Try to execute a simple database query
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        # Get database URI info (without exposing password)
        db_uri = db.engine.url
        db_info = {
            'dialect': db_uri.drivername,
            'database': db_uri.database,
            'host': db_uri.host,
            'port': db_uri.port,
            'username': db_uri.username
        }
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'database_info': db_info,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
