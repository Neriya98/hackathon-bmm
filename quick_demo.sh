#!/bin/bash

# Quick Demo Script for SecureDeal
# Demonstrates the complete Bitcoin contract workflow

echo "🎬 SecureDeal Demo Script"
echo "========================"
echo ""

# Check if services are running
check_services() {
    echo "🔍 Checking services..."
    
    if ! curl -s http://localhost:5000/health &> /dev/null; then
        echo "❌ Flask app not running. Please start with: ./simple_test.sh start"
        exit 1
    fi
    
    if ! curl -s http://localhost:3000/ &> /dev/null; then
        echo "❌ Blockchain service not running. Please start with: ./simple_test.sh start"
        exit 1
    fi
    
    echo "✅ All services are running!"
    echo ""
}

# Display demo workflow
show_demo_workflow() {
    echo "🎯 DEMO WORKFLOW SUMMARY"
    echo "======================="
    echo ""
    echo "📱 Application: http://localhost:5000"
    echo ""
    echo "👤 USERS:"
    echo "   • Notaire: notaire@test.com / test123"
    echo "   • User: user@test.com / test123"
    echo ""
    echo "🔄 WORKFLOW STEPS:"
    echo "=================="
    echo ""
    echo "1. 🔐 LOGIN (2 browser windows/profiles):"
    echo "   • Window 1: Login as notaire@test.com"
    echo "   • Window 2: Login as user@test.com"
    echo ""
    echo "2. 📝 CREATE CONTRACT (Notaire):"
    echo "   • Contracts → Create Contract → Sale Contract"
    echo "   • Fill: Title, Description, Amount (e.g., 0.001 BTC)"
    echo "   • Save Contract"
    echo ""
    echo "3. 📧 GENERATE INVITATION LINK (Notaire):"
    echo "   • Contract page → Invite Participants"
    echo "   • Enter: user@test.com"
    echo "   • Generate Invitation Link (don't send email)"
    echo "   • COPY the green shareable link"
    echo ""
    echo "4. ✍️ SIGN CONTRACT (User):"
    echo "   • PASTE invitation link in User's browser"
    echo "   • Review contract details"
    echo "   • Click 'Sign Contract'"
    echo "   • Bitcoin key auto-fills → Sign with Bitcoin Key"
    echo ""
    echo "5. 🔐 SMART CONTRACT (Automatic):"
    echo "   • Smart contract created automatically"
    echo "   • Payment address generated"
    echo "   • Notifications sent to both users"
    echo ""
    echo "6. 💰 PAYMENT & COMPLETION:"
    echo "   • Payment link in notifications"
    echo "   • Payment monitor detects payments"
    echo "   • Completion notifications sent"
    echo ""
    echo "🔧 TESTING TIPS:"
    echo "==============="
    echo "   • Use incognito/private windows for different users"
    echo "   • Or use different browser profiles"
    echo "   • Copy/paste invitation links instead of email"
    echo "   • Check notifications frequently"
    echo "   • Monitor logs: tail -f flask_app.log"
    echo ""
}

# Show API testing examples
show_api_examples() {
    echo "🔌 API TESTING EXAMPLES"
    echo "======================="
    echo ""
    echo "# Test blockchain service:"
    echo "curl http://localhost:3000/"
    echo "curl http://localhost:3000/create_wallet"
    echo ""
    echo "# Test Flask app health:"
    echo "curl http://localhost:5000/health"
    echo ""
    echo "# Login and get JWT token:"
    echo 'curl -X POST http://localhost:5000/api/auth/login \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"email": "notaire@test.com", "password": "test123"}'"'"
    echo ""
    echo "# Test smart contract creation:"
    echo 'curl -X POST http://localhost:3000/create_smart_contract \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{
    "public_keys": [
      "02a1b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3",
      "03b2c3d4e5f6789a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
    ],
    "threshold": 2,
    "network": "signet"
  }'"'"
    echo ""
}

# Main execution
main() {
    case "${1:-demo}" in
        "demo"|"show")
            check_services
            show_demo_workflow
            ;;
            
        "api")
            show_api_examples
            ;;
            
        "quick")
            echo "🚀 Starting quick demo..."
            ./simple_test.sh start
            ;;
            
        "stop")
            ./simple_test.sh stop
            ;;
            
        *)
            echo "SecureDeal Demo Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  demo   - Show demo workflow instructions (default)"
            echo "  api    - Show API testing examples"
            echo "  quick  - Start all services quickly"
            echo "  stop   - Stop all services"
            echo ""
            ;;
    esac
}

main "$@"
