# 6. Étape 5 — La base de données PostgreSQL

Fichiers : `backend/app/repositories/base.py`, `backend/app/repositories/factory.py`,
`backend/app/repositories/postgres_repository.py`.

## Pourquoi une base de données ?

Sans base, l'historique des modèles serait perdu à chaque redémarrage du serveur.
On garde dans PostgreSQL les **informations** (état, nom, catégorie, chemins…).
Les **fichiers** eux-mêmes (photos, GLB) restent sur le disque (étape 3).

> Historique : SQLite au Sprint 2, remplacé par PostgreSQL au projet DevOps (décision D5).

## Étape 5.1 — Le contrat (`repositories/base.py`)

```python
class GenerationRepository(Protocol):
    def initialize(self) -> None: ...
    def save_generation(self, record: GenerationRecord) -> None: ...
    def get_generation(self, generation_id: str) -> GenerationRecord | None: ...
    def get_generation_by_public_id(self, public_id: str) -> GenerationRecord | None: ...
    def set_embed_enabled(self, generation_id: str, enabled: bool) -> GenerationRecord | None: ...
    def list_completed_generations(self) -> list[GenerationRecord]: ...
    def create_category(self, slug: str, label: str) -> CategoryRecord: ...
    def delete_category(self, slug: str) -> None: ...
    def create_api_key(self, record: APIKeyRecord) -> APIKeyRecord: ...
    def consume_api_rate_limit(self, key_id, rate_limit_per_minute, now) -> str | None: ...
    def consume_api_daily_quota(self, key_id, daily_limit, now) -> str | None: ...
    ...   # 19 méthodes au total
```

C'est le **patron Repository** : toute la base est cachée derrière ces méthodes. Les services
ne voient jamais de SQL. Le fichier définit aussi des erreurs métier :

| Erreur | Quand |
|---|---|
| `CategoryNotFoundError` | Catégorie inconnue → 404 |
| `CategoryConflictError` | Slug déjà utilisé → 409 |
| `CategoryInUseError` | Suppression d'une catégorie encore utilisée par un modèle → 409 |

## Étape 5.2 — La fabrique (`factory.py`)

```python
def create_repository(database_url=None, *, storage_root=None) -> GenerationRepository:
    url = os.getenv("DATABASE_URL") if database_url is None else database_url
    return PostgresGenerationRepository(normalize_database_url(url), storage_root=storage_root)
```

- `DATABASE_URL` est **obligatoire**. Exemple fictif : `postgresql://forma3d:dev-password@db:5432/forma3d`.
- `normalize_database_url()` refuse une adresse vide ou d'un autre moteur, avec un message clair.
- C'est le principe **« configuration par l'environnement »** : la même image Docker fonctionne
  partout, seule la variable change (`db` dans Docker Compose, `127.0.0.1:5433` en local, base `_test` pour les tests).

### Ne jamais afficher le mot de passe

```python
def mask_database_url(database_url: str) -> str:
    ...
    netloc = f"{parts.username}:***@{host}"
```

`postgresql://forma3d:secret@db:5432/forma3d` devient `postgresql://forma3d:***@db:5432/forma3d` dans le journal.

## Étape 5.3 — L'implémentation (`postgres_repository.py`)

### Une connexion courte par opération

```python
@contextmanager
def _connection(self):
    with psycopg.connect(self._database_url, row_factory=dict_row,
                         connect_timeout=self._connect_timeout,
                         options="-c TimeZone=UTC") as connection:
        yield connection
```

- Le bloc `with` fait **commit** si tout va bien, **rollback** en cas d'erreur, puis ferme.
- `dict_row` : chaque ligne se lit comme un dictionnaire (`row["status"]`).
- `TimeZone=UTC` : toutes les dates sont en temps universel.

### Les tables (créées par `initialize()`)

