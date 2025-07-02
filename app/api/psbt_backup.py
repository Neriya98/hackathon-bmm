from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
# import securedeal_core  # Temporarily disabled

from app import db, limiter
from app.models.user import User

bp = Blueprint('psbt', __name__)

# Schémas de validation
class CreateContractSchema(Schema):
    contract_type = fields.Str(required=True, validate=lambda x: x in ['multisig', 'timelock', 'escrow'])
    participants = fields.List(fields.Str(), required=True, validate=lambda x: len(x) >= 1)
    amount = fields.Int(required=True, validate=lambda x: x > 0)
    timelock = fields.Int(missing=None)
    network = fields.Str(missing='signet', validate=lambda x: x in ['mainnet', 'testnet', 'signet', 'regtest'])

class SignPSBTSchema(Schema):
    psbt_base64 = fields.Str(required=True)
    private_key = fields.Str(required=True)
    network = fields.Str(missing='signet')

class ValidatePSBTSchema(Schema):
    psbt_base64 = fields.Str(required=True)

class FinalizePSBTSchema(Schema):
    psbt_base64 = fields.Str(required=True)
    network = fields.Str(missing='signet')
    broadcast = fields.Bool(missing=False)


@bp.route('/create-contract', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_contract():
    """Créer un nouveau contrat PSBT via le module Rust"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = CreateContractSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Appeler le module Rust pour créer le contrat
        result = securedeal_core.create_bitcoin_contract(
            contract_type=data['contract_type'],
            participants=data['participants'],
            amount=data['amount'],
            timelock=data.get('timelock'),
            network=data.get('network', 'signet')
        )
        
        return jsonify({
            'message': 'Contract created successfully',
            'contract': result
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"Contract creation error: {str(e)}")
        return jsonify({'error': f'Contract creation failed: {str(e)}'}), 500


@bp.route('/create-multisig', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_multisig_script():
    """Créer un script multisig (basé sur votre main.rs)"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Validation simple
    if not request.json or 'pubkeys' not in request.json:
        return jsonify({'error': 'Public keys required'}), 400
    
    pubkeys = request.json['pubkeys']
    threshold = request.json.get('threshold', len(pubkeys))
    
    if not isinstance(pubkeys, list) or len(pubkeys) < 2:
        return jsonify({'error': 'At least 2 public keys required'}), 400
    
    if threshold > len(pubkeys):
        return jsonify({'error': 'Threshold cannot exceed number of keys'}), 400
    
    try:
        # Appeler le module Rust pour créer le script multisig
        result = securedeal_core.create_multisig_script(
            pubkeys=pubkeys,
            threshold=threshold
        )
        
        return jsonify({
            'message': 'Multisig script created successfully',
            'script': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Multisig creation error: {str(e)}")
        return jsonify({'error': f'Multisig creation failed: {str(e)}'}), 500


@bp.route('/sign', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def sign_psbt():
    """Signer un PSBT avec une clé privée"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = SignPSBTSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Appeler le module Rust pour signer le PSBT
        result = securedeal_core.sign_psbt(
            psbt_base64=data['psbt_base64'],
            private_key=data['private_key'],
            network=data.get('network', 'signet')
        )
        
        return jsonify({
            'message': 'PSBT signed successfully',
            'signature_result': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"PSBT signing error: {str(e)}")
        return jsonify({'error': f'PSBT signing failed: {str(e)}'}), 500


@bp.route('/validate', methods=['POST'])
@jwt_required()
@limiter.limit("100 per hour")
def validate_psbt():
    """Valider un PSBT"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = ValidatePSBTSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Appeler le module Rust pour valider le PSBT
        result = securedeal_core.validate_psbt(
            psbt_base64=data['psbt_base64']
        )
        
        return jsonify({
            'message': 'PSBT validation completed',
            'validation': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"PSBT validation error: {str(e)}")
        return jsonify({'error': f'PSBT validation failed: {str(e)}'}), 500


@bp.route('/info', methods=['POST'])
@jwt_required()
@limiter.limit("100 per hour")
def get_psbt_info():
    """Obtenir les informations d'un PSBT"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = ValidatePSBTSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Appeler le module Rust pour obtenir les infos du PSBT
        result = securedeal_core.get_psbt_info(
            psbt_base64=data['psbt_base64']
        )
        
        return jsonify({
            'message': 'PSBT info retrieved successfully',
            'psbt_info': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"PSBT info error: {str(e)}")
        return jsonify({'error': f'PSBT info retrieval failed: {str(e)}'}), 500


@bp.route('/finalize', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def finalize_transaction():
    """Finaliser et optionnellement diffuser une transaction"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = FinalizePSBTSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Appeler le module Rust pour finaliser la transaction
        result = securedeal_core.finalize_transaction(
            psbt_base64=data['psbt_base64'],
            network=data.get('network', 'signet'),
            broadcast=data.get('broadcast', False)
        )
        
        return jsonify({
            'message': 'Transaction finalized successfully',
            'transaction': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Transaction finalization error: {str(e)}")
        return jsonify({'error': f'Transaction finalization failed: {str(e)}'}), 500


@bp.route('/estimate-fee', methods=['POST'])
@jwt_required()
@limiter.limit("100 per hour")
def estimate_fee():
    """Estimer les frais pour un PSBT"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not request.json or 'psbt_base64' not in request.json:
        return jsonify({'error': 'PSBT required'}), 400
    
    psbt_base64 = request.json['psbt_base64']
    fee_rates = request.json.get('fee_rates', [1, 10, 20])  # sat/vB
    
    try:
        # Obtenir les infos du PSBT pour estimer la taille
        psbt_info = securedeal_core.get_psbt_info(psbt_base64=psbt_base64)
        
        estimated_size = psbt_info.get('estimated_size_bytes', 250)  # Taille par défaut
        
        fee_estimates = {}
        for rate in fee_rates:
            fee_estimates[f"{rate}_sat_per_vb"] = {
                'fee_rate': rate,
                'estimated_fee_sats': estimated_size * rate,
                'estimated_fee_btc': (estimated_size * rate) / 100_000_000
            }
        
        return jsonify({
            'message': 'Fee estimation completed',
            'psbt_info': psbt_info,
            'fee_estimates': fee_estimates
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Fee estimation error: {str(e)}")
        return jsonify({'error': f'Fee estimation failed: {str(e)}'}), 500


@bp.route('/networks', methods=['GET'])
@jwt_required()
def get_supported_networks():
    """Obtenir les réseaux Bitcoin supportés"""
    
    networks = {
        'mainnet': {
            'name': 'Bitcoin Mainnet',
            'description': 'Production Bitcoin network',
            'explorer': 'https://blockstream.info'
        },
        'testnet': {
            'name': 'Bitcoin Testnet',
            'description': 'Bitcoin test network',
            'explorer': 'https://blockstream.info/testnet'
        },
        'signet': {
            'name': 'Bitcoin Signet',
            'description': 'Bitcoin signing test network',
            'explorer': 'https://blockstream.info/signet'
        },
        'regtest': {
            'name': 'Bitcoin Regtest',
            'description': 'Local development network',
            'explorer': 'http://localhost:3000'
        }
    }
    
    return jsonify({
        'message': 'Supported networks',
        'networks': networks,
        'default': 'signet'
    }), 200
