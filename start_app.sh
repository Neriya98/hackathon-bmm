#!/bin/bash

# SecureDeal/DealSure - Bitcoin Contract Management Platform
# Quick Start Script

echo "🚀 Starting SecureDeal - Bitcoin Contract Management Platform"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one first: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if database exists, if not initialize it
if [ ! -f "instance/securedeal_dev.db" ]; then
    echo "🗄️  Database not found. Initializing..."
    python3 init_db.py
else
    echo "✅ Database found"
fi

echo ""
echo "🔧 Configuration:"
echo "- Database: SQLite (instance/securedeal_dev.db)"
echo "- Environment: Development"
echo "- Debug Mode: Enabled"
echo "- Host: 0.0.0.0:5000"
echo ""

echo "👥 Test Users Available:"
echo "- Notaire: notaire@example.com / password123"
echo "- User 1: user@example.com / password123"
echo "- User 2: buyer@example.com / password123"
echo ""

echo "🌐 Access Points:"
echo "- Main App: http://localhost:5000"
echo "- Contracts Hub: http://localhost:5000/contracts"
echo "- Create Contract: http://localhost:5000/contracts/create"
echo ""

echo "🏁 Starting Flask development server..."
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python3 run.py run --host=0.0.0.0 --port=5000
