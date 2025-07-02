from datetime import datetime, timedelta
from enum import Enum
import secrets
import uuid

from app import db


class InvitationStatus(Enum):
    """Statuts des invitations"""
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Invitation(db.Model):
    """Modèle pour les invitations à participer aux contrats"""
    
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Relations
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Peut être null si invitation par email
    
    # Données d'invitation
    recipient_email = db.Column(db.String(120), nullable=True)  # Email si utilisateur pas encore inscrit
    public_key = db.Column(db.String(64), nullable=True)       # Clé publique fournie par l'inviteur
    role = db.Column(db.String(50), default='signer', nullable=False)  # 'signer', 'arbiter', etc.
    
    # Token sécurisé pour l'invitation
    invitation_token = db.Column(db.String(255), unique=True, nullable=False)
    
    # Statut et métadonnées
    status = db.Column(db.Enum(InvitationStatus), default=InvitationStatus.SENT, nullable=False)
    message = db.Column(db.Text, nullable=True)  # Message personnalisé de l'inviteur
    response_message = db.Column(db.Text, nullable=True)  # Message de réponse du destinataire
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Index pour performance
    __table_args__ = (
        db.Index('idx_invitation_contract', 'contract_id'),
        db.Index('idx_invitation_recipient', 'recipient_id'),
        db.Index('idx_invitation_email', 'recipient_email'),
        db.Index('idx_invitation_token', 'invitation_token'),
    )
    
    def __init__(self, contract_id, sender_id, **kwargs):
        self.contract_id = contract_id
        self.sender_id = sender_id
        self.invitation_token = self.generate_token()
        
        # Expiration par défaut à 72h
        self.expires_at = datetime.utcnow() + timedelta(hours=72)
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def generate_token(self):
        """Générer un token sécurisé pour l'invitation"""
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        """Vérifier si l'invitation a expiré"""
        if datetime.utcnow() > self.expires_at:
            if self.status == InvitationStatus.SENT:
                self.status = InvitationStatus.EXPIRED
                db.session.commit()
            return True
        return False
    
    def can_be_accepted(self):
        """Vérifier si l'invitation peut être acceptée"""
        return (
            self.status == InvitationStatus.SENT and
            not self.is_expired() and
            self.contract.status in ['draft', 'pending']
        )
    
    def accept(self, user_id=None, public_key=None, response_message=None):
        """Accepter l'invitation"""
        if not self.can_be_accepted():
            raise ValueError("Invitation cannot be accepted")
        
        self.status = InvitationStatus.ACCEPTED
        self.responded_at = datetime.utcnow()
        self.response_message = response_message
        
        # Si un utilisateur spécifique accepte (cas d'invitation par email)
        if user_id:
            self.recipient_id = user_id
        
        # Mettre à jour la clé publique si fournie
        if public_key:
            self.public_key = public_key
        
        # Créer la signature associée
        if self.recipient_id and self.public_key:
            from app.models.signature import Signature
            signature = Signature(
                contract_id=self.contract_id,
                signer_id=self.recipient_id,
                public_key=self.public_key
            )
            db.session.add(signature)
        
        return self
    
    def reject(self, response_message=None):
        """Rejeter l'invitation"""
        if self.status != InvitationStatus.SENT:
            raise ValueError("Invitation cannot be rejected")
        
        self.status = InvitationStatus.REJECTED
        self.responded_at = datetime.utcnow()
        self.response_message = response_message
    
    def resend(self, new_expiry_hours=72):
        """Renvoyer l'invitation avec un nouveau token"""
        if self.status in [InvitationStatus.ACCEPTED, InvitationStatus.REJECTED]:
            raise ValueError("Cannot resend accepted or rejected invitation")
        
        self.invitation_token = self.generate_token()
        self.sent_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=new_expiry_hours)
        self.status = InvitationStatus.SENT
        
        return self.invitation_token
    
    def get_invitation_url(self, base_url="https://securedeal.app"):
        """Générer l'URL d'invitation"""
        return f"{base_url}/invitations/{self.invitation_token}"
    
    def get_recipient_info(self):
        """Obtenir les informations du destinataire"""
        if self.recipient_id and self.recipient:
            return {
                'type': 'user',
                'id': self.recipient.public_id,
                'email': self.recipient.email,
                'username': self.recipient.username,
                'verified': self.recipient.email_verified
            }
        elif self.recipient_email:
            return {
                'type': 'email',
                'email': self.recipient_email,
                'verified': False
            }
        return None
    
    def to_dict(self, include_sensitive=False):
        """Convertir en dictionnaire pour JSON"""
        data = {
            'id': self.public_id,
            'contract_id': self.contract.public_id if self.contract else None,
            'sender': {
                'id': self.sender.public_id,
                'email': self.sender.email,
                'username': self.sender.username
            } if self.sender else None,
            'recipient_info': self.get_recipient_info(),
            'role': self.role,
            'status': self.status.value,
            'message': self.message,
            'response_message': self.response_message,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'expires_at': self.expires_at.isoformat(),
            'is_expired': self.is_expired(),
            'can_be_accepted': self.can_be_accepted()
        }
        
        if include_sensitive:
            data.update({
                'invitation_token': self.invitation_token,
                'public_key': self.public_key,
                'invitation_url': self.get_invitation_url()
            })
        
        return data
    
    @staticmethod
    def find_by_token(token):
        """Trouver une invitation par token"""
        return Invitation.query.filter_by(invitation_token=token).first()
    
    @staticmethod
    def find_by_public_id(public_id):
        """Trouver une invitation par ID public"""
        return Invitation.query.filter_by(public_id=public_id).first()
    
    @staticmethod
    def get_contract_invitations(contract_id, status=None):
        """Obtenir toutes les invitations d'un contrat"""
        query = Invitation.query.filter_by(contract_id=contract_id)
        
        if status:
            if isinstance(status, str):
                status = InvitationStatus(status)
            query = query.filter(Invitation.status == status)
        
        return query.order_by(Invitation.created_at).all()
    
    @staticmethod
    def get_user_invitations(user_id, status=None, include_sent=True, include_received=True):
        """Obtenir les invitations d'un utilisateur"""
        conditions = []
        
        if include_sent:
            conditions.append(Invitation.sender_id == user_id)
        
        if include_received:
            conditions.append(Invitation.recipient_id == user_id)
        
        if not conditions:
            return []
        
        query = Invitation.query.filter(db.or_(*conditions))
        
        if status:
            if isinstance(status, str):
                status = InvitationStatus(status)
            query = query.filter(Invitation.status == status)
        
        return query.order_by(Invitation.created_at.desc()).all()
    
    @staticmethod
    def get_pending_invitations_by_email(email):
        """Obtenir les invitations en attente pour un email"""
        return Invitation.query.filter_by(
            recipient_email=email.lower(),
            status=InvitationStatus.SENT
        ).filter(
            Invitation.expires_at > datetime.utcnow()
        ).all()
    
    @staticmethod
    def cleanup_expired_invitations():
        """Nettoyer les invitations expirées (tâche de maintenance)"""
        expired_count = Invitation.query.filter(
            Invitation.expires_at < datetime.utcnow(),
            Invitation.status == InvitationStatus.SENT
        ).update({'status': InvitationStatus.EXPIRED})
        
        db.session.commit()
        return expired_count
    
    def __repr__(self):
        return f'<Invitation {self.public_id} for Contract {self.contract_id}>'
