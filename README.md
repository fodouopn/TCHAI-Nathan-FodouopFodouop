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
│   ├── tx.json                    # Stockage des transactions
│   └── keys.json                  # Stockage des clés publiques (v4)
├── keys/                           # Clés privées (à garder secrètes)
│   └── *_private_key.pem          # Clés privées générées
├── utils/                          # Scripts utilitaires
│   ├── generate_keys.py           # Génération de paires de clés (v4)
│   └── sign_transaction.py        # Signature de transactions (v4)
├── tests/                          # Scripts de test et d'attaque
│   ├── attack_change_amount.py    # Ex4: Attaque modification montant (v1)
│   ├── test_attack_detection_v2.py # Ex7: Test détection attaque (v2)
│   ├── attack_delete_transaction.py # Ex8: Attaque suppression (v2)
│   ├── test_attacks_v3.py          # Ex10: Test détection attaques (v3)
│   ├── attack_insert_transaction.py # Ex11: Attaque insertion (v3)
│   └── migrate_to_v3.py            # Script de migration vers v3
└── README.md
```

## Installation et démarrage

### Prérequis

- Python 3.7+
- Flask (installé via pip)

### Installation

```bash
pip install flask requests cryptography
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

### Tchaï v4 (cryptographie asymétrique)

**Structure des transactions** : `(P1, P2, t, a, h, signature)`
- `P1` : expéditeur (doit avoir une clé publique enregistrée)
- `P2` : destinataire
- `t` : timestamp ISO8601
- `a` : montant
- `h` : hash SHA-256 chaîné de `P1|P2|t|a|h_prev`
- `signature` : Signature RSA de `P1|P2|t|a` (base64)

**Cryptographie** : RSA-2048 avec padding PSS et SHA-256
- Bibliothèque : `cryptography` (Python)
- Format des clés : PEM
- Format des signatures : Base64

- **POST `/keys/<personne>`** : Enregistrer la clé publique d'une personne
  - Body: `{"public_key": "..." (format PEM)}`
  - Retourne un message de confirmation

- **GET `/keys/<personne>`** : Récupérer la clé publique d'une personne
  - Retourne la clé publique au format PEM

- **A1** - POST `/transactions` : Enregistrer une transaction signée (v4)
  - Body: `{"p1": "expéditeur", "p2": "destinataire", "a": montant, "signature": "..." (base64, requis)}`
  - Le système vérifie automatiquement la signature avant d'accepter la transaction
  - Retourne une erreur si la signature est invalide ou si la clé publique n'est pas enregistrée

- **A2** - GET `/transactions` : Liste de toutes les transactions (inclut les signatures)

- **A3** - GET `/transactions/<personne>` : Liste des transactions liées à une personne (inclut les signatures)

- **A4** - GET `/balance/<personne>` : Solde d'une personne (entrées - sorties)

- **A5** - GET `/verify` : Vérifier l'intégrité des données (v4)
  - Vérifie les hashs chaînés (v3)
  - Vérifie les signatures cryptographiques (v4)
  - Retourne les transactions invalides avec la raison (hash invalide, signature invalide, etc.)

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

### Exercice 11 - Attaque : Insertion de transaction frauduleuse

