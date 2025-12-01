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

@main_bp.route('/diagnostics')
def diagnostics():
    """Diagnostic endpoint - checks all system dependencies"""
    diagnostics_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'dependencies': {}
    }
    
    # Check Tesseract OCR
    try:
        from app.extractors import ImageExtractor
        tesseract_installed = ImageExtractor._check_tesseract_installed()
        diagnostics_info['dependencies']['tesseract'] = {
            'installed': tesseract_installed,
            'status': '✅ Installed' if tesseract_installed else '❌ Not installed',
            'purpose': 'Image text extraction (OCR)'
        }
        if tesseract_installed:
            try:
                import pytesseract
                version = pytesseract.get_tesseract_version()
                # Convert version object to string for JSON serialization
                diagnostics_info['dependencies']['tesseract']['version'] = str(version)
            except Exception as e:
                diagnostics_info['dependencies']['tesseract']['version_error'] = str(e)
    except Exception as e:
        diagnostics_info['dependencies']['tesseract'] = {
            'installed': False,
            'status': f'❌ Error checking: {str(e)}',
            'purpose': 'Image text extraction (OCR)'
        }
    
    # Check Playwright
    try:
        from playwright.sync_api import sync_playwright
        diagnostics_info['dependencies']['playwright'] = {
            'python_package': '✅ Installed',
            'status': 'Checking browser...',
            'purpose': 'JavaScript-rendered URL extraction'
        }
        
        # Try to launch browser (this checks if Chromium is installed)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, timeout=10000)
                browser.close()
            diagnostics_info['dependencies']['playwright']['browser'] = '✅ Chromium installed and working'
            diagnostics_info['dependencies']['playwright']['status'] = '✅ Fully operational'
        except Exception as browser_error:
            diagnostics_info['dependencies']['playwright']['browser'] = f'❌ Error: {str(browser_error)[:200]}'
            diagnostics_info['dependencies']['playwright']['status'] = '❌ Browser not working'
    except ImportError:
        diagnostics_info['dependencies']['playwright'] = {
            'python_package': '❌ Not installed',
            'browser': '❌ Cannot check (package missing)',
            'status': '❌ Not installed',
            'purpose': 'JavaScript-rendered URL extraction'
        }
    except Exception as e:
        diagnostics_info['dependencies']['playwright'] = {
            'python_package': '✅ Installed',
            'browser': f'❌ Error: {str(e)[:200]}',
            'status': '❌ Error checking',
            'purpose': 'JavaScript-rendered URL extraction'
        }
    
    # Check Trafilatura
    try:
        import trafilatura
        diagnostics_info['dependencies']['trafilatura'] = {
            'installed': True,
            'status': '✅ Installed',
            'purpose': 'Fallback URL content extraction'
        }
    except ImportError:
        diagnostics_info['dependencies']['trafilatura'] = {
            'installed': False,
            'status': '❌ Not installed',
            'purpose': 'Fallback URL content extraction'
        }
    
    # Check other dependencies (using correct import names)
    dependencies_to_check = {
        'beautifulsoup4': ('bs4', 'HTML parsing'),
        'PyPDF2': ('PyPDF2', 'PDF extraction'),
        'python-docx': ('docx', 'Word document extraction'),
        'Pillow': ('PIL', 'Image processing')
    }
    
    for dep_name, (import_name, purpose) in dependencies_to_check.items():
        try:
            __import__(import_name)
            diagnostics_info['dependencies'][dep_name] = {
                'installed': True,
                'status': '✅ Installed',
                'purpose': purpose
            }
        except ImportError:
            diagnostics_info['dependencies'][dep_name] = {
                'installed': False,
                'status': '❌ Not installed',
                'purpose': purpose
            }
    
    # Overall status
    critical_deps = ['playwright', 'tesseract']
    all_critical_ok = all(
        diagnostics_info['dependencies'].get(dep, {}).get('status', '').startswith('✅')
        for dep in critical_deps
    )
    
    diagnostics_info['overall_status'] = '✅ All critical dependencies OK' if all_critical_ok else '⚠️ Some dependencies missing'
    
    return jsonify(diagnostics_info), 200
