#!/bin/bash

# ===================================================================
# SecureDeal Local Testing Strategy
# ===================================================================
# This script provides multiple strategies for testing the application
# with two users to simulate the complete contract workflow.
# ===================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 SecureDeal Local Testing Strategy"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_step "Checking dependencies..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check Rust/Cargo for blockchain service
    if ! command -v cargo &> /dev/null; then
        missing_deps+=("cargo (Rust)")
    fi
    
    # Check if we have browser options
    if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null && ! command -v firefox &> /dev/null; then
        print_warning "No common browsers found. You may need to manually open browsers."
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_status "All dependencies found!"
}

# Initialize the database with test data
init_database() {
    print_step "Initializing database with test data..."
    
    if [ -f "instance/securedeal_dev.db" ]; then
        print_warning "Database already exists. Backing up..."
        cp instance/securedeal_dev.db instance/securedeal_dev.db.backup.$(date +%s)
    fi
    
    python3 init_db.py
    print_status "Database initialized successfully!"
}

# Build and start the blockchain service
start_blockchain_service() {
    print_step "Starting blockchain service..."
    
    cd smart-contract-to-implement/blockchain_services
    
    # Check if already running
    if curl -s http://localhost:3000/ &> /dev/null; then
        print_status "Blockchain service is already running on port 3000"
        cd "$SCRIPT_DIR"
        return 0
    fi
    
    # Build and run
    print_status "Building blockchain service..."
    cargo build --release
    
    print_status "Starting blockchain service in background..."
    nohup cargo run --release > ../../blockchain_service.log 2>&1 &
    echo $! > ../../blockchain_service.pid
    
    cd "$SCRIPT_DIR"
    
    # Wait for service to start
    for i in {1..30}; do
        if curl -s http://localhost:3000/ &> /dev/null; then
            print_status "Blockchain service started successfully!"
            return 0
        fi
        sleep 1
    done
    
    print_error "Failed to start blockchain service"
    return 1
}

# Start the Flask application
start_flask_app() {
    print_step "Starting Flask application..."
    
    # Check if already running
    if curl -s http://localhost:5000/health &> /dev/null; then
        print_status "Flask app is already running on port 5000"
        return 0
    fi
    
    print_status "Starting Flask app in background..."
    nohup python3 run.py > flask_app.log 2>&1 &
    echo $! > flask_app.pid
    
    # Wait for app to start
    for i in {1..30}; do
        if curl -s http://localhost:5000/health &> /dev/null; then
            print_status "Flask app started successfully!"
            return 0
        fi
        sleep 1
    done
    
    print_error "Failed to start Flask app"
    return 1
}

# Start payment monitoring service
start_payment_monitor() {
    print_step "Starting payment monitoring service..."
    
    if [ -f "payment_monitor.pid" ] && kill -0 "$(cat payment_monitor.pid)" 2>/dev/null; then
        print_status "Payment monitor is already running"
        return 0
    fi
    
    print_status "Starting payment monitor in background..."
    nohup python3 payment_monitor.py > payment_monitor.log 2>&1 &
    echo $! > payment_monitor.pid
    
    print_status "Payment monitor started!"
}

# Display testing strategies
show_testing_strategies() {
    echo ""
    echo "🧪 Testing Strategies Available:"
    echo "================================"
    echo ""
    
    echo "1. BROWSER PROFILES STRATEGY (Recommended)"
    echo "   - Use Chrome/Firefox with different user profiles"
    echo "   - Easiest method, no additional setup required"
    echo ""
    
    echo "2. INCOGNITO/PRIVATE BROWSING STRATEGY"
    echo "   - Use regular browser + incognito/private window"
    echo "   - Good for quick testing"
    echo ""
    
    echo "3. DIFFERENT BROWSERS STRATEGY"
    echo "   - Use different browsers (Chrome, Firefox, Safari, etc.)"
    echo "   - Simple and effective"
    echo ""
    
    echo "4. CONTAINER/VM STRATEGY"
    echo "   - Use Docker containers or VMs for complete isolation"
    echo "   - Most realistic but requires additional setup"
    echo ""
}

# Launch browser profiles for testing
launch_browser_profiles() {
    print_step "Launching browser profiles for testing..."
    
    local app_url="http://localhost:5000"
    
    # Try Chrome first
    if command -v google-chrome &> /dev/null; then
        print_status "Launching Chrome profiles..."
        
        # Create profile directories
        mkdir -p browser_profiles/user1 browser_profiles/user2
        
        # Launch Chrome with different profiles
        google-chrome --user-data-dir="$(pwd)/browser_profiles/user1" --profile-directory="User1" "$app_url" &
        sleep 2
        google-chrome --user-data-dir="$(pwd)/browser_profiles/user2" --profile-directory="User2" "$app_url" &
        
        print_status "Chrome profiles launched!"
        echo "  - User 1: Profile in browser_profiles/user1"
        echo "  - User 2: Profile in browser_profiles/user2"
        
    elif command -v chromium-browser &> /dev/null; then
        print_status "Launching Chromium profiles..."
        
        mkdir -p browser_profiles/user1 browser_profiles/user2
        
        chromium-browser --user-data-dir="$(pwd)/browser_profiles/user1" "$app_url" &
        sleep 2
        chromium-browser --user-data-dir="$(pwd)/browser_profiles/user2" "$app_url" &
        
        print_status "Chromium profiles launched!"
        
    elif command -v firefox &> /dev/null; then
        print_status "Launching Firefox profiles..."
        
        # Create Firefox profiles
        firefox -CreateProfile "user1 $(pwd)/browser_profiles/firefox_user1" -no-remote &
        sleep 2
        firefox -CreateProfile "user2 $(pwd)/browser_profiles/firefox_user2" -no-remote &
        sleep 2
        
        firefox -P user1 -no-remote "$app_url" &
        firefox -P user2 -no-remote "$app_url" &
        
        print_status "Firefox profiles launched!"
    else
        print_warning "No supported browser found for profile launching"
        print_status "Please manually open two browser instances:"
        echo "  1. Open $app_url in your first browser/profile"
        echo "  2. Open $app_url in your second browser/profile"
    fi
}

