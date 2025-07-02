use bitcoin::Network;
use anyhow::Result;

/// Convertit une chaîne de réseau en enum Bitcoin Network
pub fn parse_network(network_str: &str) -> Network {
    match network_str.to_lowercase().as_str() {
        "mainnet" | "bitcoin" => Network::Bitcoin,
        "testnet" => Network::Testnet,
        "signet" => Network::Signet,
        "regtest" => Network::Regtest,
        _ => Network::Signet, // Par défaut pour le développement
    }
}

/// Valide le format d'une clé publique hex
pub fn validate_pubkey_format(pubkey: &str) -> Result<()> {
    if pubkey.len() != 64 {
        return Err(anyhow::anyhow!("Public key must be 64 characters long"));
    }
    
    // Vérifier que c'est un hex valide
    hex::decode(pubkey).map_err(|_| anyhow::anyhow!("Invalid hex format"))?;
    
    Ok(())
}

/// Génère un ID unique pour un contrat
pub fn generate_contract_id() -> String {
    uuid::Uuid::new_v4().to_string()
}

/// Utilitaires pour les montants Bitcoin
pub mod amounts {
    /// Convertit des satoshis en BTC
    pub fn sats_to_btc(sats: u64) -> f64 {
        sats as f64 / 100_000_000.0
    }
    
    /// Convertit des BTC en satoshis
    pub fn btc_to_sats(btc: f64) -> u64 {
        (btc * 100_000_000.0) as u64
    }
    
    /// Valide qu'un montant en satoshis est valide
    pub fn validate_amount(sats: u64) -> bool {
        sats > 0 && sats <= 21_000_000 * 100_000_000 // Max Bitcoin supply
    }
}

/// Utilitaires pour les frais de transaction
pub mod fees {
    /// Calcule les frais recommandés basés sur la priorité
    pub fn get_recommended_fee_rate(priority: &str) -> u64 {
        match priority {
            "low" => 1,      // 1 sat/vB pour transactions non urgentes
            "medium" => 10,  // 10 sat/vB pour transactions normales
            "high" => 20,    // 20 sat/vB pour transactions prioritaires
            _ => 10,         // Par défaut
        }
    }
    
    /// Estime la taille d'une transaction basique
    pub fn estimate_tx_size(inputs: usize, outputs: usize) -> usize {
        // Estimation approximative pour transactions P2TR
        10 + (inputs * 58) + (outputs * 43)
    }
}

/// Utilitaires de validation
pub mod validation {
    use super::*;
    
    /// Valide une liste de participants pour un contrat
    pub fn validate_participants(participants: &[String], min: usize, max: usize) -> Result<()> {
        if participants.len() < min {
            return Err(anyhow::anyhow!("Minimum {} participants required", min));
        }
        
        if participants.len() > max {
            return Err(anyhow::anyhow!("Maximum {} participants allowed", max));
        }
        
        // Vérifier les doublons
        let mut unique_participants = std::collections::HashSet::new();
        for participant in participants {
            if !unique_participants.insert(participant) {
                return Err(anyhow::anyhow!("Duplicate participant found: {}", participant));
            }
            
            // Valider le format de chaque clé publique
            validate_pubkey_format(participant)?;
        }
        
        Ok(())
    }
    
    /// Valide un timelock
    pub fn validate_timelock(timelock: u32) -> Result<()> {
        let current_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() as u32;
        
        if timelock <= current_time {
            return Err(anyhow::anyhow!("Timelock must be in the future"));
        }
        
        // Vérifier que le timelock n'est pas trop loin dans le futur (max 2 ans)
        let max_future = current_time + (2 * 365 * 24 * 60 * 60);
        if timelock > max_future {
            return Err(anyhow::anyhow!("Timelock too far in the future"));
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_network() {
        assert_eq!(parse_network("mainnet"), Network::Bitcoin);
        assert_eq!(parse_network("testnet"), Network::Testnet);
        assert_eq!(parse_network("signet"), Network::Signet);
        assert_eq!(parse_network("regtest"), Network::Regtest);
        assert_eq!(parse_network("invalid"), Network::Signet);
    }
    
    #[test]
    fn test_amounts() {
        assert_eq!(amounts::sats_to_btc(100_000_000), 1.0);
        assert_eq!(amounts::btc_to_sats(1.0), 100_000_000);
        assert!(amounts::validate_amount(1000));
        assert!(!amounts::validate_amount(0));
    }
    
    #[test]
    fn test_validate_pubkey_format() {
        let valid_pubkey = "c0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ff";
        assert!(validate_pubkey_format(valid_pubkey).is_ok());
        
        let invalid_pubkey = "invalid";
        assert!(validate_pubkey_format(invalid_pubkey).is_err());
    }
}
