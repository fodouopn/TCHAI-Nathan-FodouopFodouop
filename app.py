# Import des modules standards Python pour la manipulation de données
import json  # Module pour lire/écrire des fichiers JSON
import hashlib  # Module pour calculer les hashs cryptographiques (SHA-256)
import base64  # Module pour encoder/décoder en base64 (pour les signatures)
from datetime import datetime, timezone  # Module pour gérer les timestamps ISO8601
from pathlib import Path  # Module pour manipuler les chemins de fichiers de manière portable
from typing import List, Dict, Any, Optional  # Module pour les annotations de type (aide au développement)

# Import des modules Flask pour créer l'API HTTP
from flask import Flask, request, jsonify  # Flask: framework web, request: données HTTP entrantes, jsonify: réponse JSON

# Import des modules de cryptographie pour les signatures RSA (v4)
from cryptography.hazmat.primitives import hashes, serialization  # hashes: SHA-256, serialization: format PEM
from cryptography.hazmat.primitives.asymmetric import rsa, padding  # rsa: algorithme RSA, padding: PSS pour signatures
from cryptography.hazmat.backends import default_backend  # Backend cryptographique par défaut


# ===== CONFIGURATION DES CHEMINS DE STOCKAGE =====
DATA_DIR = Path("data")  # Dossier racine pour stocker les données (transactions et clés)
TX_FILE = DATA_DIR / "tx.json"  # Fichier JSON contenant toutes les transactions
KEYS_FILE = DATA_DIR / "keys.json"  # Fichier JSON contenant les clés publiques des utilisateurs (v4)


def ensure_storage():
    """
    Crée le dossier et les fichiers JSON s'ils n'existent pas.
    Cette fonction garantit que les fichiers nécessaires existent avant toute opération.
    """
    DATA_DIR.mkdir(exist_ok=True)  # Crée le dossier "data" s'il n'existe pas (exist_ok=True évite l'erreur si déjà présent)
    if not TX_FILE.exists():  # Vérifie si le fichier de transactions existe
        TX_FILE.write_text("[]", encoding="utf-8")  # Crée un fichier vide avec un tableau JSON vide (aucune transaction)
    if not KEYS_FILE.exists():  # Vérifie si le fichier de clés existe
        KEYS_FILE.write_text("{}", encoding="utf-8")  # Crée un fichier vide avec un objet JSON vide (aucune clé)


def load_transactions() -> List[Dict[str, Any]]:
    """
    Charge toutes les transactions depuis le fichier JSON.
    Retourne: Liste de dictionnaires représentant les transactions.
    """
    ensure_storage()  # S'assure que le fichier existe avant de le lire
    return json.loads(TX_FILE.read_text(encoding="utf-8"))  # Lit le fichier, décode UTF-8, parse le JSON en liste Python


def save_transactions(txs: List[Dict[str, Any]]) -> None:
    """
    Sauvegarde toutes les transactions dans le fichier JSON.
    Paramètre: txs - Liste de dictionnaires représentant les transactions à sauvegarder.
    """
    # Convertit la liste Python en JSON formaté (indent=2 pour lisibilité, ensure_ascii=False pour UTF-8)
    TX_FILE.write_text(json.dumps(txs, indent=2, ensure_ascii=False), encoding="utf-8")


def load_public_keys() -> Dict[str, str]:
    """
    Charge toutes les clés publiques depuis le fichier JSON.
    Retourne: Dictionnaire {nom_personne: clé_publique_pem}
    """
    ensure_storage()  # S'assure que le fichier existe
    return json.loads(KEYS_FILE.read_text(encoding="utf-8"))  # Parse le JSON en dictionnaire Python


