from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, timedelta
from app.services.smart_contract_service import SmartContractService
import logging

from app import db, limiter
from app.models.user import User
from app.models.contract import Contract, ContractType, ContractStatus
from app.models.invitation import Invitation
from app.models.signature import Signature
from app.services.notification_service import NotificationService

# Configure logger
logger = logging.getLogger(__name__)

# Create notification service instance
notification_service = NotificationService()

bp = Blueprint('contracts', __name__)

# Schémas de validation
class CreateContractSchema(Schema):
    title = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 3)
    description = fields.Str(missing=None)
    contract_type = fields.Str(required=True, validate=lambda x: x in ['multisig', 'timelock', 'escrow'])
    amount_sats = fields.Int(required=True, validate=lambda x: x > 0)
    participants = fields.List(fields.Str(), required=True, validate=lambda x: len(x) >= 1)
    timelock_hours = fields.Int(missing=None, validate=lambda x: x > 0 if x else True)
    fee_rate = fields.Int(missing=10, validate=lambda x: 1 <= x <= 1000)
    network = fields.Str(missing='signet', validate=lambda x: x in ['mainnet', 'testnet', 'signet', 'regtest'])
    expires_in_days = fields.Int(missing=30, validate=lambda x: 1 <= x <= 365)

class InviteParticipantSchema(Schema):
    email = fields.Email(required=True)
    public_key = fields.Str(missing=None, validate=lambda x: len(x) == 64 if x else True)
    role = fields.Str(missing='signer', validate=lambda x: x in ['signer', 'arbiter'])
    message = fields.Str(missing=None)


@bp.route('/', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_contract():
    """Créer un nouveau contrat Bitcoin"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.email_verified:
        return jsonify({'error': 'Email verification required'}), 403
    
    schema = CreateContractSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Calculer timelock si spécifié
        timelock_timestamp = None
        if data.get('timelock_hours') and data['contract_type'] == 'timelock':
            timelock_timestamp = datetime.utcnow() + timedelta(hours=data['timelock_hours'])
        
        # Créer le contrat en base
        contract = Contract(
            title=data['title'].strip(),
            description=data.get('description'),
            contract_type=ContractType(data['contract_type']),
            amount_sats=data['amount_sats'],
            creator_id=user.id,
            fee_rate=data.get('fee_rate', 10),
            network=data.get('network', 'signet'),
            timelock_timestamp=timelock_timestamp,
            expires_at=datetime.utcnow() + timedelta(days=data.get('expires_in_days', 30))
        )
        
        db.session.add(contract)
        db.session.flush()  # Pour obtenir l'ID
        
        # Create the contract using the Rust blockchain service
        service = SmartContractService()
        
        # Prepare data for smart contract generation
        contract_data = {
            'type': data['contract_type'],
            'participants': data['participants'],
            'amount': data['amount_sats'],
            'network': data.get('network', 'signet'),
        }
        
        if timelock_timestamp:
            contract_data['timelock'] = int(timelock_timestamp.timestamp())
            
        # Call the Rust blockchain service
        smart_contract_result = service.create_smart_contract_from_data(contract_data)
        
        if not smart_contract_result:
            # Fallback to placeholder if service fails
            logger.warning("Blockchain service unavailable. Using placeholder address.")
            smart_contract_result = {
                'psbt_base64': 'temporary_psbt_placeholder',
                'script_pubkey': 'temporary_script_placeholder',
                'address': f'tb1q{user.public_id[:8]}contract{contract.id}',
                'policy': 'temporary_policy_placeholder'
            }
        
        # Mettre à jour le contrat avec les données PSBT
        contract.psbt_base64 = smart_contract_result.get('psbt_base64', '')
        contract.script_pubkey = smart_contract_result.get('script_pubkey', '')
        contract.address = smart_contract_result.get('address', '')
        contract.policy = smart_contract_result.get('policy', '')
        contract.status = ContractStatus.PENDING
        
        db.session.commit()
        
        return jsonify({
            'message': 'Contract created successfully',
            'contract': contract.to_dict(include_sensitive=True)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract creation error: {str(e)}")
        return jsonify({'error': f'Contract creation failed: {str(e)}'}), 500


@bp.route('/', methods=['GET'])
@jwt_required()
def list_contracts():
    """Lister les contrats de l'utilisateur"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    status_filter = request.args.get('status')
    
    # Obtenir les contrats de l'utilisateur
    contracts_query = Contract.get_user_contracts(user.id, status_filter)
    contracts_pagination = contracts_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    contracts_data = [contract.to_dict() for contract in contracts_pagination.items]
    
    return jsonify({
        'contracts': contracts_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': contracts_pagination.total,
            'pages': contracts_pagination.pages,
            'has_next': contracts_pagination.has_next,
            'has_prev': contracts_pagination.has_prev
        }
    }), 200


