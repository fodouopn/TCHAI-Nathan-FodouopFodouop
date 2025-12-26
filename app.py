import json
import hashlib
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


# Chemins de stockage
DATA_DIR = Path("data")
TX_FILE = DATA_DIR / "tx.json"
KEYS_FILE = DATA_DIR / "keys.json"  # Stockage des clés publiques


def ensure_storage():
    """Crée le dossier et les fichiers JSON s'ils n'existent pas."""
    DATA_DIR.mkdir(exist_ok=True)
    if not TX_FILE.exists():
        TX_FILE.write_text("[]", encoding="utf-8")
    if not KEYS_FILE.exists():
        KEYS_FILE.write_text("{}", encoding="utf-8")


def load_transactions() -> List[Dict[str, Any]]:
    ensure_storage()
    return json.loads(TX_FILE.read_text(encoding="utf-8"))


def save_transactions(txs: List[Dict[str, Any]]) -> None:
    TX_FILE.write_text(json.dumps(txs, indent=2, ensure_ascii=False), encoding="utf-8")


def load_public_keys() -> Dict[str, str]:
    """Charge les clés publiques stockées."""
    ensure_storage()
    return json.loads(KEYS_FILE.read_text(encoding="utf-8"))


def save_public_key(person: str, public_key_pem: str) -> None:
    """Enregistre une clé publique pour une personne."""
    keys = load_public_keys()
    keys[person] = public_key_pem
    KEYS_FILE.write_text(json.dumps(keys, indent=2, ensure_ascii=False), encoding="utf-8")


def get_public_key(person: str) -> Optional[str]:
    """Récupère la clé publique d'une personne."""
    keys = load_public_keys()
    return keys.get(person)


def verify_signature(public_key_pem: str, message: str, signature_b64: str) -> bool:
    """
    Vérifie une signature RSA.
    public_key_pem: Clé publique au format PEM
    message: Message à vérifier
    signature_b64: Signature en base64
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def get_transaction_data_for_signing(p1: str, p2: str, t: str, a: float) -> str:
    """Crée la chaîne de données à signer pour une transaction."""
    return f"{p1}|{p2}|{t}|{a}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_hash(p1: str, p2: str, t: str, a: float, prev_hash: str = "0") -> str:
    """
    Calcule le hash SHA-256 d'une transaction.
    v2: Hash de la concaténation: p1|p2|t|a
    v3: Hash chaîné: hash(p1|p2|t|a|prev_hash)
    """
    data = f"{p1}|{p2}|{t}|{a}|{prev_hash}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


app = Flask(__name__)


@app.post("/transactions")
def add_transaction():
    """
    A1: Enregistrer une transaction (v4 avec signature).
    Attendu: JSON {
        "p1": "...", 
        "p2": "...", 
        "a": montant, 
        "t": (optionnel ISO8601),
        "signature": "..." (base64, requis en v4)
    }
    """
    payload = request.get_json(silent=True) or {}
    required = {"p1", "p2", "a"}
    if not required.issubset(payload):
        return jsonify({"error": "Champs requis: p1, p2, a"}), 400

    p1 = payload["p1"]
    p2 = payload["p2"]
    a = payload["a"]
    t = payload.get("t") or now_iso()
    
    # Vérification de la signature (v4)
    signature = payload.get("signature")
    if signature:
        public_key_pem = get_public_key(p1)
        if not public_key_pem:
            return jsonify({
                "error": f"Clé publique non trouvée pour {p1}. Enregistrez d'abord la clé publique avec POST /keys/{p1}"
            }), 400
        
        message = get_transaction_data_for_signing(p1, p2, t, a)
        if not verify_signature(public_key_pem, message, signature):
            return jsonify({"error": "Signature invalide"}), 400
    else:
        # Compatibilité avec v1-v3 (pas de signature)
        pass

    txs = load_transactions()
    tx_id = len(txs) + 1
    
    # Calcul du hash chaîné (v3)
    # Récupérer le hash de la transaction précédente
    prev_hash = "0"  # Hash initial pour la première transaction
    if txs:
        # Trier par timestamp pour obtenir la dernière transaction
        sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
        last_tx = sorted_txs[-1]
        if "h" in last_tx:
            prev_hash = last_tx["h"]
    
    # Calcul du hash de la transaction (P1, P2, t, a, h_prev)
    h = compute_hash(p1, p2, t, a, prev_hash)
    
    tx = {
        "id": tx_id,
        "p1": p1,
        "p2": p2,
        "a": a,
        "t": t,
        "h": h,  # Hash chaîné de la transaction
    }
    
    # Ajouter la signature si présente (v4)
    if signature:
        tx["signature"] = signature
    
    txs.append(tx)
    save_transactions(txs)
    return jsonify(tx), 201


@app.post("/keys/<person>")
def register_public_key(person: str):
    """
    Enregistre la clé publique d'une personne.
    Body: {"public_key": "..." (format PEM)}
    """
    payload = request.get_json(silent=True) or {}
    public_key_pem = payload.get("public_key")
    if not public_key_pem:
        return jsonify({"error": "Champ requis: public_key (format PEM)"}), 400
    
    # Vérifier que la clé est valide
    try:
        serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
    except Exception:
        return jsonify({"error": "Clé publique invalide (format PEM attendu)"}), 400
    
    save_public_key(person, public_key_pem)
    return jsonify({"person": person, "status": "Clé publique enregistrée"}), 201


@app.get("/keys/<person>")
def get_person_public_key(person: str):
    """Récupère la clé publique d'une personne."""
    public_key_pem = get_public_key(person)
    if not public_key_pem:
        return jsonify({"error": f"Clé publique non trouvée pour {person}"}), 404
    return jsonify({"person": person, "public_key": public_key_pem})