def save_public_key(person: str, public_key_pem: str) -> None:
    """
    Enregistre une clé publique pour une personne dans le fichier JSON.
    Paramètres:
        person: Nom de la personne (clé du dictionnaire)
        public_key_pem: Clé publique au format PEM (chaîne de caractères)
    """
    keys = load_public_keys()  # Charge toutes les clés existantes
    keys[person] = public_key_pem  # Ajoute ou remplace la clé publique de cette personne
    # Sauvegarde le dictionnaire mis à jour dans le fichier JSON
    KEYS_FILE.write_text(json.dumps(keys, indent=2, ensure_ascii=False), encoding="utf-8")


def get_public_key(person: str) -> Optional[str]:
    """
    Récupère la clé publique d'une personne depuis le stockage.
    Paramètre: person - Nom de la personne
    Retourne: Clé publique au format PEM, ou None si la personne n'a pas de clé enregistrée
    """
    keys = load_public_keys()  # Charge toutes les clés
    return keys.get(person)  # Retourne la clé de la personne, ou None si absente


def verify_signature(public_key_pem: str, message: str, signature_b64: str) -> bool:
    """
    Vérifie une signature RSA pour s'assurer qu'elle correspond au message et à la clé publique.
    Paramètres:
        public_key_pem: Clé publique au format PEM (chaîne de caractères)
        message: Message original qui a été signé (chaîne de caractères)
        signature_b64: Signature encodée en base64 (chaîne de caractères)
    Retourne: True si la signature est valide, False sinon
    """
    try:
        # Charge la clé publique depuis le format PEM (chaîne) vers un objet Python utilisable
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),  # Convertit la chaîne PEM en bytes
            backend=default_backend()  # Utilise le backend cryptographique par défaut
        )
        # Décode la signature base64 en bytes binaires (la signature RSA est binaire)
        signature = base64.b64decode(signature_b64)
        # Vérifie la signature: si elle correspond au message avec cette clé publique, pas d'exception
        public_key.verify(
            signature,  # Signature binaire à vérifier
            message.encode('utf-8'),  # Message original converti en bytes
            padding.PSS(  # Padding PSS (Probabilistic Signature Scheme) pour RSA
                mgf=padding.MGF1(hashes.SHA256()),  # Fonction de génération de masque utilisant SHA-256
                salt_length=padding.PSS.MAX_LENGTH  # Longueur maximale du sel pour sécurité maximale
            ),
            hashes.SHA256()  # Algorithme de hachage utilisé (SHA-256)
        )
        return True  # Si aucune exception n'est levée, la signature est valide
    except Exception:
        # Si une exception est levée (signature invalide, clé invalide, etc.), retourne False
        return False


def get_transaction_data_for_signing(p1: str, p2: str, t: str, a: float) -> str:
    """
    Crée la chaîne de données à signer pour une transaction (v4).
    Format: "P1|P2|timestamp|montant" (sans le hash, car le hash dépend de la signature)
    Paramètres:
        p1: Expéditeur
        p2: Destinataire
        t: Timestamp ISO8601
        a: Montant
    Retourne: Chaîne formatée prête à être signée
    """
    return f"{p1}|{p2}|{t}|{a}"  # Concaténation avec séparateur "|" pour éviter les ambiguïtés


def now_iso() -> str:
    """
    Génère un timestamp au format ISO8601 (UTC).
    Exemple: "2026-01-20T10:30:45.123456+00:00"
    Retourne: Chaîne de caractères représentant la date/heure actuelle en UTC
    """
    return datetime.now(timezone.utc).isoformat()  # UTC pour éviter les problèmes de fuseaux horaires


