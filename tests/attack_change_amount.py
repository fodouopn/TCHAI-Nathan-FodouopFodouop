"""
Script de test pour l'attaque de modification de montant (Exercice 4).

Ce script simule une attaque où un attaquant modifie directement
le fichier de données pour changer le montant d'une transaction.
"""

import json
from pathlib import Path

# Chemin vers le fichier de transactions
TX_FILE = Path("data/tx.json")


def attack_change_amount():
    """
    Simule l'attaque : modifie directement le montant d'une transaction
    dans le fichier JSON.
    """
    print("=== ATTAQUE : Modification de montant ===\n")
    
    # 1. Lire les transactions actuelles
    print("1. Lecture des transactions actuelles...")
    with open(TX_FILE, "r", encoding="utf-8") as f:
        txs = json.load(f)
    
    if not txs:
        print("   ❌ Aucune transaction trouvée. Créez d'abord des transactions via l'API.")
        return
    
    print(f"   ✓ {len(txs)} transaction(s) trouvée(s)")
    print("\n   Transactions avant attaque :")
    for tx in txs:
        print(f"      ID {tx['id']}: {tx['p1']} -> {tx['p2']}, montant = {tx['a']}")
    
    # 2. Choisir la première transaction et modifier son montant
    target_tx = txs[0]
    original_amount = target_tx["a"]
    new_amount = original_amount * 100  # Multiplier par 100 pour rendre l'attaque évidente
    
    print(f"\n2. Modification du montant de la transaction ID {target_tx['id']}")
    print(f"   Montant original : {original_amount}")
    print(f"   Nouveau montant  : {new_amount}")
    
    target_tx["a"] = new_amount
    
    # 3. Sauvegarder le fichier modifié
    print("\n3. Sauvegarde du fichier modifié...")
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2, ensure_ascii=False)
    print("   ✓ Fichier modifié et sauvegardé")
    
    # 4. Vérifier que le système ne détecte rien
    print("\n4. Vérification : le système ne détecte aucune anomalie")
    print("   (Aucun mécanisme d'intégrité en v1)")
    print("\n   Transactions après attaque :")
    for tx in txs:
        print(f"      ID {tx['id']}: {tx['p1']} -> {tx['p2']}, montant = {tx['a']}")
    
    # 5. Calculer l'impact sur les soldes
    print("\n5. Impact sur les soldes :")
    balances = {}
    for tx in txs:
        p1, p2, a = tx["p1"], tx["p2"], tx["a"]
        balances[p1] = balances.get(p1, 0) - a
        balances[p2] = balances.get(p2, 0) + a
    
    for person, balance in balances.items():
        print(f"   {person}: {balance:+d}")
    
    print("\n=== CONCLUSION ===")
    print("✓ L'attaque a réussi : le montant a été modifié sans détection")
    print("✓ Le système v1 n'a aucun mécanisme de vérification d'intégrité")
    print("✓ Les soldes sont maintenant incorrects")


if __name__ == "__main__":
    attack_change_amount()

