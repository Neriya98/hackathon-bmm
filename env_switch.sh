#!/bin/bash
# env_switch.sh - Switch between development and production environments

if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
    echo "🚀 Switching to PRODUCTION environment..."
    cp .env.production .env
    echo "✅ Production environment activated!"
    echo "⚠️ IMPORTANT: Remember to update sensitive values like passwords and API keys in .env"
elif [ "$1" == "dev" ] || [ "$1" == "development" ]; then
    echo "🛠️ Switching to DEVELOPMENT environment..."
    cp .env.development .env
    echo "✅ Development environment activated!"
else
    echo "❓ Please specify which environment to use:"
    echo "   ./env_switch.sh dev  - Switch to development environment"
    echo "   ./env_switch.sh prod - Switch to production environment"
    exit 1
fi

# Verify the environment type
grep "FLASK_ENV" .env