def compute_hash(p1: str, p2: str, t: str, a: float, prev_hash: str = "0") -> str:
    """
    Calcule le hash SHA-256 d'une transaction.
    v2: Hash simple de p1|p2|t|a (chaque transaction indépendante)
    v3: Hash chaîné de p1|p2|t|a|prev_hash (chaque transaction dépend de la précédente)
    Paramètres:
        p1: Expéditeur
        p2: Destinataire
        t: Timestamp ISO8601
        a: Montant
        prev_hash: Hash de la transaction précédente (défaut "0" pour la première transaction)
    Retourne: Hash SHA-256 en hexadécimal (64 caractères)
    """
    # Concaténation de toutes les données avec séparateur "|" pour éviter les ambiguïtés
    data = f"{p1}|{p2}|{t}|{a}|{prev_hash}"
    # Calcule SHA-256: encode la chaîne en UTF-8, hash, puis convertit en hexadécimal
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ===== INITIALISATION DE L'APPLICATION FLASK =====
app = Flask(__name__)  # Crée l'instance de l'application Flask (__name__ = nom du module)


# ===== ENDPOINT A1: ENREGISTRER UNE TRANSACTION =====
@app.post("/transactions")  # Décorateur Flask: route HTTP POST vers /transactions
def add_transaction():
    """
    A1: Enregistrer une transaction (v4 avec signature).
    Accepte: JSON {
        "p1": "expéditeur", 
        "p2": "destinataire", 
        "a": montant, 
        "t": (optionnel ISO8601),
        "signature": "..." (base64, requis en v4)
    }
    Retourne: Transaction créée avec ID, timestamp, hash et signature (si présente)
    """
    # Récupère le corps JSON de la requête HTTP (silent=True: retourne None si invalide au lieu de lever une exception)
    payload = request.get_json(silent=True) or {}
    # Définit les champs obligatoires pour créer une transaction
    required = {"p1", "p2", "a"}
    # Vérifie que tous les champs requis sont présents dans le payload
    if not required.issubset(payload):
        return jsonify({"error": "Champs requis: p1, p2, a"}), 400  # Code HTTP 400 = Bad Request

    # Extrait les valeurs du payload
    p1 = payload["p1"]  # Expéditeur (obligatoire)
    p2 = payload["p2"]  # Destinataire (obligatoire)
    a = payload["a"]  # Montant (obligatoire)
    t = payload.get("t") or now_iso()  # Timestamp: utilise celui fourni ou génère un nouveau (optionnel)
    
    # ===== VÉRIFICATION DE LA SIGNATURE (v4) =====
    signature = payload.get("signature")  # Récupère la signature si présente (optionnel pour compatibilité v1-v3)
    if signature:  # Si une signature est fournie, on vérifie (v4)
        public_key_pem = get_public_key(p1)  # Récupère la clé publique de l'expéditeur
        if not public_key_pem:  # Si la clé publique n'est pas enregistrée
            return jsonify({
                "error": f"Clé publique non trouvée pour {p1}. Enregistrez d'abord la clé publique avec POST /keys/{p1}"
            }), 400  # Erreur: clé publique manquante
        
        # Reconstruit le message exact qui a été signé (même format que lors de la signature)
        message = get_transaction_data_for_signing(p1, p2, t, a)
        # Vérifie que la signature correspond au message avec la clé publique
        if not verify_signature(public_key_pem, message, signature):
            return jsonify({"error": "Signature invalide"}), 400  # Erreur: signature invalide
    else:
        # Compatibilité avec v1-v3 (pas de signature requise)
        pass

    # ===== CRÉATION DE LA TRANSACTION =====
    txs = load_transactions()  # Charge toutes les transactions existantes
    tx_id = len(txs) + 1  # Génère un ID unique (nombre de transactions + 1)
    
    # ===== CALCUL DU HASH CHAÎNÉ (v3) =====
    # Récupérer le hash de la transaction précédente pour créer la chaîne
    prev_hash = "0"  # Hash initial pour la première transaction (pas de transaction précédente)
    if txs:  # S'il existe déjà des transactions
        # Trier par timestamp pour obtenir la dernière transaction chronologiquement
        sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
        last_tx = sorted_txs[-1]  # Dernière transaction (la plus récente)
        if "h" in last_tx:  # Si cette transaction a un hash (v2+)
            prev_hash = last_tx["h"]  # Utilise ce hash comme hash précédent
    
    # Calcul du hash de la transaction (P1, P2, t, a, h_prev) - hash chaîné (v3)
    h = compute_hash(p1, p2, t, a, prev_hash)
    
    # Crée le dictionnaire représentant la transaction
    tx = {
        "id": tx_id,  # Identifiant unique de la transaction
        "p1": p1,  # Expéditeur
        "p2": p2,  # Destinataire
        "a": a,  # Montant
        "t": t,  # Timestamp ISO8601
        "h": h,  # Hash chaîné de la transaction (SHA-256)
    }
    
    # Ajouter la signature si présente (v4)
    if signature:
        tx["signature"] = signature  # Ajoute le champ signature à la transaction
    
    # Sauvegarde la transaction dans la liste
    txs.append(tx)  # Ajoute la nouvelle transaction à la liste
    save_transactions(txs)  # Sauvegarde toutes les transactions dans le fichier JSON
    return jsonify(tx), 201  # Retourne la transaction créée avec code HTTP 201 (Created)


