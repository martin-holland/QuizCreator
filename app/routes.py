"""
Main routes for Quiz Application UI
"""
from flask import Blueprint, render_template

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
