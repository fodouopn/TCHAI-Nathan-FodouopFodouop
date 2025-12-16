"""
Script de test pour l'exercice 10 : Vérifier que les attaques précédentes
ne fonctionnent plus avec le hash chaîné (v3).

Ce script teste :
1. Attaque de modification de montant (exercice 4)
2. Attaque de suppression (exercice 8)
"""

import json
import requests
from pathlib import Path

# Configuration
TX_FILE = Path("data/tx.json")
API_BASE_URL = "http://localhost:5000"


def test_modification_attack():
    """
    Teste que l'attaque de modification de montant est détectée (v3).
    """
    print("=== TEST 1 : Attaque de modification de montant (v3) ===\n")
    
    # 1. Vérifier l'état initial
    print("1. État initial...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Transactions valides: {data['valid_count']}/{data['total_transactions']}")
            if data['status'] != 'OK':
                print("   ⚠️  Le système n'est pas dans un état valide initialement")
                return False
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
        print("   Assurez-vous que le serveur Flask est démarré (python app.py)")
        return False
    
    # 2. Lire les transactions
    with open(TX_FILE, "r", encoding="utf-8") as f:
        txs = json.load(f)
    
    if len(txs) < 2:
        print("   ⚠️  Il faut au moins 2 transactions pour tester")
        return False
    
    # Trouver une transaction au milieu (pas la première, pas la dernière)
    target_tx = None
    sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
    if len(sorted_txs) >= 2:
        target_tx = sorted_txs[1]  # Deuxième transaction
    
    if not target_tx or "h" not in target_tx:
        print("   ⚠️  Transaction cible invalide")
        return False
    
    print(f"   ✓ Transaction cible: ID {target_tx['id']}")
    print(f"      {target_tx['p1']} -> {target_tx['p2']}, montant = {target_tx['a']}")
    
    # Sauvegarder pour restauration
    saved_tx = target_tx.copy()
    saved_txs = txs.copy()
    
    # 3. Modifier le montant (attaque)
    print(f"\n2. ATTAQUE : Modification du montant...")
    original_amount = target_tx["a"]
    new_amount = original_amount * 10
    target_tx["a"] = new_amount
    print(f"   Montant: {original_amount} → {new_amount}")
    
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier modifié")
    
    # 4. Vérifier que l'attaque est détectée
    print("\n3. Vérification de l'intégrité...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Transactions invalides: {data['invalid_count']}")
            
            if data['status'] == 'KO' and data['invalid_count'] > 0:
                print("\n   ✅ ATTAQUE DÉTECTÉE !")
                print("   La chaîne de hash est cassée")
                for invalid in data['invalid_transactions']:
                    if invalid['id'] == target_tx['id']:
                        print(f"      Transaction ID {invalid['id']}: {invalid['reason']}")
                result = True
            else:
                print("\n   ❌ ERREUR : L'attaque n'a pas été détectée !")
                result = False
        else:
            result = False
    except:
        result = False
    
    # 5. Restaurer
    print("\n4. Restauration...")
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier restauré\n")
    
    return result


def test_deletion_attack():
    """
    Teste que l'attaque de suppression est détectée (v3).
    """
    print("=== TEST 2 : Attaque de suppression (v3) ===\n")
    
    # 1. Vérifier l'état initial
    print("1. État initial...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            if data['status'] != 'OK':
                print("   ⚠️  Le système n'est pas dans un état valide initialement")
                return False
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
        return False
    
    # 2. Lire les transactions
    with open(TX_FILE, "r", encoding="utf-8") as f:
        txs = json.load(f)
    
    if len(txs) < 2:
        print("   ⚠️  Il faut au moins 2 transactions pour tester")
        return False
    
    # Trier et trouver une transaction au milieu
    sorted_txs = sorted(txs, key=lambda tx: tx.get("t", ""))
    target_tx = sorted_txs[1] if len(sorted_txs) >= 2 else sorted_txs[0]
    
    if "h" not in target_tx:
        print("   ⚠️  Transaction cible invalide")
        return False
    
    print(f"   ✓ Transaction cible: ID {target_tx['id']}")
    print(f"      {target_tx['p1']} -> {target_tx['p2']}, montant = {target_tx['a']}")
    
    # Sauvegarder pour restauration
    saved_txs = txs.copy()
    
    # 3. Supprimer la transaction (attaque)
    print(f"\n2. ATTAQUE : Suppression de la transaction...")
    txs.remove(target_tx)
    print(f"   Transaction ID {target_tx['id']} supprimée")
    print(f"   Transactions restantes: {len(txs)}")
    
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier modifié")
    
    # 4. Vérifier que l'attaque est détectée
    print("\n3. Vérification de l'intégrité...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Transactions invalides: {data['invalid_count']}")
            
            if data['status'] == 'KO' and data['invalid_count'] > 0:
                print("\n   ✅ ATTAQUE DÉTECTÉE !")
                print("   La chaîne de hash est cassée (les transactions suivantes")
                print("   dépendent du hash de la transaction supprimée)")
                result = True
            else:
                print("\n   ❌ ERREUR : L'attaque n'a pas été détectée !")
                result = False
        else:
            result = False
    except:
        result = False
    
    # 5. Restaurer
    print("\n4. Restauration...")
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier restauré\n")
    
    return result


def main():
    """
    Exécute tous les tests.
    """
    print("=" * 60)
    print("EXERCICE 10 : Vérification des attaques avec hash chaîné (v3)")
    print("=" * 60)
    print()
    
    result1 = test_modification_attack()
    result2 = test_deletion_attack()
    
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Test 1 - Modification de montant: {'✅ RÉUSSI' if result1 else '❌ ÉCHOUÉ'}")
    print(f"Test 2 - Suppression: {'✅ RÉUSSI' if result2 else '❌ ÉCHOUÉ'}")
    print()
    
    if result1 and result2:
        print("✅ Toutes les attaques sont maintenant détectées avec le hash chaîné (v3)")
    else:
        print("⚠️  Certaines attaques ne sont pas détectées correctement")


if __name__ == "__main__":
    main()

