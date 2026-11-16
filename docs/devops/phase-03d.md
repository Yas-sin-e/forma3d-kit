# Phase P3d — Migration des données SQLite vers PostgreSQL et test complet de l'application

- **Branche :** `feature/data-migration`
- **Date :** 16 novembre 2026
- **Demande de l'étudiante :** « migrer mes données dans la nouvelle base », « tester toute l'application »,
  « comment je vois ma base de données ».
- **Barème :** consolide le point 4 (vraie base, persistance prouvée) et prépare la démonstration.

## 1. Objectif

Retrouver dans PostgreSQL **toutes** les données créées pendant les Sprints 1 à 5 (catégories, modèles,
clé API), avec leurs photos et GLB, puis prouver que l'application entière fonctionne sur la nouvelle base.

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `tools/migrate_sqlite_to_postgres.py` | créé | Outil de reprise **unique** : lit l'ancienne base SQLite en lecture seule et copie tout vers PostgreSQL en une transaction |
| `backend/tests/test_sqlite_migration.py` | créé | 4 tests : chemins portables, copie complète, rejouabilité, simulation, codes de sortie |
| `backend/app/repositories/postgres_repository.py` | modifié | Chemins **relatifs** au dossier de stockage (`storage_root`) |
| `backend/app/repositories/factory.py`, `backend/app/main.py` | modifiés | Transmettent le dossier de stockage au dépôt |
| `backend/tests/test_postgres_repository.py` | modifié | 2 tests sur les chemins portables |
| `docs/COMPRENDRE-FORMA3D.md` | modifié | Sections 3 à 6, 20 et 22 réécrites pour PostgreSQL (explication du code) |

## 3. Le problème des chemins, et sa solution

L'ancienne base enregistrait des chemins Windows **absolus** :
`C:\Users\…\backend\storage\models\4521a7f1-….glb`. Dans le conteneur Linux, ce chemin n'existe pas.

Solution : le dépôt enregistre désormais le chemin **relatif** au dossier de stockage, `models/4521a7f1-….glb`,
et le rattache au dossier de stockage de l'environnement courant à la lecture :

| Environnement | Dossier de stockage | Chemin reconstruit |
|---|---|---|
| Conteneur `api` | `/app/backend/storage` (volume `storage`) | `/app/backend/storage/models/4521a7f1-….glb` |
| Poste Windows (`dev.ps1`) | `…\forma3d-kit-codex\backend\storage` | `…\backend\storage\models\4521a7f1-….glb` |

Une seule base sert donc aux deux. Un chemin hors du stockage reste absolu (compatibilité).

## 4. La migration, pas à pas (exécutée le 16/11/2026)

**Données source** (copie en lecture seule de `backend/data/forma3d.sqlite3`) : 5 catégories, 17 générations
(3 `DONE`, 14 `FAILED`), 1 clé API (empreinte seulement), 0 quota journalier, 2 événements de débit.

```bash
docker compose -f compose.yaml -f compose.debug.yaml up -d --wait db
python tools/migrate_sqlite_to_postgres.py --dry-run     # 1. simulation
python tools/migrate_sqlite_to_postgres.py               # 2. migration réelle
python tools/migrate_sqlite_to_postgres.py               # 3. rejouée : n'insère rien
```

| Table | Simulation | Migration | 2e exécution |
|---|---|---|---|
| `categories` | 2 insérées, 3 déjà présentes | 2 insérées (`canape`, `autre`), 3 déjà présentes (catégories de départ) | 0 insérée |
| `generations` | 17 | 17 | 0 insérée, 17 déjà présentes |
| `api_keys` | 1 | 1 | 0 |
| `api_usage_daily` | 0 | 0 | 0 |

`api_rate_events` n'est pas copiée : ce sont les appels de la dernière minute, sans valeur après coup.
Avant la migration, la catégorie de test `bench` créée en P3b (sans modèle) a été supprimée de la base Compose.

**Fichiers :** les photos et GLB (29 Mo : 43 photos, 16 GLB) ont été copiés dans le volume Docker :
```bash
docker compose exec api mkdir -p /app/backend/storage/images /app/backend/storage/models
docker compose cp backend/storage/images/. api:/app/backend/storage/images
docker compose cp backend/storage/models/. api:/app/backend/storage/models
docker compose exec -u root api chown -R appuser:appuser /app/backend/storage
```
Le `chown` est indispensable : `docker cp` crée les fichiers au nom de `root`, et l'utilisateur non root
`appuser` ne pourrait plus écrire de nouveaux modèles dans ces dossiers.

