"""
Notification Service
Handles all notification creation and management for the application
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
try:
    from flask import current_app, render_template
    from flask_mail import Message
    from app import db, mail
except ImportError:
    # Handle import error for testing
    current_app = None
    db = None
    mail = None
from app.models.user import User
from app.models.contract import Contract
from app.models.invitation import Invitation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications across the application"""
    
    def __init__(self):
        self.notifications = []  # In-memory storage for demo
    
    def create_notification(self, user_id: int, notification_type: str, title: str, 
                          message: str, contract_id: Optional[str] = None, data: Optional[Dict] = None) -> Optional[Dict]:
        """Create a new notification for a user"""
        try:
            notification = {
                'id': len(self.notifications) + 1,
                'user_id': user_id,
                'type': notification_type,
                'title': title,
                'message': message,
                'contract_id': contract_id,
                'data': data or {},
                'read': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.notifications.append(notification)
            
            logger.info(f"Created notification for user {user_id}: {title}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get notifications for a specific user"""
        user_notifications = [
            n for n in self.notifications 
            if n['user_id'] == user_id
        ]
        
        # Sort by creation date (newest first)
        user_notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        return user_notifications[:limit]
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        try:
            for notification in self.notifications:
                if notification['id'] == notification_id and notification['user_id'] == user_id:
                    notification['read'] = True
                    notification['updated_at'] = datetime.utcnow().isoformat()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        return len([
            n for n in self.notifications 
            if n['user_id'] == user_id and not n['read']
        ])
    
    def create_invitation_notification(self, invitation: Invitation, contract: Contract):
        """Create notification when a user is invited to sign a contract"""
        try:
            # Find the invited user by email
            invited_user = User.query.filter_by(email=invitation.recipient_email).first()
            if not invited_user:
                logger.warning(f"User not found for email: {invitation.recipient_email}")
                return
            
            title = f"New Contract Invitation: {contract.title}"
            message = f"You've been invited to review and sign a contract. Please review the details and provide your signature."
            
            self.create_notification(
                user_id=invited_user.id,
                notification_type='invitation',
                title=title,
                message=message,
                contract_id=contract.public_id,
                data={
                    'invitation_id': invitation.public_id,
                    'contract_title': contract.title,
                    'contract_type': contract.contract_type.value,
                    'amount_sats': contract.amount_sats,
                    'creator_name': contract.creator.full_name if contract.creator else 'Unknown'
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating invitation notification: {e}")
    
    def create_signature_notification(self, contract: Contract, signer_name: str):
        """Create notification when someone signs a contract"""
        try:
            # Notify the contract creator
            creator = contract.creator
            if creator:
                title = f"Contract Signed: {contract.title}"
                message = f"{signer_name} has signed the contract. Check the contract status for more details."
                
                self.create_notification(
                    user_id=creator.id,
                    notification_type='signature',
                    title=title,
                    message=message,
                    contract_id=contract.public_id,
                    data={
                        'signer_name': signer_name,
                        'contract_title': contract.title,
                        'contract_type': contract.contract_type.value
                    }
                )
            
            # Notify other participants (optional)
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            for invitation in invitations:
                invited_user = User.query.filter_by(email=invitation.recipient_email).first()
                if invited_user and invited_user.id != creator.id:
                    title = f"Contract Update: {contract.title}"
                    message = f"{signer_name} has signed the contract. You can check the current status."
                    
                    self.create_notification(
                        user_id=invited_user.id,
                        notification_type='signature_update',
                        title=title,
                        message=message,
                        contract_id=contract.public_id,
                        data={
                            'signer_name': signer_name,
                            'contract_title': contract.title
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error creating signature notification: {e}")
    
    def create_contract_completion_notification(self, contract: Contract):
        """Create notification when all signatures are collected"""
        try:
            # Notify the contract creator
            creator = contract.creator
            if creator:
                title = f"Contract Ready: {contract.title}"
                message = f"All signatures have been collected! The smart contract is being created automatically."
                
                self.create_notification(
                    user_id=creator.id,
                    notification_type='contract_complete',
                    title=title,
                    message=message,
                    contract_id=contract.public_id,
                    data={
                        'contract_title': contract.title,
                        'contract_type': contract.contract_type.value,
                        'smart_contract_address': contract.address
                    }
                )
            
            # Notify all participants
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            for invitation in invitations:
                invited_user = User.query.filter_by(email=invitation.recipient_email).first()
                if invited_user and invited_user.id != creator.id:
                    title = f"Contract Ready: {contract.title}"
                    message = f"All signatures collected! The smart contract is being created automatically."
                    
                    self.create_notification(
                        user_id=invited_user.id,
                        notification_type='contract_complete',
                        title=title,
                        message=message,
                        contract_id=contract.public_id,
                        data={
                            'contract_title': contract.title,
                            'smart_contract_address': contract.address
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error creating contract completion notification: {e}")
    
    def create_payment_notification(self, notification_data: Dict):
        """Create notification for payment requirement"""
        try:
            # Find the user by email
            user = User.query.filter_by(email=notification_data['recipient_email']).first()
            if not user:
                logger.warning(f"User not found for email: {notification_data['recipient_email']}")
                return
            
            title = notification_data['title']
            message = notification_data['message']
            
            self.create_notification(
                user_id=user.id,
                notification_type=notification_data['type'],
                title=title,
                message=message,
                contract_id=notification_data['contract_id'],
                data={
                    'payment_link': notification_data['payment_link'],
                    'payment_address': notification_data['payment_address'],
                    'payment_amount': notification_data['payment_amount'],
                    'contract_title': notification_data.get('contract_title', 'Unknown Contract')
                }
            )
            
            logger.info(f"Payment notification created for user {user.email}")
            
        except Exception as e:
            logger.error(f"Error creating payment notification: {e}")
    
    def create_payment_completion_notification(self, notification_data: Dict):
        """Create notification when payment is completed"""
        try:
            # Find the user by email
            user = User.query.filter_by(email=notification_data['recipient_email']).first()
            if not user:
                logger.warning(f"User not found for email: {notification_data['recipient_email']}")
                return
            
            title = notification_data['title']
            message = notification_data['message']
            
            self.create_notification(
                user_id=user.id,
                notification_type=notification_data['type'],
                title=title,
                message=message,
                contract_id=notification_data['contract_id'],
                data={
                    'payment_amount': notification_data['payment_amount'],
                    'contract_title': notification_data.get('contract_title', 'Unknown Contract'),
                    'completion_date': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Payment completion notification created for user {user.email}")
            
        except Exception as e:
            logger.error(f"Error creating payment completion notification: {e}")
    
    def create_smart_contract_created_notification(self, contract: Contract):
        """Create notification when smart contract is successfully created"""
        try:
            # Notify the contract creator
            creator = contract.creator
            if creator:
                title = f"Smart Contract Created: {contract.title}"
                message = f"Your smart contract has been created successfully! Payment address: {contract.address}"
                
                self.create_notification(
                    user_id=creator.id,
                    notification_type='smart_contract_created',
                    title=title,
                    message=message,
                    contract_id=contract.public_id,
                    data={
                        'contract_title': contract.title,
                        'smart_contract_address': contract.address,
                        'payment_amount': contract.payment_amount_btc,
                        'payment_uri': contract.payment_uri
                    }
                )
            
            # Notify all participants
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            for invitation in invitations:
                invited_user = User.query.filter_by(email=invitation.recipient_email).first()
                if invited_user:
                    title = f"Smart Contract Created: {contract.title}"
                    message = f"The smart contract has been created! Address: {contract.address}"
                    
                    self.create_notification(
                        user_id=invited_user.id,
                        notification_type='smart_contract_created',
                        title=title,
                        message=message,
                        contract_id=contract.public_id,
                        data={
                            'contract_title': contract.title,
                            'smart_contract_address': contract.address
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error creating smart contract notification: {e}")
    
    def notify_all_contract_parties(self, contract_id: str, notification_type: str, data: dict):
        """Send notification to all parties involved in a contract"""
        try:
            if not current_app or not db:
                logger.warning("Flask app context not available, storing notification for later")
                return
            
            from app.models.contract import Contract
            from app.models.invitation import Invitation
            from app.models.user import User
            
            contract = Contract.query.filter_by(public_id=contract_id).first()
            if not contract:
                logger.error(f"Contract {contract_id} not found")
                return
            
            # Get contract creator
            creator = User.query.get(contract.creator_id)
            
            # Get all invited parties
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            
            # Prepare notification data
            notification_data = {
                'contract_id': contract_id,
                'contract_title': contract.title,
                **data
            }
            
            # Prepare notification content
            if notification_type == 'signature':
                title = f"Contract Signed: {contract.title}"
                message = notification_data.get('message', 'Someone signed the contract')
            elif notification_type == 'completion':
                title = f"Contract Ready: {contract.title}"
                message = notification_data.get('message', 'All signatures collected')
            elif notification_type == 'payment_completed':
                title = f"Payment Received: {contract.title}"
                message = notification_data.get('message', 'Payment completed')
            else:
                title = f"Contract Update: {contract.title}"
                message = notification_data.get('message', 'Contract update')
            
            # Notify creator
            if creator:
                self.create_notification(
                    user_id=creator.id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    contract_id=contract_id,
                    data=notification_data
                )
            
            # Notify all invited parties
            for invitation in invitations:
                invited_user = User.query.filter_by(email=invitation.recipient_email).first()
                if invited_user:
                    self.create_notification(
                        user_id=invited_user.id,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                        contract_id=contract_id,
                        data=notification_data
                    )
            
            logger.info(f"Sent {notification_type} notifications to all parties for contract {contract_id}")
            
        except Exception as e:
            logger.error(f"Error notifying contract parties: {e}")
    
    def send_invitation_email(self, invitation: 'Invitation', contract: 'Contract', sender: 'User') -> bool:
        """Send an email invitation to participate in a contract"""
        try:
            if not current_app or not mail:
                logger.error("Flask app context or mail not available for sending emails")
                return False
                
            recipient_email = invitation.recipient_email
            invitation_url = f"{current_app.config['FRONTEND_URL']}/contracts/{contract.public_id}/accept/{invitation.token}"
            
            # Create email message
            msg = Message(
                subject=f"You've been invited to a DealSure contract: {contract.title}",
                recipients=[recipient_email],
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'no-reply@dealsure.io')
            )
            
            # Prepare email content
            msg.html = render_template(
                'emails/contract_invitation.html',
                contract=contract,
                invitation=invitation,
                sender=sender,
                invitation_url=invitation_url
            )
            
            # Send the email
            mail.send(msg)
            
            logger.info(f"Sent invitation email to {recipient_email} for contract {contract.public_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            return False


# Singleton instance
notification_service = NotificationService()
