#!/bin/bash

# Simple Two-User Testing Script for SecureDeal
# Tests the complete Bitcoin contract workflow on the same computer using browser profiles

set -e

echo "🚀 SecureDeal Simple Testing Setup"
echo "=================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
FLASK_PORT=5000
BLOCKCHAIN_SERVICE_PORT=3000

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    pkill -f "python3 run.py" || true
    pkill -f "cargo run" || true
    pkill -f "payment_monitor" || true
    sleep 2
}

# Trap cleanup on exit
trap cleanup EXIT

# Start blockchain service
start_blockchain_service() {
    print_step "Starting blockchain service..."
    
    cd smart-contract-to-implement/blockchain_services
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ Rust/Cargo not found. Please install Rust first."
        exit 1
    fi
    
    # Check if already running
    if curl -s http://localhost:${BLOCKCHAIN_SERVICE_PORT}/ &> /dev/null; then
        print_status "Blockchain service already running"
        cd "$SCRIPT_DIR"
        return 0
    fi
    
    print_status "Building and starting blockchain service..."
    cargo build --release
    nohup cargo run --release > ../../blockchain_service.log 2>&1 &
    
    cd "$SCRIPT_DIR"
    
    # Wait for service to start
    for i in {1..20}; do
        if curl -s http://localhost:${BLOCKCHAIN_SERVICE_PORT}/ &> /dev/null; then
            print_status "✅ Blockchain service ready!"
            break
        fi
        if [ $i -eq 20 ]; then
            echo "❌ Blockchain service failed to start"
            exit 1
        fi
        sleep 1
    done
}

# Initialize database
setup_database() {
    print_step "Setting up database..."
    python3 init_db.py > /dev/null 2>&1
    print_status "✅ Database ready with test users"
}

# Start Flask app
start_flask_app() {
    print_step "Starting Flask application..."
    
    # Check if already running
    if curl -s http://localhost:${FLASK_PORT}/health &> /dev/null; then
        print_status "Flask app already running"
        return 0
    fi
    
    export FLASK_ENV=development
    export FLASK_DEBUG=True
    
    nohup python3 run.py > flask_app.log 2>&1 &
    
    # Wait for app to start
    for i in {1..20}; do
        if curl -s http://localhost:${FLASK_PORT}/health &> /dev/null; then
            print_status "✅ Flask app ready!"
            break
        fi
        if [ $i -eq 20 ]; then
            echo "❌ Flask app failed to start"
            exit 1
        fi
        sleep 1
    done
}

# Start payment monitor
start_payment_monitor() {
    print_step "Starting payment monitor..."
    nohup python3 payment_monitor.py > payment_monitor.log 2>&1 &
    print_status "✅ Payment monitor started"
}

# Open browser profiles
open_browsers() {
    print_step "Opening browser profiles..."
    
    local app_url="http://localhost:${FLASK_PORT}"
    
    # Create profile directories
    mkdir -p browser_profiles/notaire browser_profiles/user
    
    # Try Chrome first
    if command -v google-chrome &> /dev/null; then
        print_status "Opening Chrome profiles..."
        google-chrome --user-data-dir="$(pwd)/browser_profiles/notaire" --profile-directory="Notaire" "$app_url" &
        sleep 2
        google-chrome --user-data-dir="$(pwd)/browser_profiles/user" --profile-directory="User" "$app_url" &
        print_status "✅ Chrome profiles opened!"
    elif command -v chromium-browser &> /dev/null; then
        print_status "Opening Chromium profiles..."
        chromium-browser --user-data-dir="$(pwd)/browser_profiles/notaire" "$app_url" &
        sleep 2
        chromium-browser --user-data-dir="$(pwd)/browser_profiles/user" "$app_url" &
        print_status "✅ Chromium profiles opened!"
    elif command -v firefox &> /dev/null; then
        print_status "Opening Firefox profiles..."
        firefox -CreateProfile "notaire $(pwd)/browser_profiles/firefox_notaire" -no-remote 2>/dev/null || true
        firefox -CreateProfile "user $(pwd)/browser_profiles/firefox_user" -no-remote 2>/dev/null || true
        sleep 2
        firefox -P notaire -no-remote "$app_url" &
        sleep 2
        firefox -P user -no-remote "$app_url" &
        print_status "✅ Firefox profiles opened!"
    else
        print_status "Please manually open two browser windows:"
        echo "   Window 1: $app_url (for Notaire)"
        echo "   Window 2: $app_url (for User)"
    fi
}