```
categories                    generations                         api_keys
──────────                    ───────────                         ────────
id  (PK)  ◄──────────┐        id  (PK, UUID texte)                id  (PK)
slug  UNIQUE          └────── category_id  (FK)                   name
label                         status  CHECK (PENDING|RUNNING|     prefix
is_active                              DONE|FAILED)               fingerprint  UNIQUE
created_at                    filename, content_type              created_at
                              source_photo_path, glb_path         revoked
                              duration_seconds  CHECK (>= 0)         ▲
                              error_message, image_warning           │
                              origin  CHECK (generated|imported|     │
                                             example)                │
                              public_id  (index UNIQUE)              │
                              embed_enabled  DEFAULT FALSE           │
                              created_at, updated_at                 │
                                                                     │
          api_usage_daily (api_key_id FK, usage_date, generation_count)   ← quota du jour
          api_rate_events (id, api_key_id FK, occurred_at)               ← limite par minute
```

Les contraintes `CHECK`, `UNIQUE` et `REFERENCES` sont une **deuxième barrière** : même si le code
avait un bug, la base refuserait un état inventé ou une catégorie inexistante.

### `initialize()` : idempotente

```python
connection.execute("SELECT pg_advisory_xact_lock(%s)", (_SCHEMA_LOCK_ID,))
connection.execute("CREATE TABLE IF NOT EXISTS categories (...)")
connection.execute("ALTER TABLE generations ADD COLUMN IF NOT EXISTS public_id TEXT")
...
INSERT INTO categories (slug, label, is_active, created_at) VALUES (%s, %s, TRUE, %s)
ON CONFLICT (slug) DO NOTHING
...
UPDATE generations SET status = 'FAILED', error_message = %s ...
WHERE status IN ('PENDING', 'RUNNING')
```

- **Idempotente** = on peut l'appeler à chaque démarrage sans rien casser (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`).
- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` = **migrations** douces : les anciennes bases reçoivent les nouvelles colonnes.
- Le **verrou consultatif** (`pg_advisory_xact_lock`) : si deux serveurs démarrent en même temps, ils créent le schéma l'un après l'autre.
- Les trois catégories initiales (Chaise, Tabouret, Table d'appoint) sont ajoutées si elles manquent.
- Une génération restée PENDING/RUNNING lors d'un arrêt brutal devient **FAILED** avec « Génération interrompue au redémarrage du serveur. » : aucun modèle ne reste bloqué « en cours » pour toujours.

### Pas d'injection SQL

```python
connection.execute("SELECT id FROM categories WHERE slug = %s FOR UPDATE", (slug,))
```

Les valeurs passent **à côté** du texte SQL (`%s` + tuple). Le pilote les envoie séparément :
une catégorie nommée `'; DROP TABLE categories; --` reste un simple texte.

### Des chemins portables

```python
def _path_to_db(self, path):
    # /app/backend/storage/models/a.glb  →  « models/a.glb »
    return absolute.relative_to(self._storage_root).as_posix()
```

On enregistre `models/a.glb` (relatif) plutôt que `C:\Users\...\a.glb` : la même base fonctionne
sous Windows et dans le conteneur Linux.

### `FOR UPDATE` : la limite par minute sans tricherie

```python
active_key = connection.execute(
    "SELECT id FROM api_keys WHERE id = %s AND NOT revoked FOR UPDATE", (key_id,)).fetchone()
if active_key is None:
    return "revoked"
rate_count = connection.execute(
    "SELECT COUNT(*) AS n FROM api_rate_events WHERE api_key_id = %s AND occurred_at > %s",
    (key_id, cutoff)).fetchone()["n"]
if rate_count >= rate_limit_per_minute:
    return "rate_limit"
connection.execute("INSERT INTO api_rate_events (api_key_id, occurred_at) VALUES (%s, %s)", ...)
return None
```

`FOR UPDATE` **verrouille la ligne** de la clé jusqu'à la fin de la transaction. Si 20 requêtes
arrivent en même temps avec la même clé, elles comptent **l'une après l'autre** : impossible de
dépasser la limite en tirant toutes en même temps. Même logique pour le quota du jour
(`consume_api_daily_quota`, avec `ON CONFLICT ... DO UPDATE` pour incrémenter le compteur).

### Supprimer une catégorie en sécurité

`delete_category()` verrouille la catégorie (`FOR UPDATE`), vérifie qu'aucune génération ne l'utilise,
puis la supprime ; sinon elle lève `CategoryInUseError`.

## À retenir

> Le service demande, le dépôt exécute. PostgreSQL protège les données par ses contraintes,
> les requêtes paramétrées empêchent l'injection SQL, et `FOR UPDATE` rend les quotas fiables.
