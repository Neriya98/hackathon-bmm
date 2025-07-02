#!/bin/bash

# Two-User Testing Strategy for SecureDeal Bitcoin Contract Platform
# This script sets up and runs two separate instances for testing the complete workflow

set -e  # Exit on any error

echo "🚀 SecureDeal Two-User Testing Strategy"
echo "========================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
FLASK_PORT=5000
BLOCKCHAIN_SERVICE_PORT=3000

USER1_EMAIL="notaire@test.com"
USER1_NAME="Alice (Notaire)"
USER1_TYPE="notaire"

USER2_EMAIL="user@test.com"
USER2_NAME="Bob (User)"
USER2_TYPE="user"

function cleanup() {
    echo "🧹 Cleaning up processes..."
    pkill -f "flask.*run" || true
    pkill -f "payment_monitor" || true
    pkill -f "blockchain_services.*3000" || true
    pkill -f "cargo run" || true
    sleep 2
}

function start_blockchain_service() {
    echo "🔗 Starting Blockchain Service..."
    
    cd smart-contract-to-implement/blockchain_services
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ Cargo not found. Please install Rust first:"
        echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        exit 1
    fi
    
    echo "   Building blockchain service..."
    cargo build --release
    
    echo "   Starting blockchain service on port ${BLOCKCHAIN_SERVICE_PORT}..."
    cargo run --release &
    BLOCKCHAIN_PID=$!
    
    # Wait for service to start
    echo "   Waiting for blockchain service to be ready..."
    for i in {1..30}; do
        if curl -s "http://localhost:${BLOCKCHAIN_SERVICE_PORT}/" > /dev/null 2>&1; then
            echo "   ✅ Blockchain service is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ❌ Blockchain service failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    cd ../..
}

function setup_database() {
    echo "📊 Setting up database with test users..."
    
    # Initialize database with test data
    python3 init_db.py
    
    echo "   ✅ Database initialized with test users"
}

function start_flask_instance() {
    echo "🌐 Starting Flask application..."
    
    # Set environment variables
    export FLASK_ENV=development
    export FLASK_DEBUG=True
    
    echo "   Starting Flask application on port ${FLASK_PORT}..."
    python3 run.py &
    FLASK_PID=$!
    
    # Wait for Flask instance to start
    echo "   Waiting for Flask application to be ready..."
    for i in {1..30}; do
        if curl -s "http://localhost:${FLASK_PORT}/health" > /dev/null 2>&1; then
            echo "   ✅ Flask application is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ❌ Flask application failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
}

function start_payment_monitor() {
    echo "💰 Starting Payment Monitor..."
    
    python3 payment_monitor.py &
    MONITOR_PID=$!
    
    echo "   ✅ Payment monitor started (PID: ${MONITOR_PID})"
}

function open_browser_profiles() {
    echo "🌐 Opening browser profiles for testing..."
    
    local app_url="http://localhost:${FLASK_PORT}"
    
    # Create browser profile directories
    mkdir -p browser_profiles/user1 browser_profiles/user2
    
    # Try to open browser profiles
    if command -v google-chrome &> /dev/null; then
        echo "   Opening Chrome profiles..."
        google-chrome --user-data-dir="$(pwd)/browser_profiles/user1" --profile-directory="User1" "$app_url" &
        sleep 2
        google-chrome --user-data-dir="$(pwd)/browser_profiles/user2" --profile-directory="User2" "$app_url" &
        echo "   ✅ Chrome profiles opened!"
    elif command -v chromium-browser &> /dev/null; then
        echo "   Opening Chromium profiles..."
        chromium-browser --user-data-dir="$(pwd)/browser_profiles/user1" "$app_url" &
        sleep 2
        chromium-browser --user-data-dir="$(pwd)/browser_profiles/user2" "$app_url" &
        echo "   ✅ Chromium profiles opened!"
    elif command -v firefox &> /dev/null; then
        echo "   Opening Firefox profiles..."
        firefox -CreateProfile "user1 $(pwd)/browser_profiles/firefox_user1" -no-remote 2>/dev/null || true
        firefox -CreateProfile "user2 $(pwd)/browser_profiles/firefox_user2" -no-remote 2>/dev/null || true
        sleep 2
        firefox -P user1 -no-remote "$app_url" &
        sleep 2
        firefox -P user2 -no-remote "$app_url" &
        echo "   ✅ Firefox profiles opened!"
    else
        echo "   ⚠️  No supported browser found for automatic opening"
        echo "   Please manually open two browser windows/profiles:"
        echo "   - Window 1: $app_url (for ${USER1_NAME})"
        echo "   - Window 2: $app_url (for ${USER2_NAME})"
    fi
}

