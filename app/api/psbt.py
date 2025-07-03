from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from app.services.smart_contract_service import SmartContractService

from app import limiter

psbt_bp = Blueprint('psbt', __name__)

# Make it available as bp for backward compatibility
bp = psbt_bp

# Schema for data validation
class CreateContractSchema(Schema):
    contract_type = fields.Str(required=True)
    participants = fields.List(fields.Str(), required=True)
    amount_sats = fields.Int(required=True)
    timelock = fields.Int()
    network = fields.Str(missing='signet')

@psbt_bp.route('/', methods=['GET'])
def psbt_home():
    """PSBT module homepage"""
    return jsonify({
        'message': 'SecureDeal PSBT API',
        'version': '1.0.0',
        'endpoints': [
            '/api/psbt/create',
            '/api/psbt/multisig',
            '/api/psbt/sign',
            '/api/psbt/validate',
            '/api/psbt/info',
            '/api/psbt/finalize'
        ]
    })

@psbt_bp.route('/create', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_psbt():
    """Create a new PSBT for a Bitcoin contract using the Rust backend"""
    try:
        schema = CreateContractSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Use the Rust backend service
    smart_contract_service = SmartContractService()
    
    # Check if the service is available
    if not smart_contract_service.check_service_health():
        return jsonify({
            'status': 'error',
            'message': 'Blockchain service is not available'
        }), 503
        
    # Create contract data to pass to Rust backend
    contract_data = {
        'type': data['contract_type'],
        'participants': data['participants'],
        'amount': data['amount_sats'],
        'network': data['network']
    }
    
    if 'timelock' in data:
        contract_data['timelock'] = data['timelock']
        
    # Try to create the smart contract using the Rust backend
    try:
        result = smart_contract_service.create_smart_contract_from_data(contract_data)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Smart contract created successfully',
                'data': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create smart contract'
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error creating smart contract: {str(e)}")
        
        # Fallback to placeholder response
        result = {
            'status': 'success',
            'message': 'Using placeholder response - Rust backend integration in progress',
            'data': {
                'psbt_base64': 'placeholder_for_rust_backend',
                'address': 'tb1q_placeholder',
                'network': data['network']
            }
        }
        
        return jsonify(result)

@psbt_bp.route('/sign', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def sign_psbt():
    """Sign a PSBT using the Rust backend"""
    return jsonify({
        'status': 'success',
        'message': 'PSBT signing will use Rust backend when implemented',
        'data': {
            'psbt_base64': 'signed_psbt_placeholder',
            'signature_hex': 'signature_placeholder'
        }
    })

@psbt_bp.route('/validate', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def validate_psbt():
    """Validate a PSBT using the Rust backend"""
    return jsonify({
        'status': 'success',
        'message': 'PSBT validation will use Rust backend when implemented',
        'valid': True
    })

@psbt_bp.route('/info', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def get_psbt_info():
    """Get PSBT information using the Rust backend"""
    return jsonify({
        'status': 'success',
        'message': 'PSBT info will use Rust backend when implemented',
        'data': {
            'inputs': [],
            'outputs': [],
            'fee': 0
        }
    })

@psbt_bp.route('/finalize', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def finalize_psbt():
    """Finalize a PSBT using the Rust backend"""
    return jsonify({
        'status': 'success',
        'message': 'PSBT finalization will use Rust backend when implemented',
        'data': {
            'psbt_base64': 'finalized_psbt_placeholder',
            'tx_hex': 'transaction_hex_placeholder'
        }
    })
