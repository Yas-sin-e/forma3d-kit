# Phase P3b — Docker Compose : API + PostgreSQL

- **Branche :** `feature/compose-postgres`
- **Barème :** point 4, « Compose : api + PostgreSQL, nom de service, 5432 non publié, volume, santé » (3 pts).

## 1. Objectif

Décrire **toute la pile** dans un seul fichier déclaratif : l'API (image de P2) et une vraie base
PostgreSQL dans **son propre conteneur**, reliées par un réseau privé, avec des données qui survivent
à la destruction des conteneurs. Une seule commande démarre l'ensemble : `docker compose up -d --build`.

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `compose.yaml` | créé | Services `api`, `db`, `adminer` (profil `debug`), réseau `backend`, volumes `pgdata` et `storage` |
| `compose.debug.yaml` | créé | Surcharge qui publie PostgreSQL sur `127.0.0.1:5433` pour DBeaver/HeidiSQL (décision D4) |
| `.env.compose.example` | créé | Modèle versionné, valeurs fictives ; copié en `.env.compose` (ignoré par Git) |
| `.gitignore` | modifié | `!.env.*.example` : les modèles sont versionnés, les vrais fichiers `.env.*` restent ignorés |
| `scripts/check-project.sh` | modifié | `compose.yaml` devient un fichier requis |

## 3. Logique expliquée

| Élément | Pourquoi | Sans lui |
|---|---|---|
| `DATABASE_URL=…@db:5432/…` | `db` est le **nom du service** ; le DNS interne de Compose le résout (`getent hosts db` → `172.19.0.2`) | Avec `localhost`, l'API se cherche une base **dans son propre conteneur** → `Connection refused` |
| `db` **sans** `ports:` | La base n'est joignable que par les conteneurs du réseau `backend` | Base exposée sur le poste, voire le réseau local : surface d'attaque inutile |
| `depends_on: condition: service_healthy` | L'API attend que `pg_isready` réussisse, pas seulement que le conteneur soit lancé | L'API démarre avant que PostgreSQL accepte les connexions et plante |
| `healthcheck: pg_isready` | Donne à Docker un vrai état « healthy » de la base | `depends_on` ne saurait attendre que le démarrage du processus |
| `$${POSTGRES_USER}` | `$$` = un `$` littéral : la variable est lue **dans le conteneur**, pas par Compose | Compose remplacerait par une valeur vide |
| volume nommé `pgdata` | Les fichiers PostgreSQL vivent hors du conteneur, gérés par Docker | `docker compose down` effacerait toute la base |
| volume nommé `storage` | GLB et photos générés conservés de la même façon | Modèles 3D perdus à chaque recréation |
| `env_file: .env.compose` ignoré + modèle `.example` | Aucun mot de passe dans Git ; la procédure reste reproductible (`cp … .example …`) | Mot de passe commité, même fictif : mauvaise habitude |
| `127.0.0.1:8080:8080` | L'API n'est publiée que sur le poste | Studio (sans authentification forte) visible sur le réseau local |
| `restart: unless-stopped` | Redémarrage automatique après un plantage ou un redémarrage de Docker | Service arrêté jusqu'à intervention manuelle |
| `adminer` + `profiles: [debug]` | Défi atelier 4 : outil de debug absent d'un `up` normal | L'outil d'administration tournerait en permanence |
| `compose.debug.yaml` | Ouvre la base à DBeaver **volontairement**, sur 127.0.0.1:5433 uniquement | Il faudrait publier 5432 en permanence (contraire au barème) |

### `stop` / `down` / `down -v` (à savoir réciter)

| Commande | Conteneurs | Réseau | Volumes (données) |
|---|---|---|---|
| `docker compose stop` | arrêtés, conservés | conservé | conservés |
| `docker compose down` | supprimés | supprimé | **conservés** |
| `docker compose down -v` | supprimés | supprimé | **SUPPRIMÉS** — seule commande destructive |

## 4. Lancer et vérifier (observé le 16/11/2026)

```bash
cp .env.compose.example .env.compose
docker compose config --quiet && echo "config OK"
docker compose up -d --build
docker compose ps                              # api healthy 127.0.0.1:8080->8080 ; db healthy 5432/tcp (non publié)
curl -fsS localhost:8080/health                # {"status":"ok"}
docker compose exec api getent hosts db        # 172.19.0.2  db
(exec 3<>/dev/tcp/127.0.0.1/5432) 2>/dev/null && echo ouvert || echo "fermé (voulu)"
docker volume ls                               # forma3d_pgdata, forma3d_storage
```

L'API dans le conteneur utilise bien `PostgresGenerationRepository` (vérifié par `docker compose exec api python -c …`).

### Preuve de persistance
1. Connexion au Studio (`POST /auth/login`, mot de passe fictif) → `200` ; `POST /categories {"slug":"bench"}` → `201`.
2. `docker compose exec db psql -U forma3d -d forma3d -c "SELECT slug, label FROM categories WHERE slug='bench';"` → `bench | Banc`.
3. `docker compose down` puis `docker compose up -d`.
4. Même requête → `bench | Banc` : **la donnée a survécu** à la destruction des conteneurs.
   (La session du Studio, elle, est invalidée : sa clé de signature change à chaque démarrage, cf. étape 24.)

### Visualiser avec DBeaver (Laragon)
```bash
docker compose -f compose.yaml -f compose.debug.yaml up -d
```
DBeaver → PostgreSQL → `127.0.0.1` port `5433`, base `forma3d`, utilisateur `forma3d`, mot de passe `dev-password`.
Observé : connexion réussie, tables `api_keys`, `api_rate_events`, `api_usage_daily`, `categories`, `generations`.
Alternative web : `docker compose --profile debug up -d` → Adminer sur `http://localhost:8081`
(système PostgreSQL, serveur `db`). Observé : HTTP 200. Revenir ensuite au mode normal : `docker compose up -d`.

### Incident documenté : `DATABASE_URL` sur `localhost`
1. **État :** `docker compose ps -a api` → `Up 2 seconds (health: starting)` qui se répète : le conteneur redémarre en boucle (`restart: unless-stopped`).
2. **Journaux :** `docker compose logs api` → première erreur utile :
   `psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5432 failed: Connection refused`
3. **Configuration effective :** `docker compose exec api env | grep DATABASE_URL` → `…@localhost:5432/forma3d` (mot de passe masqué à l'affichage).
4. **Hypothèse :** dans le conteneur `api`, `localhost` est le conteneur lui-même ; la base est sur l'hôte `db`.
5. **Correction unique :** `@localhost:5432` → `@db:5432` dans `.env.compose`, puis `docker compose up -d api`.
6. **Revalidation :** `api Up 12 seconds (healthy)`, `/health` → `{"status":"ok"}`.

## 5. Preuves à conserver

`docker compose ps` (deux services healthy, 5432 non publié), `getent hosts db`, la séquence de persistance,
`docker volume ls`, l'extrait de log de l'incident, une capture DBeaver des tables.

## 6. À dire en soutenance

> Ma pile Compose contient l'API et une base PostgreSQL dans deux conteneurs séparés, sur un réseau
> privé. L'API joint la base par le nom de service `db`, résolu par le DNS de Compose ; avec `localhost`,
> elle chercherait la base dans son propre conteneur, et j'ai reproduit cette panne pour la diagnostiquer
> dans les journaux. Le port 5432 n'est pas publié et l'API attend que la base soit saine grâce à
> `depends_on: service_healthy`. Les données sont dans un volume nommé : j'ai prouvé qu'une catégorie
> survit à `docker compose down`, et seule la commande `down -v` les effacerait.
