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

4. **Rust Module Status**
   - The `rust_core/` directory contains a Rust module with Python bindings for Bitcoin PSBT and smart contract functionality
   - However, all imports and calls to this module are currently commented out with "Temporarily disabled" notes
   - The application appears to use a Python implementation for the same functionality

## Next Steps

1. **Decision on `rust_core/`**
   - Keep this directory as a reference for future Rust integration
   - All imports and function calls to the Rust module are currently disabled
   - The application is functioning with the Python implementation

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
