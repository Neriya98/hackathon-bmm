use axum::Json;
use serde::{Deserialize, Serialize};
use bdk_wallet::bitcoin::bip32::Xpriv;
use bdk_wallet::bitcoin::secp256k1::rand;
use bdk_wallet::bitcoin::secp256k1::rand::RngCore;
use bdk_wallet::bitcoin::Network;
use bdk_wallet::template::{Bip86, DescriptorTemplate};
use bdk_wallet::{KeychainKind, Wallet};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use std::str::FromStr;
use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use bdk_esplora::EsploraExt;


use std::sync::Arc;
use miniscript::bitcoin::secp256k1::Secp256k1;
use miniscript::bitcoin::{PublicKey};
use miniscript::policy::concrete::Policy;
use miniscript::Threshold;
use miniscript::{Descriptor, Tap};
use miniscript::descriptor::TapTree;

use bdk_esplora::esplora_client::{self, Builder};

use bdk_wallet::bitcoin::{Amount, FeeRate, Psbt, Address};
use bdk_wallet::rusqlite::Connection;
use bdk_wallet::{AddressInfo, SignOptions};


// --- Your existing structs and handlers ---
pub async fn root() -> &'static str {
    "Welcome to my Rust API"
}

// --- New Wallet Creation Logic ---

/// The JSON response for a newly created wallet.
#[derive(Serialize)]
pub struct WalletResponse {
    /// The secret seed phrase, encoded in hexadecimal. **SAVE THIS!**
    seed: String,
    /// The first public receiving address (Taproot).
    address: String,
    /// The external descriptor (for receiving addresses)
    external_descriptor: String,
    /// The internal descriptor (for change addresses)  
    internal_descriptor: String,
    /// The master private key
    master_private_key: String,
    /// The network this wallet is for
    network: String,
}

/// Error response for wallet operations
#[derive(Serialize)]
pub struct ErrorResponse {
    error: String,

}

/// Custom error type for wallet operations
pub struct WalletError(String);

impl IntoResponse for WalletError {
    fn into_response(self) -> Response {
        let error_response = ErrorResponse {
            error: self.0,
        };
        (StatusCode::INTERNAL_SERVER_ERROR, Json(error_response)).into_response()
    }
}

impl From<Box<dyn std::error::Error>> for WalletError {
    fn from(err: Box<dyn std::error::Error>) -> Self {
        WalletError(err.to_string())
    }
}


/// Handler to generate a new wallet.
pub async fn create_wallet() -> Result<Json<WalletResponse>, WalletError> {
    // 1. Generate random seed
    let mut seed: [u8; 32] = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut seed);
    
    // 2. Set network (you can make this configurable)
    let network: Network = Network::Signet;
    
    // 3. Create master private key from seed
    let xprv: Xpriv = Xpriv::new_master(network, &seed)
        .map_err(|e| WalletError(format!("Failed to create master key: {}", e)))?;
    
    // 4. Build external descriptor (receiving addresses)
    let (external_descriptor, external_key_map, _) = Bip86(xprv, KeychainKind::External)
        .build(network)
        .map_err(|e| WalletError(format!("Failed to build external descriptor: {}", e)))?;
    
    // 5. Build internal descriptor (change addresses)  
    let (internal_descriptor, internal_key_map, _) = Bip86(xprv, KeychainKind::Internal)
        .build(network)
        .map_err(|e| WalletError(format!("Failed to build internal descriptor: {}", e)))?;
    
    // 6. Get descriptor strings with private keys
    let external_descriptor_string = external_descriptor.to_string_with_secret(&external_key_map);
    let internal_descriptor_string = internal_descriptor.to_string_with_secret(&internal_key_map);

    
    // 7. Create wallet to generate first address
    let mut wallet = Wallet::create(external_descriptor.clone(), internal_descriptor.clone())
        .network(network)
        .create_wallet_no_persist()
        .map_err(|e| WalletError(format!("Failed to create wallet: {}", e)))?;
    
    // 8. Get the first receiving address
    let first_address = wallet.next_unused_address(KeychainKind::External).address.to_string();
    
    // 9. Convert seed to hex string
    let seed_hex = hex::encode(seed);
    
    
    // 10. Create response
    let response = WalletResponse {
        seed: seed_hex,
        address: first_address,
        external_descriptor: external_descriptor_string,
        internal_descriptor: internal_descriptor_string,
        master_private_key: xprv.to_string(),
        network: format!("{:?}", network),
    };
    // 11. Return the response
    Ok(Json(response))
}




