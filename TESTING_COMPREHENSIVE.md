# SecureDeal Testing Guide

This guide provides comprehensive testing strategies for the SecureDeal Bitcoin contract management platform.

## Overview

SecureDeal is a Bitcoin-based contract management system that enables:
- User registration with Bitcoin public keys
- Contract creation from templates
- Digital signature workflow
- Automatic smart contract creation after full signature
- Payment monitoring and notifications
- Complete contract lifecycle management

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │ Blockchain      │
│   (HTML/JS)     │◄──►│   (Python)      │◄──►│ Service (Rust)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Templates     │    │   Database      │    │  Bitcoin        │
│   & Static      │    │   (SQLite)      │    │  Network        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Testing Strategies

### 1. Two-User Local Testing (Recommended for Demo)

This strategy runs two separate Flask instances to simulate two different users.

#### Quick Start
```bash
# Start all services
./test_two_users.sh

# Check status
./test_two_users.sh status

# Stop all services
./test_two_users.sh stop
```

#### Manual Setup
```bash
# 1. Start blockchain service
cd smart-contract-to-implement/blockchain_services
cargo run --release &

# 2. Initialize database
python3 init_db.py

# 3. Start Flask instances
FLASK_RUN_PORT=5000 python3 run.py &  # User 1
FLASK_RUN_PORT=5001 python3 run.py &  # User 2

# 4. Start payment monitor
python3 payment_monitor.py &
```

#### Test Users
- **Alice (Notaire)**: alice@example.com / password123
- **Bob (User)**: bob@example.com / password123

#### Testing Workflow
1. **Contract Creation** (Alice - Port 5000)
   - Login as alice@example.com
   - Create sale/rental contract
   - Fill contract details

2. **Invitation** (Alice)
   - Invite bob@example.com
   - Send invitation email

3. **Contract Signing** (Bob - Port 5001)
   - Login as bob@example.com
   - Check notifications
   - Sign contract with Bitcoin key

4. **Smart Contract Creation** (Automatic)
   - Triggered after all signatures
   - Payment address generated
   - Notifications sent

5. **Payment Monitoring** (Automatic)
   - Monitor detects payments
   - Notifications sent on completion

### 2. Browser Profile Testing

Use different browser profiles for better isolation:

```bash
# Start single instance
python3 run.py

# Chrome profiles
google-chrome --user-data-dir=/tmp/chrome-user1 --profile-directory=Default http://localhost:5000
google-chrome --user-data-dir=/tmp/chrome-user2 --profile-directory=Default http://localhost:5000

# Firefox profiles
firefox -P user1 -new-instance http://localhost:5000
firefox -P user2 -new-instance http://localhost:5000
```

### 3. Docker Testing (Advanced)

For complete isolation, use Docker containers:

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Scale Flask app for multiple users
docker-compose up -d --scale web=2

# Check logs
docker-compose logs -f web
docker-compose logs -f blockchain
```

### 4. API Testing

Test the API endpoints directly:

```bash
# Health check
curl http://localhost:5000/api/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "username": "testuser",
    "user_type": "user",
    "bitcoin_public_key": "02a1b2c3d4e5f6..."
  }'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Check notifications
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/notifications/

# Check payment status
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/contracts/CONTRACT_ID/payment/status
```

## Service Management

### Start/Stop Commands

```bash
# Start blockchain service
cd smart-contract-to-implement/blockchain_services
cargo run --release

# Start Flask app
python3 run.py

# Start payment monitor
python3 payment_monitor.py

# Check payment monitor status
python3 payment_monitor.py status

# Stop all Python processes
pkill -f "python3.*run.py"
pkill -f "python3.*payment_monitor"

# Stop Rust processes
pkill -f "blockchain_services"
```

### Health Checks

```bash
# Flask app
curl http://localhost:5000/health

# Blockchain service
curl http://localhost:3000/

