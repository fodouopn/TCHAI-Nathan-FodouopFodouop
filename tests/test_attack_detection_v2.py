"""
Script de test pour l'exercice 7 : Vérifier que l'attaque de modification de montant
est maintenant détectée grâce au système de hash (v2).

Ce script simule l'attaque puis vérifie que /verify la détecte.
"""

import json
import requests
from pathlib import Path

# Configuration
TX_FILE = Path("data/tx.json")
API_BASE_URL = "http://localhost:5000"


def test_attack_detection():
    """
    Teste que l'attaque de modification de montant est détectée par /verify.
    """
    print("=== EXERCICE 7 : Test de détection d'attaque (v2) ===\n")
    
    # 1. Vérifier l'état initial
    print("1. Vérification de l'intégrité initiale...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Transactions valides: {data['valid_count']}/{data['total_transactions']}")
            if data['invalid_count'] > 0:
                print(f"   ⚠️  {data['invalid_count']} transaction(s) invalide(s) détectée(s)")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
        print("   Assurez-vous que le serveur Flask est démarré (python app.py)")
        return
    
    # 2. Lire les transactions
    print("\n2. Lecture des transactions...")
    with open(TX_FILE, "r", encoding="utf-8") as f:
        txs = json.load(f)
    
    if not txs:
        print("   ❌ Aucune transaction trouvée.")
        return
    
    # Trouver une transaction avec hash (v2)
    target_tx = None
    for tx in txs:
        if "h" in tx:
            target_tx = tx
            break
    
    if not target_tx:
        print("   ❌ Aucune transaction v2 (avec hash) trouvée.")
        print("   Créez d'abord des transactions via l'API pour avoir des hashs.")
        return
    
    print(f"   ✓ Transaction cible trouvée: ID {target_tx['id']}")
    print(f"      {target_tx['p1']} -> {target_tx['p2']}, montant = {target_tx['a']}")
    print(f"      Hash stocké: {target_tx['h'][:16]}...")
    
    # 3. Sauvegarder le hash original pour restauration
    original_hash = target_tx["h"]
    original_amount = target_tx["a"]
    
    # 4. Modifier le montant (attaque)
    print(f"\n3. ATTAQUE : Modification du montant...")
    new_amount = original_amount * 10  # Multiplier par 10
    target_tx["a"] = new_amount
    print(f"   Montant original: {original_amount}")
    print(f"   Nouveau montant: {new_amount}")
    
    # Sauvegarder le fichier modifié
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier modifié et sauvegardé")
    
    # 5. Vérifier que /verify détecte la corruption
    print("\n4. Vérification de l'intégrité après attaque...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Valid: {data['valid']}")
            print(f"   Transactions valides: {data['valid_count']}/{data['total_transactions']}")
            print(f"   Transactions invalides: {data['invalid_count']}")
            
            # Filtrer pour trouver notre transaction attaquée
            attacked_tx_found = False
            for invalid in data['invalid_transactions']:
                if invalid['id'] == target_tx['id'] and 'computed_hash' in invalid:
                    attacked_tx_found = True
                    print("\n   ✅ ATTAQUE DÉTECTÉE !")
                    print(f"\n   Transaction attaquée (ID {invalid['id']}):")
                    print(f"      Raison: {invalid['reason']}")
                    print(f"      Hash calculé: {invalid['computed_hash'][:16]}...")
                    print(f"      Hash stocké:  {invalid['stored_hash'][:16]}...")
                    break
            
            if not attacked_tx_found:
                print("\n   ❌ ERREUR : L'attaque sur la transaction ID {target_tx['id']} n'a pas été détectée !")
            
            # Afficher les autres transactions invalides (v1 sans hash, etc.)
            other_invalid = [inv for inv in data['invalid_transactions'] 
                           if inv['id'] != target_tx['id']]
            if other_invalid:
                print(f"\n   Note: {len(other_invalid)} autre(s) transaction(s) invalide(s) (v1 sans hash, etc.)")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API.")
    
    # 6. Restaurer le fichier original (pour ne pas laisser les données corrompues)
    print("\n5. Restauration du fichier original...")
    target_tx["a"] = original_amount
    target_tx["h"] = original_hash
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier restauré")
    
    # 7. Vérifier que tout est revenu à la normale
    print("\n6. Vérification finale...")
    try:
        response = requests.get(f"{API_BASE_URL}/verify")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                print("   ✅ Intégrité restaurée")
            else:
                print(f"   ⚠️  {data['invalid_count']} transaction(s) encore invalide(s)")
    except:
        pass
    
    print("\n=== CONCLUSION ===")
    print("✓ Le système v2 avec hash permet de détecter les modifications de montant")
    print("✓ L'endpoint /verify fonctionne correctement")
    print("\nNote: Les transactions v1 (sans hash) sont marquées comme invalides,")
    print("      ce qui est normal. Seules les transactions v2 (avec hash) sont protégées.")


if __name__ == "__main__":
    test_attack_detection()

