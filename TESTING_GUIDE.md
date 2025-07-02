# SecureDeal Testing Guide

## Overview
This guide provides comprehensive strategies for testing the SecureDeal application locally with two users to simulate the complete Bitcoin contract workflow.

## Quick Start

### Method 1: Automated Setup (Recommended)
```bash
# Start all services and setup testing environment
./test_local.sh start

# Check service status
./test_local.sh status

# Stop all services when done
./test_local.sh stop
```

### Method 2: Manual Setup
```bash
# 1. Initialize database
python3 init_db.py

# 2. Start blockchain service
cd smart-contract-to-implement/blockchain_services
cargo run --release &
cd ../..

# 3. Start Flask app
python3 run.py &

# 4. Start payment monitor
python3 payment_monitor.py &
```

## Testing Strategies

### Strategy 1: Browser Profiles (Recommended)
This is the easiest and most reliable method for local testing.

**Chrome/Chromium:**
```bash
# Create profile directories
mkdir -p browser_profiles/user1 browser_profiles/user2

# Launch Chrome with different profiles
google-chrome --user-data-dir="$(pwd)/browser_profiles/user1" --profile-directory="User1" http://localhost:5000 &
google-chrome --user-data-dir="$(pwd)/browser_profiles/user2" --profile-directory="User2" http://localhost:5000 &
```

**Firefox:**
```bash
# Create Firefox profiles
firefox -CreateProfile "user1 $(pwd)/browser_profiles/firefox_user1" -no-remote
firefox -CreateProfile "user2 $(pwd)/browser_profiles/firefox_user2" -no-remote

# Launch with different profiles
firefox -P user1 -no-remote http://localhost:5000 &
firefox -P user2 -no-remote http://localhost:5000 &
```

### Strategy 2: Incognito/Private Browsing
- Open http://localhost:5000 in a regular browser window
- Open http://localhost:5000 in an incognito/private window
- Each window will have separate session data

### Strategy 3: Different Browsers
- Use Chrome for User 1: http://localhost:5000
- Use Firefox for User 2: http://localhost:5000
- Each browser maintains separate sessions

### Strategy 4: Docker Containers (Advanced)
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.test.yml up

# Access via VNC for browser testing
# User 1 Browser: vnc://localhost:7900 (password: secret)
# User 2 Browser: vnc://localhost:7901 (password: secret)
```

## Test Users

The application comes with pre-configured test users:

### User 1 - Notaire/Contract Creator
- **Email:** `notaire@test.com`
- **Password:** `test123`
- **Type:** `notaire` (can create all contract types)
- **Bitcoin Public Key:** `02a1b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4`

### User 2 - Regular User/Buyer
- **Email:** `user@test.com`
- **Password:** `test123`
- **Type:** `user` (can create sale/rental contracts only)
- **Bitcoin Public Key:** `03b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5`

### User 3 - Another User/Seller
- **Email:** `seller@test.com`
- **Password:** `test123`
- **Type:** `user`
- **Bitcoin Public Key:** `04c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6`

## Complete Testing Workflow

### Phase 1: Initial Setup and Login
1. **Open two browser instances** using your preferred method above
2. **Browser 1:** Navigate to http://localhost:5000 and login as `notaire@test.com`
3. **Browser 2:** Navigate to http://localhost:5000 and login as `user@test.com`
4. **Verify:** Both users can access their respective dashboards

### Phase 2: Contract Creation
1. **User 1 (Notaire):**
   - Go to Dashboard → "Create New Contract"
   - Select "Sale Contract" or "Rental Contract"
   - Fill in contract details:
     - Title: "Test Property Sale"
     - Description: "Test contract for demo"
     - Property details (address, price, etc.)
     - Amount: Set a test amount (e.g., 0.001 BTC)
   - Click "Generate Preview"
   - Review the generated contract
   - Click "Save Contract"

### Phase 3: Invitation and Notification
1. **User 1 (Notaire):**
   - Click "Invite Participants"
   - Enter User 2's email: `user@test.com`
   - Add invitation message
   - Click "Send Invitation"
   - **Expected:** Invitation sent notification

2. **User 2 (Buyer):**
   - Check notifications (bell icon in navbar)
   - **Expected:** New invitation notification
   - Click on the invitation or go to Dashboard
   - **Expected:** See pending invitation in dashboard

### Phase 4: Contract Review and Signing
1. **User 2 (Buyer):**
   - Click on the invitation link or "Review Contract"
   - Read through the contract details
   - **Expected:** Contract preview with all details
   - Click "Sign Contract"
   - **Expected:** Bitcoin public key auto-loaded
   - **Expected:** Signer name auto-filled
   - Review signature details
   - Click "Sign with Bitcoin Key"
   - **Expected:** Success message and signature confirmation

2. **User 1 (Notaire):**
   - Check notifications
   - **Expected:** "Contract Signed" notification
   - Go to Contracts list
   - **Expected:** Contract status shows signature collected

### Phase 5: Smart Contract Creation (Automatic)
1. **Monitor logs:**
   ```bash
   # Watch Flask app logs
   tail -f flask_app.log
   
   # Watch blockchain service logs
   tail -f blockchain_service.log
   
   # Watch payment monitor logs
   tail -f payment_monitor.log
   ```

2. **Expected automatic actions:**
   - Smart contract creation triggered
   - Bitcoin multisig address generated
   - Payment link created
   - All parties notified

3. **Both Users:**
   - Check notifications
   - **Expected:** "Smart Contract Created" notifications
   - **Expected:** Payment required notification (for payer)

### Phase 6: Payment Simulation (Manual Testing)
Since we're on Signet testnet, you can:

1. **Check the smart contract address:**
   - Look in the notifications or contract details
   - Note the Bitcoin address created

2. **Monitor payment status:**
   - The payment monitor will check for payments every 30 seconds
   - You can manually check payment status via API:
   ```bash
   # Get contract payment status (requires JWT token)
   curl -X GET "http://localhost:5000/api/contracts/{contract_id}/payment-status" \
        -H "Authorization: Bearer {your_jwt_token}"
   ```

3. **Simulate payment completion:**
   - For testing, you can send Signet testnet coins to the address
   - Or modify the payment monitor to simulate payment detection

### Phase 7: Completion Notifications
1. **When payment is detected:**
   - Payment monitor updates contract status
   - All parties receive completion notifications
   - Contract status changes to "completed"

2. **Both Users:**
   - Check notifications
   - **Expected:** "Payment Received" notifications
   - Go to Contracts list
   - **Expected:** Contract status shows "Completed"

## API Testing

You can also test the API directly:

### Authentication
```bash
# Login and get JWT token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "notaire@test.com", "password": "test123"}'
```

### Contract Management
```bash
# Get user contracts
curl -X GET http://localhost:5000/api/contracts/ \
  -H "Authorization: Bearer {jwt_token}"

