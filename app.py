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
        
        if computed_hash == stored_hash:
            valid_txs.append(tx.get("id"))
            prev_hash = stored_hash  # Utiliser le hash stocké pour la prochaine transaction
        else:
            invalid_txs.append({
                "id": tx.get("id"),
                "reason": "Hash invalide ou chaîne cassée",
                "computed_hash": computed_hash,
                "stored_hash": stored_hash,
                "expected_prev_hash": prev_hash,
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

