#!/usr/bin/env python3
"""
Database Initialization Script for SecureDeal
This script sets up the database with proper tables and sample data for testing
"""

import os
import sys
from datetime import datetime
from app import create_app, db
from app.models.user import User
from app.models.contract import Contract, ContractType, ContractStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.signature import Signature

def init_database():
    """Initialize database with tables and sample data"""
    
    print("🔄 Initializing SecureDeal database...")
    
    # Create application
    app = create_app()
    
    with app.app_context():
        # Drop all tables (fresh start)
        print("📝 Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("🏗️  Creating database tables...")
        db.create_all()
        
        # Create sample users for testing
        print("👥 Creating sample users...")
        
        # Sample Notaire user
        notaire = User(
            email="notaire@test.com",
            password="test123",
            public_id="notaire-001",
            user_type="notaire",
            bitcoin_public_key="02a1b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3",
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Sample regular user
        user1 = User(
            email="user@test.com",
            password="test123",
            public_id="user-001",
            user_type="user",
            bitcoin_public_key="03b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4",
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Another sample user
        user2 = User(
            email="seller@test.com",
            password="test123",
            public_id="user-002",
            user_type="user",
            bitcoin_public_key="04c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5",
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Add users to session
        db.session.add(notaire)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        print("✅ Sample users created:")
        print(f"   📧 Notaire: notaire@test.com (password: test123)")
        print(f"   📧 User 1: user@test.com (password: test123)")
        print(f"   📧 User 2: seller@test.com (password: test123)")
        
        # Create sample contracts
        print("📄 Creating sample contracts...")
        
        sample_contract = Contract(
            title="Sample Property Sale",
            contract_type=ContractType.ESCROW,  # Using a valid enum value
            amount_sats=150000000,  # 1.5 BTC in satoshis
            creator_id=notaire.id,
            public_id="contract-001",
            status=ContractStatus.DRAFT,
            description="Sample property sale contract for testing purposes"
        )
        
        db.session.add(sample_contract)
        db.session.commit()
        
        print("✅ Sample contract created:")
        print(f"   📋 Title: {sample_contract.title}")
        print(f"   🆔 ID: {sample_contract.public_id}")
        
        # Create sample invitation
        print("✉️  Creating sample invitation...")
        
        sample_invitation = Invitation(
            contract_id=sample_contract.id,
            sender_id=notaire.id,
            public_id="invitation-001",
            recipient_email="user@test.com",
            status=InvitationStatus.SENT,
            invitation_token="sample-token-001"
        )
        
        db.session.add(sample_invitation)
        db.session.commit()
        
        print("✅ Sample invitation created:")
        print(f"   📧 Invitee: {sample_invitation.recipient_email}")
        print(f"   🆔 Token: {sample_invitation.invitation_token}")
        print(f"   🔗 DIRECT LINK: http://localhost:5000/invitations/{sample_invitation.invitation_token}")
        print(f"   📋 USER CAN IMMEDIATELY SIGN AT THIS LINK!")
        
        print("🎉 Database initialization completed successfully!")
        print("\n📊 Database Summary:")
        print(f"   👥 Users: {User.query.count()}")
        print(f"   📄 Contracts: {Contract.query.count()}")
        print(f"   ✉️  Invitations: {Invitation.query.count()}")
        print(f"   ✍️  Signatures: {Signature.query.count()}")
        
        print("\n🚀 You can now start the application with:")
        print("   python run.py")
        print("\n🔐 Test login credentials:")
        print("   Notaire: notaire@test.com / test123")
        print("   User: user@test.com / test123")
        print("   Seller: seller@test.com / test123")

if __name__ == "__main__":
    init_database()
