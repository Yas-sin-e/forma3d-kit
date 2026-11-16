# Révision soutenance — questions probables et réponses

Les énoncés exacts des quiz des ateliers 1 à 5 ne sont pas dans le dépôt : voici les questions les plus
probables sur chaque notion, avec des réponses appuyées sur ce projet. À compléter avec les vrais
énoncés des ateliers.

## Atelier 1 — Git

- **Pourquoi des branches et des pull requests ?** Isoler chaque changement, le faire vérifier par la CI et le relire avant qu'il n'atteigne `main`, qui reste toujours livrable.
- **Différence entre `git merge` et `git rebase` ?** `merge` crée un commit de fusion et garde l'historique réel ; `rebase` réécrit les commits sur une nouvelle base (historique linéaire) — à ne jamais faire sur une branche partagée déjà poussée.
- **Que mettre dans `.gitignore` ?** Secrets (`.env`), environnements (`.venv`), caches, données générées (`backend/data/`, `backend/storage/`). Ici `.env.*` est ignoré sauf les modèles `*.example`.
- **Un secret a été commité, que faire ?** Le **révoquer** d'abord (il est compromis dès le push), puis seulement nettoyer l'historique, avec accord, car c'est une réécriture.
- **Tag léger ou annoté ?** Annoté (`git tag -a`) : il a un auteur, une date, un message — c'est un objet de livraison.

## Atelier 2 — Bash

- **Que signifie le code de sortie ?** 0 = succès, autre = échec ; `$?` contient le code de la dernière commande. La CI s'arrête sur un code non nul.
- **`set -e`, `-u`, `-o pipefail` ?** `-e` arrête au premier échec ; `-u` interdit les variables non définies ; `pipefail` fait échouer un pipeline si une étape échoue. `check-project.sh` n'utilise pas `-e` pour lister toutes les erreurs.
- **stdout ou stderr ?** Les erreurs vont sur stderr (`>&2`) pour être séparables (`2>erreurs.txt`).
- **Pourquoi `#!/usr/bin/env bash` ?** Trouver `bash` dans le `PATH`, quel que soit le système.
- **« bash\r: No such file or directory » ?** Fins de ligne Windows (CRLF) : corrigé par `.gitattributes` `*.sh text eol=lf`.

## Atelier 3 — Docker

- **Image ou conteneur ?** L'image est un modèle immuable en couches ; le conteneur est une instance en cours d'exécution de cette image.
- **Pourquoi copier `requirements.txt` avant le code ?** Cache des couches : les dépendances ne sont réinstallées que si ce fichier change.
- **Pourquoi `0.0.0.0` ?** Avec `127.0.0.1`, l'application n'écoute que dans le conteneur ; le port publié ne reçoit rien.
- **`EXPOSE` publie-t-il le port ?** Non, il documente ; c'est `-p hôte:conteneur` (ou `ports:` dans Compose) qui publie.
- **Pourquoi un utilisateur non root ?** Limiter les dégâts si l'application est compromise (moindre privilège).
- **`HEALTHCHECK` suffit-il ?** Non : il teste depuis l'intérieur. L'incident v1.1.0 était `healthy` mais injoignable depuis l'hôte.
- **Un conteneur s'arrête tout de suite ?** `docker ps -a` (état `Exited`), puis `docker logs` : première erreur utile.

## Atelier 4 — Docker Compose

- **Comment l'API trouve-t-elle la base ?** Par le nom de service `db`, résolu par le DNS du réseau Compose ; `localhost` désigne le conteneur lui-même.
- **`depends_on` seul suffit-il ?** Non, il attend le démarrage du conteneur ; `condition: service_healthy` attend que `pg_isready` réussisse.
- **Pourquoi un volume nommé ?** Les données vivent hors du conteneur et survivent à `down`.
- **`stop` / `down` / `down -v` ?** Arrête ; supprime conteneurs et réseau ; supprime en plus les volumes (seule commande destructive).
- **Pourquoi ne pas publier 5432 ?** La base n'a pas à être joignable hors du réseau de la pile ; accès debug volontaire via `compose.debug.yaml` sur 127.0.0.1:5433.
- **À quoi sert un profil ?** Un service `profiles: [debug]` (Adminer) ne démarre qu'avec `--profile debug`.

## Atelier 5 — CI/CD

- **Intégration, livraison, déploiement continus ?** CI : chaque changement est testé automatiquement. Livraison continue : chaque version produit automatiquement un artefact prêt (image GHCR). Déploiement continu : mise en service automatique — ici volontaire (`deploy.sh`), sauf bonus B2.
- **À quoi sert `needs` ?** Ordonner les jobs : `docker-build` ne tourne que si `test` réussit.
- **Pourquoi `if: always()` sur l'artefact ?** Publier le rapport même quand les tests échouent.
- **Comment publier sans secret dans le dépôt ?** `secrets.GITHUB_TOKEN`, temporaire, avec `permissions: packages: write`.
- **Pourquoi ne pas reconstruire en staging ?** Pour déployer exactement l'image testée ; la version est la variable `IMAGE_TAG`.
- **Comment faire un rollback ?** Remettre le tag sain précédent dans `IMAGE_TAG`, `up -d`, vérifier `/health` ; corriger ensuite en `vX.Y.Z+1`, jamais en déplaçant un tag.
- **Méthode de diagnostic ?** État → journaux (première erreur utile) → configuration effective → hypothèse → une seule correction → revalidation.
