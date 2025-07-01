use miniscript::{policy::concrete::Policy, DescriptorPublicKey, Descriptor};
use miniscript::bitcoin::secp256k1::Secp256k1;
use miniscript::bitcoin::XOnlyPublicKey;

fn main() {
    let secp = Secp256k1::new();

    // Replace with real x-only pubkeys
    let pubkey1 = "c0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ffeec0ff";
    let pubkey2 = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef";

    let pk1: XOnlyPublicKey = pubkey1.parse().unwrap();
    let pk2: XOnlyPublicKey = pubkey2.parse().unwrap();

    // Create 2-of-2 policy
    let policy: Policy<XOnlyPublicKey> = Policy::Threshold(2, vec![
        Policy::Key(pk1),
        Policy::Key(pk2),
    ]);

    // Compile to Miniscript (Taproot context)
    let miniscript = policy.compile::<miniscript::Tap>().unwrap();

    // Convert to Script (this is the scriptPubKey for a Tapscript path)
    let script_pubkey = miniscript.encode();

    println!("scriptPubKey: {}", script_pubkey);
}
