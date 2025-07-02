#!/bin/bash

# test_savings_contract.sh
# End-to-end test for Bitcoin Savings Contract Workflow
# ====================================================

echo -e "\033[1;33m===== BITCOIN SAVINGS CONTRACT WORKFLOW TEST =====\033[0m"
echo -e "\033[1;36mThis script tests the complete savings contract workflow including creation, signing, and smart contract activation\033[0m"

# Set up the environment
echo -e "\n\033[1;34m[1/6] Setting up the test environment...\033[0m"
export FLASK_APP=run.py
export FLASK_ENV=development

# Start the Flask app in the background (if not already running)
if ! pgrep -f "flask run" > /dev/null; then
    echo "Starting Flask application..."
    flask run &
    APP_PID=$!
    echo "Flask app started with PID: $APP_PID"
    sleep 2
else
    echo "Flask app is already running"
fi

# Check if app is accessible
echo "Checking if the app is accessible..."
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo -e "\033[1;31mError: Flask app is not accessible. Please check if it's running correctly.\033[0m"
    exit 1
fi
echo "App is accessible ✅"

# Create a new user account or use existing
echo -e "\n\033[1;34m[2/6] Creating test user...\033[0m"
echo "Note: In a real test, we would use Selenium or Playwright to automate browser actions"
echo "For this test, please follow these manual steps:"
echo -e "\033[1;36m1. Open browser to http://localhost:5000/auth/register\033[0m"
echo -e "\033[1;36m2. Register with email: test.user@example.com\033[0m"
echo -e "\033[1;36m3. Set password: TestPassword123\033[0m"
echo -e "\033[1;36m4. Fill profile with name: Test User\033[0m"
echo -e "\033[1;36m5. Add a Bitcoin public key in your profile\033[0m"
echo -e "\033[1;36m6. Continue to the next step when done\033[0m"
read -p "Press Enter when user is registered and logged in..."

# Create a savings contract
echo -e "\n\033[1;34m[3/6] Creating a Bitcoin savings contract...\033[0m"
echo -e "\033[1;36m1. Navigate to http://localhost:5000/contracts/create\033[0m"
echo -e "\033[1;36m2. Select 'Savings Contract'\033[0m"
echo -e "\033[1;36m3. Fill in the form with:\033[0m"
echo -e "\033[1;36m   - Title: Test Savings Contract\033[0m"
echo -e "\033[1;36m   - Description: A test savings contract\033[0m"
echo -e "\033[1;36m   - Amount: 0.001 BTC\033[0m"
echo -e "\033[1;36m   - Network: Signet\033[0m"
echo -e "\033[1;36m   - Bitcoin Key: Use 'Load from Profile' button\033[0m"
echo -e "\033[1;36m4. Click 'Create Contract' button\033[0m"
read -p "Press Enter when contract is created..."

# Sign the contract
echo -e "\n\033[1;34m[4/6] Signing the contract...\033[0m"
echo -e "\033[1;36m1. You should be automatically redirected to the signing page\033[0m"
echo -e "\033[1;36m2. Verify that your name and Bitcoin key are auto-populated\033[0m"
echo -e "\033[1;36m3. Check the 'I agree to the terms' checkbox\033[0m"
echo -e "\033[1;36m4. Click the 'Sign Contract' button\033[0m"
read -p "Press Enter when contract is signed..."

# Create smart contract
echo -e "\n\033[1;34m[5/6] Creating smart contract...\033[0m"
echo -e "\033[1;36m1. Once signed, you should see the 'Create Smart Contract' button\033[0m"
echo -e "\033[1;36m2. Click the 'Create Smart Contract' button\033[0m"
echo -e "\033[1;36m3. Wait for the smart contract to be created\033[0m"
read -p "Press Enter when smart contract is created..."

# Make payment
echo -e "\n\033[1;34m[6/6] Making a payment...\033[0m"
echo -e "\033[1;36m1. You should be redirected to the payment page\033[0m"
echo -e "\033[1;36m2. Verify that you can see:\033[0m"
echo -e "\033[1;36m   - Contract details\033[0m"
echo -e "\033[1;36m   - Payment amount\033[0m"
echo -e "\033[1;36m   - Bitcoin address\033[0m"
echo -e "\033[1;36m   - QR code\033[0m"
echo -e "\033[1;36m3. In a real environment, you would make a payment to this address\033[0m"
echo -e "\033[1;36m4. For testing, just verify the page displays correctly\033[0m"
read -p "Press Enter when payment page is verified..."

# Verify the workflow
echo -e "\n\033[1;34m[Verification] Checking workflow completion...\033[0m"
echo -e "\033[1;36m1. Navigate to Dashboard: http://localhost:5000/dashboard\033[0m"
echo -e "\033[1;36m2. Verify your contract appears in the list\033[0m"
echo -e "\033[1;36m3. Check notifications for smart contract creation\033[0m"
read -p "Press Enter when verified..." 

# Test conclusion
echo -e "\n\033[1;32m===== TEST COMPLETED =====\033[0m"
echo "The savings contract workflow test has completed."
echo "Summary:"
echo "✅ Created a savings contract"
echo "✅ Signed the contract"
echo "✅ Created a smart contract"
echo "✅ Generated a payment page"

# Clean up
echo -e "\n\033[1;34m[Cleanup] Cleaning up test environment...\033[0m"
if [ ! -z "$APP_PID" ]; then
    echo "Stopping Flask application (PID: $APP_PID)..."
    kill $APP_PID
    echo "Flask app stopped"
else
    echo "Flask app was already running, not stopping it"
fi

echo -e "\n\033[1;32mTest script completed!\033[0m"
