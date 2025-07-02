from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import uuid

from app import db


class User(db.Model):
    """Modèle utilisateur avec authentification sécurisée"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Informations personnelles
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    
    # Vérification email
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Informations de profil
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    # User type and role
    user_type = db.Column(db.String(20), default='user', nullable=False)  # 'user' or 'notaire'
    
    # Bitcoin/Crypto
    bitcoin_public_key = db.Column(db.String(130), nullable=True)  # Bitcoin public key for signing
    default_network = db.Column(db.String(20), default='signet', nullable=False)
    preferred_fee_rate = db.Column(db.Integer, default=10, nullable=False)  # sat/vB
    
    # Sécurité
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # Relations
    created_contracts = db.relationship('Contract', backref='creator', lazy='dynamic', foreign_keys='Contract.creator_id')
    signatures = db.relationship('Signature', backref='signer', lazy='dynamic')
    sent_invitations = db.relationship('Invitation', backref='sender', lazy='dynamic', foreign_keys='Invitation.sender_id')
    received_invitations = db.relationship('Invitation', backref='recipient', lazy='dynamic', foreign_keys='Invitation.recipient_id')
    
    def __init__(self, email, password, **kwargs):
        self.email = email.lower()
        self.set_password(password)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """Hasher le mot de passe avec un salt sécurisé"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        """Générer un token de vérification email"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token
    
    def verify_email(self, token):
        """Vérifier l'email avec le token"""
        if not self.email_verification_token or self.email_verification_token != token:
            return False
        
        # Vérifier l'expiration (24h)
        if self.email_verification_sent_at:
            expiry = self.email_verification_sent_at + timedelta(hours=24)
            if datetime.utcnow() > expiry:
                return False
        
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        return True
    
    def generate_tokens(self):
        """Générer les tokens JWT d'accès et de rafraîchissement"""
        additional_claims = {
            "user_id": self.public_id,
            "email": self.email,
            "email_verified": self.email_verified,
            "is_admin": self.is_admin
        }
        
        access_token = create_access_token(
            identity=self.public_id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=self.public_id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
    
    def lock_account(self, duration_minutes=30):
        """Verrouiller le compte temporairement"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts += 1
    
    def unlock_account(self):
        """Déverrouiller le compte"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def is_locked(self):
        """Vérifier si le compte est verrouillé"""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        elif self.locked_until and datetime.utcnow() >= self.locked_until:
            # Auto-déverrouillage
            self.unlock_account()
        return False
    
    def record_login(self):
        """Enregistrer une connexion réussie"""
        self.last_login_at = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def to_dict(self, include_sensitive=False):
        """Convertir en dictionnaire pour JSON"""
        data = {
            'id': self.public_id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'avatar_url': self.avatar_url,
            'email_verified': self.email_verified,
            'default_network': self.default_network,
            'preferred_fee_rate': self.preferred_fee_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
        
        if include_sensitive:
            data.update({
                'is_admin': self.is_admin,
                'failed_login_attempts': self.failed_login_attempts,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })
        
        return data
    
    @staticmethod
    def find_by_email(email):
        """Trouver un utilisateur par email"""
        return User.query.filter_by(email=email.lower()).first()
    
    @staticmethod
    def find_by_public_id(public_id):
        """Trouver un utilisateur par ID public"""
        return User.query.filter_by(public_id=public_id).first()
    
    @staticmethod
    def verify_email_token(token):
        """Vérifier un token de vérification email"""
        user = User.query.filter_by(email_verification_token=token).first()
        if user and user.verify_email(token):
            db.session.commit()
            return user
        return None
    
    def __repr__(self):
        return f'<User {self.email}>'
