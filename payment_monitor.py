#!/usr/bin/env python3
"""
Payment Monitor
Continuously monitors contract payments and notifies parties when payments are received
"""

import time
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.contract import Contract, ContractStatus
from app.services.smart_contract_service import smart_contract_service
from app.services.notification_service import notification_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('payment_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PaymentMonitor:
    """Monitor payments for all active contracts"""
    
    def __init__(self, app):
        self.app = app
        self.check_interval = 30  # Check every 30 seconds
        self.running = False
    
    def start(self):
        """Start the payment monitoring loop"""
        logger.info("Starting payment monitor...")
        self.running = True
        
        with self.app.app_context():
            try:
                # Check blockchain service health
                if not smart_contract_service.check_service_health():
                    logger.error("Blockchain service is not available. Please start it first.")
                    return
                
                logger.info("Blockchain service is healthy. Starting monitoring loop...")
                
                while self.running:
                    self.check_all_contracts()
                    time.sleep(self.check_interval)
                    
            except KeyboardInterrupt:
                logger.info("Payment monitor stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Payment monitor error: {e}")
                self.running = False
    
    def stop(self):
        """Stop the payment monitoring loop"""
        logger.info("Stopping payment monitor...")
        self.running = False
    
    def check_all_contracts(self):
        """Check payment status for all active contracts"""
        try:
            # Get all contracts that have payment addresses but haven't been paid yet
            contracts = Contract.query.filter(
                Contract.payment_address.isnot(None),
                Contract.payment_received == False,
                Contract.status == 'active'
            ).all()
            
            logger.info(f"Checking {len(contracts)} contracts for payments")
            
            for contract in contracts:
                self.check_contract_payment(contract)
                
        except Exception as e:
            logger.error(f"Error checking contracts: {e}")
    
    def check_contract_payment(self, contract):
        """Check payment status for a specific contract"""
        try:
            logger.info(f"Checking payment for contract {contract.public_id}")
            
            payment_status = smart_contract_service.check_payment_status(contract.public_id)
            
            if payment_status and payment_status.get('payment_received'):
                logger.info(f"Payment received for contract {contract.public_id}!")
                
                # Update contract status to paid
                contract.payment_received = True
                # Update the contract status from "await payment" to "paid"
                contract.status = ContractStatus.PAID
                db.session.commit()
                
                # Notify all parties
                notification_service.notify_all_contract_parties(
                    contract.public_id,
                    'payment_completed',
                    {
                        'message': f"Payment of {payment_status.get('current_balance', 0)} sats received!",
                        'payment_amount': payment_status.get('current_balance', 0)
                    }
                )
                
                logger.info(f"Payment completion notifications sent for contract {contract.public_id}")
            else:
                logger.debug(f"No payment yet for contract {contract.public_id}")
                
        except Exception as e:
            logger.error(f"Error checking payment for contract {contract.public_id}: {e}")


def main():
    """Main function to run the payment monitor"""
    
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        # Show status and exit
        app = create_app()
        
        with app.app_context():
            try:
                # Count contracts being monitored
                monitored_contracts = Contract.query.filter(
                    Contract.payment_address.isnot(None),
                    Contract.payment_received == False,
                    Contract.status == 'active'
                ).count()
                
                # Count completed payments
                completed_payments = Contract.query.filter(
                    Contract.payment_received == True
                ).count()
                
                print("Payment Monitor Status:")
                print(f"  Monitored Contracts: {monitored_contracts}")
                print(f"  Completed Payments: {completed_payments}")
                print(f"  Blockchain Service: {'Healthy' if smart_contract_service.check_service_health() else 'Unhealthy'}")
                
            except Exception as e:
                print(f"  Error: {e}")
        
        return
    
    # Start the monitor
    logger.info("Initializing payment monitor...")
    
    app = create_app()
    monitor = PaymentMonitor(app)
    monitor.start()


if __name__ == '__main__':
    main()
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all active contracts with payment addresses
            active_contracts = Contract.query.filter(
                Contract.status == ContractStatus.ACTIVE,
                Contract.payment_address.isnot(None),
                Contract.payment_received == False
            ).all()
            
            logger.info(f"Monitoring {len(active_contracts)} active contracts for payments")
            
            for contract in active_contracts:
                try:
                    logger.info(f"Checking payment for contract {contract.public_id}")
                    
                    # Check payment status
                    payment_status = smart_contract_service.check_payment_status(contract.public_id)
                    
                    if payment_status and payment_status.get('payment_received'):
                        logger.info(f"Payment received for contract {contract.public_id}!")
                        
                        # Payment notifications are handled within the service
                        # No additional action needed here
                        
                    else:
                        logger.debug(f"No payment yet for contract {contract.public_id}")
                
                except Exception as e:
                    logger.error(f"Error checking payment for contract {contract.public_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error during payment monitoring: {e}")


def monitor_blockchain_service():
    """Check if blockchain service is running"""
    
    try:
        if smart_contract_service.check_service_health():
            logger.info("Blockchain service is running")
            return True
        else:
            logger.warning("Blockchain service is not responding")
            return False
    except Exception as e:
        logger.error(f"Error checking blockchain service: {e}")
        return False


def main():
    """Main monitoring loop"""
    
    logger.info("Starting payment monitoring service...")
    
    # Check if blockchain service is available
    if not monitor_blockchain_service():
        logger.error("Blockchain service is not available. Exiting.")
        sys.exit(1)
    
    # Monitoring loop
    check_interval = 30  # seconds
    
    try:
        while True:
            logger.info("Running payment monitoring cycle...")
            
            # Monitor payments
            monitor_payments()
            
            # Check blockchain service health periodically
            if not monitor_blockchain_service():
                logger.warning("Blockchain service health check failed")
            
            logger.info(f"Monitoring cycle complete. Sleeping for {check_interval} seconds...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("Payment monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in monitoring service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
