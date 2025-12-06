"""
REST API endpoints for Quiz Application
"""
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import re
import time
from app.models import (
    create_source, get_all_sources, get_source_by_id, delete_source,
    create_topic, get_topics_by_source, get_topic_by_id, update_topic,
    create_question, get_questions_by_topic, get_question_by_id,
    create_quiz, get_all_quizzes, get_quiz_by_id, get_quiz_with_questions, delete_quiz,
    create_quiz_attempt, get_quiz_attempt_by_id, get_quiz_attempt_with_details,
    get_quiz_attempts_by_quiz
)
from app.extractors import extract_from_source
from app.openai_service import openai_service

api_bp = Blueprint('api', __name__)

def _get_unique_topic_title(base_title: str, existing_topics: list) -> str:
    """
    Generate a unique topic title by appending iteration numbers.
    
    Examples:
    - First topic: "Introduction to Python" -> "Introduction to Python"
    - Second topic: "Introduction to Python" -> "Introduction to Python 1"
    - Third topic: "Introduction to Python" -> "Introduction to Python 2"
    
    If a topic already has a number suffix, it will be considered when finding the next number.
    """
    if not existing_topics:
        return base_title
    
    # Pattern to match titles with number suffix: "Title 1", "Title 2", etc.
    # Matches: "Title 1", "Title 2", "Title 10", etc.
    pattern = re.compile(r'^(.+?)\s+(\d+)$')
    
    # Find all existing titles that match the base title (with or without numbers)
    matching_titles = []
    base_title_lower = base_title.lower().strip()
    
    for topic in existing_topics:
        existing_title = topic.get('title', '').strip()
        existing_title_lower = existing_title.lower()
        
        # Check if it's an exact match (first iteration)
        if existing_title_lower == base_title_lower:
            matching_titles.append(0)  # 0 means no number suffix
        else:
            # Check if it matches the pattern with a number suffix
            match = pattern.match(existing_title)
            if match:
                title_base = match.group(1).strip().lower()
                number = int(match.group(2))
                
                # If the base matches, record this number
                if title_base == base_title_lower:
                    matching_titles.append(number)
    
    # If no matches found, return the base title as-is
    if not matching_titles:
        return base_title
    
    # Find the highest number used
    max_number = max(matching_titles)
    
    # If 0 is in the list, it means the base title exists, so start numbering at 1
    # Otherwise, increment the max number
    if 0 in matching_titles:
        next_number = 1
    else:
        next_number = max_number + 1
    
    return f"{base_title} {next_number}"

