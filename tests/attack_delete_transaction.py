"""
Script de test pour l'exercice 8 : Attaque de suppression de transaction.

Ce script simule une attaque où un attaquant supprime directement
une transaction du fichier de données.
"""

import json
import requests
from pathlib import Path

# Configuration
TX_FILE = Path("data/tx.json")
API_BASE_URL = "http://localhost:5000"


def attack_delete_transaction():
    """
    Simule l'attaque : supprime directement une transaction
    du fichier JSON.
    """
    print("=== EXERCICE 8 : Attaque de suppression de transaction ===\n")
    
    # 1. Vérifier l'état initial
    print("1. État initial des transactions...")
    try:
        response = requests.get(f"{API_BASE_URL}/transactions")
        if response.status_code == 200:
            txs = response.json()
            print(f"   ✓ {len(txs)} transaction(s) trouvée(s)")
            for tx in txs:
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
            print(f"   Transactions valides: {data['valid_count']}/{data['total_transactions']}")
    except:
        pass
    
    # 3. Lire le fichier et sauvegarder une copie
    print("\n3. Lecture du fichier de transactions...")
    with open(TX_FILE, "r", encoding="utf-8") as f:
        txs = json.load(f)
    
    if len(txs) < 2:
        print("   ⚠️  Il faut au moins 2 transactions pour tester la suppression.")
        print("   Créez plus de transactions via l'API.")
        return
    
    # Trouver une transaction avec hash (v2) si possible
    target_tx = None
    for tx in txs:
        if "h" in tx:
            target_tx = tx
            break
    
    if not target_tx:
        target_tx = txs[0]  # Utiliser la première si aucune n'a de hash
    
    print(f"   ✓ Transaction cible: ID {target_tx['id']}")
    print(f"      {target_tx['p1']} -> {target_tx['p2']}, montant = {target_tx['a']}")
    
    # Sauvegarder la transaction pour restauration
    saved_tx = target_tx.copy()
    saved_txs = txs.copy()
    
    # 4. Supprimer la transaction (attaque)
    print(f"\n4. ATTAQUE : Suppression de la transaction ID {target_tx['id']}...")
    txs.remove(target_tx)
    print(f"   ✓ Transaction supprimée")
    print(f"   Transactions restantes: {len(txs)}")
    
    # Sauvegarder le fichier modifié
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier modifié et sauvegardé")
    
    # 5. Vérifier l'intégrité après suppression
    print("\n5. Vérification de l'intégrité après suppression...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Transactions valides: {data['valid_count']}/{data['total_transactions']}")
            print(f"   Transactions invalides: {data['invalid_count']}")
            
            if data['invalid_count'] == 0 and data['status'] == 'OK':
                print("\n   ⚠️  PROBLÈME : La suppression n'a PAS été détectée !")
                print("   Le système v2 ne peut pas détecter les suppressions de transactions")
                print("   car chaque hash est indépendant.")
            else:
                print("\n   Note: Les transactions invalides sont dues à d'autres raisons")
                print("   (ex: transactions v1 sans hash), pas à la suppression.")
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
    
    # 6. Vérifier l'impact sur les soldes
    print("\n6. Impact sur les soldes...")
    try:
        # Calculer les soldes avant et après
        balances_before = {}
        for tx in saved_txs:
            p1, p2, a = tx["p1"], tx["p2"], tx["a"]
            balances_before[p1] = balances_before.get(p1, 0) - a
            balances_before[p2] = balances_before.get(p2, 0) + a
        
        balances_after = {}
        for tx in txs:
            p1, p2, a = tx["p1"], tx["p2"], tx["a"]
            balances_after[p1] = balances_after.get(p1, 0) - a
            balances_after[p2] = balances_after.get(p2, 0) + a
        
        print("   Soldes avant suppression:")
        for person in set(list(balances_before.keys()) + list(balances_after.keys())):
            before = balances_before.get(person, 0)
            after = balances_after.get(person, 0)
            if before != after:
                print(f"      {person}: {before} → {after} (différence: {after - before:+d}) ⚠️")
            else:
                print(f"      {person}: {before}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # 7. Restaurer le fichier original
    print("\n7. Restauration du fichier original...")
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier restauré")
    
    print("\n=== CONCLUSION ===")
    print("✓ L'attaque de suppression a réussi : la transaction a été supprimée")
    print("✓ Le système v2 ne peut PAS détecter les suppressions")
    print("  → Chaque transaction a un hash indépendant")
    print("  → Supprimer une transaction ne casse pas les hashs des autres")
    print("✓ Les soldes sont maintenant incorrects (double dépense possible)")
    print("\n⚠️  RISQUE : La suppression peut entraîner la double dépense")
    print("   (une transaction peut être dépensée deux fois si elle est supprimée)")


if __name__ == "__main__":
    attack_delete_transaction()