**Garanties :** la base SQLite n'est jamais modifiée (ouverte en `mode=ro`) ; tout est fait dans une seule
transaction (une erreur = rien n'est écrit) ; une ligne déjà présente n'est jamais écrasée.

## 5. Test complet de l'application (navigateur intégré, http://localhost:8080, 16/11/2026)

| Parcours | Résultat observé |
|---|---|
| Connexion au Studio (mot de passe fictif de `.env.compose`) | page Accueil |
| Accueil | **3 modèles enregistrés, 1 clé API active, 5 catégories** (tes données migrées) |
| Fiche du fauteuil vert `4521a7f1` | viewer 3D affiché, GLB chargé depuis le volume |
| GLB des 3 modèles migrés | HTTP 200 (1,97 Mo, 1,97 Mo, 1,57 Mo) ; photos sources HTTP 200 |
| Catégories : créer / renommer + désactiver / supprimer | 201 / 200 / 204 |
| Supprimer une catégorie utilisée (`chair`) | 409, refus attendu |
| Clé API : créer / lire `/api/v1` avec clé / sans clé | 201 / 200 (`DONE`) / 401 |
| Code d'intégration `/api/v1/.../integration-code` | 200 |
| Modèle activé : `/public/models/{public_id}`, `/glb`, `/embed/{public_id}` | 200, 200, 200 |
| Révoquer la clé puis l'utiliser / suppression définitive | 200 puis 401 / 204 |
| Import d'un GLB minimal → téléchargement → suppression → téléchargement | 201 → 200 (48 octets) → 204 → 404 |
| Pages Créer, Mes modèles, Catégories, Clés API, Exemples | titres corrects, aucune erreur JavaScript inattendue |
| `docker compose down` puis `up -d` | 3 modèles toujours présents, GLB migré HTTP 200 |
| `/health/provider` | `UNCONFIGURED` : normal, aucun fournisseur 3D configuré dans Compose |

Erreurs de console observées : uniquement les codes 401, 404 et 409 **provoqués volontairement** par ces tests.
Diagnostic d'un faux échec pendant le test : `/models/{id}/download` → 404, car la vraie route est
`/models/{id}/glb` (vérifié dans `routers/models.py`) ; erreur du test, pas de l'application.

**Non testé :** une génération 3D réelle (aucun fournisseur gratuit configuré ni joignable) et `dev.ps1`
lancé de bout en bout (son bloc PostgreSQL a été testé seul en P3c).

## 6. Comment voir ta base de données

### Option A — DBeaver (fourni par Laragon) : recommandé
1. Démarrer la base avec l'accès debug :
   ```bash
   docker compose -f compose.yaml -f compose.debug.yaml up -d
   ```
   (ou lancer `./scripts/dev.ps1`, qui le fait aussi).
2. Ouvrir `C:\laragon\bin\dbeaver\dbeaver.exe`.
3. *Base de données* → *Nouvelle connexion* → **PostgreSQL** → *Suivant*.
4. Hôte `127.0.0.1`, port **`5433`**, base **`forma3d`**, utilisateur **`forma3d`**, mot de passe **`dev-password`**
   (valeur fictive de `.env.compose`). Cocher « Enregistrer le mot de passe » si tu le souhaites.
5. *Tester la connexion* : la première fois, DBeaver propose de télécharger le pilote PostgreSQL → accepter.
6. Dérouler `forma3d` → *Schémas* → `public` → *Tables* : `categories`, `generations`, `api_keys`,
   `api_usage_daily`, `api_rate_events`. Double-clic sur une table → onglet *Données*.
7. Requête utile (*Éditeur SQL*, Ctrl+Entrée) :
   ```sql
   SELECT c.label, g.status, g.filename, g.glb_path, g.embed_enabled, g.created_at
   FROM generations g JOIN categories c ON c.id = g.category_id
   ORDER BY g.created_at DESC;
   ```
8. *Diagramme ER* (clic droit sur `public` → *Afficher le diagramme*) : schéma des relations, utile pour la soutenance.

### Option B — Adminer dans le navigateur
```bash
docker compose --profile debug up -d
```
Ouvrir http://localhost:8081 → Système **PostgreSQL**, Serveur **`db`**, utilisateur `forma3d`,
mot de passe `dev-password`, base `forma3d`.

### Option C — Ligne de commande
```bash
docker compose exec db psql -U forma3d -d forma3d -c "SELECT slug, label FROM categories;"
```

Après l'inspection, revenir au mode normal (port 5433 fermé) : `docker compose up -d`.

## 7. À dire en soutenance

> J'ai migré les données de l'ancienne base SQLite vers PostgreSQL avec un script dédié : il lit la source
> en lecture seule, écrit tout dans une seule transaction et peut être rejoué sans créer de doublon, ce que
> j'ai vérifié par une simulation puis une seconde exécution. J'ai dû rendre les chemins de fichiers
> relatifs au dossier de stockage, car des chemins Windows absolus n'ont aucun sens dans un conteneur
> Linux. J'ai ensuite testé tout le Studio dans le navigateur sur la nouvelle base, y compris après un
> redémarrage de la pile, et je visualise les tables dans DBeaver via un port de debug réservé au poste.
