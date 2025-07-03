# Project Structure Reorganization

## Changes Made

1. **Reorganized Flask Routes**
   - Split routes into logical modules: `auth.py`, `contracts.py`, `invitations.py`, and `main.py`
   - Registered each as a blueprint with a unique name to avoid conflicts
   - Simplified `main.py` to remove legacy code

2. **Moved Contract Templates**
   - HTML templates moved from `CONTRACT/` to `app/templates/contract_templates/`
   - JSON contract data moved from `CONTRACT/` to `app/static/js/contract_templates/`

3. **Cleaned Up Unnecessary Files**
   - Removed backup files, logs, `__pycache__` directories, and redundant test scripts
   - Removed duplicate template files

4. **Rust Backend Status**
   - The `blockchain_services/` directory contains a Rust backend service that provides Bitcoin wallet and smart contract functionality via HTTP API
   - The Flask app communicates with this Rust backend through the `SmartContractService` class
   - All blockchain operations should be delegated to this Rust backend for better performance and security

## Next Steps

1. **Complete Migration to Rust Backend**
   - All smart contract and blockchain operations should be handled by the Rust backend
   - Update all Python placeholder implementations to use the Rust backend API
   - Remove any remaining references to the obsolete `rust_core` module

2. **Complete Documentation**
   - Update README with new project structure
   - Document the role of each component

3. **Further Improvements**
   - Consider containerizing the application for easier deployment
   - Add comprehensive testing for the new structure
   - Review error handling and logging

## Running the Application

To start the application:
```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Initialize the database (if needed)
python run.py init-db

# Start the application
./start_app.sh
# or
python run.py run
```
