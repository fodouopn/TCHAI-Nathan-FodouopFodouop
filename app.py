import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, request, jsonify


# Chemins de stockage
DATA_DIR = Path("data")
TX_FILE = DATA_DIR / "tx.json"


def ensure_storage():
    """Crée le dossier et le fichier JSON s'ils n'existent pas."""
    DATA_DIR.mkdir(exist_ok=True)
    if not TX_FILE.exists():
        TX_FILE.write_text("[]", encoding="utf-8")


def load_transactions() -> List[Dict[str, Any]]:
    ensure_storage()
    return json.loads(TX_FILE.read_text(encoding="utf-8"))


def save_transactions(txs: List[Dict[str, Any]]) -> None:
    TX_FILE.write_text(json.dumps(txs, indent=2, ensure_ascii=False), encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_hash(p1: str, p2: str, t: str, a: float) -> str:
    """
    Calcule le hash SHA-256 d'une transaction.
    Hash de la concaténation: p1|p2|t|a
    """
    data = f"{p1}|{p2}|{t}|{a}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


app = Flask(__name__)


@app.post("/transactions")
def add_transaction():
    """
    A1: Enregistrer une transaction.
    Attendu: JSON {"p1": "...", "p2": "...", "a": montant, "t": (optionnel ISO8601)}
    """
    payload = request.get_json(silent=True) or {}
    required = {"p1", "p2", "a"}
    if not required.issubset(payload):
        return jsonify({"error": "Champs requis: p1, p2, a"}), 400

    txs = load_transactions()
    tx_id = len(txs) + 1
    p1 = payload["p1"]
    p2 = payload["p2"]
    a = payload["a"]
    t = payload.get("t") or now_iso()
    
    # Calcul du hash de la transaction (P1, P2, t, a)
    h = compute_hash(p1, p2, t, a)
    
    tx = {
        "id": tx_id,
        "p1": p1,
        "p2": p2,
        "a": a,
        "t": t,
        "h": h,  # Hash de la transaction
    }
    txs.append(tx)
    save_transactions(txs)
    return jsonify(tx), 201


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
    """
    txs = load_transactions()
    valid_txs = []
    invalid_txs = []
    
    for tx in txs:
        # Vérifier si la transaction a un hash (compatibilité v1)
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
        
        computed_hash = compute_hash(tx["p1"], tx["p2"], tx["t"], tx["a"])
        stored_hash = tx["h"]
        
        if computed_hash == stored_hash:
            valid_txs.append(tx.get("id"))
        else:
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "Hash invalide",
                "computed_hash": computed_hash,
                "stored_hash": stored_hash,
                "transaction": tx
            })
    
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

