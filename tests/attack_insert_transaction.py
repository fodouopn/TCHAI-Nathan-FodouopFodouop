"""
Script de test pour l'exercice 11 : Attaque d'insertion de transaction frauduleuse.

Ce script simule une attaque où un attaquant insère une transaction frauduleuse
dans le fichier de données (ex: une transaction vers son propre compte).
"""

import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone

# Configuration
TX_FILE = Path("data/tx.json")
API_BASE_URL = "http://localhost:5000"


def compute_hash(p1: str, p2: str, t: str, a: float, prev_hash: str = "0") -> str:
    """
    Calcule le hash SHA-256 chaîné d'une transaction (v3).
    """
    data = f"{p1}|{p2}|{t}|{a}|{prev_hash}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def attack_insert_transaction():
    """
    Simule l'attaque : insère une transaction frauduleuse dans le fichier JSON.
    """
    print("=== EXERCICE 11 : Attaque d'insertion de transaction frauduleuse ===\n")
    
    # 1. Vérifier l'état initial
    print("1. État initial des transactions...")
    try:
        response = requests.get(f"{API_BASE_URL}/transactions")
        if response.status_code == 200:
            txs = response.json()
            print(f"   ✓ {len(txs)} transaction(s) trouvée(s)")
            if len(txs) < 2:
                print("   ⚠️  Il faut au moins 2 transactions pour tester l'insertion")
                return
            for tx in txs[:3]:  # Afficher les 3 premières
                print(f"      ID {tx['id']}: {tx['p1']} -> {tx['p2']}, montant = {tx['a']}")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
        print("   Assurez-vous que le serveur Flask est démarré (python app.py)")
        return
    
    # 2. Vérifier l'intégrité initiale
    print("\n2. Vérification de l'intégrité initiale...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            if data['status'] != 'OK':
                print("   ⚠️  Le système n'est pas dans un état valide initialement")
                return
    except:
        pass
    
    # 3. Lire le fichier
    print("\n3. Lecture du fichier de transactions...")
    with open(TX_FILE, "r", encoding="utf-8") as f:
        txs = json.load(f)
    
    if len(txs) < 2:
        print("   ⚠️  Il faut au moins 2 transactions")
        return
    
    # Trier par timestamp
    sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
    
    # Sauvegarder pour restauration
    saved_txs = txs.copy()
    
    # 4. Créer une transaction frauduleuse
    print("\n4. ATTAQUE : Insertion d'une transaction frauduleuse...")
    
    # L'attaquant veut insérer une transaction qui lui donne de l'argent
    attacker = "attacker"
    victim = sorted_txs[0]["p1"]  # Prendre l'expéditeur de la première transaction
    
    # Insérer la transaction entre la première et la deuxième
    # Utiliser le hash de la première transaction comme prev_hash
    first_tx = sorted_txs[0]
    prev_hash = first_tx.get("h", "0")
    
    # Créer une transaction frauduleuse
    fake_tx = {
        "id": max(tx.get("id", 0) for tx in txs) + 1000,  # ID élevé pour éviter les conflits
        "p1": victim,
        "p2": attacker,
        "a": 1000,  # Montant frauduleux
        "t": (datetime.fromisoformat(first_tx["t"].replace("Z", "+00:00")) 
              if "Z" in first_tx["t"] 
              else datetime.fromisoformat(first_tx["t"])).isoformat(),
        "h": compute_hash(victim, attacker, 
                         (datetime.fromisoformat(first_tx["t"].replace("Z", "+00:00")) 
                          if "Z" in first_tx["t"] 
                          else datetime.fromisoformat(first_tx["t"])).isoformat(),
                         1000, prev_hash)
    }
    
    print(f"   Transaction frauduleuse créée:")
    print(f"      {fake_tx['p1']} -> {fake_tx['p2']}, montant = {fake_tx['a']}")
    print(f"      Hash calculé avec prev_hash = {prev_hash[:16]}...")
    
    # Insérer la transaction dans la liste (après la première)
    # Trouver l'index de la première transaction dans la liste originale
    first_index = next(i for i, tx in enumerate(txs) if tx.get("id") == first_tx.get("id"))
    txs.insert(first_index + 1, fake_tx)
    
    print(f"   ✓ Transaction insérée à la position {first_index + 1}")
    
    # Sauvegarder le fichier modifié
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier modifié et sauvegardé")
    
    # 5. Vérifier l'intégrité après insertion
    print("\n5. Vérification de l'intégrité après insertion...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Transactions valides: {data['valid_count']}/{data['total_transactions']}")
            print(f"   Transactions invalides: {data['invalid_count']}")
            
            if data['status'] == 'KO' and data['invalid_count'] > 0:
                print("\n   ✅ ATTAQUE DÉTECTÉE !")
                print("   La chaîne de hash est cassée")
                print("\n   Détails des transactions invalides:")
                for invalid in data['invalid_transactions'][:3]:  # Afficher les 3 premières
                    print(f"      - ID {invalid['id']}: {invalid['reason']}")
                    if 'expected_prev_hash' in invalid:
                        print(f"        Hash précédent attendu: {invalid['expected_prev_hash'][:16]}...")
            else:
                print("\n   ⚠️  PROBLÈME : L'attaque n'a pas été détectée !")
                print("   Cela peut arriver si la transaction a été insérée avec le bon hash")
                print("   mais le problème est que l'ordre chronologique est cassé")
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
    
    # 6. Vérifier l'impact sur les soldes
    print("\n6. Impact sur les soldes...")
    try:
        response = requests.get(f"{API_BASE_URL}/balance/{attacker}")
        if response.status_code == 200:
            balance_data = response.json()
            print(f"   Solde de l'attaquant ({attacker}): {balance_data.get('balance', 0)}")
            if balance_data.get('balance', 0) > 0:
                print("   ⚠️  L'attaquant a maintenant un solde positif (frauduleux)")
    except:
        pass
    
    # 7. Restaurer le fichier original
    print("\n7. Restauration du fichier original...")
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier restauré")
    
    print("\n=== CONCLUSION ===")
    print("✓ L'attaque d'insertion a été tentée")
    print("✓ Le système v3 avec hash chaîné devrait détecter cette attaque")
    print("  car les transactions suivantes auront un hash qui ne correspond pas")
    print("  au hash précédent attendu (la transaction frauduleuse a cassé la chaîne)")


if __name__ == "__main__":
    attack_insert_transaction()

