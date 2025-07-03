from flask import Blueprint, render_template, jsonify

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Homepage of SecureDeal"""
    return render_template('index.html')

@bp.route('/dashboard')
def dashboard():
    """Dashboard page - authentication handled by JavaScript"""
    return render_template('dashboard.html')

@bp.route('/profile')
def profile():
    """User profile page - authentication handled by JavaScript"""
    return render_template('profile.html')

@bp.route('/notifications')
def notifications():
    """Notifications page - authentication handled by JavaScript"""
    return render_template('notifications.html')

@bp.route('/health')
def health():
    """Health check endpoint for Docker and monitoring"""
    try:
        # Test database connection
        from app import db
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'service': 'SecureDeal',
            'version': '1.0.0',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }), 503
