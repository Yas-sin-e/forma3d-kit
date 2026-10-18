# Étape 2 — Dépôt, structure et CI

## Objectif et résultat vérifiable

Installer la structure initiale du projet, préparer son suivi Git et ajouter une CI gratuite qui vérifie les documents essentiels sur chaque push et pull request.

Résultat local vérifiable : le projet se trouve sous forma3d-studio/forma3d-kit-codex, le dépôt Git local est initialisé sur main, la structure documentaire existe et le workflow de CI décrit un contrôle concret. La création du dépôt GitHub distant et le premier push restent à confirmer par l’étudiante.

## Décisions et périmètre

- Le dossier demandé est forma3d-studio/forma3d-kit-codex afin de conserver le nom du projet.
- Windows a refusé le déplacement direct car le dossier source est utilisé par la session Codex. Une copie de travail a donc été créée au nouvel emplacement et vérifiée par SHA-256 ; la source reste intacte.
- La structure initiale inclut les dossiers backend et frontend avec un README chacun. Le code applicatif sera créé aux étapes prévues, sans serveur ou fichier de code factice.
- Le workflow GitHub Actions vérifie la présence des documents requis. Il ne lance pas de tests Python ou frontend avant l’existence des applications. Le dossier .agents/ et PROMPT-1.md restent locaux et sont exclus de Git.
- Aucun déploiement continu n’est configuré à ce stade : le produit n’a pas encore d’application exécutable. Le déploiement sera cadré à l’étape 11.
- Le dépôt distant et sa visibilité doivent être choisis avant sa création. Aucun contenu n’a été envoyé à GitHub.

## Fichiers et dossiers

| Élément | Rôle |
|---|---|
| README.md | Présente le produit, ses contraintes, sa structure et son état réel |
| .gitignore | Exclut secrets, environnements locaux, caches, données générées et artefacts d’assistant locaux |
| .github/workflows/ci.yml | Vérifie les documents requis sur push et pull request |
| backend/README.md | Explique le rôle prévu du backend et reporte ses commandes à l’étape 4 |
| frontend/README.md | Explique le rôle prévu du frontend et reporte ses commandes à l’étape 8 |
| docs/etapes/etape-02.md | Explique les choix de structure, la CI et les limites de l’étape |
| docs/ETAT.md | Suit l’avancement local et le travail distant restant |

Les fichiers AGENTS.md, PRODUCT.md, DESIGN.md et la documentation de l’étape 1 ont été conservés à l’identique dans la copie vérifiée.

## Logique de la CI

Le workflow se déclenche sur push et pull request. Il s’exécute sur un runner Ubuntu hébergé par GitHub, récupère le dépôt avec l’action officielle actions/checkout, puis vérifie chaque fichier requis avec la commande test.

Si un document manque, le job échoue immédiatement. Cette vérification est volontairement limitée au contenu déjà présent ; les tests du backend et du frontend seront ajoutés quand leur code sera créé.

## Lancement et vérification

La CI s’exécutera sur GitHub après la création du dépôt distant et un push. Avant cette autorisation, vérifier localement :

- git status --short --branch : le dépôt local est sur main et montre les nouveaux fichiers.
- git log -1 --oneline : le commit local initial existe.
- git status --ignored --short : .agents/ et PROMPT-1.md sont ignorés.
- Test-Path -LiteralPath '.github/workflows/ci.yml' : le workflow existe.
- Répéter les commandes Test-Path des documents listés dans le workflow : toutes doivent retourner True.

Aucun serveur d’application ne peut être lancé à l’étape 2. Aucun test applicatif n’est ajouté puisque cette étape ne crée pas de fonction d’application.

## Pourquoi ces choix

- Une structure courte laisse les étapes 4 et 8 créer le backend et le frontend au moment prévu.
- Une CI documentaire est réellement exécutable aujourd’hui et ne prétend pas tester du code inexistant.
- Le workflow n’utilise qu’une action officielle et des commandes shell fournies par le runner.
- Le déploiement est différé jusqu’à ce qu’une application existe ; cela évite un pipeline de publication sans produit à publier.

## État de l’étape

Préparation locale terminée et commit initial créé. Le dépôt distant GitHub et le premier push restent en attente de confirmation de visibilité et d’autorisation.
