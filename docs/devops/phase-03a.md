# Phase P3a — Dépôt PostgreSQL derrière `GenerationRepository`

- **Branche :** `feature/postgres-repository` (partie du point 4 du barème, 3 pts avec P3b)
- **Date :** 16 novembre 2026
- **Décision D2 :** phase avancée juste après P0, à la demande de l'étudiante.

## 1. Objectif

Remplacer le fichier SQLite par une **vraie base de données serveur** (PostgreSQL) quand on le
demande, sans casser le lancement local ni les tests existants. SQLite est une bibliothèque qui
écrit dans un fichier ; PostgreSQL est un **serveur** séparé, joignable par le réseau, multi-utilisateur,
avec des types stricts et des verrous. C'est ce qui permettra en P3b de le mettre dans **son propre
conteneur**, comme l'exige le barème (« application + base de données »).

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `backend/app/repositories/postgres_repository.py` | créé | Les 19 méthodes du contrat `GenerationRepository`, écrites pour PostgreSQL |
| `backend/app/repositories/factory.py` | créé | Choisit SQLite ou PostgreSQL selon `DATABASE_URL` ; masque le mot de passe pour les journaux |
| `backend/app/main.py` | modifié | Utilise la fabrique au lieu de créer SQLite en dur ; journalise le type de base (jamais l'URL) |
| `backend/requirements.txt` | modifié | Ajoute `psycopg[binary]>=3.2,<4` (accord de l'étudiante le 16/11/2026) |
| `.env.example` | modifié | Documente `DATABASE_URL` avec une valeur fictive |
| `backend/tests/test_repository_factory.py` | créé | 8 tests sans base : choix du moteur, URL refusée, masquage du mot de passe |
| `backend/tests/test_postgres_repository.py` | créé | 7 tests contre un vrai PostgreSQL (ignorés si `TEST_DATABASE_URL` est vide) |

## 3. Logique expliquée

### 3.1 Le patron Repository (pourquoi on n'a touché à aucun service)
Les services (`GenerationService`, `CategoryService`, `APIKeyService`) ne parlent jamais à SQLite
directement : ils appellent l'interface `GenerationRepository` (`repositories/base.py`). Il suffit donc
d'écrire **une deuxième implémentation** de cette interface. C'est l'inversion de dépendance :
le métier dépend d'un contrat, pas d'une technologie. Sans cela, il aurait fallu modifier chaque service.

### 3.2 Configuration par l'environnement (`factory.py`)
```
DATABASE_URL vide           -> SQLiteGenerationRepository (backend/data/forma3d.sqlite3)
DATABASE_URL=postgresql://… -> PostgresGenerationRepository
autre schéma (mysql://…)    -> DatabaseUrlError avec message clair, dès le démarrage
```
C'est le principe « 12-factor : la configuration est dans l'environnement ». La **même image Docker**
tournera en dev, en CI et en staging ; seule la variable change. Sans cela, il faudrait une image
par environnement, ce qui contredit l'idée d'image immuable (P5).

### 3.3 Différences SQLite → PostgreSQL

| Sujet | SQLite | PostgreSQL | Pourquoi |
|---|---|---|---|
| Paramètres SQL | `?` | `%s` | Syntaxe du pilote ; dans les deux cas les valeurs sont envoyées **à part** du SQL (pas d'injection SQL) |
| Booléens | `INTEGER 0/1` + `CHECK` | `BOOLEAN` | Type natif, plus lisible dans DBeaver |
| Dates | texte ISO | `TIMESTAMPTZ` (connexion en UTC) | Le serveur trie et compare de vraies dates |
| Clé auto | `AUTOINCREMENT` | `GENERATED ALWAYS AS IDENTITY` | Norme SQL moderne |
| Migration | lire `PRAGMA table_info` puis `ALTER` | `ADD COLUMN IF NOT EXISTS` | Idempotent en une instruction |
| Atomicité des quotas | `BEGIN IMMEDIATE` (verrou de toute la base) | `SELECT … FOR UPDATE` (verrou de **la ligne** de la clé) | Deux clés différentes ne se bloquent plus entre elles |
| Démarrage concurrent | — | `pg_advisory_xact_lock` | Si deux API démarrent ensemble, une seule crée le schéma à la fois |
| Id après INSERT/UPDATE | `lastrowid` | `RETURNING *` | Une seule requête au lieu de deux |

### 3.4 Transactions
Chaque méthode ouvre **une connexion courte** : `with psycopg.connect(...)` valide (*commit*) si le
bloc réussit et annule (*rollback*) en cas d'exception. Même règle que côté SQLite : aucune transaction
ne reste ouverte pendant l'appel (long) au fournisseur 3D. Un pool de connexions serait l'étape suivante
si le trafic augmentait ; il n'est pas nécessaire ici.

### 3.5 Remarque observée : « trous » dans les identifiants
Dans DBeaver, les catégories ont les id 1, 2, 3 puis 10. C'est normal : `INSERT … ON CONFLICT DO NOTHING`
(exécuté à chaque démarrage) consomme un numéro de séquence même quand la ligne existe déjà.
PostgreSQL garantit l'unicité des identifiants, pas leur continuité.

### 3.6 Sécurité
- L'URL contient le mot de passe : elle n'est **jamais** journalisée. Le démarrage écrit seulement
  `Base de données utilisée : postgresql`. `mask_database_url()` existe si un message doit citer l'URL.
- Le mot de passe de démonstration `dev-password` est fictif et n'apparaît que dans des exemples.
- Le test PostgreSQL **refuse** de tourner si le nom de la base ne contient pas « test »,
  car il supprime les tables à chaque test.

## 4. Lancer et tester (bash / WSL2, depuis la racine du dépôt)

```bash
# 1. Base PostgreSQL de test jetable, accessible seulement depuis le poste (127.0.0.1)
docker run -d --name forma3d-pg-test -e POSTGRES_USER=forma3d -e POSTGRES_PASSWORD=dev-password \
  -e POSTGRES_DB=forma3d_test -p 127.0.0.1:55432:5432 postgres:17-alpine

# 2. Suite complète en mode SQLite (les 7 tests PostgreSQL sont ignorés)
cd backend
PYTHON_DOTENV_DISABLED=true HF_SPACE_ID= python -m pytest -q

# 3. Suite complète avec PostgreSQL
PYTHON_DOTENV_DISABLED=true HF_SPACE_ID= \
  TEST_DATABASE_URL=postgresql://forma3d:dev-password@127.0.0.1:55432/forma3d_test python -m pytest -q

# 4. Regarder les tables
docker exec forma3d-pg-test psql -U forma3d -d forma3d_test -c '\dt'

# 5. Nettoyage
docker rm -f forma3d-pg-test
```

**Résultats observés le 16/11/2026 :** SQLite `169 passed, 7 skipped` ; avec PostgreSQL `176 passed`.
Test de bout en bout : l'application démarrée avec `DATABASE_URL` vers PostgreSQL utilise
`PostgresGenerationRepository`, `GET /health` → `{"status":"ok"}`, `POST /categories` → `201`, et la
ligne apparaît dans `SELECT … FROM categories` exécuté par `psql`.

### Visualiser avec DBeaver (fourni par Laragon)
`C:\laragon\bin\dbeaver` → *Nouvelle connexion* → **PostgreSQL** → hôte `127.0.0.1`, port `55432`,
base `forma3d_test`, utilisateur `forma3d`, mot de passe `dev-password` (fictif). DBeaver propose de
télécharger le pilote JDBC PostgreSQL la première fois. En P3b, la base de Compose sera visible sur
`127.0.0.1:5433` uniquement avec `compose.debug.yaml` (décision D4).

## 5. Preuves à conserver

- Sortie `169 passed, 7 skipped` (SQLite) et `176 passed` (PostgreSQL).
- Capture DBeaver montrant les tables `categories`, `generations`, `api_keys`, `api_usage_daily`, `api_rate_events`.
- Sortie du test de concurrence (`test_rate_limit_is_atomic_under_concurrency`).

## 6. À dire en soutenance

> SQLite étant un simple fichier, j'ai ajouté une implémentation PostgreSQL de l'interface
> `GenerationRepository` ; grâce au patron Repository, aucun service métier n'a été modifié.
> Le choix du moteur se fait par la variable `DATABASE_URL`, ce qui permet à une même image Docker de
> tourner partout : vide, on garde SQLite pour le développement ; renseignée, on utilise PostgreSQL.
> J'ai remplacé le verrou global de SQLite par un verrou de ligne `SELECT … FOR UPDATE`, et un test
> lance huit requêtes simultanées pour prouver que la limite de débit reste exacte. Les mêmes tests
> tournent sur SQLite et sur un vrai PostgreSQL, et l'URL de connexion n'est jamais journalisée.
