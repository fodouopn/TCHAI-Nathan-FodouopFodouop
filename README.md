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
- **Fonction de hachage** : SHA-256 (bibliothèque standard `hashlib`)
- **Justification** : 
  - Flask est léger et simple pour une API REST
  - Le stockage JSON facilite les tests d'attaque (modification directe du fichier)
  - Pas de dépendance à une base de données externe
  - SHA-256 est une fonction de hachage cryptographique standard, sécurisée et rapide

## Structure du projet

```
.
├── app.py                          # Application Flask principale
├── data/
│   └── tx.json                    # Stockage des transactions
├── tests/                          # Scripts de test et d'attaque
│   ├── attack_change_amount.py    # Ex4: Attaque modification montant (v1)
│   ├── test_attack_detection_v2.py # Ex7: Test détection attaque (v2)
│   ├── attack_delete_transaction.py # Ex8: Attaque suppression (v2)
│   ├── test_attacks_v3.py          # Ex10: Test détection attaques (v3)
│   └── migrate_to_v3.py            # Script de migration vers v3
└── README.md
```

## Installation et démarrage

### Prérequis

- Python 3.7+
- Flask (installé via pip)

### Installation

```bash
pip install flask requests
```

### Démarrage du serveur

```bash
python app.py
```

Le serveur sera accessible sur `http://localhost:5000`

### Tests

Les scripts de test nécessitent que le serveur Flask soit démarré :

```bash
# Dans un terminal : démarrer le serveur
python app.py

# Dans un autre terminal : exécuter les tests
python tests/test_attacks_v3.py
```

## API HTTP

### Tchaï v1

- **A1** - POST `/transactions` : Enregistrer une transaction
  - Body: `{"p1": "expéditeur", "p2": "destinataire", "a": montant}`
  - Retourne la transaction créée avec ID et timestamp

- **A2** - GET `/transactions` : Liste de toutes les transactions (ordre chronologique)

- **A3** - GET `/transactions/<personne>` : Liste des transactions liées à une personne

- **A4** - GET `/balance/<personne>` : Solde d'une personne (entrées - sorties)

### Tchaï v2 (avec hash)

**Structure des transactions** : `(P1, P2, t, a, h)`
- `P1` : expéditeur
- `P2` : destinataire
- `t` : timestamp ISO8601
- `a` : montant
- `h` : hash SHA-256 de `P1|P2|t|a`

**Fonction de hachage** : SHA-256
- Format du hash : hexadécimal (64 caractères)
- Données hachées : concaténation de `p1|p2|t|a` (séparateur `|`)
- Bibliothèque : `hashlib` (standard Python)

- **A1** - POST `/transactions` : Enregistrer une transaction (calcule automatiquement le hash)
  - Body: `{"p1": "expéditeur", "p2": "destinataire", "a": montant}`
  - Retourne la transaction avec ID, timestamp et hash

- **A2** - GET `/transactions` : Liste de toutes les transactions (ordre chronologique, inclut les hashs)

- **A3** - GET `/transactions/<personne>` : Liste des transactions liées à une personne (inclut les hashs)

- **A4** - GET `/balance/<personne>` : Solde d'une personne (entrées - sorties)

- **A5** - GET `/verify` : Vérifier l'intégrité des données
  - Recalcule les hashs de toutes les transactions
  - Compare avec les hashs stockés
  - Retourne un rapport avec :
    - `status` : "OK" si toutes les transactions sont valides, "KO" sinon
    - `valid` : booléen indiquant si toutes les transactions sont valides
    - `total_transactions` : nombre total de transactions
    - `valid_count` : nombre de transactions valides
    - `invalid_count` : nombre de transactions invalides
    - `valid_transactions` : liste des IDs des transactions valides
    - `invalid_transactions` : liste détaillée des transactions invalides (avec raison)

### Tchaï v3 (hash chaîné)

**Structure des transactions** : `(P1, P2, t, a, h)`
- `P1` : expéditeur
- `P2` : destinataire
- `t` : timestamp ISO8601
- `a` : montant
- `h` : hash SHA-256 chaîné de `P1|P2|t|a|h_prev`

**Fonction de hachage** : SHA-256 (hash chaîné)
- Format du hash : hexadécimal (64 caractères)
- Données hachées : concaténation de `p1|p2|t|a|h_prev` (séparateur `|`)
- `h_prev` : hash de la transaction précédente (ou "0" pour la première transaction)
- **Avantage** : Chaque transaction dépend de la précédente, ce qui permet de détecter les suppressions et modifications

- **A1** - POST `/transactions` : Enregistrer une transaction (calcule automatiquement le hash chaîné)
  - Body: `{"p1": "expéditeur", "p2": "destinataire", "a": montant}`
  - Le hash inclut automatiquement le hash de la transaction précédente
  - Retourne la transaction avec ID, timestamp et hash chaîné

- **A2** - GET `/transactions` : Liste de toutes les transactions (ordre chronologique, inclut les hashs chaînés)

- **A3** - GET `/transactions/<personne>` : Liste des transactions liées à une personne (inclut les hashs chaînés)

- **A4** - GET `/balance/<personne>` : Solde d'une personne (entrées - sorties)

- **A5** - GET `/verify` : Vérifier l'intégrité des données (v3)
  - Recalcule les hashs chaînés de toutes les transactions dans l'ordre chronologique
  - Vérifie que chaque hash dépend correctement du hash précédent
  - Détecte les modifications, suppressions et insertions
  - Retourne un rapport détaillé avec les transactions invalides

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

