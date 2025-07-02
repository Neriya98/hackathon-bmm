from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.models.contract import Contract
from app.models.invitation import Invitation
from datetime import datetime

bp = Blueprint('main', __name__)


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
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@bp.route('/')
def index():
    """Page d'accueil de SecureDeal"""
    return render_template('index.html')


@bp.route('/dashboard')
def dashboard():
    """Dashboard page - authentication handled by JavaScript"""
    return render_template('dashboard.html')


@bp.route('/contracts')
@jwt_required()
def contracts():
    """Page de gestion des contrats"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('contracts/list.html', user=user)


@bp.route('/contracts/create')
@jwt_required()
def create_contract():
    """Page de création de contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.email_verified:
        return render_template('auth/verify_email_required.html', user=user)
    
    return render_template('contracts/create.html', user=user)


@bp.route('/contracts/<contract_id>')
@jwt_required()
def contract_details(contract_id):
    """Page de détails d'un contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return render_template('errors/404.html'), 404
    
    # Vérifier l'accès
    user_contracts = Contract.get_user_contracts(user.id).all()
    if contract not in user_contracts:
        return render_template('errors/403.html'), 403
    
    return render_template('contracts/details.html', user=user, contract=contract)


@bp.route('/invitations/<token>')
def accept_invitation(token):
    """Page d'acceptation d'invitation"""
    
    invitation = Invitation.find_by_token(token)
    
    if not invitation:
        return render_template('invitations/invalid.html'), 404
    
    if invitation.is_expired():
        return render_template('invitations/expired.html', invitation=invitation), 410
    
    if invitation.status != 'sent':
        return render_template('invitations/already_responded.html', invitation=invitation)
    
    # Vérifier si l'utilisateur est connecté
    user = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user = User.find_by_public_id(user_id)
    except:
        pass
    
    return render_template('invitations/accept.html', 
                         invitation=invitation, 
                         user=user)


@bp.route('/auth/login')
def login():
    """Login page"""
    return render_template('auth/login.html')


@bp.route('/auth/register')
def register():
    """Registration page"""
    return render_template('auth/register.html')


@bp.route('/auth/logout')
def logout():
    """Logout page"""
    return redirect(url_for('main.index'))


@bp.route('/auth/verify-email')
def verify_email():
    """Page de vérification email"""
    token = request.args.get('token')
    
    if not token:
        return render_template('auth/verify_email.html')
    
    user = User.verify_email_token(token)
    
    if user:
        return render_template('auth/email_verified.html', user=user)
    else:
        return render_template('auth/invalid_token.html'), 400


@bp.route('/auth/forgot-password')
def forgot_password():
    """Page de mot de passe oublié"""
    return render_template('auth/forgot_password.html')


@bp.route('/auth/reset-password')
def reset_password():
    """Page de réinitialisation de mot de passe"""
    token = request.args.get('token')
    
    if not token:
        return redirect(url_for('main.forgot_password'))
    
    # Vérifier la validité du token
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        return render_template('auth/invalid_token.html'), 400
    
    return render_template('auth/reset_password.html', token=token)


@bp.route('/profile')
@jwt_required()
def profile():
    """Page de profil utilisateur"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('profile.html', user=user)


@bp.route('/docs')
def documentation():
    """Documentation API"""
    return render_template('docs.html')


@bp.route('/about')
def about():
    """Page à propos"""
    return render_template('about.html')


@bp.route('/privacy')
def privacy():
    """Politique de confidentialité"""
    return render_template('legal/privacy.html')


@bp.route('/terms')
def terms():
    """Conditions d'utilisation"""
    return render_template('legal/terms.html')


# API pour les données dynamiques du frontend
@bp.route('/api/health')
def health_check():
    """Point de contrôle de santé de l'application"""
    
    try:
        # Vérifier la base de données
        User.query.first()
        
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': current_app.config.get('STARTUP_TIME', 'unknown')
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Database connection failed'
        }), 503


# Gestion d'erreurs
@bp.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404


@bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


@bp.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403