//createtion du smart contract

/// Request structure for creating a multisig smart contract
#[derive(Deserialize)]
pub struct CreateSmartContractRequest {
    /// Array of public keys (hex-encoded)
    public_keys: Vec<String>,
    /// Number of signatures required (threshold)
    threshold: usize,
    /// Optional network (defaults to Signet)
    network: Option<String>,
}

/// Response structure for a created smart contract
#[derive(Serialize)]
pub struct SmartContractResponse {
    /// The policy as string
    policy: String,
    /// The miniscript as string
    miniscript: String,
    /// The Taproot descriptor
    descriptor: String,
    /// The address for this smart contract
    address: String,
    /// The network
    network: String,
    /// Threshold information
    threshold: usize,
    /// Number of public keys
    total_keys: usize,
}

// Handler to create a smart contract (multisig)
pub async fn create_smart_contract(
    Json(payload): Json<CreateSmartContractRequest>,
) -> Result<Json<SmartContractResponse>, WalletError> {
    
    // 1. Validate input
    if payload.public_keys.is_empty() {
        return Err(WalletError("Public keys array cannot be empty".to_string()));
    }
    
    if payload.threshold == 0 || payload.threshold > payload.public_keys.len() {
        return Err(WalletError(format!(
            "Invalid threshold: {} (must be between 1 and {})", 
            payload.threshold, 
            payload.public_keys.len()
        )));
    }
    
    // 2. Parse network
    let network = match payload.network.as_deref() {
        Some("mainnet") => Network::Bitcoin,
        Some("testnet") => Network::Testnet,
        Some("regtest") => Network::Regtest,
        Some("signet") | None => Network::Signet,
        Some(other) => return Err(WalletError(format!("Unknown network: {}", other))),
    };
    
    // 3. Parse public keys
    let mut public_keys = Vec::new();
    for (i, pk_str) in payload.public_keys.iter().enumerate() {
        let pk = PublicKey::from_str(pk_str)
            .map_err(|e| WalletError(format!("Invalid public key at index {}: {}", i, e)))?;
        public_keys.push(pk);
    }
    
    // 4. Create policies for each public key
    let key_policies: Vec<Arc<Policy<PublicKey>>> = public_keys
        .iter()
        .map(|pk| Arc::new(Policy::Key(*pk)))
        .collect();
    
    // 5. Create threshold policy
    let threshold = Threshold::new(payload.threshold, key_policies)
        .map_err(|e| WalletError(format!("Failed to create threshold: {}", e)))?;
    
    let policy = Policy::Thresh(threshold);
    
    // 6. Compile policy to miniscript
    let miniscript = policy.compile::<Tap>()
        .map_err(|e| WalletError(format!("Failed to compile policy: {}", e)))?;
    
    // 7. Create Taproot descriptor
    // Use the first public key as the internal key (you might want to use a different approach)
    let internal_key = public_keys[0];
    let tap_tree = TapTree::Leaf(Arc::new(miniscript.clone()));
    let descriptor = Descriptor::new_tr(internal_key, Some(tap_tree))
        .map_err(|e| WalletError(format!("Failed to create descriptor: {}", e)))?;
    
    // 8. Generate address
    let address = descriptor.address(network)
        .map_err(|e| WalletError(format!("Failed to generate address: {}", e)))?;
    
    // 9. Create response
    let response = SmartContractResponse {
        policy: policy.to_string(),
        miniscript: miniscript.to_string(),
        descriptor: descriptor.to_string(),
        address: address.to_string(),
        network: format!("{:?}", network),
        threshold: payload.threshold,
        total_keys: payload.public_keys.len(),
    };
    
    Ok(Json(response))
}




//get balance
// Response structure for address balance
#[derive(Serialize)]
pub struct BalanceResponse {
    /// The address that was checked
    address: String,
    /// Confirmed balance in satoshis
    confirmed_balance: u64,
    /// Unconfirmed balance in satoshis  
    unconfirmed_balance: u64,
    /// Total balance in satoshis
    total_balance: u64,
    /// Balance in BTC (for readability)
    balance_btc: f64,
    /// Network used
    network: String,
}

