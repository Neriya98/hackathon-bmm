"""
Smart Contract Integration Service
Connects Flask app with Rust blockchain service for automatic contract execution
"""

import requests
import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging
from app.models.contract import Contract
from app.models.signature import Signature
from app.models.user import User
from app.models.invitation import Invitation
from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartContractService:
    """Service for managing smart contract creation and execution"""
    
    def __init__(self, blockchain_service_url: str = "http://localhost:3000"):
        self.blockchain_service_url = blockchain_service_url
        self.session = requests.Session()
        self.session.timeout = 30
    
    def check_service_health(self) -> bool:
        """Check if blockchain service is running"""
        try:
            response = self.session.get(f"{self.blockchain_service_url}/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Blockchain service health check failed: {e}")
            return False
    
    def create_smart_contract(self, contract_id: str) -> Optional[Dict]:
        """Create smart contract when all signatures are collected"""
        try:
            # Get contract and all signatures
            contract = Contract.query.filter_by(public_id=contract_id).first()
            if not contract:
                logger.error(f"Contract {contract_id} not found")
                return None
            
            # Get all signatures for this contract
            signatures = Signature.query.filter_by(contract_id=contract.id).all()
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            
            # Check if all required signatures are collected
            if len(signatures) < len(invitations):
                logger.info(f"Contract {contract_id}: {len(signatures)}/{len(invitations)} signatures collected")
                return None
            
            # Extract public keys from signatures
            public_keys = []
            for signature in signatures:
                if signature.bitcoin_public_key:
                    public_keys.append(signature.bitcoin_public_key)
            
            # For savings contracts, we only need one key (self-signed)
            if contract.contract_type.value == 'savings':
                if len(public_keys) < 1:
                    logger.error(f"No public key for savings contract {contract_id}")
                    return None
                
                # Use the same key twice to maintain compatibility with the smart contract service
                if len(public_keys) == 1:
                    public_keys = [public_keys[0], public_keys[0]]
            else:
                # For other contract types, we need at least 2 keys
                if len(public_keys) < 2:
                    logger.error(f"Not enough public keys for contract {contract_id}")
                    return None
            
            # Create smart contract payload
            payload = {
                "public_keys": public_keys,
                "threshold": len(public_keys),  # All signatures required
                "network": "signet"  # Using signet for testing
            }
            
            # Call blockchain service
            response = self.session.post(
                f"{self.blockchain_service_url}/create_smart_contract",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                smart_contract_data = response.json()
                
                # Update contract with smart contract info
                contract.script_pubkey = smart_contract_data.get('miniscript')
                contract.address = smart_contract_data.get('address')
                contract.policy = smart_contract_data.get('policy')
                contract.status = 'active'
                
                # Store smart contract details
                contract.smart_contract_data = smart_contract_data
                
                db.session.commit()
                
                logger.info(f"Smart contract created for contract {contract_id}: {smart_contract_data.get('address')}")
                
                # Notify all parties about smart contract creation
                self.notify_smart_contract_creation(contract)
                
                # Generate payment link
                payment_link = self.generate_payment_link(contract, smart_contract_data)
                
                # Send payment link to payer
                self.send_payment_link(contract, payment_link)
                
                # Start monitoring for payment
                self.start_payment_monitoring(contract)
                
                return smart_contract_data
            else:
                logger.error(f"Failed to create smart contract: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating smart contract for {contract_id}: {e}")
            return None
    
    def generate_payment_link(self, contract: Contract, smart_contract_data: Dict) -> str:
        """Generate payment link for the contract"""
        address = smart_contract_data.get('address')
        amount_btc = contract.amount_sats / 100_000_000 if contract.amount_sats else 0.001
        
        # Generate Bitcoin payment URI
        payment_uri = f"bitcoin:{address}?amount={amount_btc}&label=Contract%20Payment%20{contract.public_id}"
        
        # Store payment info
        contract.payment_address = address
        contract.payment_amount_btc = amount_btc
        contract.payment_uri = payment_uri
        
        db.session.commit()
        
        return payment_uri
    
    def send_payment_link(self, contract: Contract, payment_link: str):
        """Send payment link to the person responsible for payment"""
        try:
            # For demo purposes, we'll use the notification system
            from app.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Determine who should pay (for now, assume the first non-creator participant)
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            payer_invitation = invitations[0] if invitations else None
            
            if payer_invitation:
                notification_data = {
                    'type': 'payment_required',
                    'title': 'Payment Required for Contract',
                    'message': f'Smart contract is ready. Please send payment to complete the contract.',
                    'contract_id': contract.public_id,
                    'payment_link': payment_link,
                    'payment_address': contract.payment_address,
                    'payment_amount': contract.payment_amount_btc,
                    'recipient_email': payer_invitation.recipient_email
                }
                
                notification_service.create_payment_notification(notification_data)
                logger.info(f"Payment link sent for contract {contract.public_id}")
        
        except Exception as e:
            logger.error(f"Error sending payment link: {e}")
    
    def start_payment_monitoring(self, contract: Contract):
        """Start monitoring for payment to the smart contract address"""
        if not contract.payment_address:
            return
        
        # For now, we'll simulate payment monitoring
        # In production, you'd use webhooks or periodic polling
        logger.info(f"Started payment monitoring for address: {contract.payment_address}")
        
        # Store monitoring info
        contract.payment_monitoring_started = datetime.utcnow()
        db.session.commit()
    
    def check_payment_status(self, contract_id: str) -> Optional[Dict]:
        """Check if payment has been made to the contract address"""
        try:
            contract = Contract.query.filter_by(public_id=contract_id).first()
            if not contract or not contract.payment_address:
                return None
            
            # Check balance using blockchain service
            payload = {
                "address": contract.payment_address,
                "network": "signet"
            }
            
            response = self.session.post(
                f"{self.blockchain_service_url}/check_balance",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                balance_data = response.json()
                current_balance = balance_data.get('total_balance', 0)
                
                # Check if payment received
                expected_amount_sats = int((contract.payment_amount_btc or 0) * 100_000_000)
                
                if current_balance >= expected_amount_sats:
                    # Payment received!
                    if contract.status != 'completed':
                        contract.status = 'completed'
                        contract.payment_received = True
                        contract.payment_received_at = datetime.utcnow()
                        contract.actual_payment_amount = current_balance
                        
                        db.session.commit()
                        
                        # Notify all parties
                        self.notify_payment_completion(contract)
                        
                        logger.info(f"Payment completed for contract {contract_id}: {current_balance} sats")
                
                return {
                    'contract_id': contract_id,
                    'address': contract.payment_address,
                    'expected_amount': expected_amount_sats,
                    'current_balance': current_balance,
                    'payment_received': current_balance >= expected_amount_sats,
                    'balance_data': balance_data
                }
            
        except Exception as e:
            logger.error(f"Error checking payment status for {contract_id}: {e}")
            return None
    
    def notify_payment_completion(self, contract: Contract):
        """Notify all parties when payment is completed"""
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Get all parties involved
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            creator = User.query.get(contract.creator_id)
            
            # Notify contract creator
            if creator:
                notification_data = {
                    'type': 'payment_completed',
                    'title': 'Contract Payment Received',
                    'message': f'Payment has been received for contract "{contract.title}". The contract is now complete.',
                    'contract_id': contract.public_id,
                    'payment_amount': contract.actual_payment_amount,
                    'recipient_email': creator.email
                }
                notification_service.create_payment_completion_notification(notification_data)
            
            # Notify all invited parties
            for invitation in invitations:
                notification_data = {
                    'type': 'payment_completed',
                    'title': 'Contract Payment Received',
                    'message': f'Payment has been received for contract "{contract.title}". The contract is now complete.',
                    'contract_id': contract.public_id,
                    'payment_amount': contract.actual_payment_amount,
                    'recipient_email': invitation.recipient_email
                }
                notification_service.create_payment_completion_notification(notification_data)
            
            logger.info(f"Payment completion notifications sent for contract {contract.public_id}")
            
        except Exception as e:
            logger.error(f"Error sending payment completion notifications: {e}")
    
    def notify_smart_contract_creation(self, contract: Contract):
        """Notify all parties when smart contract is created"""
        try:
            from app.services.notification_service import notification_service
            notification_service.create_smart_contract_created_notification(contract)
        except Exception as e:
            logger.error(f"Error notifying smart contract creation: {e}")


class ContractSignatureMonitor:
    """Monitor contract signatures and trigger smart contract creation"""
    
    def __init__(self):
        self.smart_contract_service = SmartContractService()
    
    def check_signature_completion(self, contract_id: str):
        """Check if all signatures are completed and trigger smart contract creation"""
        try:
            contract = Contract.query.filter_by(public_id=contract_id).first()
            if not contract:
                return False
            
            signatures = Signature.query.filter_by(contract_id=contract.id).all()
            invitations = Invitation.query.filter_by(contract_id=contract.id).all()
            
            # Check if all invitations have been signed
            signed_invitations = 0
            for invitation in invitations:
                signature_exists = any(
                    sig.signer_email == invitation.recipient_email 
                    for sig in signatures
                )
                if signature_exists:
                    signed_invitations += 1
            
            if signed_invitations >= len(invitations) and len(invitations) > 0:
                logger.info(f"All signatures completed for contract {contract_id}")
                
                # Notify all parties about contract completion
                self.notify_contract_completion(contract)
                
                # Create smart contract
                smart_contract_data = self.smart_contract_service.create_smart_contract(contract_id)
                
                if smart_contract_data:
                    logger.info(f"Smart contract creation initiated for {contract_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking signature completion: {e}")
            return False
        
    def notify_contract_completion(self, contract: Contract):
        """Notify all parties when contract is completed"""
        try:
            from app.services.notification_service import notification_service
            notification_service.create_contract_completion_notification(contract)
        except Exception as e:
            logger.error(f"Error notifying contract completion: {e}")


# Singleton instances
smart_contract_service = SmartContractService()
signature_monitor = ContractSignatureMonitor()
