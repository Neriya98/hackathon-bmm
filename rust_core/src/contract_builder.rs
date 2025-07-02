use anyhow::{anyhow, Result};
use bitcoin::Network;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use miniscript::{policy::concrete::Policy, bitcoin::XOnlyPublicKey};
use miniscript::bitcoin::secp256k1::Secp256k1;

use crate::ContractResult;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ContractType {
    MultiSig,
    TimeLock, 
    Escrow,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractConfig {
    pub contract_type: ContractType,
    pub participants: Vec<String>,
    pub amount: u64,
    pub timelock: Option<u32>,
    pub network: Network,
}

pub struct ContractBuilder {
    network: Network,
    secp: Secp256k1<bitcoin::secp256k1::All>,
}

impl ContractBuilder {
    pub fn new(network: Network) -> Result<Self> {
        Ok(Self {
            network,
            secp: Secp256k1::new(),
        })
    }

    pub async fn create_contract(&self, config: &ContractConfig) -> Result<ContractResult> {
        // Validation de base
        self.validate_config(config)?;
        
        let contract_id = Uuid::new_v4().to_string();
        
        match config.contract_type {
            ContractType::MultiSig => self.create_multisig_contract(config, &contract_id).await,
            ContractType::TimeLock => self.create_timelock_contract(config, &contract_id).await,
            ContractType::Escrow => self.create_escrow_contract(config, &contract_id).await,
        }
    }

    async fn create_multisig_contract(&self, config: &ContractConfig, contract_id: &str) -> Result<ContractResult> {
        // Parser les clés publiques des participants
        let pubkeys: Result<Vec<XOnlyPublicKey>, _> = config.participants
            .iter()
            .map(|pk| pk.parse())
            .collect();
        
        let keys = pubkeys?;
        let threshold = (keys.len() + 1) / 2; // Majorité simple

        // Créer la policy comme dans votre main.rs
        let policies: Vec<Policy<XOnlyPublicKey>> = keys
            .into_iter()
            .map(Policy::Key)
            .collect();
        
        let policy: Policy<XOnlyPublicKey> = Policy::Threshold(threshold, policies);

        // Compiler vers Miniscript (contexte Taproot)
        let miniscript = policy.compile::<miniscript::Tap>()?;
        let script_pubkey = miniscript.encode();
        
        // Pour cette démo, on génère une adresse factice
        // En production, il faudrait utiliser BDK pour créer un vrai PSBT
        let address = format!("tb1p{}...example", &contract_id[..8]);
        let policy_str = format!("{}", policy);

        Ok(ContractResult {
            contract_id: contract_id.to_string(),
            psbt_base64: format!("psbt_placeholder_{}", contract_id), // Placeholder
            script_pubkey: script_pubkey.to_hex_string(),
            address,
            amount: config.amount,
            policy: policy_str,
        })
    }

    async fn create_timelock_contract(&self, config: &ContractConfig, contract_id: &str) -> Result<ContractResult> {
        if config.participants.len() != 1 {
            return Err(anyhow!("TimeLock contract requires exactly 1 participant"));
        }
        
        let timelock = config.timelock.ok_or_else(|| anyhow!("TimeLock requires timelock value"))?;
        
        // Parser la clé publique
        let pubkey: XOnlyPublicKey = config.participants[0].parse()?;
        
        // Créer policy avec timelock
        let policy: Policy<XOnlyPublicKey> = Policy::And(vec![
            Policy::Key(pubkey),
            Policy::After(timelock),
        ]);

        let miniscript = policy.compile::<miniscript::Tap>()?;
        let script_pubkey = miniscript.encode();
        
        let address = format!("tb1p{}...timelock", &contract_id[..8]);
        let policy_str = format!("{}", policy);

        Ok(ContractResult {
            contract_id: contract_id.to_string(),
            psbt_base64: format!("psbt_timelock_{}", contract_id),
            script_pubkey: script_pubkey.to_hex_string(),
            address,
            amount: config.amount,
            policy: policy_str,
        })
    }

    async fn create_escrow_contract(&self, config: &ContractConfig, contract_id: &str) -> Result<ContractResult> {
        if config.participants.len() != 3 {
            return Err(anyhow!("Escrow contract requires exactly 3 participants (buyer, seller, arbiter)"));
        }

        // Parser les 3 clés publiques
        let pubkeys: Result<Vec<XOnlyPublicKey>, _> = config.participants
            .iter()
            .map(|pk| pk.parse())
            .collect();
        
        let keys = pubkeys?;

        // Créer policy 2-of-3 pour escrow
        let policies: Vec<Policy<XOnlyPublicKey>> = keys
            .into_iter()
            .map(Policy::Key)
            .collect();
        
        let policy: Policy<XOnlyPublicKey> = Policy::Threshold(2, policies);

        let miniscript = policy.compile::<miniscript::Tap>()?;
        let script_pubkey = miniscript.encode();
        
        let address = format!("tb1p{}...escrow", &contract_id[..8]);
        let policy_str = format!("{}", policy);

        Ok(ContractResult {
            contract_id: contract_id.to_string(),
            psbt_base64: format!("psbt_escrow_{}", contract_id),
            script_pubkey: script_pubkey.to_hex_string(),
            address,
            amount: config.amount,
            policy: policy_str,
        })
    }

    fn validate_config(&self, config: &ContractConfig) -> Result<()> {
        if config.participants.is_empty() {
            return Err(anyhow!("At least one participant is required"));
        }

        if config.amount == 0 {
            return Err(anyhow!("Amount must be greater than 0"));
        }

        // Validation spécifique par type
        match config.contract_type {
            ContractType::MultiSig => {
                if config.participants.len() < 2 {
                    return Err(anyhow!("MultiSig requires at least 2 participants"));
                }
                if config.participants.len() > 15 {
                    return Err(anyhow!("MultiSig supports maximum 15 participants"));
                }
            }
            ContractType::TimeLock => {
                if config.participants.len() != 1 {
                    return Err(anyhow!("TimeLock requires exactly 1 participant"));
                }
                if config.timelock.is_none() {
                    return Err(anyhow!("TimeLock requires timelock value"));
                }
            }
            ContractType::Escrow => {
                if config.participants.len() != 3 {
                    return Err(anyhow!("Escrow requires exactly 3 participants"));
                }
            }
        }

        // Valider que les participants sont des clés publiques valides
        for participant in &config.participants {
            if participant.len() != 64 {
                return Err(anyhow!("Invalid public key format: {}", participant));
            }
            // Tenter de parser pour validation
            let _: XOnlyPublicKey = participant.parse()
                .map_err(|_| anyhow!("Invalid public key: {}", participant))?;
        }

        Ok(())
    }

    pub fn get_required_signatures(&self, config: &ContractConfig) -> u32 {
        match config.contract_type {
            ContractType::MultiSig => (config.participants.len() as u32 + 1) / 2,
            ContractType::TimeLock => 1,
            ContractType::Escrow => 2,
        }
    }
}
