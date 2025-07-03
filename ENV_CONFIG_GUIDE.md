# DealSure Environment Configuration Guide

This document explains the environment configuration for the DealSure project.

## Environment Files

The project uses three environment files:

- **`.env`** - The active configuration file used by the application
- **`.env.development`** - Template for development settings
- **`.env.production`** - Template for production settings

## Switching Environments

Use the provided script to switch between environments:

```bash
# Switch to development environment
./env_switch.sh dev

# Switch to production environment
./env_switch.sh prod
```

## Key Environment Variables

### Application Environment
- Development: `FLASK_ENV=development`, `FLASK_DEBUG=True`
- Production: `FLASK_ENV=production`, `FLASK_DEBUG=False`

### Database
- Development: `DATABASE_URL=sqlite:///dealsure.db`
- Production: `DATABASE_URL=postgresql://username:password@localhost/dealsure`

### Security
- Development: `SESSION_COOKIE_SECURE=False`
- Production: `SESSION_COOKIE_SECURE=True` (requires HTTPS)

### Blockchain
- Configure Bitcoin network settings in both files
- Production requires `BITCOIN_RPC_USER` and `BITCOIN_RPC_PASSWORD`

### Rust Backend
- Development: `RUST_LOG=info` (more verbose for debugging)
- Production: `RUST_LOG=warn` (only warnings and errors)

## Production Deployment

When deploying to production:

1. Copy the production configuration to the server
2. Update sensitive values like passwords and API keys
3. Ensure all required services (Redis, PostgreSQL) are running

```bash
# On your production server
cp .env.production .env
nano .env  # Edit sensitive values
```
