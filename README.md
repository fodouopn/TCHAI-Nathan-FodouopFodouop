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