# File upload configuration
# Use system temp directory for uploads (works in all environments)
import tempfile
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(tempfile.gettempdir(), 'quiz_app_uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# Source Endpoints
# ============================================================================

@api_bp.route('/sources', methods=['POST'])
def submit_source():
    """Submit a source (URL or file) and extract content"""
    try:
        # Handle both form data and JSON
        source_type = None
        url = None
        
        # Try to get from form data first (multipart/form-data)
        if request.form:
            source_type = request.form.get('type')
            url = request.form.get('url')
        
        # If not in form, try JSON
        if not source_type and request.is_json:
            data = request.get_json() or {}
            source_type = data.get('type')
            url = data.get('url')
        
        # Also check args (query parameters) as fallback
        if not source_type:
            source_type = request.args.get('type')
            url = request.args.get('url')
        
        if not source_type:
            # Return helpful error with debug info
            debug_info = {
                'content_type': request.content_type,
                'method': request.method,
                'has_form': bool(request.form),
                'form_keys': list(request.form.keys()) if request.form else [],
                'is_json': request.is_json,
                'has_args': bool(request.args),
                'args_keys': list(request.args.keys()) if request.args else []
            }
            return jsonify({
                'success': False,
                'error': 'Source type is required (url, pdf, word, image)',
                'debug': debug_info
            }), 400
        
        extracted_data = None
        
        if source_type == 'url':
            if not url:
                return jsonify({'success': False, 'error': 'URL is required'}), 400
            
            # Clean and validate URL
            url = url.strip()
            if not url:
                return jsonify({'success': False, 'error': 'URL cannot be empty'}), 400
            
            # For URLs, we'll store the URL directly
            # Content will be extracted when generating questions
            from urllib.parse import urlparse
            parsed = urlparse(url)
            title = parsed.netloc or url
            
            extracted_data = {
                'title': title,
                'content': url,  # Store URL as content - will be extracted when generating questions
                'metadata': {'url': url, 'is_url': True}
            }
        
        elif source_type in ['pdf', 'word', 'image']:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'File is required'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400
            
            # Save file temporarily
            original_filename = file.filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            try:
                # Extract content
                file_type = 'pdf' if filename.endswith('.pdf') else 'word' if filename.endswith(('.doc', '.docx')) else 'image'
                extracted_data = extract_from_source(file_type, file_path)
                
                # Store original filename in metadata
                if 'metadata' not in extracted_data:
                    extracted_data['metadata'] = {}
                extracted_data['metadata']['original_filename'] = original_filename
            finally:
                # Delete file after extraction
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            return jsonify({'success': False, 'error': 'Invalid source type'}), 400
        
        # Create source
        try:
            source = create_source(
                source_type=source_type,
                title=extracted_data['title'],
                content=extracted_data['content'],
                metadata=extracted_data.get('metadata', {})
            )
        except KeyError as e:
            return jsonify({
                'success': False,
                'error': f'Storage error: Missing key {str(e)}. Data structure may be corrupted.'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to create source: {str(e)}'
            }), 500
        
        return jsonify({
            'success': True,
            'data': source
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except KeyError as e:
        return jsonify({
            'success': False,
            'error': f'Data structure error: {str(e)}. Please check storage file.'
        }), 500
    except Exception as e:
        import traceback
        error_details = str(e)
        # Don't expose full traceback in production, but helpful for debugging
        return jsonify({
            'success': False,
            'error': f'Internal error: {error_details}'
        }), 500

@api_bp.route('/sources', methods=['GET'])
def get_sources():
    """Get all sources"""
    sources = get_all_sources()
    return jsonify({
        'success': True,
        'data': sources,
        'count': len(sources)
    }), 200

@api_bp.route('/sources/<int:source_id>', methods=['GET'])
def get_source(source_id):
    """Get source by ID"""
    source = get_source_by_id(source_id)
    if source:
        return jsonify({'success': True, 'data': source}), 200
    return jsonify({'success': False, 'error': 'Source not found'}), 404

@api_bp.route('/sources/<int:source_id>', methods=['DELETE'])
def delete_source_endpoint(source_id):
    """Delete a source"""
    if delete_source(source_id):
        return jsonify({'success': True, 'message': 'Source deleted'}), 200
    return jsonify({'success': False, 'error': 'Source not found'}), 404

# ============================================================================
# Topic & Question Generation Endpoints
# ============================================================================

@api_bp.route('/sources/<int:source_id>/generate-topic', methods=['POST'])
def generate_topic_and_questions(source_id):
    """Generate a topic and 5 questions from a source"""
    source = get_source_by_id(source_id)
    if not source:
        return jsonify({'success': False, 'error': 'Source not found'}), 404
    
    data = request.get_json() or {}
    # Allow user to override AI-generated topic name, but generate by default
    user_provided_title = data.get('title')
    user_provided_description = data.get('description', '')
    
    try:
        # Check if this is a URL source (stored as URL, not extracted content)
        is_url = source.get('metadata', {}).get('is_url', False) or source.get('type') == 'url'
        
        # For URLs, we need to extract content first since OpenAI can't fetch URLs directly
        content_to_use = None
        if is_url:
            url = source['content']  # This is the URL
            try:
                # Try to extract content from URL
                from app.extractors import extract_from_source
                extracted = extract_from_source('url', url)
                content_to_use = extracted['content']
                
                # Check if we got meaningful content
                if not content_to_use or len(content_to_use.strip()) < 100:
                    return jsonify({
                        'success': False,
                        'error': f'Extracted content from URL is too short ({len(content_to_use) if content_to_use else 0} chars). The page might require JavaScript to render content. Try: 1) Using a different URL, 2) Copying the page content manually, or 3) Using a PDF/Word document instead.'
                    }), 400
            except Exception as e:
                # If extraction fails, return helpful error
                return jsonify({
                    'success': False,
                    'error': f'Failed to extract content from URL: {str(e)}. OpenAI cannot fetch URLs directly. Please try: 1) A different URL, 2) Copying the content manually, or 3) Using a PDF/Word document.'
                }), 400
        else:
            # For non-URL sources, use the stored content
            content_to_use = source['content']
        
        # Generate topic name and description using AI (unless user provided one)
        if user_provided_title:
            topic_title = user_provided_title
            topic_description = user_provided_description
        else:
            # Use AI to generate topic name and description
            topic_info = openai_service.generate_topic_name(content_to_use)
            topic_title = topic_info['title']
            topic_description = topic_info['description'] or user_provided_description
        
        # Check for existing topics with the same base title and add iteration number
        existing_topics = get_topics_by_source(source_id)
        topic_title = _get_unique_topic_title(topic_title, existing_topics)
        
        # Add delay between API calls to avoid hitting rate limits
        # This helps stay within OpenAI's tokens-per-minute limits
        # Increased to 3 seconds to accommodate smarter content selection (more tokens but better quality)
        time.sleep(3)  # 3 second delay between topic and question generation
        
        # Generate questions using OpenAI with the extracted/stored content
        questions_data = openai_service.generate_questions(
            content_to_use, 
            num_questions=5,
            is_url=False  # Always False since we have content now
        )
        
        # Create topic
        topic = create_topic(
            source_id=source_id,
            title=topic_title,
            description=topic_description
        )
        
        # Create questions
        created_questions = []
        for q_data in questions_data:
            question = create_question(
                topic_id=topic['id'],
                question_text=q_data['question_text'],
                answers=q_data['answers']
            )
            created_questions.append(question)
        
        # Add questions to topic
        topic['questions'] = created_questions
        
        return jsonify({
            'success': True,
            'data': topic
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to generate questions: {str(e)}'}), 500

@api_bp.route('/sources/<int:source_id>/topics', methods=['GET'])
def get_source_topics(source_id):
    """Get all topics for a source"""
    topics = get_topics_by_source(source_id)
    # Add questions to each topic
    for topic in topics:
        topic['questions'] = get_questions_by_topic(topic['id'])
    
    return jsonify({
        'success': True,
        'data': topics,
        'count': len(topics)
    }), 200

@api_bp.route('/topics/<int:topic_id>', methods=['PUT'])
def update_topic_endpoint(topic_id):
    """Update a topic (title and/or description)"""
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description')
    
    topic = update_topic(topic_id, title=title, description=description)
    if topic:
        return jsonify({
            'success': True,
            'data': topic
        }), 200
    return jsonify({'success': False, 'error': 'Topic not found'}), 404

# ============================================================================
# Quiz Endpoints
# ============================================================================

@api_bp.route('/quizzes', methods=['POST'])
def create_quiz_endpoint():
    """Create a new quiz"""
    data = request.get_json() or {}
    
    title = data.get('title')
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'}), 400
    
    question_ids = data.get('question_ids', [])
    if not question_ids:
        return jsonify({'success': False, 'error': 'At least one question is required'}), 400
    
    quiz = create_quiz(
        title=title,
        description=data.get('description'),
        question_ids=question_ids
    )
    
    return jsonify({
        'success': True,
        'data': quiz
    }), 201

@api_bp.route('/quizzes', methods=['GET'])
def get_quizzes():
    """Get all quizzes"""
    quizzes = get_all_quizzes()
    return jsonify({
        'success': True,
        'data': quizzes,
        'count': len(quizzes)
    }), 200

@api_bp.route('/quizzes/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get quiz with questions"""
    quiz = get_quiz_with_questions(quiz_id)
    if quiz:
        return jsonify({'success': True, 'data': quiz}), 200
    return jsonify({'success': False, 'error': 'Quiz not found'}), 404

@api_bp.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_quiz_endpoint(quiz_id):
    """Delete a quiz"""
    if delete_quiz(quiz_id):
        return jsonify({'success': True, 'message': 'Quiz deleted'}), 200
    return jsonify({'success': False, 'error': 'Quiz not found'}), 404

# ============================================================================
# Quiz Taking Endpoints
# ============================================================================

@api_bp.route('/quizzes/<int:quiz_id>/take', methods=['GET'])
def get_quiz_for_taking(quiz_id):
    """Get quiz for taking (without correct answers marked)"""
    quiz = get_quiz_with_questions(quiz_id)
    if not quiz:
        return jsonify({'success': False, 'error': 'Quiz not found'}), 404
    
    # Remove is_correct from answers for quiz taking
    for question in quiz.get('questions', []):
        for answer in question.get('answers', []):
            answer.pop('is_correct', None)
    
    return jsonify({'success': True, 'data': quiz}), 200

@api_bp.route('/quizzes/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    """Submit quiz answers and calculate score"""
    data = request.get_json() or {}
    selected_answers = data.get('selected_answers', {})
    
    # Convert string keys to int
    selected_answers = {int(k): v for k, v in selected_answers.items()}
    
    try:
        attempt = create_quiz_attempt(quiz_id, selected_answers)
        if not attempt:
            return jsonify({'success': False, 'error': 'Quiz not found'}), 404
        
        # Get detailed attempt with answer correctness
        detailed_attempt = get_quiz_attempt_with_details(attempt['id'])
        
        return jsonify({
            'success': True,
            'data': detailed_attempt
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to submit quiz: {str(e)}'}), 500

@api_bp.route('/quizzes/<int:quiz_id>/attempts', methods=['GET'])
def get_quiz_attempts(quiz_id):
    """Get all attempts for a quiz"""
    attempts = get_quiz_attempts_by_quiz(quiz_id)
    return jsonify({
        'success': True,
        'data': attempts,
        'count': len(attempts)
    }), 200

@api_bp.route('/quiz-attempts/<int:attempt_id>', methods=['GET'])
def get_quiz_attempt(attempt_id):
    """Get quiz attempt with details"""
    attempt = get_quiz_attempt_with_details(attempt_id)
    if attempt:
        return jsonify({'success': True, 'data': attempt}), 200
    return jsonify({'success': False, 'error': 'Attempt not found'}), 404

# ============================================================================
# Error Handlers
# ============================================================================

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