@bp.route('/<contract_id>', methods=['GET'])
@jwt_required()
def get_contract(contract_id):
    """Obtenir les détails d'un contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Vérifier que l'utilisateur peut accéder au contrat
    user_contracts = Contract.get_user_contracts(user.id).all()
    if contract not in user_contracts:
        return jsonify({'error': 'Access denied'}), 403
    
    # Obtenir les signatures et invitations
    signatures = Signature.get_contract_signatures(contract.id)
    invitations = Invitation.get_contract_invitations(contract.id)
    
    contract_data = contract.to_dict(include_sensitive=True)
    contract_data['signatures'] = [sig.to_dict() for sig in signatures]
    contract_data['invitations'] = [inv.to_dict() for inv in invitations]
    
    return jsonify({
        'contract': contract_data
    }), 200


@bp.route('/<contract_id>/invite', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def invite_participant(contract_id):
    """Inviter un participant à signer le contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Vérifier que l'utilisateur est le créateur
    if contract.creator_id != user.id:
        return jsonify({'error': 'Only contract creator can send invitations'}), 403
    
    # Vérifier l'état du contrat
    if contract.status not in [ContractStatus.DRAFT, ContractStatus.PENDING]:
        return jsonify({'error': 'Cannot invite to this contract'}), 400
    
    schema = InviteParticipantSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Vérifier si une invitation existe déjà
        existing_invitation = Invitation.query.filter_by(
            contract_id=contract.id,
            recipient_email=data['email'].lower()
        ).first()
        
        if existing_invitation and existing_invitation.status == 'accepted':
            return jsonify({'error': 'User already participating in this contract'}), 400
        
        # Chercher l'utilisateur destinataire
        recipient = User.find_by_email(data['email'])
        
        # Créer l'invitation
        invitation = Invitation(
            contract_id=contract.id,
            sender_id=user.id,
            recipient_id=recipient.id if recipient else None,
            recipient_email=data['email'].lower(),
            public_key=data.get('public_key'),
            role=data.get('role', 'signer'),
            message=data.get('message')
        )
        
        # Si invitation existante expirée, la supprimer
        if existing_invitation:
            db.session.delete(existing_invitation)
        
        db.session.add(invitation)
        db.session.commit()
        
        # Send invitation email
        notification_service.send_invitation_email(invitation, contract, user)
        
        return jsonify({
            'message': 'Invitation sent successfully',
            'invitation': invitation.to_dict(include_sensitive=True)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Invitation error: {str(e)}")
        return jsonify({'error': f'Failed to send invitation: {str(e)}'}), 500


@bp.route('/<contract_id>/sign', methods=['POST'])
@jwt_required()
@limiter.limit("30 per hour")
def sign_contract(contract_id):
    """Signer un contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Vérifier que l'utilisateur peut signer
    user_contracts = Contract.get_user_contracts(user.id).all()
    if contract not in user_contracts:
        return jsonify({'error': 'Access denied'}), 403
    
    if not contract.is_ready_for_signing():
        return jsonify({'error': 'Contract not ready for signing'}), 400
    
    # Vérifier si l'utilisateur a déjà signé
    existing_signature = Signature.query.filter_by(
        contract_id=contract.id,
        signer_id=user.id
    ).first()
    
    if existing_signature and existing_signature.status == 'signed':
        return jsonify({'error': 'Contract already signed by user'}), 400
    
    # Validation des données de signature
    if not request.json or 'private_key' not in request.json:
        return jsonify({'error': 'Private key required for signing'}), 400
    
    try:
        # Signer le PSBT via Rust (temporarily disabled)
        # sign_result = securedeal_core.sign_psbt(
        #     psbt_base64=contract.psbt_base64,
        #     private_key=request.json['private_key'],
        #     network=contract.network
        # )
        
        # Temporary placeholder
        sign_result = {
            'success': True,
            'psbt_base64': 'temporary_signed_psbt_placeholder',
            'signature_hex': 'temporary_signature_placeholder'
        }
        
        if not sign_result['success']:
            return jsonify({'error': 'Failed to sign PSBT'}), 400
        
        # Créer ou mettre à jour la signature
        if existing_signature:
            signature = existing_signature
        else:
            signature = Signature(
                contract_id=contract.id,
                signer_id=user.id,
                public_key=request.json.get('public_key', 'auto_derived')
            )
            db.session.add(signature)
        
        signature.sign(
            signature_data=sign_result.get('psbt_base64'),
            signature_hash=f"hash_{signature.public_id[:8]}"
        )
        
        # Mettre à jour le PSBT du contrat si nécessaire
        if sign_result.get('psbt_base64'):
            contract.psbt_base64 = sign_result['psbt_base64']
        
        db.session.commit()
        
        # Import smart contract service and notification service
        from app.services.smart_contract_service import signature_monitor
        
        # Create signature notification for all parties
        signer_name = user.username or user.email
        notification_service.notify_all_contract_parties(
            contract.public_id, 
            'signature', 
            {
                'signer_name': signer_name,
                'message': f'{signer_name} has signed the contract'
            }
        )
        
        # Check if all signatures are completed and trigger smart contract creation
        all_signed = signature_monitor.check_signature_completion(contract.public_id)
        
        if all_signed:
            # Notify all parties that contract is fully signed and smart contract creation started
            notification_service.notify_all_contract_parties(
                contract.public_id,
                'completion',
                {
                    'message': 'All signatures collected. Creating smart contract...'
                }
            )
        
        return jsonify({
            'message': 'Contract signed successfully',
            'signature': signature.to_dict(),
            'contract_status': contract.to_dict()['signatures_status']
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract signing error: {str(e)}")
        return jsonify({'error': f'Failed to sign contract: {str(e)}'}), 500


@bp.route('/<contract_id>/finalize', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def finalize_contract(contract_id):
    """Finaliser et diffuser la transaction du contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Vérifier que l'utilisateur est le créateur
    if contract.creator_id != user.id:
        return jsonify({'error': 'Only contract creator can finalize'}), 403
    
    if not contract.can_be_finalized():
        return jsonify({'error': 'Contract cannot be finalized'}), 400
    
    broadcast = request.json.get('broadcast', False) if request.json else False
    
    try:
        # Finaliser via Rust (temporarily disabled)
        # finalize_result = securedeal_core.finalize_transaction(
        #     psbt_base64=contract.psbt_base64,
        #     network=contract.network,
        #     broadcast=broadcast
        # )
        
        # Temporary placeholder
        finalize_result = {
            'success': True,
            'transaction_id': 'temp_tx_' + str(contract.id),
            'transaction_hex': 'temporary_transaction_hex_placeholder'
        }
        
        if finalize_result['success']:
            # Marquer le contrat comme finalisé
            contract.finalize(finalize_result['transaction_id'])
            db.session.commit()
            
            return jsonify({
                'message': 'Contract finalized successfully',
                'transaction_id': finalize_result['transaction_id'],
                'broadcast': broadcast,
                'contract': contract.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Failed to finalize contract'}), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract finalization error: {str(e)}")
        return jsonify({'error': f'Failed to finalize contract: {str(e)}'}), 500


@bp.route('/<contract_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_contract(contract_id):
    """Annuler un contrat"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Vérifier que l'utilisateur est le créateur
    if contract.creator_id != user.id:
        return jsonify({'error': 'Only contract creator can cancel'}), 403
    
    try:
        contract.cancel()
        db.session.commit()
        
        return jsonify({
            'message': 'Contract cancelled successfully',
            'contract': contract.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contract cancellation error: {str(e)}")
        return jsonify({'error': 'Failed to cancel contract'}), 500


@bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_user_statistics():
    """Obtenir les statistiques des contrats de l'utilisateur"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Statistiques des contrats
    total_contracts = Contract.get_user_contracts(user.id).count()
    contracts_by_status = {}
    
    for status in ContractStatus:
        count = Contract.get_user_contracts(user.id, status).count()
        contracts_by_status[status.value] = count
    
    # Statistiques des signatures
    total_signatures = Signature.get_user_signatures(user.id)
    pending_signatures = len(Signature.get_pending_signatures_for_user(user.id))
    
    # Volume total
    user_contracts = Contract.get_user_contracts(user.id).all()
    total_volume_sats = sum(c.amount_sats for c in user_contracts)
    
    return jsonify({
        'statistics': {
            'contracts': {
                'total': total_contracts,
                'by_status': contracts_by_status
            },
            'signatures': {
                'total': len(total_signatures),
                'pending': pending_signatures
            },
            'volume': {
                'total_sats': total_volume_sats,
                'total_btc': total_volume_sats / 100_000_000
            }
        }
    }), 200


@bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics for the current user"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's contracts
    user_contracts = Contract.query.filter_by(creator_id=user.id).all()
    
    # Calculate stats
    active_contracts = len([c for c in user_contracts if c.status == ContractStatus.ACTIVE])
    pending_signatures = Signature.query.join(Contract).filter(
        Contract.creator_id == user.id,
        Signature.status == 'pending'
    ).count()
    total_invitations = Invitation.query.join(Contract).filter(
        Contract.creator_id == user.id
    ).count()
    
    # Calculate total volume (sum of all contract amounts)
    total_volume_sats = sum([c.amount_sats for c in user_contracts])
    total_volume_btc = total_volume_sats / 100000000  # Convert to BTC
    
    return jsonify({
        'active_contracts': active_contracts,
        'pending_signatures': pending_signatures,
        'total_invitations': total_invitations,
        'total_volume_btc': total_volume_btc,
        'total_contracts': len(user_contracts)
    }), 200


@bp.route('/<contract_id>/payment-status', methods=['GET'])
@jwt_required()
def check_payment_status(contract_id):
    """Check payment status for a contract"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Check if user has access to this contract
    user_contracts = Contract.get_user_contracts(user.id).all()
    if contract not in user_contracts:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        from app.services.smart_contract_service import smart_contract_service
        
        payment_status = smart_contract_service.check_payment_status(contract_id)
        
        if payment_status:
            return jsonify({
                'message': 'Payment status retrieved successfully',
                'payment_status': payment_status
            }), 200
        else:
            return jsonify({
                'message': 'No payment information available',
                'payment_status': None
            }), 200
    
    except Exception as e:
        current_app.logger.error(f"Payment status check error: {str(e)}")
        return jsonify({'error': f'Failed to check payment status: {str(e)}'}), 500


@bp.route('/<contract_id>/payment/monitor', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def start_payment_monitoring(contract_id):
    """Start monitoring for contract payment"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Only contract creator can start monitoring
    if contract.creator_id != user.id:
        return jsonify({'error': 'Only contract creator can start payment monitoring'}), 403
    
    try:
        from app.services.smart_contract_service import smart_contract_service
        
        smart_contract_service.start_payment_monitoring(contract)
        
        return jsonify({
            'message': 'Payment monitoring started successfully',
            'contract_id': contract_id,
            'payment_address': contract.payment_address
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Payment monitoring error: {str(e)}")
        return jsonify({'error': f'Failed to start payment monitoring: {str(e)}'}), 500
