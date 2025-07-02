from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
from email_validator import validate_email, EmailNotValidError
import redis

from app import db, limiter
from app.models.user import User

bp = Blueprint('auth', __name__)

# Schémas de validation Marshmallow
class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8)
    username = fields.Str(missing=None, validate=lambda x: len(x) >= 3 if x else True)
    first_name = fields.Str(missing=None)
    last_name = fields.Str(missing=None)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember = fields.Bool(missing=False)

class PasswordResetSchema(Schema):
    email = fields.Email(required=True)

class PasswordResetConfirmSchema(Schema):
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=lambda x: len(x) >= 8)


@bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Inscription d'un nouvel utilisateur"""
    
    schema = RegisterSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = User.find_by_email(data['email'])
    if existing_user:
        return jsonify({'error': 'User already exists with this email'}), 400
    
    # Vérifier l'unicité du nom d'utilisateur
    if data.get('username'):
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({'error': 'Username already taken'}), 400
    
    try:
        # Créer le nouvel utilisateur
        user = User(
            email=data['email'],
            password=data['password'],
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        
        # Générer token de vérification email
        verification_token = user.generate_email_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # TODO: Envoyer email de vérification
        # send_verification_email(user.email, verification_token)
        
        # Générer tokens JWT
        tokens = user.generate_tokens()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'tokens': tokens,
            'email_verification_required': True
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Connexion utilisateur"""
    
    schema = LoginSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Trouver l'utilisateur
    user = User.find_by_email(data['email'])
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Vérifier si le compte est verrouillé
    if user.is_locked():
        return jsonify({
            'error': 'Account is temporarily locked due to failed login attempts',
            'locked_until': user.locked_until.isoformat() if user.locked_until else None
        }), 423
    
    # Vérifier si le compte est actif
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    try:
        # Enregistrer la connexion réussie
        user.record_login()
        db.session.commit()
        
        # Générer tokens JWT
        tokens = user.generate_tokens()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'tokens': tokens
        }), 200
    
    except Exception as e:
        # En cas d'erreur, incrémenter les tentatives échouées
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lock_account(30)  # Verrouiller pour 30 minutes
        
        db.session.commit()
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnexion utilisateur (blacklist du token)"""
    
    jti = get_jwt()['jti']
    
    # Ajouter le token à la blacklist Redis
    try:
        redis_client = redis.from_url(current_app.config['REDIS_URL'])
        # Expirer le token en même temps que son expiration naturelle
        redis_client.setex(jti, current_app.config['JWT_ACCESS_TOKEN_EXPIRES'], 'blacklisted')
        
        return jsonify({'message': 'Successfully logged out'}), 200
    
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Obtenir le profil utilisateur"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(),
        'contracts_count': user.created_contracts.count(),
        'signatures_count': user.signatures.count()
    }), 200


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Mettre à jour le profil utilisateur"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Validation des données
    allowed_fields = ['username', 'first_name', 'last_name', 'preferred_fee_rate', 'default_network']
    updates = {}
    
    for field in allowed_fields:
        if field in request.json:
            updates[field] = request.json[field]
    
    # Vérifier l'unicité du nom d'utilisateur si modifié
    if 'username' in updates and updates['username'] != user.username:
        existing = User.query.filter_by(username=updates['username']).first()
        if existing:
            return jsonify({'error': 'Username already taken'}), 400
    
    try:
        # Appliquer les mises à jour
        for field, value in updates.items():
            setattr(user, field, value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Profile update failed'}), 500


@bp.route('/verify-email/<token>', methods=['POST'])
def verify_email(token):
    """Vérifier l'email avec le token"""
    
    user = User.verify_email_token(token)
    
    if not user:
        return jsonify({'error': 'Invalid or expired verification token'}), 400
    
    return jsonify({
        'message': 'Email verified successfully',
        'user': user.to_dict()
    }), 200


@bp.route('/resend-verification', methods=['POST'])
@jwt_required()
@limiter.limit("3 per hour")
def resend_verification():
    """Renvoyer l'email de vérification"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.email_verified:
        return jsonify({'error': 'Email already verified'}), 400
    
    try:
        verification_token = user.generate_email_verification_token()
        db.session.commit()
        
        # TODO: Envoyer email de vérification
        # send_verification_email(user.email, verification_token)
        
        return jsonify({'message': 'Verification email sent'}), 200
    
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'Failed to send verification email'}), 500


@bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Demander une réinitialisation de mot de passe"""
    
    schema = PasswordResetSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    user = User.find_by_email(data['email'])
    
    # Toujours retourner succès pour éviter l'énumération d'emails
    response = {'message': 'If the email exists, a password reset link has been sent'}
    
    if user:
        try:
            # Générer token de réinitialisation
            reset_token = user.generate_email_verification_token()  # Réutiliser la méthode
            db.session.commit()
            
            # TODO: Envoyer email de réinitialisation
            # send_password_reset_email(user.email, reset_token)
            
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
    
    return jsonify(response), 200


@bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """Réinitialiser le mot de passe avec token"""
    
    schema = PasswordResetConfirmSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    user = User.verify_email_token(data['token'])
    
    if not user:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    try:
        user.set_password(data['new_password'])
        user.unlock_account()  # Débloquer si verrouillé
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset confirm error: {str(e)}")
        return jsonify({'error': 'Password reset failed'}), 500


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Rafraîchir le token d'accès"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 404
    
    tokens = user.generate_tokens()
    
    return jsonify({
        'message': 'Token refreshed successfully',
        'tokens': tokens
    }), 200
