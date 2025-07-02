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
def contracts():
    """Contracts list page - temporarily simplified for frontend testing"""
    return render_template('contracts/list.html')


@bp.route('/contracts/create')
def create_contract():
    """Contract creation page - temporarily simplified for frontend testing"""
    return render_template('contracts/create.html')


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


# Mock API endpoints for frontend testing
@bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """Mock registration endpoint"""
    return jsonify({
        'message': 'User registered successfully',
        'user': {'email': 'test@example.com'},
        'token': 'mock-token-123'
    }), 201


@bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """Mock login endpoint"""
    return jsonify({
        'message': 'Login successful',
        'user': {'email': 'test@example.com'},
        'token': 'mock-token-123'
    }), 200


@bp.route('/api/send-invitation-email', methods=['POST'])
def send_invitation_email():
    """Send email invitation for contract signing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'contract_title', 'signing_link', 'inviter_name']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Email content
        subject = f"Contract Signature Request - {data['contract_title']}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f97316; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">
                        ₿ SecureDeal
                    </h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Contract Signature Request</p>
                </div>
                
                <div style="background-color: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #374151; margin-top: 0;">You've been invited to sign a contract</h2>
                    
                    <p>Hello,</p>
                    
                    <p><strong>{data['inviter_name']}</strong> has invited you to review and digitally sign the following contract:</p>
                    
                    <div style="background-color: #f9fafb; border-left: 4px solid #f97316; padding: 15px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #374151;">{data['contract_title']}</h3>
                        {f"<p style='margin: 0; color: #6b7280;'>{data.get('contract_description', '')}</p>" if data.get('contract_description') else ''}
                    </div>
                    
                    <p><strong>What you need to do:</strong></p>
                    <ol style="color: #6b7280;">
                        <li>Click the link below to access the contract</li>
                        <li>Review the contract terms and conditions</li>
                        <li>Sign the contract with your Bitcoin public key</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{data['signing_link']}" 
                           style="display: inline-block; background-color: #f97316; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                            Review & Sign Contract
                        </a>
                    </div>
                    
                    <div style="background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #92400e;"><strong>🔐 Security Note:</strong></p>
                        <p style="margin: 5px 0 0 0; color: #92400e; font-size: 14px;">
                            This contract uses Bitcoin cryptographic signatures for security. You'll need your Bitcoin public key to sign.
                        </p>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        If you have any questions about this contract, please contact <strong>{data['inviter_name']}</strong> directly.
                    </p>
                    
                    <p style="color: #6b7280; font-size: 14px;">
                        This invitation was sent via SecureDeal, a secure Bitcoin-based contract management platform.
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                    <p>SecureDeal - Secure Bitcoin Contract Management</p>
                    <p>Powered by Bitcoin blockchain technology</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # For demo purposes, we'll simulate sending the email
        # In production, you would use Flask-Mail or similar service
        print(f"📧 EMAIL SIMULATION:")
        print(f"To: {data['email']}")
        print(f"Subject: {subject}")
        print(f"Signing Link: {data['signing_link']}")
        print("✅ Email would be sent in production environment")
        
        return jsonify({
            'success': True,
            'message': 'Invitation email sent successfully',
            'recipient': data['email']
        })
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return jsonify({'error': 'Failed to send email'}), 500


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


@bp.route('/contracts/create/sale')
def create_sale():
    """Sale contract form"""
    return render_template('contracts/sale.html')


@bp.route('/contracts/create/rental')
def create_rental():
    """Rental contract form"""
    return render_template('contracts/rental.html')


@bp.route('/contracts/create/multisig')
def create_multisig():
    """Multi-signature contract form"""
    return render_template('contracts/multisig.html')


@bp.route('/contracts/create/escrow')
def create_escrow():
    """Escrow contract form"""
    return render_template('contracts/escrow.html')


@bp.route('/contracts/create/timelock')
def create_timelock():
    """Timelock contract form"""
    return render_template('contracts/timelock.html')


@bp.route('/contracts/create/savings')
def create_savings():
    """Savings contract form"""
    return render_template('contracts/savings.html')


@bp.route('/contracts/preview')
def preview_contract():
    """Contract preview page"""
    return render_template('contracts/preview.html')


@bp.route('/contracts/invite')
@bp.route('/contracts/<contract_id>/invite')
def invite_participants(contract_id=None):
    """Invite participants page"""
    return render_template('contracts/invite.html', contract_id=contract_id)


@bp.route('/contracts/sign')
def sign_contract():
    """Electronic signing page"""
    return render_template('contracts/sign.html')


@bp.route('/contracts/payment')
def payment():
    """Contract payment page"""
    return render_template('contracts/payment.html')


@bp.route('/notifications')
def notifications():
    """Notifications page"""
    return render_template('notifications.html')
