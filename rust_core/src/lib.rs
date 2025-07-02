use pyo3::prelude::*;
use pyo3::types::PyDict;
use bitcoin::{Address, Amount, Network, Psbt, Transaction};
use miniscript::{policy::concrete::Policy, DescriptorPublicKey, Descriptor};
use miniscript::bitcoin::secp256k1::Secp256k1;
use miniscript::bitcoin::XOnlyPublicKey;
use serde::{Deserialize, Serialize};
use std::str::FromStr;
use anyhow::{anyhow, Result};
use uuid::Uuid;

mod psbt_manager;
mod contract_builder;
mod signature_handler;
mod utils;

use psbt_manager::PSBTManager;
use contract_builder::{ContractBuilder, ContractType, ContractConfig};
use signature_handler::SignatureHandler;

#[derive(Debug, Serialize, Deserialize)]
pub struct ContractResult {
    pub contract_id: String,
    pub psbt_base64: String,
    pub script_pubkey: String,
    pub address: String,
    pub amount: u64,
    pub policy: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SignatureResult {
    pub success: bool,
    pub psbt_base64: Option<String>,
    pub signatures_count: u32,
    pub required_signatures: u32,
    pub is_complete: bool,
    pub transaction_id: Option<String>,
}

/// Crée un contrat Bitcoin basé sur votre logique main.rs existante
#[pyfunction]
fn create_bitcoin_contract(
    py: Python,
    contract_type: &str,
    participants: Vec<&str>,
    amount: u64,
    timelock: Option<u32>,
    network: Option<&str>,
) -> PyResult<PyObject> {
    let network = parse_network(network.unwrap_or("signet"));
    
    let contract_config = ContractConfig {
        contract_type: match contract_type {
            "multisig" => ContractType::MultiSig,
            "timelock" => ContractType::TimeLock,
            "escrow" => ContractType::Escrow,
            _ => return Err(pyo3::exceptions::PyValueError::new_err("Invalid contract type")),
        },
        participants: participants.iter().map(|s| s.to_string()).collect(),
        amount,
        timelock,
        network,
    };

    let rt = tokio::runtime::Runtime::new().unwrap();
    let result = rt.block_on(async {
        let builder = ContractBuilder::new(network)?;
        builder.create_contract(&contract_config).await
    });

    match result {
        Ok(contract_result) => {
            let dict = PyDict::new(py);
            dict.set_item("contract_id", contract_result.contract_id)?;
            dict.set_item("psbt_base64", contract_result.psbt_base64)?;
            dict.set_item("script_pubkey", contract_result.script_pubkey)?;
            dict.set_item("address", contract_result.address)?;
            dict.set_item("amount", contract_result.amount)?;
            dict.set_item("policy", contract_result.policy)?;
            Ok(dict.into())
        }
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Failed to create contract: {}",
            e
        ))),
    }
}

/// Améliore votre logique de script existant avec support multi-sig
#[pyfunction]
fn create_multisig_script(
    py: Python,
    pubkeys: Vec<&str>,
    threshold: u32,
) -> PyResult<PyObject> {
    let result = (|| -> Result<(String, String)> {
        let secp = Secp256k1::new();
        
        // Parser les clés publiques
        let parsed_keys: Result<Vec<XOnlyPublicKey>, _> = pubkeys
            .iter()
            .map(|pk| pk.parse())
            .collect();
        
        let keys = parsed_keys?;
        
        if keys.len() < threshold as usize {
            return Err(anyhow!("Threshold cannot be greater than number of keys"));
        }

        // Créer la policy threshold comme dans votre main.rs
        let policies: Vec<Policy<XOnlyPublicKey>> = keys
            .into_iter()
            .map(Policy::Key)
            .collect();
        
        let policy: Policy<XOnlyPublicKey> = Policy::Threshold(threshold as usize, policies);

        // Compiler vers Miniscript (contexte Taproot)
        let miniscript = policy.compile::<miniscript::Tap>()?;

        // Convertir vers Script
        let script_pubkey = miniscript.encode();
        let script_hex = script_pubkey.to_hex_string();
        let policy_str = format!("{}", policy);

        Ok((script_hex, policy_str))
    })();

    match result {
        Ok((script_pubkey, policy)) => {
            let dict = PyDict::new(py);
            dict.set_item("script_pubkey", script_pubkey)?;
            dict.set_item("policy", policy)?;
            Ok(dict.into())
        }
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Failed to create multisig script: {}",
            e
        ))),
    }
}

/// Signe un PSBT avec une clé privée
#[pyfunction]
fn sign_psbt(
    py: Python,
    psbt_base64: &str,
    private_key: &str,
    network: Option<&str>,
) -> PyResult<PyObject> {
    let network = parse_network(network.unwrap_or("signet"));

    let rt = tokio::runtime::Runtime::new().unwrap();
    let result = rt.block_on(async {
        let handler = SignatureHandler::new(network)?;
        handler.sign_psbt(psbt_base64, private_key).await
    });

    match result {
        Ok(sig_result) => {
            let dict = PyDict::new(py);
            dict.set_item("success", sig_result.success)?;
            dict.set_item("psbt_base64", sig_result.psbt_base64)?;
            dict.set_item("signatures_count", sig_result.signatures_count)?;
            dict.set_item("required_signatures", sig_result.required_signatures)?;
            dict.set_item("is_complete", sig_result.is_complete)?;
            dict.set_item("transaction_id", sig_result.transaction_id)?;
            Ok(dict.into())
        }
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Failed to sign PSBT: {}",
            e
        ))),
    }
}

