from datetime import datetime
from enum import Enum
import uuid

from app import db


class SignatureStatus(Enum):
    """Statuts des signatures"""
    PENDING = "pending"
    SIGNED = "signed"
    REJECTED = "rejected"


class Signature(db.Model):
    """Modèle pour les signatures de contrats"""
    
    __tablename__ = 'signatures'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Relations
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    signer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Données de signature
    public_key = db.Column(db.String(64), nullable=False)  # Clé publique du signataire
    signature_data = db.Column(db.Text, nullable=True)     # Données de signature (PSBT partiel)
    signature_hash = db.Column(db.String(128), nullable=True)  # Hash de la signature pour validation
    
    # Statut et métadonnées
    status = db.Column(db.Enum(SignatureStatus), default=SignatureStatus.PENDING, nullable=False)
    signed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(500), nullable=True)
    
    # Validation
    is_valid = db.Column(db.Boolean, default=False, nullable=False)
    validation_data = db.Column(db.Text, nullable=True)  # JSON avec détails de validation
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index pour performance
    __table_args__ = (
        db.Index('idx_signature_contract_signer', 'contract_id', 'signer_id'),
        db.UniqueConstraint('contract_id', 'signer_id', name='uq_contract_signer'),
    )
    
    def __init__(self, contract_id, signer_id, public_key, **kwargs):
        self.contract_id = contract_id
        self.signer_id = signer_id
        self.public_key = public_key
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def sign(self, signature_data, signature_hash=None):
        """Enregistrer la signature"""
        self.signature_data = signature_data
        self.signature_hash = signature_hash
        self.status = SignatureStatus.SIGNED
        self.signed_at = datetime.utcnow()
        
        # Valider la signature
        self.validate_signature()
        
        # Mettre à jour le compteur de signatures du contrat
        if self.is_valid:
            self.contract.collected_signatures = Signature.query.filter_by(
                contract_id=self.contract_id,
                status=SignatureStatus.SIGNED,
                is_valid=True
            ).count()
            
            # Vérifier si le contrat peut passer à l'état ACTIVE
            if self.contract.collected_signatures >= self.contract.required_signatures:
                from app.models.contract import ContractStatus
                self.contract.status = ContractStatus.ACTIVE
    
    def reject(self, reason=None):
        """Rejeter la signature"""
        self.status = SignatureStatus.REJECTED
        self.rejection_reason = reason
        self.signed_at = None
        self.signature_data = None
        self.signature_hash = None
        self.is_valid = False
    
    def validate_signature(self):
        """Valider la signature cryptographique"""
        # Dans une vraie implémentation, on utiliserait le module Rust
        # pour valider la signature PSBT
        if self.signature_data and len(self.signature_data) > 0:
            self.is_valid = True
            self.validation_data = '{"method": "psbt_validation", "status": "valid"}'
        else:
            self.is_valid = False
            self.validation_data = '{"method": "psbt_validation", "status": "invalid", "error": "No signature data"}'
    
    def get_signature_info(self):
        """Obtenir les informations de signature pour l'API"""
        return {
            'signer': {
                'id': self.signer.public_id,
                'email': self.signer.email,
                'username': self.signer.username
            } if self.signer else None,
            'public_key': self.public_key,
            'status': self.status.value,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'is_valid': self.is_valid,
            'rejection_reason': self.rejection_reason
        }
    
    def to_dict(self, include_sensitive=False):
        """Convertir en dictionnaire pour JSON"""
        data = {
            'id': self.public_id,
            'contract_id': self.contract.public_id if self.contract else None,
            'signer_info': self.get_signature_info(),
            'status': self.status.value,
            'is_valid': self.is_valid,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'created_at': self.created_at.isoformat(),
            'rejection_reason': self.rejection_reason
        }
        
        if include_sensitive:
            data.update({
                'signature_data': self.signature_data,
                'signature_hash': self.signature_hash,
                'validation_data': self.validation_data
            })
        
        return data
    
    @staticmethod
    def find_by_public_id(public_id):
        """Trouver une signature par ID public"""
        return Signature.query.filter_by(public_id=public_id).first()
    
    @staticmethod
    def get_contract_signatures(contract_id, status=None):
        """Obtenir toutes les signatures d'un contrat"""
        query = Signature.query.filter_by(contract_id=contract_id)
        
        if status:
            if isinstance(status, str):
                status = SignatureStatus(status)
            query = query.filter(Signature.status == status)
        
        return query.order_by(Signature.created_at).all()
    
    @staticmethod
    def get_user_signatures(user_id, status=None):
        """Obtenir toutes les signatures d'un utilisateur"""
        query = Signature.query.filter_by(signer_id=user_id)
        
        if status:
            if isinstance(status, str):
                status = SignatureStatus(status)
            query = query.filter(Signature.status == status)
        
        return query.order_by(Signature.created_at.desc()).all()
    
    @staticmethod
    def get_pending_signatures_for_user(user_id):
        """Obtenir les signatures en attente pour un utilisateur"""
        return Signature.query.filter_by(
            signer_id=user_id,
            status=SignatureStatus.PENDING
        ).join(Signature.contract).filter(
            Contract.status.in_(['pending', 'active'])
        ).order_by(Signature.created_at).all()
    
    @staticmethod
    def create_signatures_for_contract(contract, participants_data):
        """Créer les signatures pour un nouveau contrat"""
        signatures = []
        
        for participant_data in participants_data:
            signature = Signature(
                contract_id=contract.id,
                signer_id=participant_data['user_id'],
                public_key=participant_data['public_key']
            )
            signatures.append(signature)
            db.session.add(signature)
        
        return signatures
    
    def __repr__(self):
        return f'<Signature {self.public_id} for Contract {self.contract_id}>'