// Define the structure for the incoming JSON request
#[derive(Deserialize)]
pub struct CheckBalanceRequest {
    pub address: String,
    pub network: Option<String>,
}

// Handler to check balance of a public address
pub async fn check_balance(
    Json(payload): Json<CheckBalanceRequest>,
) -> Result<Json<BalanceResponse>, WalletError> {

    
    // 1. Parse network and determine Esplora URL
    let (network, esplora_url) = match payload.network.as_deref() {
        Some("mainnet") => (Network::Bitcoin, "https://blockstream.info/api/"),
        Some("testnet") => (Network::Testnet, "https://blockstream.info/testnet/api/"),
        Some("regtest") => return Err(WalletError("Regtest not supported for balance checking".to_string())),
        Some("signet") | None => (Network::Signet, "https://blockstream.info/signet/api/"),
        Some(other) => return Err(WalletError(format!("Unknown network: {}", other))),
    };
    
    // 2. Validate the address
    let address = Address::from_str(&payload.address)
        .map_err(|e| WalletError(format!("Invalid address: {}", e)))?
        .require_network(network)
        .map_err(|e| WalletError(format!("Address not valid for network {}: {}", network, e)))?;
    
    // 3. Create Esplora client
    let client = Builder::new(esplora_url)
        .build_blocking();
    
    // 4. Get address stats from Esplora
    let address_stats = client
        .get_address_stats(&address)
        .map_err(|e| WalletError(format!("Failed to fetch address info: {}", e)))?;
    
    // 5. Calculate balances
    let confirmed_balance = address_stats.chain_stats.funded_txo_sum - address_stats.chain_stats.spent_txo_sum;
    let unconfirmed_balance = address_stats.mempool_stats.funded_txo_sum - address_stats.mempool_stats.spent_txo_sum;
    let total_balance = confirmed_balance + unconfirmed_balance;
    
    // 6. Convert to BTC for readability
    let balance_btc = total_balance as f64 / 100_000_000.0;
    
    // 7. Create response
    let response = BalanceResponse {
        address: payload.address,
        confirmed_balance,
        unconfirmed_balance,
        total_balance,
        balance_btc,
        network: format!("{:?}", network),
    };
    
    Ok(Json(response))
}

//send a transaction

 // create and send a transaction
    // Request structure for sending coins
    #[derive(Deserialize)]
    pub struct SendCoinsRequest {
        /// Destination address to send coins to
        to_address: String,
        /// Amount to send in satoshis
        amount_sat: u64,
        /// Fee rate in sat/vB (optional, defaults to 4)
        fee_rate: Option<u64>,
        /// Optional network (defaults to Signet)
        network: Option<String>,
    }

    /// Response structure for send transaction
    #[derive(Serialize)]
    pub struct SendTransactionResponse {
        /// Transaction ID of the broadcast transaction
        txid: String,
        /// Amount sent in satoshis
        amount_sent: u64,
        /// Fee paid in satoshis
        fee_paid: u64,
        /// Destination address
        to_address: String,
        /// Network used
        network: String,
        /// Wallet balance after transaction
        remaining_balance: u64,
    }

    /// Constants for wallet descriptors
const EXTERNAL_DESCRIPTOR: &str = "tr(tprv8ZgxMBicQKsPeLghCWZTwDejxQKobZ5EK8sSkcoCG1JZaSQ84zBoSyJP2kSdtcpxufTCUq85Unjy4TKiTpuuWtfavqPmCks89k8dhrQtKFx/86'/1'/0'/0/*)#f4uvc87f";
const INTERNAL_DESCRIPTOR: &str = "tr(tprv8ZgxMBicQKsPeLghCWZTwDejxQKobZ5EK8sSkcoCG1JZaSQ84zBoSyJP2kSdtcpxufTCUq85Unjy4TKiTpuuWtfavqPmCks89k8dhrQtKFx/86'/1'/0'/1/*)#cped9jw3";
const STOP_GAP: usize = 10;
const PARALLEL_REQUESTS: usize = 5;