# Database check
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('DB OK' if db.engine.execute('SELECT 1').scalar() == 1 else 'DB Error')"
```

## Testing Scenarios

### Scenario 1: Complete Sale Contract Workflow

1. **Alice creates sale contract**
   - Property: "123 Main St"
   - Price: 0.5 BTC
   - Buyer: Bob

2. **Alice invites Bob**
   - Send invitation email
   - Bob receives notification

3. **Bob signs contract**
   - Reviews terms
   - Signs with Bitcoin key
   - Alice gets notification

4. **Smart contract created**
   - Multisig address generated
   - Payment link sent to Bob
   - Both parties notified

5. **Bob makes payment**
   - Sends BTC to address
   - Monitor detects payment
   - Completion notifications sent

### Scenario 2: Rental Contract with Multiple Parties

1. **Alice creates rental contract**
   - Property: "456 Oak Ave"
   - Monthly rent: 0.1 BTC
   - Tenant: Bob
   - Guarantor: Charlie

2. **Multiple invitations**
   - Invite Bob as tenant
   - Invite Charlie as guarantor

3. **Sequential signing**
   - Bob signs first
   - Charlie signs second
   - Alice gets updates

4. **Contract completion**
   - Smart contract created
   - Payment monitoring starts

### Scenario 3: Error Handling

Test various error conditions:
- Invalid Bitcoin public keys
- Network connection issues
- Database errors
- Blockchain service downtime
- Invalid signatures

## Monitoring and Debugging

### Log Files
```bash
# Application logs
tail -f app.log

# Payment monitor logs
tail -f payment_monitor.log

# Blockchain service logs
# (check terminal where cargo run was executed)
```

### Database Inspection
```bash
# SQLite command line
sqlite3 instance/securedeal_dev.db

# Useful queries
.schema
SELECT * FROM users;
SELECT * FROM contracts;
SELECT * FROM signatures;
SELECT * FROM notifications;
```

### Performance Monitoring
```bash
# Process monitoring
htop
ps aux | grep python
ps aux | grep cargo

# Network monitoring
netstat -tulpn | grep :5000
netstat -tulpn | grep :3000

# Disk usage
du -sh instance/
du -sh logs/
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   lsof -ti:5000 | xargs kill -9
   lsof -ti:3000 | xargs kill -9
   ```

2. **Database locked**
   ```bash
   rm instance/securedeal_dev.db
   python3 init_db.py
   ```

3. **Blockchain service not responding**
   ```bash
   cd smart-contract-to-implement/blockchain_services
   cargo clean
   cargo build --release
   cargo run --release
   ```

4. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   cargo update
   ```

### Debug Mode

Enable debug mode for detailed logging:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python3 run.py
```

## Security Considerations

### Testing vs Production

- **Testing**: Uses Signet testnet (safe)
- **Production**: Would use Bitcoin mainnet (real money)

### Key Management

- Test keys are generated automatically
- Never use test keys in production
- Implement proper key storage for production

### Network Security

- Test environment uses HTTP (insecure)
- Production should use HTTPS only
- Implement rate limiting and authentication

## Performance Testing

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test login endpoint
ab -n 100 -c 10 -p login.json -T application/json http://localhost:5000/api/auth/login

# Test contract creation
ab -n 50 -c 5 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/contracts/
```

### Memory Usage
```bash
# Monitor memory usage
ps aux --sort=-%mem | head
free -h
```

## Deployment Testing

### Environment Variables
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=your-database-url
export BITCOIN_NETWORK=mainnet  # For production
```

### Production Checklist
- [ ] HTTPS enabled
- [ ] Database secured
- [ ] Environment variables set
- [ ] Error handling tested
- [ ] Monitoring configured
- [ ] Backup system in place
- [ ] Rate limiting enabled
- [ ] Authentication secured

## Conclusion

This testing guide provides multiple strategies for testing SecureDeal:

1. **Quick Demo**: Use `./test_two_users.sh`
2. **Development**: Use browser profiles
3. **Integration**: Use Docker setup
4. **API**: Use curl commands

Choose the strategy that best fits your testing needs. For pitching/demo purposes, the two-user script provides the most realistic simulation of the complete workflow.
