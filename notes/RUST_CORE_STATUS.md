# Rust Backend Implementation

The project now uses a standalone Rust backend service in the `blockchain_services` folder that provides Bitcoin wallet and smart contract functionality through an HTTP API.

## Current Status
- The Rust backend runs as a separate service exposing an HTTP API on port 3000
- The Flask application communicates with this backend through the `SmartContractService` class
- All blockchain and Bitcoin operations should be handled by this Rust backend

## Running the Rust Backend
To run the Rust backend service:

1. Navigate to the blockchain_services directory:
   ```
   cd blockchain_services
   ```

2. Build and run the service:
   ```
   cargo run
   ```

3. The service will be available at http://localhost:3000

## Architecture Note
The Python Flask application serves as the frontend and application layer, while the Rust backend handles the core Bitcoin smart contract functionality for better performance and security.

## API Endpoints
The Rust backend provides the following endpoints:

- `GET /` - Welcome message
- `GET /create_wallet` - Create a new wallet
- `POST /create_smart_contract` - Create a custom multisig smart contract
- `POST /check_balance` - Check balance of an address
- `POST /send_coins` - Send coins from wallet
