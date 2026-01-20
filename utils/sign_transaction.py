"""
Script utilitaire pour signer une transaction avec une clé privée.

Usage:
    python utils/sign_transaction.py <personne> <p1> <p2> <montant> [timestamp]
    
Cela génère la signature d'une transaction que vous pouvez utiliser dans POST /transactions
"""

# Import des modules standards Python
import sys  # Module pour accéder aux arguments de la ligne de commande
import base64  # Module pour encoder les signatures en base64 (pour transmission JSON/HTTP)
from pathlib import Path  # Module pour manipuler les chemins de fichiers
from datetime import datetime, timezone  # Module pour générer des timestamps ISO8601

# Import des modules de cryptographie pour signer avec RSA
from cryptography.hazmat.primitives import hashes, serialization  # hashes: SHA-256, serialization: format PEM
from cryptography.hazmat.primitives.asymmetric import padding  # padding: PSS pour signatures RSA
from cryptography.hazmat.backends import default_backend  # Backend cryptographique par défaut

# ===== CONFIGURATION =====
KEYS_DIR = Path("keys")  # Dossier où sont stockées les clés privées


def load_private_key(person: str):
    """
    Charge la clé privée d'une personne depuis le fichier.
    Paramètre: person - Nom de la personne
    Retourne: Objet clé privée RSA
    """
    # Chemin du fichier de clé privée
    private_key_file = KEYS_DIR / f"{person}_private_key.pem"
    # Vérifie que le fichier existe
    if not private_key_file.exists():
        raise FileNotFoundError(f"Clé privée non trouvée pour {person}. Générez-la d'abord avec generate_keys.py")
    
    # Ouvre le fichier en mode binaire et charge la clé privée
    with open(private_key_file, "rb") as f:  # "rb" = read binary
        # Charge la clé privée depuis le format PEM
        private_key = serialization.load_pem_private_key(
            f.read(),  # Lit tout le contenu du fichier (bytes)
            password=None,  # Pas de mot de passe (clé non chiffrée)
            backend=default_backend()  # Backend cryptographique
        )
    return private_key  # Retourne l'objet clé privée


def sign_transaction(person: str, p1: str, p2: str, amount: float, timestamp: str = None):
    """
    Signe une transaction avec la clé privée de la personne (v4).
    Paramètres:
        person: Personne qui signe (doit avoir une clé privée)
        p1: Expéditeur
        p2: Destinataire
        amount: Montant
        timestamp: Timestamp ISO8601 (optionnel, généré si absent)
    """
    # Génère un timestamp si non fourni
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()  # Timestamp UTC au format ISO8601
    
    # ===== CRÉATION DU MESSAGE À SIGNER =====
    # Créer le message à signer (même format que dans app.py: "P1|P2|timestamp|montant")
    message = f"{p1}|{p2}|{timestamp}|{amount}"  # Format identique à get_transaction_data_for_signing()
    
    # ===== CHARGEMENT DE LA CLÉ PRIVÉE =====
    # Charger la clé privée de la personne depuis le fichier
    private_key = load_private_key(person)
    
    # ===== SIGNATURE RSA =====
    # Signe le message avec la clé privée
    signature = private_key.sign(
        message.encode('utf-8'),  # Convertit le message en bytes UTF-8
        padding.PSS(  # Padding PSS (Probabilistic Signature Scheme) pour RSA
            mgf=padding.MGF1(hashes.SHA256()),  # Fonction de génération de masque utilisant SHA-256
            salt_length=padding.PSS.MAX_LENGTH  # Longueur maximale du sel pour sécurité maximale
        ),
        hashes.SHA256()  # Algorithme de hachage SHA-256
    )
    
    # ===== ENCODAGE BASE64 =====
    # Encode la signature binaire en base64 pour transmission JSON/HTTP
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # ===== AFFICHAGE DES RÉSULTATS =====
    print(f"✓ Transaction signée par {person}")
    print(f"\nMessage signé: {message}")  # Affiche le message original
    print(f"\nSignature (base64):")
    print(signature_b64)  # Affiche la signature encodée
    # Instructions pour utiliser la signature dans l'API
    print(f"\n📋 Utilisez cette signature dans POST /transactions:")
    print(f"   {{")
    print(f"     \"p1\": \"{p1}\",")
    print(f"     \"p2\": \"{p2}\",")
    print(f"     \"a\": {amount},")
    print(f"     \"t\": \"{timestamp}\",")
    print(f"     \"signature\": \"{signature_b64}\"")
    print(f"   }}")


# ===== POINT D'ENTRÉE PRINCIPAL =====
if __name__ == "__main__":  # S'exécute seulement si le script est lancé directement
    # Vérifie que les arguments minimaux sont fournis
    if len(sys.argv) < 5:  # Besoin d'au moins: script, personne, p1, p2, montant
        print("Usage: python utils/sign_transaction.py <personne> <p1> <p2> <montant> [timestamp]")
        print("Exemple: python utils/sign_transaction.py alice alice bob 100")
        sys.exit(1)  # Quitte avec code d'erreur 1
    
    # Récupère les arguments de la ligne de commande
    person = sys.argv[1]  # Personne qui signe (doit avoir une clé privée)
    p1 = sys.argv[2]  # Expéditeur
    p2 = sys.argv[3]  # Destinataire
    amount = float(sys.argv[4])  # Montant (convertit en float)
    timestamp = sys.argv[5] if len(sys.argv) > 5 else None  # Timestamp optionnel (5ème argument)
    
    try:
        sign_transaction(person, p1, p2, amount, timestamp)  # Signe la transaction
    except FileNotFoundError as e:  # Si la clé privée n'existe pas
        print(f"❌ Erreur: {e}")
        sys.exit(1)  # Quitte avec code d'erreur 1

