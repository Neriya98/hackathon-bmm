from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models.contract import Contract
from app.models.user import User
from app.models.invitation import Invitation

bp = Blueprint('contracts_routes', __name__)

@bp.route('/contracts')
def list_contracts():
    """Contracts list page - authentication handled by JavaScript"""
    return render_template('contracts/list.html')

@bp.route('/contracts/create')
def create_contract():
    """Contract creation page - authentication handled by JavaScript"""
    return render_template('contracts/create.html')

@bp.route('/contracts/create/sale')
def create_sale_contract():
    """Sale contract creation page"""
    return render_template('contracts/sale.html')

@bp.route('/contracts/create/rental')
def create_rental_contract():
    """Rental contract creation page"""
    return render_template('contracts/rental.html')

@bp.route('/contracts/create/savings')
def create_savings_contract():
    """Savings contract creation page"""
    return render_template('contracts/savings.html')

@bp.route('/contracts/create/escrow')
def create_escrow_contract():
    """Escrow contract creation page"""
    return render_template('contracts/escrow.html')

@bp.route('/contracts/create/multisig')
def create_multisig_contract():
    """Multisig contract creation page"""
    return render_template('contracts/multisig.html')

@bp.route('/contracts/create/timelock')
def create_timelock_contract():
    """Timelock contract creation page"""
    return render_template('contracts/timelock.html')

@bp.route('/contracts/preview')
def preview_contract():
    """Contract preview page"""
    return render_template('contracts/preview.html')

@bp.route('/contracts/invite')
def invite_to_contract():
    """Contract invitation page"""
    return render_template('contracts/invite.html')

@bp.route('/contracts/sign')
def sign_contract():
    """Contract signing page"""
    return render_template('contracts/sign.html')

@bp.route('/contracts/payment')
def contract_payment():
    """Contract payment page"""
    return render_template('contracts/payment.html')

@bp.route('/contracts/<contract_id>')
@jwt_required()
def contract_details(contract_id):
    """Contract details page"""
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    contract = Contract.find_by_public_id(contract_id)
    
    if not contract:
        return render_template('errors/404.html'), 404
    
    # Verify access
    user_contracts = Contract.get_user_contracts(user.id).all()
    if contract not in user_contracts:
        return render_template('errors/403.html'), 403
    
    return render_template('contracts/details.html', user=user, contract=contract)

# API endpoints
@bp.route('/api/contracts', methods=['GET'])
@jwt_required()
def api_get_contracts():
    """Get all contracts for the authenticated user"""
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contracts = Contract.get_user_contracts(user.id).all()
    return jsonify({'contracts': [contract.to_dict() for contract in contracts]}), 200

@bp.route('/api/contracts', methods=['POST'])
@jwt_required()
def api_create_contract():
    """Create a new contract"""
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        contract = Contract(
            title=data.get('title'),
            description=data.get('description'),
            contract_type=data.get('contract_type'),
            creator_id=user.id,
            terms=data.get('terms'),
            status='draft',
            amount=data.get('amount', 0)
        )
        
        contract.save()
        return jsonify({'message': 'Contract created', 'contract': contract.to_dict()}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/api/send-invitation-email', methods=['POST'])
def send_invitation_email():
    """Send email invitation for contract signing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'contract_title', 'signing_link', 'inviter_name']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # In a real application, email would be sent here
        # For now, just return success
        
        return jsonify({
            'message': 'Invitation sent successfully',
            'recipient': data['email']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
