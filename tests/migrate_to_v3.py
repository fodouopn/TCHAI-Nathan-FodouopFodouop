"""
Script pour migrer les transactions vers v3 (hash chaîné).

Ce script supprime les anciennes transactions et permet de repartir
avec un système v3 propre.
"""

import json
from pathlib import Path

TX_FILE = Path("data/tx.json")


def migrate_to_v3():
    """
    Nettoie le fichier de transactions pour repartir avec v3.
    """
    print("=== Migration vers Tchaï v3 (hash chaîné) ===\n")
    
    print("⚠️  ATTENTION : Ce script va supprimer toutes les transactions existantes.")
    print("   Les transactions créées avant v3 ne sont pas compatibles avec le hash chaîné.\n")
    
    response = input("Voulez-vous continuer ? (oui/non): ")
    if response.lower() not in ["oui", "o", "yes", "y"]:
        print("Annulé.")
        return
    
    # Sauvegarder une copie de sauvegarde
    backup_file = TX_FILE.parent / "tx.json.backup"
    if TX_FILE.exists():
        with open(TX_FILE, "r", encoding="utf-8") as f:
            old_data = f.read()
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(old_data)
        print(f"\n✓ Sauvegarde créée : {backup_file}")
    
    # Réinitialiser le fichier
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)
    
    print("✓ Fichier de transactions réinitialisé")
    print("\nVous pouvez maintenant créer de nouvelles transactions via l'API.")
    print("Elles seront automatiquement créées avec le hash chaîné (v3).")


if __name__ == "__main__":
    migrate_to_v3()

