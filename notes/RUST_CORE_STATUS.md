# Rust Core Implementation Status

The `rust_core` folder contains a Rust module with Python bindings for Bitcoin PSBT and smart contract functionality. This is a critical part of the application's architecture for handling Bitcoin smart contracts.

## Current Status
- The Rust module needs to be built and installed to enable the smart contract functionality
- All imports and calls to this module are currently commented out with 'Temporarily disabled' notes
- The application is temporarily using a Python implementation as a placeholder

## Enabling the Rust Core
To enable the Rust core implementation:

1. Build the Rust extension:
   ```
   python run.py build-rust
   ```

2. Install the built Rust extension:
   ```
   python run.py install-rust
   ```

3. Uncomment the imports and function calls in:
   - `app/api/contracts.py`
   - `app/api/psbt.py`
   - `app/api/psbt_simple.py`

## Architecture Note
The Python Flask application serves as the frontend and application layer, while the Rust implementation handles the core Bitcoin smart contract functionality for better performance and security.