# ===== ENDPOINT: ENREGISTRER UNE CLÉ PUBLIQUE (v4) =====
@app.post("/keys/<person>")  # Route POST avec paramètre dynamique <person> dans l'URL
def register_public_key(person: str):
    """
    Enregistre la clé publique d'une personne dans le système (v4).
    Body JSON: {"public_key": "-----BEGIN PUBLIC KEY-----\n..."}
    Paramètre URL: person - Nom de la personne
    """
    payload = request.get_json(silent=True) or {}  # Récupère le JSON de la requête
    public_key_pem = payload.get("public_key")  # Extrait la clé publique du payload
    if not public_key_pem:  # Vérifie que la clé publique est fournie
        return jsonify({"error": "Champ requis: public_key (format PEM)"}), 400
    
    # Vérifier que la clé est valide (format PEM correct)
    try:
        # Tente de charger la clé publique depuis le format PEM
        serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),  # Convertit la chaîne PEM en bytes
            backend=default_backend()  # Backend cryptographique
        )
    except Exception:  # Si le chargement échoue, la clé est invalide
        return jsonify({"error": "Clé publique invalide (format PEM attendu)"}), 400
    
    # Si la clé est valide, on l'enregistre
    save_public_key(person, public_key_pem)  # Sauvegarde la clé publique dans le fichier JSON
    return jsonify({"person": person, "status": "Clé publique enregistrée"}), 201  # Code 201 = Created


# ===== ENDPOINT: RÉCUPÉRER UNE CLÉ PUBLIQUE (v4) =====
@app.get("/keys/<person>")  # Route GET avec paramètre dynamique <person> dans l'URL
def get_person_public_key(person: str):
    """
    Récupère la clé publique d'une personne depuis le stockage (v4).
    Paramètre URL: person - Nom de la personne
    Retourne: Clé publique au format PEM
    """
    public_key_pem = get_public_key(person)  # Récupère la clé publique depuis le stockage
    if not public_key_pem:  # Si la clé n'existe pas
        return jsonify({"error": f"Clé publique non trouvée pour {person}"}), 404  # Code 404 = Not Found
    return jsonify({"person": person, "public_key": public_key_pem})  # Retourne la clé publique


# ===== ENDPOINT A2: LISTER TOUTES LES TRANSACTIONS =====
@app.get("/transactions")  # Route GET vers /transactions
def list_transactions():
    """
    A2: Liste de toutes les transactions dans l'ordre chronologique.
    Retourne: Tableau JSON de toutes les transactions triées par timestamp
    """
    # Charge toutes les transactions et les trie par timestamp (ordre chronologique)
    txs = sorted(load_transactions(), key=lambda tx: tx["t"])  # key=lambda: fonction de tri (par champ "t")
    return jsonify(txs)  # Retourne la liste triée en JSON