@app.get("/transactions")
def list_transactions():
    """
    A2: Liste de toutes les transactions (ordre chronologique).
    """
    txs = sorted(load_transactions(), key=lambda tx: tx["t"])
    return jsonify(txs)


@app.get("/transactions/<person>")
def list_transactions_for_person(person: str):
    """
    A3: Liste des transactions impliquant une personne (p1 ou p2).
    """
    txs = sorted(load_transactions(), key=lambda tx: tx["t"])
    filtered = [tx for tx in txs if tx["p1"] == person or tx["p2"] == person]
    return jsonify(filtered)


@app.get("/balance/<person>")
def balance(person: str):
    """
    A4: Solde d'une personne = entrées - sorties.
    """
    txs = load_transactions()
    incoming = sum(tx["a"] for tx in txs if tx.get("p2") == person)
    outgoing = sum(tx["a"] for tx in txs if tx.get("p1") == person)
    return jsonify({"person": person, "balance": incoming - outgoing})


@app.get("/verify")
def verify_integrity():
    """
    A5: Vérifier l'intégrité des données en recalculant les hashs
    et en les comparant avec les hashs stockés.
    v3: Vérifie aussi la chaîne de hashs (chaque hash dépend du précédent).
    """
    txs = load_transactions()
    valid_txs = []
    invalid_txs = []
    
    # Trier les transactions par timestamp pour vérifier la chaîne dans l'ordre
    sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
    prev_hash = "0"  # Hash initial pour la première transaction
    
    for tx in sorted_txs:
        # Vérifier si la transaction a un hash (compatibilité v1/v2)
        if "h" not in tx:
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "Transaction v1 sans hash",
                "transaction": tx
            })
            continue
        
        # Recalculer le hash à partir des données (sans utiliser le hash stocké)
        required_fields = ["p1", "p2", "t", "a"]
        if not all(field in tx for field in required_fields):
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "Champs manquants pour le calcul du hash",
                "transaction": tx
            })
            continue
        
        # Calculer le hash avec le hash précédent (v3: hash chaîné)
        computed_hash = compute_hash(tx["p1"], tx["p2"], tx["t"], tx["a"], prev_hash)
        stored_hash = tx["h"]
        
        hash_valid = computed_hash == stored_hash
        
        # Vérifier la signature si présente (v4)
        signature_valid = True
        if "signature" in tx:
            public_key_pem = get_public_key(tx["p1"])
            if public_key_pem:
                message = get_transaction_data_for_signing(tx["p1"], tx["p2"], tx["t"], tx["a"])
                signature_valid = verify_signature(public_key_pem, message, tx["signature"])
            else:
                signature_valid = False
        
        if hash_valid and signature_valid:
            valid_txs.append(tx.get("id"))
            prev_hash = stored_hash  # Utiliser le hash stocké pour la prochaine transaction
        else:
            reasons = []
            if not hash_valid:
                reasons.append("Hash invalide ou chaîne cassée")
            if not signature_valid:
                reasons.append("Signature invalide ou clé publique manquante")
            
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "; ".join(reasons),
                "computed_hash": computed_hash if not hash_valid else None,
                "stored_hash": stored_hash if not hash_valid else None,
                "expected_prev_hash": prev_hash if not hash_valid else None,
                "signature_valid": signature_valid if "signature" in tx else None,
                "transaction": tx
            })
            # Si la chaîne est cassée, on ne peut plus vérifier les suivantes correctement
            # mais on continue quand même pour voir toutes les erreurs
            prev_hash = stored_hash  # Continuer avec le hash stocké (même s'il est invalide)
    
    is_valid = len(invalid_txs) == 0
    status = "OK" if is_valid else "KO"
    
    return jsonify({
        "status": status,
        "valid": is_valid,
        "total_transactions": len(txs),
        "valid_count": len(valid_txs),
        "invalid_count": len(invalid_txs),
        "valid_transactions": valid_txs,
        "invalid_transactions": invalid_txs
    })


if __name__ == "__main__":
    ensure_storage()
    app.run(host="0.0.0.0", port=5000, debug=True)