# Show test users information
show_test_users() {
    echo ""
    echo "👥 Test Users Available:"
    echo "======================="
    echo ""
    echo "USER 1 (Notaire/Creator):"
    echo "  Email: notaire@test.com"
    echo "  Password: test123"
    echo "  Type: notaire"
    echo "  Bitcoin Key: 02a1b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
    echo ""
    echo "USER 2 (Regular User/Buyer):"
    echo "  Email: user@test.com"
    echo "  Password: test123"
    echo "  Type: user"
    echo "  Bitcoin Key: 03b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5"
    echo ""
    echo "USER 3 (Another User/Seller):"
    echo "  Email: seller@test.com"
    echo "  Password: test123"
    echo "  Type: user"
    echo "  Bitcoin Key: 04c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6"
    echo ""
}

# Show testing workflow
show_testing_workflow() {
    echo ""
    echo "🔄 Testing Workflow:"
    echo "==================="
    echo ""
    echo "1. LOGIN PHASE:"
    echo "   - Browser/Profile 1: Login as notaire@test.com"
    echo "   - Browser/Profile 2: Login as user@test.com"
    echo ""
    echo "2. CONTRACT CREATION:"
    echo "   - User 1 (Notaire): Create a new contract (sale/rental)"
    echo "   - Fill in contract details including amount"
    echo "   - Generate preview and review"
    echo ""
    echo "3. INVITATION PHASE:"
    echo "   - User 1: Send invitation to user@test.com"
    echo "   - User 2: Check notifications/dashboard for invitation"
    echo "   - User 2: Click invitation link"
    echo ""
    echo "4. SIGNING PHASE:"
    echo "   - User 2: Review contract and sign with Bitcoin key"
    echo "   - User 1: Check notifications for signature confirmation"
    echo "   - Watch for smart contract creation notification"
    echo ""
    echo "5. PAYMENT PHASE:"
    echo "   - Check notifications for payment link"
    echo "   - Monitor blockchain service logs for smart contract creation"
    echo "   - Payment monitor will detect when payment is made"
    echo ""
    echo "6. COMPLETION:"
    echo "   - All users receive completion notifications"
    echo "   - Contract status changes to 'completed'"
    echo ""
}

# Show service status
show_service_status() {
    echo ""
    echo "🔍 Service Status:"
    echo "=================="
    echo ""
    
    # Check Flask app
    if curl -s http://localhost:5000/health &> /dev/null; then
        print_status "✅ Flask App: Running (http://localhost:5000)"
    else
        print_error "❌ Flask App: Not running"
    fi
    
    # Check blockchain service
    if curl -s http://localhost:3000/ &> /dev/null; then
        print_status "✅ Blockchain Service: Running (http://localhost:3000)"
    else
        print_error "❌ Blockchain Service: Not running"
    fi
    
    # Check payment monitor
    if [ -f "payment_monitor.pid" ] && kill -0 "$(cat payment_monitor.pid)" 2>/dev/null; then
        print_status "✅ Payment Monitor: Running"
    else
        print_warning "⚠️  Payment Monitor: Not running"
    fi
    
    echo ""
    echo "📊 Useful URLs:"
    echo "  - Main App: http://localhost:5000"
    echo "  - Health Check: http://localhost:5000/health"
    echo "  - Blockchain API: http://localhost:3000"
    echo ""
    echo "📁 Log Files:"
    echo "  - Flask App: flask_app.log"
    echo "  - Blockchain Service: blockchain_service.log"
    echo "  - Payment Monitor: payment_monitor.log"
}

# Stop all services
stop_services() {
    print_step "Stopping all services..."
    
    # Stop Flask app
    if [ -f "flask_app.pid" ]; then
        if kill "$(cat flask_app.pid)" 2>/dev/null; then
            print_status "Flask app stopped"
        fi
        rm -f flask_app.pid
    fi
    
    # Stop blockchain service
    if [ -f "blockchain_service.pid" ]; then
        if kill "$(cat blockchain_service.pid)" 2>/dev/null; then
            print_status "Blockchain service stopped"
        fi
        rm -f blockchain_service.pid
    fi
    
    # Stop payment monitor
    if [ -f "payment_monitor.pid" ]; then
        if kill "$(cat payment_monitor.pid)" 2>/dev/null; then
            print_status "Payment monitor stopped"
        fi
        rm -f payment_monitor.pid
    fi
    
    print_status "All services stopped!"
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            check_dependencies
            init_database
            start_blockchain_service
            start_flask_app
            start_payment_monitor
            show_service_status
            show_testing_strategies
            show_test_users
            show_testing_workflow
            
            echo ""
            read -p "Launch browser profiles for testing? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                launch_browser_profiles
            fi
            
            echo ""
            print_status "Setup complete! Ready for testing."
            print_status "Run './test_local.sh status' to check service status"
            print_status "Run './test_local.sh stop' to stop all services"
            ;;
            
        "status")
            show_service_status
            ;;
            
        "stop")
            stop_services
            ;;
            
        "restart")
            stop_services
            sleep 2
            "$0" start
            ;;
            
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start    - Start all services and setup testing environment"
            echo "  status   - Show status of all services"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  help     - Show this help message"
            echo ""
            ;;
            
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information."
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'echo ""; print_warning "Script interrupted. Run ./test_local.sh stop to clean up."; exit 130' INT

# Run main function
main "$@"