# ===== ENDPOINT A3: LISTER LES TRANSACTIONS D'UNE PERSONNE =====
@app.get("/transactions/<person>")  # Route GET avec paramètre dynamique <person> dans l'URL
def list_transactions_for_person(person: str):
    """
    A3: Liste des transactions impliquant une personne donnée (en tant qu'expéditeur ou destinataire).
    Paramètre URL: person - Nom de la personne
    Retourne: Tableau JSON des transactions où la personne est p1 (expéditeur) ou p2 (destinataire)
    """
    # Charge toutes les transactions et les trie par timestamp
    txs = sorted(load_transactions(), key=lambda tx: tx["t"])
    # Filtre les transactions: garde seulement celles où la personne est expéditeur (p1) ou destinataire (p2)
    filtered = [tx for tx in txs if tx["p1"] == person or tx["p2"] == person]
    return jsonify(filtered)  # Retourne la liste filtrée en JSON


# ===== ENDPOINT A4: CALCULER LE SOLDE D'UNE PERSONNE =====
@app.get("/balance/<person>")  # Route GET avec paramètre dynamique <person> dans l'URL
def balance(person: str):
    """
    A4: Calcule le solde d'une personne = entrées (reçues) - sorties (envoyées).
    Paramètre URL: person - Nom de la personne
    Retourne: Solde (positif si la personne a reçu plus qu'elle n'a envoyé, négatif sinon)
    """
    txs = load_transactions()  # Charge toutes les transactions
    # Calcule la somme des montants reçus (transactions où la personne est destinataire p2)
    incoming = sum(tx["a"] for tx in txs if tx.get("p2") == person)
    # Calcule la somme des montants envoyés (transactions où la personne est expéditeur p1)
    outgoing = sum(tx["a"] for tx in txs if tx.get("p1") == person)
    # Retourne le solde (entrées - sorties)
    return jsonify({"person": person, "balance": incoming - outgoing})