# Check payment status
curl -X GET http://localhost:5000/api/contracts/{contract_id}/payment-status \
  -H "Authorization: Bearer {jwt_token}"
```

### Notifications
```bash
# Get notifications
curl -X GET http://localhost:5000/api/notifications/ \
  -H "Authorization: Bearer {jwt_token}"

# Get unread count
curl -X GET http://localhost:5000/api/notifications/unread-count \
  -H "Authorization: Bearer {jwt_token}"
```

## Troubleshooting

### Services Not Starting
```bash
# Check service status
./test_local.sh status

# Check logs
tail -f flask_app.log
tail -f blockchain_service.log
tail -f payment_monitor.log
```

### Browser Issues
- Clear browser cache/cookies
- Try different browser/profile
- Check browser console for JavaScript errors

### Database Issues
```bash
# Reset database
rm instance/securedeal_dev.db
python3 init_db.py
```

### Port Conflicts
- Flask app: port 5000
- Blockchain service: port 3000
- Check for conflicts: `lsof -i :5000` and `lsof -i :3000`

## Performance Testing

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Ubuntu/Debian

# Test login endpoint
ab -n 100 -c 10 -p login_data.json -T application/json http://localhost:5000/api/auth/login
```

### Database Performance
```bash
# Check database size
ls -lh instance/securedeal_dev.db

# Monitor SQLite performance
sqlite3 instance/securedeal_dev.db ".explain query plan SELECT * FROM contracts"
```

## Security Testing

### Input Validation
- Test with invalid Bitcoin public keys
- Test with malformed email addresses
- Test SQL injection attempts
- Test XSS attempts in contract descriptions

### Authentication
- Test expired JWT tokens
- Test invalid credentials
- Test unauthorized access to contracts

## Cleanup

After testing, clean up resources:
```bash
# Stop all services
./test_local.sh stop

# Remove browser profiles (if created)
rm -rf browser_profiles/

# Remove log files
rm -f *.log *.pid

# Reset database (optional)
rm instance/securedeal_dev.db
```

## Tips for Pitch/Demo

1. **Pre-setup:** Run the setup before your presentation
2. **Have screenshots:** Prepare screenshots of each step
3. **Test the flow:** Practice the complete workflow beforehand
4. **Monitor logs:** Have log windows open to show real-time activity
5. **Backup plan:** Have a video recording of the workflow as backup
6. **Clear data:** Reset the database between demos if needed

## Next Steps

For production deployment:
1. Use real Bitcoin network (mainnet/testnet)
2. Implement proper email service (SendGrid, AWS SES)
3. Add database migrations
4. Set up proper monitoring (Prometheus, Grafana)
5. Implement proper logging (ELK stack)
6. Add comprehensive tests (pytest, Jest)
7. Set up CI/CD pipeline
8. Implement proper secrets management
