#!/bin/bash
# cleanup.sh
# Script to clean up unnecessary files in the DealSure project

echo "🧹 Cleaning up DealSure project..."

# Remove compiled Python files
echo "Removing __pycache__ directories..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete

# Remove logs
echo "Removing log files..."
find . -name "*.log" -delete

# Remove backup files
echo "Removing backup files..."
find . -name "*~" -delete
find . -name "*.bak" -delete
find . -name "*.swp" -delete
find . -name "*.old" -delete

# Remove IDE-specific files
echo "Removing IDE-specific files..."
find . -name ".idea" -type d -exec rm -rf {} +
find . -name ".vscode" -type d -exec rm -rf {} +
find . -name "*.sublime-*" -delete

# Clean up Rust artifacts if needed (be careful with this)
# Uncomment if you want to clean Rust build artifacts
# echo "Cleaning Rust build artifacts..."
# cd blockchain_services && cargo clean && cd ..

echo "✅ Cleanup complete!"