# ===== ENDPOINT A5: VÉRIFIER L'INTÉGRITÉ DES DONNÉES =====
@app.get("/verify")  # Route GET vers /verify
def verify_integrity():
    """
    A5: Vérifie l'intégrité des données en recalculant les hashs et en les comparant avec les hashs stockés.
    v3: Vérifie aussi la chaîne de hashs (chaque hash dépend du précédent).
    v4: Vérifie aussi les signatures cryptographiques.
    Retourne: Rapport détaillé avec les transactions valides et invalides
    """
    txs = load_transactions()  # Charge toutes les transactions depuis le fichier
    valid_txs = []  # Liste des IDs des transactions valides
    invalid_txs = []  # Liste des transactions invalides avec détails
    
    # Trier les transactions par timestamp pour vérifier la chaîne dans l'ordre chronologique
    sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
    prev_hash = "0"  # Hash initial pour la première transaction (pas de transaction précédente)
    
    # Parcourt chaque transaction dans l'ordre chronologique
    for tx in sorted_txs:
        # ===== VÉRIFICATION: TRANSACTION V1 SANS HASH =====
        # Vérifier si la transaction a un hash (compatibilité v1/v2)
        if "h" not in tx:  # Transaction v1 n'a pas de hash
            invalid_txs.append({
                "id": tx.get("id"),  # ID de la transaction
                "reason": "Transaction v1 sans hash",  # Raison de l'invalidité
                "transaction": tx  # Transaction complète pour debug
            })
            continue  # Passe à la transaction suivante
        
        # ===== VÉRIFICATION: CHAMPS OBLIGATOIRES PRÉSENTS =====
        # Recalculer le hash à partir des données (sans utiliser le hash stocké)
        required_fields = ["p1", "p2", "t", "a"]  # Champs nécessaires pour calculer le hash
        if not all(field in tx for field in required_fields):  # Vérifie que tous les champs sont présents
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "Champs manquants pour le calcul du hash",
                "transaction": tx
            })
            continue  # Passe à la transaction suivante
        
        # ===== VÉRIFICATION DU HASH CHAÎNÉ (v3) =====
        # Calculer le hash avec le hash précédent (v3: hash chaîné)
        computed_hash = compute_hash(tx["p1"], tx["p2"], tx["t"], tx["a"], prev_hash)
        stored_hash = tx["h"]  # Hash stocké dans la transaction
        
        # Compare le hash calculé avec le hash stocké
        hash_valid = computed_hash == stored_hash
        
        # ===== VÉRIFICATION DE LA SIGNATURE (v4) =====
        signature_valid = True  # Par défaut valide (pour compatibilité v1-v3)
        if "signature" in tx:  # Si la transaction a une signature (v4)
            public_key_pem = get_public_key(tx["p1"])  # Récupère la clé publique de l'expéditeur
            if public_key_pem:  # Si la clé publique existe
                # Reconstruit le message exact qui a été signé
                message = get_transaction_data_for_signing(tx["p1"], tx["p2"], tx["t"], tx["a"])
                # Vérifie la signature
                signature_valid = verify_signature(public_key_pem, message, tx["signature"])
            else:  # Clé publique manquante
                signature_valid = False
        
        # ===== DÉCISION: TRANSACTION VALIDE OU INVALIDE =====
        if hash_valid and signature_valid:  # Si le hash ET la signature sont valides
            valid_txs.append(tx.get("id"))  # Ajoute l'ID à la liste des valides
            prev_hash = stored_hash  # Utilise le hash stocké pour la prochaine transaction (chaîne)
        else:  # Transaction invalide
            reasons = []  # Liste des raisons d'invalidité
            if not hash_valid:  # Hash invalide
                reasons.append("Hash invalide ou chaîne cassée")
            if not signature_valid:  # Signature invalide
                reasons.append("Signature invalide ou clé publique manquante")
            
            # Ajoute les détails de la transaction invalide
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "; ".join(reasons),  # Concatène toutes les raisons
                "computed_hash": computed_hash if not hash_valid else None,  # Hash calculé (pour debug)
                "stored_hash": stored_hash if not hash_valid else None,  # Hash stocké (pour debug)
                "expected_prev_hash": prev_hash if not hash_valid else None,  # Hash précédent attendu (pour debug)
                "signature_valid": signature_valid if "signature" in tx else None,  # État de la signature
                "transaction": tx  # Transaction complète pour debug
            })
            # Si la chaîne est cassée, on ne peut plus vérifier les suivantes correctement
            # mais on continue quand même pour voir toutes les erreurs
            prev_hash = stored_hash  # Continue avec le hash stocké (même s'il est invalide) pour voir toutes les erreurs
    
    # ===== PRÉPARATION DU RAPPORT FINAL =====
    is_valid = len(invalid_txs) == 0  # True si aucune transaction invalide
    status = "OK" if is_valid else "KO"  # Statut textuel
    
    # Retourne le rapport complet en JSON
    return jsonify({
        "status": status,  # "OK" ou "KO"
        "valid": is_valid,  # Booléen: toutes les transactions sont valides
        "total_transactions": len(txs),  # Nombre total de transactions
        "valid_count": len(valid_txs),  # Nombre de transactions valides
        "invalid_count": len(invalid_txs),  # Nombre de transactions invalides
        "valid_transactions": valid_txs,  # Liste des IDs des transactions valides
        "invalid_transactions": invalid_txs  # Liste détaillée des transactions invalides
    })


# ===== POINT D'ENTRÉE PRINCIPAL =====
if __name__ == "__main__":  # S'exécute seulement si le script est lancé directement (pas importé)
    ensure_storage()  # S'assure que les fichiers de stockage existent avant de démarrer
    # Démarre le serveur Flask
    app.run(
        host="0.0.0.0",  # Écoute sur toutes les interfaces réseau (accessible depuis l'extérieur)
        port=5000,  # Port HTTP 5000
        debug=True  # Mode debug activé (rechargement automatique, messages d'erreur détaillés)
    )

