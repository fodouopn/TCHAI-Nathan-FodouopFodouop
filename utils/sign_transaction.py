"""
Script utilitaire pour signer une transaction avec une clé privée.

Usage:
    python utils/sign_transaction.py <personne> <p1> <p2> <montant> [timestamp]
    
Cela génère la signature d'une transaction que vous pouvez utiliser dans POST /transactions
"""

import sys
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timezone

KEYS_DIR = Path("keys")


def load_private_key(person: str):
    """Charge la clé privée d'une personne."""
    private_key_file = KEYS_DIR / f"{person}_private_key.pem"
    if not private_key_file.exists():
        raise FileNotFoundError(f"Clé privée non trouvée pour {person}. Générez-la d'abord avec generate_keys.py")
    
    with open(private_key_file, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    return private_key


def sign_transaction(person: str, p1: str, p2: str, amount: float, timestamp: str = None):
    """
    Signe une transaction.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    
    # Créer le message à signer (même format que dans app.py)
    message = f"{p1}|{p2}|{timestamp}|{amount}"
    
    # Charger la clé privée
    private_key = load_private_key(person)
    
    # Signer
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Encoder en base64
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    print(f"✓ Transaction signée par {person}")
    print(f"\nMessage signé: {message}")
    print(f"\nSignature (base64):")
    print(signature_b64)
    print(f"\n📋 Utilisez cette signature dans POST /transactions:")
    print(f"   {{")
    print(f"     \"p1\": \"{p1}\",")
    print(f"     \"p2\": \"{p2}\",")
    print(f"     \"a\": {amount},")
    print(f"     \"t\": \"{timestamp}\",")
    print(f"     \"signature\": \"{signature_b64}\"")
    print(f"   }}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python utils/sign_transaction.py <personne> <p1> <p2> <montant> [timestamp]")
        print("Exemple: python utils/sign_transaction.py alice alice bob 100")
        sys.exit(1)
    
    person = sys.argv[1]
    p1 = sys.argv[2]
    p2 = sys.argv[3]
    amount = float(sys.argv[4])
    timestamp = sys.argv[5] if len(sys.argv) > 5 else None
    
    try:
        sign_transaction(person, p1, p2, amount, timestamp)
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

