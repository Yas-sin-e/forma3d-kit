# Phase P0 — Diagnostic d'entrée et cadrage

- **Branche :** `docs/devops-kickoff`
- **Date :** 16 novembre 2026
- **Barème visé :** point 1 « Git propre » (2 pts), partie « aucun secret dans l'historique ».

## 1. Objectif

Partir d'un **état connu** avant de modifier quoi que ce soit, et écrire les décisions qui
encadrent le projet. En DevOps, on ne corrige jamais un système qu'on n'a pas d'abord observé :
c'est la première étape de la méthode de diagnostic (« observer l'état sans rien modifier »).

## 2. Fichiers de la phase

| Fichier | Action | Rôle |
|---|---|---|
| `docs/devops/README.md` | créé | Sommaire des phases, état d'avancement, décisions D1 à D4 |
| `docs/devops/phase-00.md` | créé | Ce compte rendu : commandes, résultats, justification |
| `AGENTS.md` | modifié | Trace l'exception « Docker et PostgreSQL autorisés pour le projet DevOps » |
| `docs/STRUCTURE.md` | modifié | Une ligne par nouveau fichier |
| `docs/ETAT.md` | modifié | Section « Projet DevOps » |

Aucun code applicatif n'est modifié dans cette phase.

## 3. Diagnostic réalisé (sorties observées le 16/11/2026)

| Commande | Résultat observé | Interprétation |
|---|---|---|
| `git status` | aucune modification | On part d'un arbre propre : tout changement à venir sera le nôtre. |
| `git log --oneline --graph -n 15` | historique en « fusions de PR » (#8 à #12), dernier commit `c447aca` | Le travail passe déjà par branches + pull requests, jamais en direct sur `main`. |
| `git remote -v` | `origin` → `github.com/Yas-sin-e/forma3d-kit-codex.git` | Un seul dépôt distant, en HTTPS. |
| `git ls-files \| wc -l` | 141 fichiers suivis | Taille raisonnable, pas de données lourdes versionnées. |
| `docker version` | client 29.2.1, **moteur injoignable** (`dockerDesktopLinuxEngine` absent) | Docker Desktop n'était pas démarré. À lancer avant P2 (avec intégration WSL2). |
| `docker compose version` | v5.0.2 | Compose v2 intégré au CLI (`docker compose`, sans tiret). |
| `netstat -ano` sur 8080 / 5432 / 5433 | aucun processus en écoute | Les ports prévus pour l'API, PostgreSQL et l'accès debug sont libres. |

### Contrôle « aucun secret dans l'historique »

| Commande | Résultat |
|---|---|
| `git log --all --full-history --oneline -- "*.env" ".env" "backend/.env"` | aucun commit |
| `git ls-files \| grep -E '(^\|/)\.env$'` | aucun fichier |
| `git log --all -p \| grep -Ec '(hf_[A-Za-z0-9]{20,}\|ghp_[A-Za-z0-9]{20,})'` | `0` |

- Aucun fichier `.env` n'a **jamais** été commité, sur aucune branche.
- Aucun jeton Hugging Face (`hf_…`) ni GitHub (`ghp_…`) n'apparaît dans l'historique complet.
- La recherche compte les lignes sans les afficher : on ne fait jamais apparaître un éventuel secret dans un terminal ou un journal.
- Conséquence : aucune réécriture d'historique n'est nécessaire, et rendre le dépôt public (bonus B1) resterait possible sans fuite.

### Outils de visualisation disponibles

Laragon est installé avec **DBeaver** et **HeidiSQL**, qui savent tous deux se connecter à
PostgreSQL. Laragon ne fournit pas PostgreSQL lui-même : la base tournera dans Docker (P3b) et
sera visible depuis DBeaver via un accès debug local (décision D4).

## 4. Décisions

Voir le tableau complet dans [README.md](README.md#décisions-tracées) :
- **D1** Docker et PostgreSQL autorisés pour le projet DevOps uniquement ;
- **D2** P3a (dépôt PostgreSQL) avancée juste après P0, à la demande de l'étudiante ;
- **D3** SQLite reste le défaut quand `DATABASE_URL` est vide ;
- **D4** visualisation par DBeaver/HeidiSQL sur `127.0.0.1:5433` via `compose.debug.yaml`.

## 5. Commandes de vérification (bash / WSL2)

```bash
git status
git log --oneline --graph -n 15
git remote -v
git log --all --full-history --oneline -- "*.env" ".env" "backend/.env"
git ls-files | grep -E '(^|/)\.env$' || echo "aucun .env suivi"
git log --all -p | grep -Ec '(hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})'
docker version
docker compose version
ss -ltn | grep -E ':(8080|5432|5433)\b' || echo "ports libres"
```

## 6. Preuves à conserver pour le rendu

- Capture de `git log --oneline --graph -n 15` (historique en PR).
- Capture des trois commandes du contrôle de secrets (résultats vides et `0`).
- Capture de `docker version` **après** démarrage de Docker Desktop (section *Server* remplie).
- URL de la pull request P0 fusionnée.

## 7. À dire en soutenance

> Avant de construire la chaîne DevOps, j'ai fait un diagnostic d'entrée sans rien modifier : état
> Git, dépôt distant, versions de Docker et ports libres. J'ai vérifié que l'historique complet ne
> contient aucun fichier `.env` ni jeton, en comptant les correspondances sans les afficher pour ne
> jamais exposer un secret. Le diagnostic a révélé que le moteur Docker n'était pas démarré : je l'ai
> noté plutôt que de supposer qu'il fonctionnait. J'ai ensuite écrit mes décisions, notamment
> l'autorisation de Docker et PostgreSQL et le maintien de SQLite par défaut, pour que chaque choix
> soit traçable dans le dépôt.
