"""
Script utilitaire pour générer des paires de clés RSA pour Tchaï v4.

Usage:
    python utils/generate_keys.py <personne>
    
Cela génère une paire de clés (privée et publique) pour une personne.
La clé privée est sauvegardée localement (à garder secrète).
La clé publique doit être enregistrée dans le système via POST /keys/<personne>
"""

# Import des modules standards Python
import sys  # Module pour accéder aux arguments de la ligne de commande (sys.argv)
from pathlib import Path  # Module pour manipuler les chemins de fichiers de manière portable

# Import des modules de cryptographie pour générer des clés RSA
from cryptography.hazmat.primitives.asymmetric import rsa  # Module pour générer des clés RSA
from cryptography.hazmat.primitives import serialization  # Module pour sérialiser les clés au format PEM
from cryptography.hazmat.backends import default_backend  # Backend cryptographique par défaut

# ===== CONFIGURATION =====
KEYS_DIR = Path("keys")  # Dossier où seront stockées les clés privées (à garder secrètes)


def generate_key_pair(person: str):
    """
    Génère une paire de clés RSA pour une personne (v4).
    Paramètre: person - Nom de la personne pour qui générer les clés
    """
    # Créer le dossier keys s'il n'existe pas (exist_ok=True évite l'erreur si déjà présent)
    KEYS_DIR.mkdir(exist_ok=True)
    
    # ===== GÉNÉRATION DE LA PAIRE DE CLÉS RSA =====
    # Génère une clé privée RSA avec les paramètres standards de sécurité
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Exposant public standard (nombre premier de Fermat, rapide et sécurisé)
        key_size=2048,  # Taille de la clé en bits (2048 bits = niveau de sécurité recommandé)
        backend=default_backend()  # Backend cryptographique par défaut
    )
    # Extrait la clé publique correspondante (dérivée de la clé privée)
    public_key = private_key.public_key()
    
    # ===== SAUVEGARDE DE LA CLÉ PRIVÉE (format PEM) =====
    # Convertit la clé privée en format PEM (Privacy-Enhanced Mail) pour stockage
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,  # Format PEM (texte avec en-têtes)
        format=serialization.PrivateFormat.PKCS8,  # Format PKCS#8 (standard)
        encryption_algorithm=serialization.NoEncryption()  # Pas de chiffrement (stockage local)
    )
    
    # Chemin du fichier de clé privée
    private_key_file = KEYS_DIR / f"{person}_private_key.pem"
    # Sauvegarde la clé privée dans un fichier binaire
    with open(private_key_file, "wb") as f:  # "wb" = write binary
        f.write(private_key_pem)  # Écrit les bytes de la clé privée
    print(f"✓ Clé privée sauvegardée : {private_key_file}")
    print("  ⚠️  GARDEZ CETTE CLÉ SECRÈTE !")  # Avertissement de sécurité
    
    # ===== AFFICHAGE DE LA CLÉ PUBLIQUE (format PEM) =====
    # Convertit la clé publique en format PEM pour affichage
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,  # Format PEM
        format=serialization.PublicFormat.SubjectPublicKeyInfo  # Format standard pour clés publiques
    ).decode('utf-8')  # Décode les bytes en chaîne UTF-8 pour affichage
    
    # Affiche la clé publique à l'utilisateur
    print(f"\n✓ Clé publique pour {person}:")
    print("-" * 60)
    print(public_key_pem)  # Affiche la clé publique au format PEM
    print("-" * 60)
    # Instructions pour enregistrer la clé publique dans le système
    print("\n📋 Copiez cette clé publique et enregistrez-la dans le système:")
    print(f"   POST http://localhost:5000/keys/{person}")
    print("   Body: {\"public_key\": \"...\"}")


# ===== POINT D'ENTRÉE PRINCIPAL =====
if __name__ == "__main__":  # S'exécute seulement si le script est lancé directement
    # Vérifie que le nom de la personne est fourni en argument
    if len(sys.argv) < 2:  # sys.argv[0] = nom du script, sys.argv[1] = premier argument
        print("Usage: python utils/generate_keys.py <personne>")
        print("Exemple: python utils/generate_keys.py alice")
        sys.exit(1)  # Quitte avec code d'erreur 1
    
    person = sys.argv[1]  # Récupère le nom de la personne depuis les arguments
    generate_key_pair(person)  # Génère la paire de clés pour cette personne