### Exercice 7 - Vérification : Détection de l'attaque de modification

**Scénario** : Vérifier que l'attaque de modification de montant (exercice 4) est maintenant détectée grâce au système de hash (v2).

**Procédure** :
1. Créer des transactions légitimes via l'API (elles auront automatiquement un hash)
2. Modifier manuellement un montant dans `data/tx.json`
3. Appeler GET `/verify` pour vérifier l'intégrité
4. Le système doit détecter la corruption

**Résultat** : 
- ✅ L'attaque est détectée : `/verify` retourne `"status": "KO"`
- ✅ La transaction corrompue est identifiée avec le hash invalide
- ✅ Le système v2 avec hash protège contre les modifications de montant

**Script de test** : `tests/test_attack_detection_v2.py`

**Exécution du test** :
```bash
# Assurez-vous que le serveur Flask est démarré (python app.py)
python tests/test_attack_detection_v2.py
```

**Test manuel** :
1. Créer une transaction via Postman :
   - POST `http://localhost:5000/transactions` avec `{"p1": "alice", "p2": "bob", "a": 50}`
   - Noter le hash retourné

2. Vérifier l'intégrité :
   - GET `http://localhost:5000/verify` → devrait retourner `"status": "OK"`

3. Modifier le montant dans `data/tx.json` (ex: changer 50 en 500)

4. Vérifier à nouveau :
   - GET `http://localhost:5000/verify` → devrait retourner `"status": "KO"`
   - La transaction modifiée doit apparaître dans `invalid_transactions`

### Exercice 8 - Attaque : Suppression de transaction

**Scénario** : Un attaquant supprime directement une transaction du fichier `data/tx.json`.

**Procédure** :
1. Créer plusieurs transactions légitimes via l'API
2. Ouvrir `data/tx.json` et supprimer manuellement une transaction
3. Vérifier que le système ne détecte pas la suppression

**Résultat** : 
- ✅ L'attaque réussit : la transaction est supprimée sans détection
- ❌ Le système v2 ne peut pas détecter les suppressions
  - Chaque transaction a un hash indépendant
  - Supprimer une transaction ne casse pas les hashs des autres
- ⚠️  **RISQUE** : La suppression peut entraîner la double dépense
  - Une transaction peut être dépensée deux fois si elle est supprimée
  - Les soldes deviennent incorrects

**Script de test** : `tests/attack_delete_transaction.py`

**Exécution du test** :
```bash
# Assurez-vous que le serveur Flask est démarré (python app.py)
python tests/attack_delete_transaction.py
```

**Test manuel** :
1. Créer au moins 2 transactions via Postman :
   - POST `http://localhost:5000/transactions` avec `{"p1": "alice", "p2": "bob", "a": 100}`
   - POST `http://localhost:5000/transactions` avec `{"p1": "bob", "p2": "charlie", "a": 50}`

2. Vérifier les soldes :
   - GET `http://localhost:5000/balance/alice` → devrait être -100
   - GET `http://localhost:5000/balance/bob` → devrait être +50
   - GET `http://localhost:5000/balance/charlie` → devrait être +50

3. Ouvrir `data/tx.json` et supprimer une transaction (ex: supprimer la transaction de 100)

4. Vérifier l'intégrité :
   - GET `http://localhost:5000/verify` → peut retourner `"status": "OK"` (si les transactions restantes sont valides)
   - Le système ne détecte pas la suppression

5. Vérifier les soldes à nouveau :
   - Les soldes sont maintenant incorrects
   - La transaction supprimée n'est plus comptabilisée

### Exercice 10 - Vérification : Détection des attaques avec hash chaîné (v3)

**Scénario** : Vérifier que les attaques précédentes (modification et suppression) sont maintenant détectées grâce au hash chaîné (v3).

**Procédure** :
1. Créer plusieurs transactions légitimes via l'API (elles auront automatiquement le hash chaîné)
2. Tester l'attaque de modification de montant
3. Tester l'attaque de suppression
4. Vérifier que `/verify` détecte ces attaques

**Résultat** : 
- ✅ **Modification de montant** : Détectée car le hash change, ce qui casse la chaîne pour toutes les transactions suivantes
- ✅ **Suppression** : Détectée car les transactions suivantes dépendent du hash de la transaction supprimée
- ✅ Le système v3 avec hash chaîné protège contre les modifications et suppressions

**Script de test** : `tests/test_attacks_v3.py`

**Exécution du test** :
```bash
# Assurez-vous que le serveur Flask est démarré (python app.py)
python tests/test_attacks_v3.py
```

**Test manuel - Modification** :
1. Créer au moins 3 transactions via Postman
2. Vérifier l'intégrité : GET `/verify` → `"status": "OK"`
3. Modifier un montant dans `data/tx.json` (ex: transaction du milieu)
4. Vérifier à nouveau : GET `/verify` → `"status": "KO"`
   - La transaction modifiée est détectée
   - Les transactions suivantes sont aussi invalides (chaîne cassée)

**Test manuel - Suppression** :
1. Créer au moins 3 transactions via Postman
2. Vérifier l'intégrité : GET `/verify` → `"status": "OK"`
3. Supprimer une transaction dans `data/tx.json` (ex: transaction du milieu)
4. Vérifier à nouveau : GET `/verify` → `"status": "KO"`
   - Les transactions suivantes sont invalides (chaîne cassée)
   - Le système détecte que le hash précédent attendu ne correspond pas