**Scénario** : Un attaquant insère une transaction frauduleuse dans le fichier `data/tx.json` (ex: une transaction vers son propre compte depuis le compte d'une victime).

**Procédure** :
1. Créer plusieurs transactions légitimes via l'API
2. Insérer manuellement une transaction frauduleuse dans `data/tx.json`
   - La transaction doit avoir un hash calculé avec le hash de la transaction précédente
   - Mais elle est insérée au milieu de la chaîne
3. Vérifier que le système détecte cette insertion

**Résultat** : 
- ✅ L'attaque est détectée : les transactions suivantes ont un hash invalide
- ✅ Le système v3 avec hash chaîné protège contre les insertions
  - Si une transaction est insérée au milieu, elle casse la chaîne
  - Les transactions suivantes dépendent du hash de la transaction précédente
  - Le hash attendu ne correspond plus au hash réel
- ⚠️  **Note** : Si l'attaquant calcule correctement le hash avec le prev_hash, la transaction insérée peut sembler valide, mais elle casse quand même la chaîne pour les transactions suivantes

**Script de test** : `tests/attack_insert_transaction.py`

**Exécution du test** :
```bash
# Assurez-vous que le serveur Flask est démarré (python app.py)
python tests/attack_insert_transaction.py
```

**Test manuel** :
1. Créer au moins 3 transactions via Postman :
   - POST `http://localhost:5000/transactions` avec `{"p1": "alice", "p2": "bob", "a": 100}`
   - POST `http://localhost:5000/transactions` avec `{"p1": "bob", "p2": "charlie", "a": 50}`
   - POST `http://localhost:5000/transactions` avec `{"p1": "charlie", "p2": "alice", "a": 25}`

2. Vérifier l'intégrité : GET `/verify` → `"status": "OK"`

3. Ouvrir `data/tx.json` et insérer une transaction frauduleuse :
   - Prendre le hash de la première transaction
   - Créer une nouvelle transaction avec ce hash comme `prev_hash`
   - Insérer cette transaction entre la première et la deuxième
   - Exemple : `{"id": 999, "p1": "alice", "p2": "attacker", "a": 1000, "t": "...", "h": "..."}`

4. Vérifier à nouveau : GET `/verify` → `"status": "KO"`
   - Les transactions suivantes sont invalides (chaîne cassée)
   - Le système détecte que le hash précédent attendu ne correspond pas

## Tchaï cryptographique (v4)

### Exercice 12 - Lecture des ressources Bitcoin

**Objectif** : Lire et comprendre les concepts fondamentaux de Bitcoin et de la blockchain.

**Ressources à lire** :
1. **Message de Satoshi Nakamoto** sur "The Cryptography and Cryptography Policy Mailing List" (2008)
   - Archive 1 : https://www.metzdowd.com/pipermail/cryptography/2008-October/014810.html
   - Archive 2 : https://www.mail-archive.com/cryptography@metzdowd.com/msg09959.html

2. **Papier original Bitcoin** : "Bitcoin: A Peer-to-Peer Electronic Cash System" (2008)
   - https://web.archive.org/web/20140320135003/https://bitcoin.org/bitcoin.pdf

**Résumé complet des ressources Bitcoin** :

#### Message de Satoshi Nakamoto (2008)

Satoshi Nakamoto présente Bitcoin comme une solution au problème de la double dépense dans un système de paiement électronique sans autorité centrale. Il explique que le système utilise :
- Des **signatures cryptographiques** pour garantir l'authenticité des transactions
- Un **réseau peer-to-peer** pour éviter le besoin d'une banque centrale
- Une **chaîne de preuves de travail** (blockchain) pour maintenir un historique public des transactions
- Un système de **consensus distribué** où les nœuds du réseau valident les transactions

Le problème principal résolu : comment empêcher qu'une même pièce électronique soit dépensée deux fois sans avoir besoin d'une autorité centrale de confiance.

#### Papier Bitcoin : "A Peer-to-Peer Electronic Cash System" (2008)

**1. Introduction et problème**
- Les systèmes de paiement électronique nécessitent une confiance en une autorité centrale (banque)
- Le problème de la **double dépense** : une même pièce peut être dépensée plusieurs fois
- Solution proposée : un système de paiement électronique **peer-to-peer** sans autorité centrale

**2. Transactions électroniques**
- Une transaction transfère des pièces d'un propriétaire à un autre
- Chaque propriétaire signe numériquement la transaction avec sa **clé privée**
- La transaction est diffusée à tous les nœuds du réseau
- Les nœuds vérifient la signature avec la **clé publique** du propriétaire

**3. Timestamp Server (Serveur d'horodatage)**
- Le système utilise un **serveur d'horodatage distribué** basé sur la preuve de travail
- Chaque bloc contient un hash du bloc précédent, créant une **chaîne de blocs** (blockchain)
- Cette chaîne garantit l'ordre chronologique des transactions
- Modifier un bloc nécessiterait de recalculer tous les blocs suivants (impossible en pratique)

**4. Preuve de travail (Proof of Work)**
- Mécanisme pour créer un consensus distribué sans autorité centrale
- Les nœuds (mineurs) résolvent un problème cryptographique difficile (trouver un hash avec un certain nombre de zéros)
- Le premier à résoudre le problème peut ajouter un bloc à la chaîne
- La difficulté s'ajuste automatiquement pour maintenir un rythme constant de création de blocs
- La preuve de travail rend très coûteux de modifier l'historique des transactions

**5. Réseau**
- Architecture **peer-to-peer** : pas de serveur central
- Les nouveaux nœuds rejoignent le réseau en se connectant à d'autres nœuds
- Les transactions sont diffusées à tous les nœuds
- Chaque nœud valide indépendamment les transactions et les blocs
- Le consensus émerge naturellement : la chaîne la plus longue est considérée comme valide

**6. Incitation (Incentive)**
- Les mineurs sont récompensés avec de nouvelles pièces pour chaque bloc créé
- Cela incite les nœuds à participer au réseau et à maintenir sa sécurité
- Les frais de transaction peuvent également récompenser les mineurs

**7. Réclamation d'espace disque**
- Les anciennes transactions peuvent être supprimées pour économiser l'espace
- Seul le hash du bloc (Merkle root) est conservé, pas toutes les transactions
- Cela permet de réduire la taille de la blockchain tout en maintenant l'intégrité

**8. Vérification des paiements simplifiée**
- Les nœuds peuvent vérifier les transactions sans télécharger toute la blockchain
- Un nœud peut vérifier qu'une transaction est valide en vérifiant la chaîne de blocs jusqu'à la transaction

**9. Combinaison et division de valeur**
- Les transactions peuvent combiner plusieurs entrées (pièces reçues) et créer plusieurs sorties (destinations)
- Cela permet de diviser et combiner les valeurs de manière flexible

**10. Confidentialité**
- Les transactions sont publiques mais les identités sont protégées
- Les clés publiques sont utilisées comme adresses (pseudonymes)
- Un utilisateur peut générer de nouvelles paires de clés pour chaque transaction pour plus de confidentialité

**11. Calculs**
- Analyse de la probabilité qu'un attaquant puisse créer une chaîne alternative plus longue
- Plus la chaîne légitime est longue, plus il devient improbable qu'un attaquant puisse la dépasser
- La probabilité diminue exponentiellement avec le nombre de blocs

**Concepts clés pour Tchaï v4** :
- **Signatures cryptographiques** : Chaque transaction doit être signée avec la clé privée de l'expéditeur
- **Vérification** : La signature est vérifiée avec la clé publique correspondante
- **Authenticité** : Seul le détenteur de la clé privée peut créer une transaction valide
- **Intégrité** : La signature garantit que la transaction n'a pas été modifiée
- **Non-répudiation** : L'expéditeur ne peut pas nier avoir créé la transaction
- **Chaîne de blocs** : Chaque bloc dépend du précédent, rendant les modifications impossibles
- **Consensus distribué** : Pas besoin d'autorité centrale, le réseau valide les transactions

**Application à Tchaï v4** :
- Chaque transaction doit inclure la signature de l'expéditeur (P1)
- La clé publique de P1 doit être disponible pour vérifier la signature
- Le système doit rejeter toute transaction avec une signature invalide
- Cela empêche qu'un attaquant crée des transactions au nom d'autres personnes

### Exercice 13 - Cryptographie asymétrique (v4)

**Objectif** : Utiliser la cryptographie asymétrique pour assurer l'authenticité de l'expéditeur.

**Implémentation** :
- **Algorithme** : RSA avec padding PSS et SHA-256
- **Bibliothèque** : `cryptography` (Python)
- **Format des clés** : PEM
- **Format des signatures** : Base64

**Structure des transactions v4** : `(P1, P2, t, a, h, signature)`
- `P1` : expéditeur (doit avoir une clé publique enregistrée)
- `P2` : destinataire
- `t` : timestamp ISO8601
- `a` : montant
- `h` : hash SHA-256 chaîné de `P1|P2|t|a|h_prev`
- `signature` : Signature RSA de `P1|P2|t|a` (base64)

**Nouveaux endpoints** :
- **POST `/keys/<personne>`** : Enregistrer la clé publique d'une personne
  - Body: `{"public_key": "..." (format PEM)}`
  - Retourne un message de confirmation

- **GET `/keys/<personne>`** : Récupérer la clé publique d'une personne
  - Retourne la clé publique au format PEM

**Modification de l'endpoint A1** :
- **POST `/transactions`** (v4) : Enregistrer une transaction signée
  - Body: `{"p1": "...", "p2": "...", "a": montant, "t": (optionnel), "signature": "..." (base64, requis)}`
  - Le système vérifie automatiquement la signature avant d'accepter la transaction
  - Retourne une erreur si la signature est invalide ou si la clé publique n'est pas enregistrée

**Modification de l'endpoint A5** :
- **GET `/verify`** (v4) : Vérifie l'intégrité ET les signatures
  - Vérifie les hashs chaînés (v3)
  - Vérifie les signatures cryptographiques (v4)
  - Retourne les transactions invalides avec la raison (hash invalide, signature invalide, etc.)

**Scripts utilitaires** :
- `utils/generate_keys.py` : Génère une paire de clés RSA pour une personne
  ```bash
  python utils/generate_keys.py alice
  ```
  - Génère `keys/alice_private_key.pem` (à garder secret)
  - Affiche la clé publique à enregistrer dans le système

- `utils/sign_transaction.py` : Signe une transaction avec une clé privée
  ```bash
  python utils/sign_transaction.py alice alice bob 100
  ```
  - Génère la signature à utiliser dans POST `/transactions`

**Procédure complète pour créer une transaction signée** :

1. **Générer une paire de clés** :
   ```bash
   python utils/generate_keys.py alice
   ```

2. **Enregistrer la clé publique dans le système** :
   ```bash
   POST http://localhost:5000/keys/alice
   Body: {"public_key": "-----BEGIN PUBLIC KEY-----\n..."}
   ```

3. **Signer une transaction** :
   ```bash
   python utils/sign_transaction.py alice alice bob 100
   ```

4. **Créer la transaction avec la signature** :
   ```bash
   POST http://localhost:5000/transactions
   Body: {
     "p1": "alice",
     "p2": "bob",
     "a": 100,
     "signature": "..."
   }
   ```

**Avantages de la v4** :
- ✅ **Authenticité** : Seul le détenteur de la clé privée peut créer une transaction valide
- ✅ **Intégrité** : La signature garantit que la transaction n'a pas été modifiée
- ✅ **Non-répudiation** : L'expéditeur ne peut pas nier avoir créé la transaction
- ✅ **Protection contre les attaques** : Un attaquant ne peut pas créer de transactions au nom d'autres personnes

**Installation des dépendances** :
```bash
pip install cryptography
```
