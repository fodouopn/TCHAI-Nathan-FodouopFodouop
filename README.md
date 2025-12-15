# Projet Tchaï - Système de transactions électroniques

## Objectif

Concevoir un système de transactions électroniques avec une intégrité garantie, accessible par le protocole HTTP.

## Auteurs

- Nathan Fodouop Fodouop
- Mail: nathan_fodouop-fodouop@etu.u-bourgogne.fr

## Choix techniques

- **Langage** : Python 3
- **Framework web** : Flask
- **Stockage** : Fichier JSON (`data/tx.json`)
- **Justification** : 
  - Flask est léger et simple pour une API REST
  - Le stockage JSON facilite les tests d'attaque (modification directe du fichier)
  - Pas de dépendance à une base de données externe

## Structure du projet

```
.
├── app.py              # Application Flask principale
├── data/
│   └── tx.json        # Stockage des transactions
├── tests/              # Scripts de test et d'attaque
│   └── attack_change_amount.py
└── README.md
```

## API HTTP

### Tchaï v1

- **A1** - POST `/transactions` : Enregistrer une transaction
  - Body: `{"p1": "expéditeur", "p2": "destinataire", "a": montant}`
  - Retourne la transaction créée avec ID et timestamp

- **A2** - GET `/transactions` : Liste de toutes les transactions (ordre chronologique)

- **A3** - GET `/transactions/<personne>` : Liste des transactions liées à une personne

- **A4** - GET `/balance/<personne>` : Solde d'une personne (entrées - sorties)

## Attaques et tests

### Exercice 4 - Attaque : Modification de montant

**Scénario** : Un attaquant modifie directement le fichier `data/tx.json` pour changer le montant d'une transaction.

**Procédure** :
1. Créer des transactions légitimes via l'API
2. Ouvrir `data/tx.json` et modifier manuellement un montant
3. Vérifier que le système ne détecte aucune anomalie

**Résultat** : 
- ✅ L'attaque réussit : le montant est modifié sans détection
- ❌ Le système v1 n'a aucun mécanisme de vérification d'intégrité
- ❌ Les soldes deviennent incorrects

**Script de test** : `tests/attack_change_amount.py`

**Exécution du test** :
```bash
python tests/attack_change_amount.py
```

**Test manuel** :
1. Créer quelques transactions via Postman :
   - POST `http://localhost:5000/transactions` avec `{"p1": "alice", "p2": "bob", "a": 10}`
   - POST `http://localhost:5000/transactions` avec `{"p1": "bob", "p2": "charlie", "a": 5}`

2. Vérifier les soldes :
   - GET `http://localhost:5000/balance/alice` → devrait être -10
   - GET `http://localhost:5000/balance/bob` → devrait être +5
   - GET `http://localhost:5000/balance/charlie` → devrait être +5

3. Ouvrir `data/tx.json` et modifier manuellement un montant (ex: changer 10 en 1000)

4. Vérifier à nouveau les soldes :
   - Les soldes sont maintenant incorrects
   - Le système ne signale aucune erreur
