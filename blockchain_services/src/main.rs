mod handlers;

use axum::{
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use handlers::{create_wallet, create_smart_contract, root , check_balance , send_coins};
use log::{info, warn, error};

#[tokio::main]
async fn main() {
    // Initialize logger from RUST_LOG environment variable
    env_logger::init();
    
    info!("Starting blockchain services backend");
    
    // Set up routes
    let app = Router::new()
        .route("/", get(root))
        // Wallet creation endpoint
        .route("/create_wallet", get(create_wallet))
        // Smart contract (multisig) endpoints
        .route("/create_smart_contract", post(create_smart_contract))
        .route("/check_balance", post(check_balance))
        .route("/send_coins", post(send_coins));
        //.route("/create_simple_multisig", get(create_simple_multisig));

    // Run the server
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    println!("🚀 Server listening on http://{}", addr);
    println!("📝 Available endpoints:");
    println!("  GET  / - Welcome message");
    println!("  GET  /create_wallet - Create a new wallet");
    println!("  POST /create_smart_contract - Create a custom multisig smart contract");
    println!("  POST /check_balance - Check balance of an address (JSON body)");
    println!("  GET  /create_simple_multisig - Create a simple 2-of-2 multisig example");
    println!("  POST /send_coins - Send coins from hardcoded wallet");
    
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}