/// Handler to create, sign, and broadcast a transaction from a hardcoded wallet.
/// This function now operates on a persistent wallet stored in "test_wallet.sqlite3".
pub async fn send_coins(
    Json(payload): Json<SendCoinsRequest>,
) -> Result<Json<SendTransactionResponse>, WalletError> {
    
    // Parse destination address
    let to_address = Address::from_str(&payload.to_address)
        .unwrap()
        .require_network(Network::Signet)
        .unwrap();
    
    let descriptor: &str = "tr(tprv8ZgxMBicQKsPeLghCWZTwDejxQKobZ5EK8sSkcoCG1JZaSQ84zBoSyJP2kSdtcpxufTCUq85Unjy4TKiTpuuWtfavqPmCks89k8dhrQtKFx/86'/1'/0'/0/*)#f4uvc87f";
    let change_descriptor: &str = "tr(tprv8ZgxMBicQKsPeLghCWZTwDejxQKobZ5EK8sSkcoCG1JZaSQ84zBoSyJP2kSdtcpxufTCUq85Unjy4TKiTpuuWtfavqPmCks89k8dhrQtKFx/86'/1'/0'/1/*)#cped9jw3";
    
    // Initiate the connection to the database
    let file_path = "wallet_BD.sqlite3";
    let mut conn = Connection::open(file_path)
    .map_err(|e| WalletError(format!("Failed to open database: {}", e)))?;
    
    // Create the wallet
    let wallet_opt = Wallet::load()
        .descriptor(KeychainKind::External, Some(descriptor))
        .descriptor(KeychainKind::Internal, Some(change_descriptor))
        .extract_keys()
        .check_network(Network::Signet)
        .load_wallet(&mut conn)
        .unwrap();
    
    let mut wallet = if let Some(loaded_wallet) = wallet_opt {
        loaded_wallet
    } else {
        Wallet::create(descriptor, change_descriptor)
            .network(Network::Signet)
            .create_wallet(&mut conn)
            .unwrap()
    };
    
    // Sync the wallet
    let client: esplora_client::BlockingClient =
        Builder::new("https://blockstream.info/signet/api/").build_blocking();
    
    let full_scan_request = wallet.start_full_scan();
    let update = client
        .full_scan(full_scan_request, STOP_GAP, PARALLEL_REQUESTS)
        .unwrap();
    
    // Apply the update from the full scan to the wallet
    wallet.apply_update(update).unwrap();
    
    let balance = wallet.balance();
    let initial_balance = balance.total().to_sat();
    
    if initial_balance < payload.amount_sat {
        return Err(WalletError(format!(
            "Insufficient balance: {} sat available, {} sat requested", 
            initial_balance, 
            payload.amount_sat
        )));
    }
    
    // Create a transaction
    let send_amount: Amount = Amount::from_sat(payload.amount_sat);
    let fee_rate_value = payload.fee_rate.unwrap_or(4);
    
    let mut builder = wallet.build_tx();
    builder
        .fee_rate(FeeRate::from_sat_per_vb(fee_rate_value).unwrap())
        .add_recipient(to_address.script_pubkey(), send_amount);
    
    let mut psbt: Psbt = builder.finish().unwrap();
    let finalized = wallet.sign(&mut psbt, SignOptions::default()).unwrap();
    assert!(finalized);
    
    let tx = psbt.extract_tx().unwrap();
    
    // Calculate estimated fee
    let estimated_fee = (tx.vsize() as u64) * fee_rate_value;
    
    client.broadcast(&tx).unwrap();
    
    wallet.persist(&mut conn).expect("Cannot persist");
    
    // Calculate remaining balance
    let remaining_balance = initial_balance - payload.amount_sat - estimated_fee;
    
    let response = SendTransactionResponse {
        txid: tx.compute_txid().to_string(),
        amount_sent: payload.amount_sat,
        fee_paid: estimated_fee,
        to_address: payload.to_address,
        network: "Signet".to_string(),
        remaining_balance,
    };
    
    Ok(Json(response))
}

// /// Request structure for generating addresses from existing descriptors
// #[derive(Deserialize)]
// pub struct GenerateAddressRequest {
//     external_descriptor: String,
//     internal_descriptor: String,
//     count: Option<u32>, // Optional, defaults to 1
//     network: Option<String>, // Optional, defaults to "Signet"
// }

// /// Response for address generation
// #[derive(Serialize)]
// pub struct AddressResponse {
//     addresses: Vec<String>,
//     network: String,
// }