function display_testing_instructions() {
    echo ""
    echo "🎯 TESTING INSTRUCTIONS"
    echo "======================="
    echo ""
    echo "The application is now running with two browser profiles for testing:"
    echo ""
    echo "🌐 APPLICATION URL: http://localhost:${FLASK_PORT}"
    echo ""
    echo "👩‍💼 USER 1 (${USER1_NAME}):"
    echo "   Browser: Profile 1 (user1)"
    echo "   Email: ${USER1_EMAIL}"
    echo "   Password: test123"
    echo "   Role: Contract creator (can create all contract types)"
    echo "   Bitcoin Key: 02a1b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3"
    echo ""
    echo "👨‍💼 USER 2 (${USER2_NAME}):"
    echo "   Browser: Profile 2 (user2)"  
    echo "   Email: ${USER2_EMAIL}"
    echo "   Password: test123"
    echo "   Role: Contract signer (can create sale/rental only)"
    echo "   Bitcoin Key: 03b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
    echo ""
    echo "🔗 SERVICES:"
    echo "   Flask App: http://localhost:${FLASK_PORT}"
    echo "   Blockchain API: http://localhost:${BLOCKCHAIN_SERVICE_PORT}"
    echo "   Health Check: http://localhost:${FLASK_PORT}/health"
    echo ""
    echo "🧪 COMPLETE TESTING WORKFLOW:"
    echo "=============================="
    echo ""
    echo "1. 📝 CREATE CONTRACT (Browser Profile 1 - ${USER1_NAME}):"
    echo "   - Login as ${USER1_EMAIL}"
    echo "   - Go to 'Contracts' → 'Create Contract'"
    echo "   - Create a sale or rental contract"
    echo "   - Fill in contract details and save"
    echo ""
    echo "2. 📧 INVITE PARTICIPANT (Browser Profile 1 - ${USER1_NAME}):"
    echo "   - In the contract, click 'Invite Participants'"
    echo "   - Add ${USER2_EMAIL} as a signer"
    echo "   - Send invitation"
    echo ""
    echo "3. ✍️ SIGN CONTRACT (Browser Profile 2 - ${USER2_NAME}):"
    echo "   - Login as ${USER2_EMAIL}"
    echo "   - Check 'Notifications' for invitation"
    echo "   - Click on invitation link"
    echo "   - Review and sign the contract"
    echo ""
    echo "4. 🔐 SMART CONTRACT CREATION (Automatic):"
    echo "   - After all signatures are collected"
    echo "   - Smart contract is automatically created"
    echo "   - Payment link is generated and sent"
    echo "   - Check notifications for payment details"
    echo ""
    echo "5. 💳 MAKE PAYMENT (Simulate):"
    echo "   - Use the payment address from notifications"
    echo "   - Send Bitcoin to the address (use signet testnet)"
    echo "   - Or simulate payment via API for testing"
    echo ""
    echo "6. 🎉 PAYMENT COMPLETION (Automatic):"
    echo "   - Payment monitor detects the payment"
    echo "   - All parties receive completion notifications"
    echo "   - Contract status changes to 'completed'"
    echo ""
    echo "🛠️ TESTING COMMANDS:"
    echo "===================="
    echo ""
    echo "# Check service status:"
    echo "curl http://localhost:${BLOCKCHAIN_SERVICE_PORT}/"
    echo "curl http://localhost:${FLASK_PORT}/health"
    echo ""
    echo "# Test smart contract service:"
    echo "curl -X GET http://localhost:${BLOCKCHAIN_SERVICE_PORT}/create_wallet"
    echo ""
    echo "# Check payment monitor:"
    echo "tail -f payment_monitor.log"
    echo ""
    echo "# Stop all services:"
    echo "bash $0 stop"
    echo ""
    echo "⚠️  IMPORTANT NOTES:"
    echo "==================="
    echo "• Both users can access the same database"
    echo "• Use different browser profiles/windows for isolation"
    echo "• All Bitcoin operations use Signet testnet"
    echo "• Payment monitoring runs automatically"
    echo "• Check notifications frequently during testing"
    echo ""
    echo "🎬 Press Ctrl+C to stop all services when done testing"
    echo ""
}

function stop_services() {
    echo "🛑 Stopping all services..."
    cleanup
    echo "✅ All services stopped"
    exit 0
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        stop_services
        ;;
    "status")
        echo "📊 Service Status:"
        echo "=================="
        echo -n "Blockchain Service: "
        if curl -s "http://localhost:${BLOCKCHAIN_SERVICE_PORT}/" > /dev/null 2>&1; then
            echo "✅ Running"
        else
            echo "❌ Not running"
        fi
        
        echo -n "Flask Application: "
        if curl -s "http://localhost:${FLASK_PORT}/health" > /dev/null 2>&1; then
            echo "✅ Running (http://localhost:${FLASK_PORT})"
        else
            echo "❌ Not running"
        fi
        
        echo -n "Payment Monitor: "
        if pgrep -f "payment_monitor" > /dev/null; then
            echo "✅ Running"
        else
            echo "❌ Not running"
        fi
        exit 0
        ;;
    *)
        # Default: start all services
        ;;
esac

# Trap to cleanup on exit
trap cleanup EXIT

# Main execution
echo "🚀 Starting SecureDeal testing environment..."
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "❌ curl not found. Please install curl"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start services
start_blockchain_service
setup_database
start_flask_instance
start_payment_monitor

# Display instructions
display_testing_instructions

# Ask user if they want to open browser profiles
echo ""
read -p "Open browser profiles automatically? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open_browser_profiles
else
    echo "Please manually open two browser windows/profiles:"
    echo "1. http://localhost:${FLASK_PORT} (for ${USER1_NAME})"
    echo "2. http://localhost:${FLASK_PORT} (for ${USER2_NAME})"
fi

# Keep running until interrupted
echo "🔄 Services are running. Press Ctrl+C to stop all services."
echo ""

wait