/// Finalise et diffuse une transaction Bitcoin
#[pyfunction]
fn finalize_transaction(
    py: Python,
    psbt_base64: &str,
    network: Option<&str>,
    broadcast: Option<bool>,
) -> PyResult<PyObject> {
    let network = parse_network(network.unwrap_or("signet"));

    let rt = tokio::runtime::Runtime::new().unwrap();
    let result = rt.block_on(async {
        let manager = PSBTManager::new(network)?;
        manager.finalize_and_broadcast(psbt_base64, broadcast.unwrap_or(false)).await
    });

    match result {
        Ok(tx_id) => {
            let dict = PyDict::new(py);
            dict.set_item("success", true)?;
            dict.set_item("transaction_id", tx_id)?;
            Ok(dict.into())
        }
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Failed to finalize transaction: {}",
            e
        ))),
    }
}

/// Valide un PSBT
#[pyfunction]
fn validate_psbt(py: Python, psbt_base64: &str) -> PyResult<PyObject> {
    let result = (|| -> Result<(bool, Option<String>)> {
        let psbt = Psbt::from_str(psbt_base64)?;
        
        // Validations de base
        if psbt.unsigned_tx.input.is_empty() {
            return Ok((false, Some("No inputs found".to_string())));
        }
        
        if psbt.unsigned_tx.output.is_empty() {
            return Ok((false, Some("No outputs found".to_string())));
        }
        
        // Vérifier que chaque input a les données nécessaires
        for (i, input) in psbt.inputs.iter().enumerate() {
            if input.witness_utxo.is_none() && input.non_witness_utxo.is_none() {
                return Ok((false, Some(format!("Input {} missing UTXO data", i))));
            }
        }
        
        Ok((true, None))
    })();

    match result {
        Ok((is_valid, error)) => {
            let dict = PyDict::new(py);
            dict.set_item("valid", is_valid)?;
            if let Some(err) = error {
                dict.set_item("error", err)?;
            }
            Ok(dict.into())
        }
        Err(e) => {
            let dict = PyDict::new(py);
            dict.set_item("valid", false)?;
            dict.set_item("error", format!("{}", e))?;
            Ok(dict.into())
        }
    }
}

/// Obtient les informations d'un PSBT
#[pyfunction]
fn get_psbt_info(py: Python, psbt_base64: &str) -> PyResult<PyObject> {
    let result = (|| -> Result<PyObject> {
        let psbt = Psbt::from_str(psbt_base64)?;
        let dict = PyDict::new(py);
        
        // Informations de base
        dict.set_item("input_count", psbt.unsigned_tx.input.len())?;
        dict.set_item("output_count", psbt.unsigned_tx.output.len())?;
        dict.set_item("version", psbt.unsigned_tx.version.0)?;
        dict.set_item("lock_time", psbt.unsigned_tx.lock_time.to_consensus_u32())?;
        
        // Montants
        let total_output: u64 = psbt.unsigned_tx.output.iter()
            .map(|output| output.value.to_sat())
            .sum();
        dict.set_item("total_output_amount", total_output)?;
        
        // Statut des signatures
        let signatures_count: usize = psbt.inputs.iter()
            .map(|input| input.partial_sigs.len())
            .sum();
        dict.set_item("signatures_count", signatures_count)?;
        
        // Estimation des frais
        if !psbt.inputs.is_empty() {
            let estimated_size = psbt.unsigned_tx.weight().to_wu() / 4; // Estimation approximative
            dict.set_item("estimated_size_bytes", estimated_size)?;
        }
        
        Ok(dict.into())
    })();

    match result {
        Ok(info) => Ok(info),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Failed to get PSBT info: {}",
            e
        ))),
    }
}

/// Utilitaire pour parser le réseau
fn parse_network(network_str: &str) -> Network {
    match network_str.to_lowercase().as_str() {
        "mainnet" | "bitcoin" => Network::Bitcoin,
        "testnet" => Network::Testnet,
        "signet" => Network::Signet,
        "regtest" => Network::Regtest,
        _ => Network::Signet, // Par défaut
    }
}

/// Module Python principal
#[pymodule]
fn securedeal_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_bitcoin_contract, m)?)?;
    m.add_function(wrap_pyfunction!(create_multisig_script, m)?)?;
    m.add_function(wrap_pyfunction!(sign_psbt, m)?)?;
    m.add_function(wrap_pyfunction!(finalize_transaction, m)?)?;
    m.add_function(wrap_pyfunction!(validate_psbt, m)?)?;
    m.add_function(wrap_pyfunction!(get_psbt_info, m)?)?;
    Ok(())
}
