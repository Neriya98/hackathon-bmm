from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models.invitation import Invitation
from app.models.user import User

bp = Blueprint('invitations_routes', __name__)

@bp.route('/invitations/<token>')
def accept_invitation(token):
    """Page for accepting an invitation"""
    invitation = Invitation.find_by_token(token)
    
    if not invitation:
        return render_template('invitations/invalid.html'), 404
    
    if invitation.is_expired():
        return render_template('invitations/expired.html', invitation=invitation), 410
    
    if invitation.status != 'sent':
        return render_template('invitations/already_responded.html', invitation=invitation)
    
    # Check if user is logged in
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

# API endpoints
@bp.route('/api/invitations', methods=['POST'])
@jwt_required()
def api_create_invitation():
    """Create a new invitation"""
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        invitation = Invitation(
            contract_id=data.get('contract_id'),
            sender_id=user.id,
            recipient_email=data.get('email'),
            role=data.get('role', 'signer'),
            message=data.get('message', ''),
            status='sent'
        )
        
        invitation.save()
        return jsonify({'message': 'Invitation created', 'invitation': invitation.to_dict()}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/api/invitations/<invitation_id>', methods=['GET'])
def api_get_invitation(invitation_id):
    """Get invitation details"""
    invitation = Invitation.find_by_public_id(invitation_id)
    
    if not invitation:
        return jsonify({'error': 'Invitation not found'}), 404
    
    return jsonify({'invitation': invitation.to_dict()}), 200

@bp.route('/api/invitations/<invitation_id>/accept', methods=['POST'])
def api_accept_invitation(invitation_id):
    """Accept an invitation"""
    invitation = Invitation.find_by_public_id(invitation_id)
    
    if not invitation:
        return jsonify({'error': 'Invitation not found'}), 404
    
    if invitation.status != 'sent':
        return jsonify({'error': 'Invitation already processed'}), 400
    
    invitation.status = 'accepted'
    invitation.save()
    
    return jsonify({'message': 'Invitation accepted', 'invitation': invitation.to_dict()}), 200

@bp.route('/api/invitations/<invitation_id>/decline', methods=['POST'])
def api_decline_invitation(invitation_id):
    """Decline an invitation"""
    invitation = Invitation.find_by_public_id(invitation_id)
    
    if not invitation:
        return jsonify({'error': 'Invitation not found'}), 404
    
    if invitation.status != 'sent':
        return jsonify({'error': 'Invitation already processed'}), 400
    
    invitation.status = 'declined'
    invitation.save()
    
    return jsonify({'message': 'Invitation declined', 'invitation': invitation.to_dict()}), 200
