#!/usr/bin/env python3
"""
Test Backend Integration
Quick test to verify smart contract service and notification system
"""

import sys
import os
import requests
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_blockchain_service():
    """Test blockchain service endpoints"""
    print("🔗 Testing Blockchain Service...")
    
    try:
        # Test root endpoint
        response = requests.get("http://localhost:3000/")
        if response.status_code == 200:
            print("  ✅ Root endpoint working")
        else:
            print(f"  ❌ Root endpoint failed: {response.status_code}")
            return False
        
        # Test wallet creation
        response = requests.get("http://localhost:3000/create_wallet")
        if response.status_code == 200:
            wallet_data = response.json()
            print("  ✅ Wallet creation working")
            print(f"      Generated address: {wallet_data.get('address', 'N/A')}")
        else:
            print(f"  ❌ Wallet creation failed: {response.status_code}")
            return False
        
        # Test smart contract creation
        test_keys = [
            "02a1b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3",
            "03b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
        ]
        
        payload = {
            "public_keys": test_keys,
            "threshold": 2,
            "network": "signet"
        }
        
        response = requests.post(
            "http://localhost:3000/create_smart_contract",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            contract_data = response.json()
            print("  ✅ Smart contract creation working")
            print(f"      Contract address: {contract_data.get('address', 'N/A')}")
            print(f"      Threshold: {contract_data.get('threshold', 'N/A')}")
            return True
        else:
            print(f"  ❌ Smart contract creation failed: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Blockchain service test failed: {e}")
        return False

def test_notification_service():
    """Test notification service"""
    print("\n📱 Testing Notification Service...")
    
    try:
        from app.services.notification_service import notification_service
        
        # Test notification creation
        notification = notification_service.create_notification(
            user_id=1,
            notification_type='test',
            title='Test Notification',
            message='This is a test notification.',
            contract_id=None,
            data={'test': True}
        )
        
        if notification:
            print("  ✅ Notification creation working")
            print(f"      Notification ID: {notification.get('id', 'N/A')}")
        else:
            print("  ❌ Notification creation failed")
            return False
        
        # Test getting notifications
        notifications = notification_service.get_user_notifications(1)
        if notifications:
            print(f"  ✅ Getting notifications working ({len(notifications)} found)")
        else:
            print("  ⚠️  No notifications found (this is okay)")
        
        # Test unread count
        count = notification_service.get_unread_count(1)
        print(f"  ✅ Unread count working: {count}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Notification service test failed: {e}")
        return False

def test_smart_contract_service():
    """Test smart contract service"""
    print("\n🔐 Testing Smart Contract Service...")
    
    try:
        from app.services.smart_contract_service import smart_contract_service
        
        # Test service health
        health = smart_contract_service.check_service_health()
        if health:
            print("  ✅ Smart contract service health check passed")
        else:
            print("  ❌ Smart contract service health check failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Smart contract service test failed: {e}")
        return False

def test_database_connection():
    """Test database connection and models"""
    print("\n📊 Testing Database Connection...")
    
    try:
        from app import create_app, db
        from app.models.user import User
        from app.models.contract import Contract
        
        app = create_app()
        with app.app_context():
            # Test user query
            users = User.query.limit(5).all()
            print(f"  ✅ Database connection working ({len(users)} users found)")
            
            # Test contract query
            contracts = Contract.query.limit(5).all()
            print(f"  ✅ Contract model working ({len(contracts)} contracts found)")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 SecureDeal Backend Integration Test")
    print("=====================================")
    
    tests = [
        ("Blockchain Service", test_blockchain_service),
        ("Database Connection", test_database_connection),
        ("Notification Service", test_notification_service),
        ("Smart Contract Service", test_smart_contract_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Results Summary:")
    print("========================")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Backend integration is ready.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
