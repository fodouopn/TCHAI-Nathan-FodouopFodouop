"""
Script utilitaire pour générer des paires de clés RSA pour Tchaï v4.

Usage:
    python utils/generate_keys.py <personne>
    
Cela génère une paire de clés (privée et publique) pour une personne.
La clé privée est sauvegardée localement (à garder secrète).
La clé publique doit être enregistrée dans le système via POST /keys/<personne>
"""

import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

KEYS_DIR = Path("keys")


def generate_key_pair(person: str):
    """
    Génère une paire de clés RSA pour une personne.
    """
    # Créer le dossier keys s'il n'existe pas
    KEYS_DIR.mkdir(exist_ok=True)
    
    # Générer la paire de clés
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    # Sauvegarder la clé privée (format PEM)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    private_key_file = KEYS_DIR / f"{person}_private_key.pem"
    with open(private_key_file, "wb") as f:
        f.write(private_key_pem)
    print(f"✓ Clé privée sauvegardée : {private_key_file}")
    print("  ⚠️  GARDEZ CETTE CLÉ SECRÈTE !")
    
    # Afficher la clé publique (format PEM)
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    print(f"\n✓ Clé publique pour {person}:")
    print("-" * 60)
    print(public_key_pem)
    print("-" * 60)
    print("\n📋 Copiez cette clé publique et enregistrez-la dans le système:")
    print(f"   POST http://localhost:5000/keys/{person}")
    print("   Body: {\"public_key\": \"...\"}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils/generate_keys.py <personne>")
        print("Exemple: python utils/generate_keys.py alice")
        sys.exit(1)
    
    person = sys.argv[1]
    generate_key_pair(person)

