from datetime import datetime
from enum import Enum
import uuid

from app import db


class ContractType(Enum):
    """Types de contrats Bitcoin supportés"""
    MULTISIG = "multisig"
    TIMELOCK = "timelock"
    ESCROW = "escrow"


class ContractStatus(Enum):
    """Statuts possibles d'un contrat"""
    DRAFT = "draft"              # Brouillon, en cours de création
    PENDING = "pending"          # En attente de signatures
    ACTIVE = "active"            # Actif, toutes signatures collectées
    FINALIZED = "finalized"      # Finalisé, transaction diffusée
    EXPIRED = "expired"          # Expiré
    CANCELLED = "cancelled"      # Annulé


class Contract(db.Model):
    """Modèle principal pour les contrats Bitcoin"""
    
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Informations de base
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    contract_type = db.Column(db.Enum(ContractType), nullable=False)
    status = db.Column(db.Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False)
    
    # Configuration Bitcoin
    network = db.Column(db.String(20), default='signet', nullable=False)
    amount_sats = db.Column(db.BigInteger, nullable=False)  # Montant en satoshis
    fee_rate = db.Column(db.Integer, default=10, nullable=False)  # sat/vB
    
    # PSBT et transaction
    psbt_base64 = db.Column(db.Text, nullable=True)
    script_pubkey = db.Column(db.String(500), nullable=True)
    address = db.Column(db.String(100), nullable=True)
    policy = db.Column(db.Text, nullable=True)
    transaction_id = db.Column(db.String(64), nullable=True)
    
    # Configuration spécifique
    required_signatures = db.Column(db.Integer, nullable=False)
    collected_signatures = db.Column(db.Integer, default=0, nullable=False)
    timelock_timestamp = db.Column(db.DateTime, nullable=True)  # Pour les contrats TimeLock
    
    # Métadonnées
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    participants_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    finalized_at = db.Column(db.DateTime, nullable=True)
    
    # Relations
    signatures = db.relationship('Signature', backref='contract', lazy='dynamic', cascade='all, delete-orphan')
    invitations = db.relationship('Invitation', backref='contract', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, contract_type, amount_sats, creator_id, **kwargs):
        self.title = title
        self.contract_type = contract_type
        self.amount_sats = amount_sats
        self.creator_id = creator_id
        
        # Configuration par défaut basée sur le type
        if contract_type == ContractType.MULTISIG:
            self.required_signatures = kwargs.get('required_signatures', 2)
        elif contract_type == ContractType.TIMELOCK:
            self.required_signatures = 1
            self.timelock_timestamp = kwargs.get('timelock_timestamp')
        elif contract_type == ContractType.ESCROW:
            self.required_signatures = 2  # 2-of-3 pour escrow
        
        # Autres attributs
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['title', 'contract_type', 'amount_sats', 'creator_id']:
                setattr(self, key, value)
    
    def add_participant(self, user_id, public_key=None):
        """Ajouter un participant au contrat"""
        from app.models.invitation import Invitation
        
        invitation = Invitation(
            contract_id=self.id,
            sender_id=self.creator_id,
            recipient_id=user_id,
            public_key=public_key
        )
        
        db.session.add(invitation)
        self.participants_count += 1
        return invitation
    
    def is_ready_for_signing(self):
        """Vérifier si le contrat est prêt pour signature"""
        return (
            self.status == ContractStatus.PENDING and
            self.psbt_base64 is not None and
            self.participants_count >= self.required_signatures
        )
    
    def is_fully_signed(self):
        """Vérifier si toutes les signatures requises sont collectées"""
        return self.collected_signatures >= self.required_signatures
    
    def is_expired(self):
        """Vérifier si le contrat a expiré"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            if self.status not in [ContractStatus.FINALIZED, ContractStatus.CANCELLED]:
                self.status = ContractStatus.EXPIRED
                db.session.commit()
            return True
        return False
    
    def can_be_finalized(self):
        """Vérifier si le contrat peut être finalisé"""
        return (
            self.status == ContractStatus.ACTIVE and
            self.is_fully_signed() and
            not self.is_expired()
        )
    
    def finalize(self, transaction_id):
        """Finaliser le contrat avec l'ID de transaction"""
        if not self.can_be_finalized():
            raise ValueError("Contract cannot be finalized")
        
        self.status = ContractStatus.FINALIZED
        self.transaction_id = transaction_id
        self.finalized_at = datetime.utcnow()
    
    def cancel(self):
        """Annuler le contrat"""
        if self.status in [ContractStatus.FINALIZED, ContractStatus.CANCELLED]:
            raise ValueError("Contract cannot be cancelled")
        
        self.status = ContractStatus.CANCELLED
    
    def get_amount_btc(self):
        """Obtenir le montant en BTC"""
        return self.amount_sats / 100_000_000
    
    def get_participants(self):
        """Obtenir la liste des participants via les invitations"""
        from app.models.user import User
        from app.models.invitation import Invitation
        
        participants = []
        
        # Créateur
        participants.append(self.creator)
        
        # Invités acceptés
        accepted_invitations = Invitation.query.filter_by(
            contract_id=self.id,
            status='accepted'
        ).all()
        
        for invitation in accepted_invitations:
            if invitation.recipient and invitation.recipient not in participants:
                participants.append(invitation.recipient)
        
        return participants
    
    def get_signatures_status(self):
        """Obtenir le statut des signatures"""
        signatures = self.signatures.all()
        return {
            'required': self.required_signatures,
            'collected': len(signatures),
            'remaining': max(0, self.required_signatures - len(signatures)),
            'percentage': min(100, (len(signatures) / self.required_signatures) * 100) if self.required_signatures > 0 else 0
        }
    
    def to_dict(self, include_sensitive=False):
        """Convertir en dictionnaire pour JSON"""
        data = {
            'id': self.public_id,
            'title': self.title,
            'description': self.description,
            'contract_type': self.contract_type.value,
            'status': self.status.value,
            'network': self.network,
            'amount_sats': self.amount_sats,
            'amount_btc': self.get_amount_btc(),
            'fee_rate': self.fee_rate,
            'address': self.address,
            'required_signatures': self.required_signatures,
            'collected_signatures': self.collected_signatures,
            'participants_count': self.participants_count,
            'signatures_status': self.get_signatures_status(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'finalized_at': self.finalized_at.isoformat() if self.finalized_at else None,
            'timelock_timestamp': self.timelock_timestamp.isoformat() if self.timelock_timestamp else None,
            'is_expired': self.is_expired(),
            'can_be_finalized': self.can_be_finalized()
        }
        
        if include_sensitive:
            data.update({
                'psbt_base64': self.psbt_base64,
                'script_pubkey': self.script_pubkey,
                'policy': self.policy,
                'transaction_id': self.transaction_id,
                'creator_id': self.creator.public_id if self.creator else None
            })
        
        return data
    
    @staticmethod
    def find_by_public_id(public_id):
        """Trouver un contrat par ID public"""
        return Contract.query.filter_by(public_id=public_id).first()
    
    @staticmethod
    def get_user_contracts(user_id, status=None):
        """Obtenir les contrats d'un utilisateur"""
        from app.models.invitation import Invitation
        
        query = Contract.query.filter(
            db.or_(
                Contract.creator_id == user_id,
                Contract.id.in_(
                    db.session.query(Invitation.contract_id)
                    .filter(Invitation.recipient_id == user_id)
                    .filter(Invitation.status == 'accepted')
                )
            )
        )
        
        if status:
            if isinstance(status, str):
                status = ContractStatus(status)
            query = query.filter(Contract.status == status)
        
        return query.order_by(Contract.created_at.desc())
    
    def __repr__(self):
        return f'<Contract {self.title} ({self.contract_type.value})>'