# Display testing instructions
show_instructions() {
    echo ""
    echo "🎯 SIMPLE TESTING WORKFLOW"
    echo "=========================="
    echo ""
    echo "📱 Two browser windows are now open:"
    echo "   • Window 1: Notaire (contract creator)"
    echo "   • Window 2: User (contract signer)"
    echo ""
    echo "👤 LOGIN CREDENTIALS:"
    echo "   📧 Notaire: notaire@test.com / test123"
    echo "   📧 User: user@test.com / test123"
    echo ""
    echo "🔄 TESTING STEPS:"
    echo "================"
    echo ""
    echo "1. 🔐 LOGIN (Both Windows):"
    echo "   • Window 1: Login as notaire@test.com"
    echo "   • Window 2: Login as user@test.com"
    echo ""
    echo "2. 📝 CREATE CONTRACT (Window 1 - Notaire):"
    echo "   • Click 'Contracts' → 'Create Contract'"
    echo "   • Choose 'Sale Contract' or 'Rental Contract'"
    echo "   • Fill in details (amount, description, etc.)"
    echo "   • Click 'Save Contract'"
    echo ""
    echo "3. 🔗 GET INVITATION LINK (Window 1 - Notaire):"
    echo "   • In the contract page, click 'Invite Participants'"
    echo "   • Enter user@test.com as recipient"
    echo "   • Click 'Generate Invitation Link'"
    echo "   • COPY the shareable link (don't send email)"
    echo ""
    echo "4. ✍️ SIGN CONTRACT (Window 2 - User):"
    echo "   • PASTE the invitation link in the browser"
    echo "   • Review the contract details"
    echo "   • Click 'Sign Contract'"
    echo "   • The Bitcoin key will auto-fill"
    echo "   • Click 'Sign with Bitcoin Key'"
    echo ""
    echo "5. 🔐 SMART CONTRACT CREATION (Automatic):"
    echo "   • After signing, smart contract is created automatically"
    echo "   • Both users will see notifications"
    echo "   • Payment address will be generated"
    echo ""
    echo "6. 💰 PAYMENT MONITORING:"
    echo "   • Payment link will be shown in notifications"
    echo "   • For testing, payment detection is simulated"
    echo "   • All parties get completion notifications"
    echo ""
    echo "🛠️ USEFUL COMMANDS:"
    echo "==================="
    echo "   • Check logs: tail -f flask_app.log"
    echo "   • Check blockchain: curl http://localhost:3000/"
    echo "   • Stop all: press Ctrl+C"
    echo ""
    echo "⚠️ IMPORTANT NOTES:"
    echo "==================="
    echo "   • Use different browser windows/profiles for each user"
    echo "   • Copy/paste the invitation link instead of email"
    echo "   • Check notifications frequently during testing"
    echo "   • Bitcoin keys are auto-filled from user profiles"
    echo ""
}

# Main execution
main() {
    case "${1:-start}" in
        "start")
            echo "🚀 Starting all services..."
            start_blockchain_service
            setup_database
            start_flask_app
            start_payment_monitor
            
            echo ""
            read -p "Open browser profiles for testing? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open_browsers
            fi
            
            show_instructions
            
            echo "🎬 Press Ctrl+C to stop all services when done"
            echo ""
            
            # Wait for interrupt
            while true; do
                sleep 1
            done
            ;;
            
        "stop")
            cleanup
            echo "✅ All services stopped"
            ;;
            
        "status")
            echo "📊 Service Status:"
            echo "=================="
            
            if curl -s http://localhost:${BLOCKCHAIN_SERVICE_PORT}/ &> /dev/null; then
                echo "✅ Blockchain Service: Running"
            else
                echo "❌ Blockchain Service: Not running"
            fi
            
            if curl -s http://localhost:${FLASK_PORT}/health &> /dev/null; then
                echo "✅ Flask App: Running"
            else
                echo "❌ Flask App: Not running"
            fi
            
            if pgrep -f "payment_monitor" > /dev/null; then
                echo "✅ Payment Monitor: Running"
            else
                echo "❌ Payment Monitor: Not running"
            fi
            ;;
            
        *)
            echo "Usage: $0 [start|stop|status]"
            echo ""
            echo "Commands:"
            echo "  start  - Start all services and open browsers"
            echo "  stop   - Stop all services"
            echo "  status - Check service status"
            ;;
    esac
}

main "$@"
