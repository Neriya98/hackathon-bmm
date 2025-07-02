"""
Notifications API endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.services.notification_service import notification_service

bp = Blueprint('notifications', __name__)


@bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for the current user"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        limit = request.args.get('limit', 50, type=int)
        notifications = notification_service.get_user_notifications(user.id, limit)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total': len(notifications)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': f'Failed to get notifications: {str(e)}'}), 500


@bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        success = notification_service.mark_as_read(notification_id, user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Notification not found or access denied'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Mark notification read error: {str(e)}")
        return jsonify({'error': f'Failed to mark notification as read: {str(e)}'}), 500


@bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get count of unread notifications for the current user"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        count = notification_service.get_unread_count(user.id)
        
        return jsonify({
            'success': True,
            'unread_count': count
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get unread count error: {str(e)}")
        return jsonify({'error': f'Failed to get unread count: {str(e)}'}), 500


@bp.route('/test', methods=['POST'])
@jwt_required()
def create_test_notification():
    """Create a test notification (for development)"""
    
    user_id = get_jwt_identity()
    user = User.find_by_public_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        notification = notification_service.create_notification(
            user_id=user.id,
            notification_type='test',
            title='Test Notification',
            message='This is a test notification for development purposes.',
            contract_id=None,
            data={'test': True}
        )
        
        return jsonify({
            'success': True,
            'notification': notification
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Create test notification error: {str(e)}")
        return jsonify({'error': f'Failed to create test notification: {str(e)}'}), 500
