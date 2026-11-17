# Structure expliquée — Forma3D Studio

Mis à jour le 11 novembre 2026. Le Sprint 2 est terminé ; les Sprints 3 et 4 sont retirés. Les étapes 11, 11b et 12 ont amélioré le Studio avant le Sprint 5, maintenant actif (étapes 0, 13 / 5a, 14 / 5b, 15 / 5c et 16 / 5d terminées, plus la refonte visuelle 16b ; étapes 17 / 5e et 18 / 5f terminées). Le Sprint 6 n'est pas démarré.

## Racine et documents de cadrage

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `AGENTS.md` | Instructions de travail, vision et périmètre du sprint | Garde les règles partagées entre les sessions | Avant toute intervention |
| `PRODUCT.md` | Vision, utilisateurs, parcours et limites du SaaS | Évite d'ajouter au sprint une fonction hors sujet | Pendant le cadrage et la soutenance |
| `DESIGN.md` | Source de vérité des couleurs, du texte, des composants et du mouvement | Maintient la cohérence visuelle | Avant de créer ou modifier l'interface |
| `README.md` | Démarrage du dépôt (dont « Démarrer en une commande » avec Docker Compose), état et commandes Windows | Point d'entrée pour l'étudiante et le jury | Au clonage et au lancement |
| `PROMPT-1.md` | Prompt local de démarrage de session v2 | Rappelle les règles au travail quotidien | Au début d'une session Codex ; ignoré par Git |
| `.gitignore` | Exclut secrets (dont `.env.*` sauf les modèles `*.example`), environnements, caches, données locales (`backend/data/`, `backend/storage/`) et sorties générées | Évite de versionner les données locales ou sensibles | Avant chaque commit |
| `.env.example` | Variables fournisseur, plafond GLB, quotas, débit API, origines CORS et origines autorisées à intégrer (aucune par défaut) mot de passe propriétaire `FORMA3D_OWNER_PASSWORD` (vide = connexion refusée) et choix du fournisseur `IMAGE3D_PROVIDER` / `TRELLIS_SPACE_ID` | Rend la configuration explicite sans cible ni secret ni politique de cadrage ouverte | Avant le lancement du service intégrable |
| `sprint-1-v2-saas-3d-ecommerce.docx` | Cahier des charges remis pour le sprint | Conserve la référence de départ et ses exigences | Au cadrage et à la soutenance |
| `.github/` | Configuration destinée au dépôt GitHub | Sépare l'automatisation distante des sources | Sur GitHub |
| `.github/workflows/` | Répertoire des workflows CI | Range les vérifications reproductibles | À chaque push ou pull request |
| `.agents/.ai/` et `.agents/.ai/rules/` | Emplacement local des règles d'assistance | Sépare le contexte d'agent du code livré | Pendant les sessions locales ; règles actuellement vides |
| `.agents/` | Configuration locale de l'assistant, exclue de Git | Sépare les paramètres de Codex des sources applicatives | Pendant le travail local ; pas requis à l'exécution |
| `.agents/skills/` | Emplacement local des skills | N'ajoute pas de dépendance au produit | Quand une skill locale est installée |
| `.agents/skills/.gitkeep` | Marqueur local du répertoire de skills | Rend visible l'emplacement réservé même s'il est vide | Dans le dossier de travail local |
| `.github/workflows/ci.yml` | Pipeline CI : job `test` (check-project, pytest sur service PostgreSQL, artefact JUnit `rapport-tests`) en matrice Python 3.12 et 3.13 (bonus B3), puis job `docker-build` (`needs: test`, image `forma3d:ci`, test de fumée `/health` avec PostgreSQL) | Aucune image construite à partir d.un code qui échoue | À chaque pull request et push sur `main` |
| `.github/workflows/release.yml` | Sur tag `vX.Y.Z` : rejoue contrôles et tests puis publie `ghcr.io/yas-sin-e/forma3d:<tag>` (sans tag `latest`) avec labels OCI, via `GITHUB_TOKEN`, puis job `deploy-staging` (bonus B2) : mise en service sur le runner et contrôle de santé | Image immuable versionnée, sans aucun secret stocké | Au push d'un tag de version |
| `scripts/` | Regroupe les commandes de développement Windows | Évite de mémoriser les étapes venv/tests/serveur | Au démarrage local |
| `scripts/dev.ps1` | Démarre PostgreSQL (`compose.yaml` + `compose.debug.yaml`, 127.0.0.1:5433), crée la base de test, crée le venv absent, installe les dépendances si nécessaire, exécute pytest, démarre Uvicorn et ouvre Edge | Donne un seul parcours reproductible au projet | Depuis PowerShell à la racine |
| `scripts/check-project.sh` | Contrôle Bash du dépôt (fichiers requis, aucun `.env`, fichier de base locale ou GLB suivi, conflits, contrat de port image ↔ Compose, `--strict`), code 0/1 | Un seul contrôle rejoué à l'identique par l'étudiante et par la CI | Avant un commit, une PR, un tag, et dans le job CI `test` |
| `scripts/wait-healthy.sh` | Interroge `/health` (12 × 5 s, `HEALTH_URL` paramétrable) ; « staging sain » code 0, sinon code 1 | Décision automatique et bornée de la mise en service | Après chaque mise en service et par `deploy.sh` |
| `scripts/deploy.sh` | Met en service un tag (`.env.deploy`, pull, up, santé) et revient automatiquement au dernier tag sain (`.last-good-tag`) | Rollback sans reconstruction ni intervention de code | `./scripts/deploy.sh vX.Y.Z` en staging |
| `.gitattributes` | Force les fins de ligne LF pour scripts Bash, Dockerfile et YAML | Évite l'erreur `bash\r` sous Linux quand on travaille sous Windows | Automatiquement à chaque checkout et commit |
| `Dockerfile` | Image de l'API : `python:3.12-slim` fixée, dépendances avant le code, utilisateur `appuser`, `EXPOSE 8080`, `HEALTHCHECK` Python, uvicorn sur 0.0.0.0 | Même environnement en local, en CI et en staging | `docker build`, `docker compose build`, CI et release |
| `.dockerignore` | Exclut Git, `.env`, données locales, caches, tests et docs du contexte de construction | Aucun secret ni donnée locale dans l'image ; construction plus rapide | À chaque construction d'image |
| `compose.yaml` | Pile de développement : `api` (image locale) + `db` PostgreSQL 17 sans port publié, réseau `backend`, volumes `pgdata`/`storage`, Adminer en profil `debug` | Une commande démarre l'application et sa vraie base | `docker compose up -d --build` |
| `compose.debug.yaml` | Surcharge qui publie PostgreSQL sur `127.0.0.1:5433` pour DBeaver/HeidiSQL | Visualiser la base sans laisser 5432 ouvert en usage normal | `docker compose -f compose.yaml -f compose.debug.yaml up -d` |
| `.env.compose.example` | Modèle sans secret de `.env.compose` (identifiants PostgreSQL fictifs, `DATABASE_URL` vers `db`) | Configuration reproductible sans mot de passe dans Git | Copié une fois avant le premier `docker compose up` |
| `compose.staging.yaml` | Staging : image GHCR `${IMAGE_TAG}` sans `build:`, PostgreSQL, volumes, `restart: unless-stopped` | On déploie exactement l'image testée et publiée | Par `deploy.sh` ou `docker compose -p forma3d-staging …` |
| `.env.staging.example` | Modèle sans secret de `.env.staging` (base `forma3d_staging`) | Configuration du staging reproductible, hors Git | Copié une fois avant le premier déploiement |
| `.env.deploy.example` | Modèle de `.env.deploy` : `IMAGE_TAG` seul | La version en service est une variable | Écrit par `deploy.sh` à chaque mise en service |

## Serveur temporaire TripoSR

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `tools/` | Regroupe les outils de développement hors de l'application | Le notebook serveur ne fait pas partie du backend livré | Pour lancer le fournisseur dans un environnement GPU distant |
| `tools/colab/` | Range le notebook d'apprentissage et de contrôle du runtime distant | Isole les dépendances TripoSR des sources backend | Pour vérifier le GPU et comprendre l'historique des essais |
| `tools/trials/` | Outils d'essai de fournisseurs 3D, hors application | Sépare les expériences du code livré | Pendant la sous-étape C |
| `tools/trials/trial_trellis.py` | Lit le contrat d'un Space TRELLIS, envoie une photo et mesure le GLB selon la grille | Rend l'essai reproductible et s'arrête au premier message de quota | Pour comparer un fournisseur à TripoSR |
| `tools/trials/trial_models.py` | Essaie Stable Fast 3D, TRELLIS détouré et InstantMesh en reproduisant l'enchaînement de chaque Space (détourage puis génération) | Compare plusieurs modèles sur les mêmes photos avec les mêmes mesures | Sous-étape C2 |
| tools/colab/triposr_server.ipynb | Contrôle le GPU et explique l'installation distante, mais arrête le lancement d'un serveur web public sur Colab géré gratuit | Respecte la FAQ Colab, qui restreint les services web de génération sur ses runtimes gérés | Pour comprendre l'ancien essai, ses dépendances et la limite d'hébergement actuelle |

## Backend Python

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/` | Regroupe l'API, ses tests et son environnement local | Isole le service Python du reste du produit | Au développement et à l'exécution |
| `backend/app/` | Contient le code importé par FastAPI | Sépare l'application des tests et de sa configuration d'installation | Au démarrage de l'API |
| `backend/app/routers/` | Regroupe les routes HTTP | Sépare les points d'entrée web du métier | À chaque requête |
| `backend/app/services/` | Regroupe validation et orchestration métier | Rend les règles testables sans navigateur | À la réception d'un upload |
| `backend/app/providers/` | Regroupe les adaptateurs image-vers-3D | Isole les SDK et APIs externes | Quand une photo doit être convertie |
| `backend/app/storage/` | Regroupe contrat et implémentation de stockage | Permet de remplacer le disque local sans réécrire le service | À l'enregistrement et au téléchargement |
| `backend/README.md` | Explique l'API, ses limites et ses commandes | Permet de lancer le serveur sans deviner les étapes | À l'installation et au développement |
| `backend/requirements.txt` | Déclare FastAPI, Uvicorn, HTTPX2, pytest, multipart, Gradio Client, python-dotenv, Pillow et psycopg (PostgreSQL, projet DevOps) | Recrée les dépendances du service et de la préparation légère dans le venv | À l'installation et en CI |
| `backend/app/__init__.py` | Marque `app` comme paquet Python | Rend les imports déterministes | Au démarrage et pendant les tests |
| `backend/app/main.py` | Construit FastAPI, initialise le dépôt PostgreSQL désigné par `DATABASE_URL` (obligatoire), câble l’API v1 et la page embed, applique CORS exact ainsi que les erreurs JSON | Configure les services sans modifier le fournisseur ; CORS tiers et cadrage tiers restent fermés par défaut | À l'import et au démarrage d'Uvicorn |
| backend/.env | Configuration locale, dont la cible d'un serveur Gradio autorisé | Fichier ignoré par Git ; ne jamais copier son contenu dans un document, un journal ou un commit | Pour configurer un fournisseur disponible |
| `backend/app/models.py` | Définit les catégories, générations et métadonnées des clés API sans secret en clair | Sépare les données métier du format de stockage et distingue les valeurs sensibles | Pendant la gestion, le suivi et l'authentification |
| `backend/app/repositories/` | Regroupe le contrat de dépôt et les adaptateurs de persistance | Isole SQL des règles métier | Quand le service lit ou écrit l'historique |
| `backend/app/repositories/__init__.py` | Marque le paquet Python des dépôts | Rend leur rôle d'accès aux données explicite | À l'import du service ou de l'adaptateur |
| `backend/app/repositories/base.py` | Définit le contrat de dépôt pour générations, catégories et clés API | Permet de tester ou remplacer l'adaptateur indépendamment | Dans les services et leurs tests |
| `backend/app/repositories/postgres_repository.py` | Seule implémentation du contrat `GenerationRepository` sur PostgreSQL (types natifs, `FOR UPDATE`, verrou consultatif au démarrage, chemins relatifs au stockage) | Vraie base serveur, seule base du projet depuis le 16/11/2026 ; aucun service métier modifié | Au démarrage de l'API et à chaque opération de données |
| `backend/app/repositories/factory.py` | Valide `DATABASE_URL` (obligatoire, `postgresql://` seulement), crée le dépôt PostgreSQL et masque le mot de passe pour les journaux | Configuration par l'environnement : une seule image pour tous les environnements ; erreur claire si la variable manque | Une fois, au chargement de `main.py` |
| `backend/app/config.py` | Charge les paramètres fournisseur, taille GLB, quotas API, débit, origines CORS et origines embed | Centralise les valeurs configurables ; refuse les jokers et valide les origines HTTP(S) exactes | À la création des services et au démarrage |
| `backend/app/providers/huggingface.py` | Sonde la cible sous 5 secondes, découvre les appels et bornes de TripoSR et valide le GLB 2.0 | Évite les noms/plages inventés et n'affiche pas d'adresse dans l'état de santé | Au badge de santé et à chaque génération |
| `backend/app/schemas.py` | Fixe les réponses JSON avec l'origine, l'état, la date, les liens et les deux extraits d'intégration | Stabilise les contrats HTTP sans exposer les chemins locaux | Sur `/categories`, `/models`, `/api-keys` et les contrats publics |
| `backend/app/routers/__init__.py` | Marque le paquet des routes | Clarifie l'organisation Python | À l'import des routes |
| `backend/app/routers/categories.py` | Expose lister, créer, renommer, activer/désactiver et supprimer les catégories | Garde la validation HTTP distincte des règles métier | Aux actions de gestion et au chargement des choix |
| `backend/app/providers/trellis.py` | Fournisseur TRELLIS : contrat vérifié, session, détourage puis GLB texturé ; erreurs claires et jeton masqué | Meilleures couleurs que TripoSR, sans changer le contrat Image3DProvider | Quand `IMAGE3D_PROVIDER=trellis` |
| `backend/app/routers/auth.py` | Routes `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` et dépendance `require_owner` qui protège les routes du Studio | Cookie HttpOnly SameSite=Lax ; `/api/v1`, `/embed`, `/public`, `/static` et le widget restent hors session | À la connexion et à chaque appel du Studio |
| `backend/app/routers/api_keys.py` | Crée, liste et révoque les clés ; supprime définitivement une clé déjà révoquée (`DELETE /api-keys/{id}/permanent`) ; fournit `require_api_key` pour authentifier `X-API-Key` | Ne renvoie le secret qu’à la création et compare des empreintes à temps constant | Sur `#/cles-api` et `/api/v1` |
| `backend/app/routers/api_v1.py` | Crée les modèles avec le service existant, sert l’état et le GLB et retourne les codes iframe/widget | Versionne les URL, impose une clé, un quota quotidien et un débit par clé | Aux appels externes `/api/v1` |
| `backend/app/routers/embed.py` | Sert le viewer isolé d'un modèle terminé et activé sous `/embed/{public_id}` | N'inclut pas la navigation du Studio ; applique `frame-ancestors` limité au même site et aux origines configurées | Quand une boutique intègre un modèle |
| `backend/app/routers/models.py` | Reçoit les photos, importe les GLB, copie les exemples autorisés, expose les états et les routes d’activation/intégration publique | Sépare HTTP du métier et valide les catégories avant l'enregistrement | À l'envoi, au suivi, à l'import, à l'activation et à la consultation des modèles |
| `backend/app/services/__init__.py` | Marque le paquet métier | Clarifie les imports de services | À l'import du validateur et du service |
| `backend/app/services/category_service.py` | Vérifie les catégories, les slugs et les libellés puis traduit les erreurs de persistance | Centralise les règles réutilisables par les routes et les tests | Lors du CRUD et avant chaque upload |
| `backend/app/services/glb_finisher.py` | Ajoute aux GLB générés un matériau mat et des normales par sommet, sans modifier positions, indices ni couleurs ; renvoie l'original en cas de doute | Rend le fichier correct dans tout viewer, sans dépendance ajoutée | Juste avant l'enregistrement d'un GLB généré |
| `backend/app/services/owner_auth.py` | Compare le mot de passe avec `hmac.compare_digest`, signe des jetons HMAC expirant après 8 h et limite à 5 tentatives par minute et par IP (en mémoire) | Aucune dépendance ajoutée ; clé de signature aléatoire par processus | À chaque connexion et vérification de session |
| `backend/app/services/api_key_service.py` | Génère un secret aléatoire, persiste son empreinte SHA-256, vérifie les clés et applique leurs limites | La clé complète n’est jamais stockée ni journalisée | À la création, à la révocation et sur `/api/v1` |
| `backend/app/services/upload_validator.py` | Contrôle extension, MIME, signature et plafond de 10 Mo | Le nom ou le type annoncé seul ne suffit pas | Avant d'enregistrer une photo |
| `backend/app/services/image_preparer.py` | Redresse, compose une image carrée avec marges et mesure petite taille/netteté via Pillow | Prépare une copie temporaire sans modifier l'original ni ajouter de modèle | Juste avant l'appel du fournisseur |
| `backend/app/services/demo_gallery.py` | Liste les cinq GLB autorisés, valide le GLB 2.0 en fichier ou en mémoire et résout les exemples copiables | Partage un validateur strict sans exposer de chemin arbitraire | À l'ouverture de la galerie, à l'import et à la copie d'exemple |
| `backend/app/services/generation_service.py` | Orchestre génération, enregistrement, identifiant public et activation d'intégration des modèles | Garde la validation métier indépendante de la base et du stockage | Après un upload photo, import GLB ou copie d'exemple |
| `backend/app/providers/__init__.py` | Marque le paquet d'adaptateurs | Isole les fournisseurs externes | À l'import fournisseur |
| `backend/app/providers/base.py` | Définit `Image3DProvider.generate(Path) -> bytes` et l'erreur commune | Permet de remplacer Hugging Face sans réécrire le service | Dans GenerationService et les adaptateurs |
| backend/app/providers/huggingface.py | Découvre le contrat avec view_api, lit les valeurs courantes de client.config, exécute les étapes TripoSR et valide GLB 2.0 | Évite d'interpréter les exemples comme des valeurs par défaut et prend la vraie sortie GLB | À chaque génération distante |
| `backend/app/storage/__init__.py` | Marque le paquet des adaptateurs de stockage | Sépare les fichiers de persistance du métier | À l'import du stockage |
| `backend/app/storage/base.py` | Définit le contrat `Storage` pour photos et GLB | Permet de changer la persistance derrière une interface | Dans GenerationService et ses tests |
| `backend/app/storage/local_storage.py` | Écrit les photos et GLB avec des noms UUID serveur et refuse l'écrasement d'un GLB | Évite les chemins client et conserve un stockage atomique sans service payant | À l'import et à la fin d'une génération |

## Interface

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `frontend/` | Contient la page, les styles et les modules JavaScript du Sprint 1 | Offre une interface modulaire sans deuxième serveur ni build | Quand une personne visite / |
| `frontend/README.md` | Explique les modules, le parcours et les limites du navigateur | Rend les responsabilités et dépendances compréhensibles | Avant de lancer ou modifier le frontend |
| `frontend/index.html` | Coque commune : favicon, navigation à icônes, menu Administration (Catégories, Clés API), badge santé, déconnexion, pied de page utile et point de montage `#app` | Sépare la navigation persistante des pages chargées au hash ; masque la navigation sur l'écran de connexion | À chaque visite du Studio |
| `frontend/css/` | Regroupe le thème et les styles de composants | Sépare les jetons visuels de la mise en page | Au chargement de la page et pour une retouche visuelle |
| `frontend/css/theme.css` | Définit la palette sombre, l'échelle d'espacement, les ombres, le focus, les animations partagées (entrée de page, rotation, squelette) et la réduction du mouvement | Centralise les jetons visuels réutilisés par tous les composants | Avant les styles des composants |
| `frontend/css/components.css` | Styles de tous les composants, en 14 sections numérotées : coque, connexion, accueil, cartes, Créer, viewer, suivi, fiche, clés API, catégories, modales et adaptations écran | Un sommaire en tête rend le fichier parcourable ; panneaux et sections aérés (24-32 px) | Au rendu et quand la fenêtre change de largeur/hauteur |
| `frontend/js/` | Regroupe l'état, l'API et les vues ES modules | Permet de suivre une responsabilité par fichier sans framework | Quand le navigateur charge le module principal |
| `frontend/js/api.js` | Centralise fetch pour génération, bibliothèque, catégories, disponibilité et clés API | Empêche les vues de disperser les appels serveur | À chaque action Studio et aux vérifications périodiques |
| `frontend/js/router.js` | Résout les routes hash (dont `#/login` et `#/accueil`), redirige vers la connexion sans session, gère `?query` et `#ancre`, conserve la page Créer, active le lien courant et focalise le titre | Gère plusieurs pages protégées sans framework et respecte le clavier et l'historique du navigateur | À l'ouverture, au clic dans le menu et lors de Précédent/Suivant |
| `frontend/js/pages/` | Contient un module par page visible dans le Studio | Isole le balisage et le montage de chaque route | Lorsqu'une route hash est ouverte |
| `frontend/js/pages/create.js` | Deux colonnes (photo et catégorie / viewer), suivi compact en dessous, conseils et détails techniques repliés | Concentre l'écran sur l'essentiel ; le stepper redondant a été retiré à l'étape 16b | Sur `#/creer` |
| `frontend/js/pages/models.js` | Affiche les modèles persistés, le formulaire d'import GLB (ouvrable par `?import=1`), les filtres avec compteurs et un état vide illustré | Réunit créations, imports et exemples copiés avec la même fiche | Sur `#/modeles` |
| `frontend/js/pages/model-detail.js` | Fiche du modèle : bascule Vue 3D / Photo / Comparer, informations, téléchargement et intégration guidée en 4 étapes (interrupteur, iframe ou widget, code à copier, aperçu réel `/embed`) et suppression confirmée du modèle (étape 23) | Rend l'intégration compréhensible par un débutant sans changer les routes existantes | Sur `#/modeles/{id}` |
| `frontend/js/pages/categories.js` | Page de gestion des catégories avec compteur de modèles enregistrés par catégorie | Montre quelles catégories sont utilisées avant une suppression | Sur `#/categories` |
| `frontend/js/pages/login.js` | Écran de connexion plein écran avec mot de passe unique | Le Studio est mono-propriétaire : pas de nom d'utilisateur | Sur `#/login` et pour toute visite non connectée |
| `frontend/js/pages/dashboard.js` | Accueil : héros, chiffres clés (modèles, clés actives, catégories), modèles récents, exemples et raccourcis | Remplace l'entrée directe sur Créer par une vue d'ensemble | Sur `#/accueil`, page par défaut |
| `frontend/js/pages/guide.js` | Guide d'intégration affiché dans le Studio : clé, envoi, suivi, activation, iframe/widget, quotas, origines et sécurité | `docs/` n'est pas servi par FastAPI ; cette page rend le guide accessible depuis l'accueil, le menu et le pied de page | Sur `#/guide` |
| `frontend/js/pages/api-keys.js` | Guide en 4 étapes, exemple curl des routes `/api/v1`, création, cartes de clés avec badge et révocation confirmée ; secret affiché une seule fois | Rend l'API compréhensible sans renvoyer la clé au navigateur après création | Sur `#/cles-api` |
| `frontend/js/pages/examples.js` | Présente les exemples avec la durée réellement mesurée à l'étape 6 et propose de les copier dans Mes modèles | Montre la qualité actuelle sans inventer de chiffres | Sur `#/exemples` |
| `frontend/widget.js` | Définit `<forma3d-viewer>` et crée une iframe vers le modèle public activé | Isole le viewer du site client et vérifie l'identifiant public avant de construire l'URL | Lorsqu'une boutique colle le code du widget |
| `examples/integration.html` | Page HTML autonome qui demande l'origine du service et un UUID public puis charge le widget | Permet de tester avec un modèle réel déjà activé sans inventer de GLB | Pour valider le snippet d'intégration en développement |
| `frontend/js/pages/viewer-markup.js` | Balisage du viewer de Créer : scène avec grille et halo, squelette de chargement, bascule photo/3D, barre d'outils et note discrète | Évite de dupliquer les commandes accessibles | Au montage du parcours de création |
| `frontend/js/state.js` | Garde en mémoire photo, statut, durée et minuteries de la session | Évite une base de données pour cet état temporaire | Pendant l'envoi et le suivi d'une demande |
| `frontend/js/main.js` | Pose l'état de connexion, démarre le routeur, relie la déconnexion et diffuse l'état de disponibilité | Garde le contrôle santé unique et indépendant des pages | Au chargement et toutes les 30 secondes |
| `frontend/js/auth.js` | Suit l'état de connexion fourni par `GET /auth/me`, appelle login/logout et renvoie vers `#/login` après un 401 | Le mot de passe n'est plus dans le navigateur ; le cookie de session est illisible en JavaScript | Au démarrage, à chaque route et à la connexion |
| `frontend/js/format.js` | Mises en forme partagées : dates relatives, tailles, durées, détection des modèles enregistrés et durées mesurées des exemples | Évite de dupliquer ces petites fonctions dans chaque page | Par les pages et la galerie |
| `frontend/favicon.svg` | Icône d'onglet du Studio (cube Forma3D) | Format SVG léger, sans dépendance | À chaque chargement de la page |
| `frontend/js/views/` | Regroupe les vues de l'interface | Isole les responsabilités visibles du studio | Quand une vue est modifiée ou réutilisée |
| `frontend/js/views/uploader.js` | Gère dépôt, validation photo, catégorie et explication visible du bouton désactivé | Évite une action bloquée sans raison compréhensible | À chaque changement de photo, catégorie, santé ou activité |
| `frontend/js/views/categories.js` | Gère le CRUD, affiche statut et compteur, confirme désactivation et suppression par fenêtre modale | Protège les actions destructives et traduit les erreurs en mots simples | Sur `#/categories` |
| `frontend/js/views/progress.js` | Traduit les états observés en cinq étapes horizontales, avec état à faire, actif, terminé ou en échec | N'invente ni pourcentage ni délai restant et conserve une annonce aria-live polie | Pendant et après une génération |
| `frontend/js/views/viewer.js` | Charge le GLB avec squelette et rotation douce, bascule Vue 3D / Photo / Comparer et ouvre la photo source agrandie | Améliore la perception du modèle et facilite la comparaison avec la source | Après une génération ou un aperçu local |
| `frontend/js/views/gallery.js` | Construit les cartes (badge d'origine, date relative, rotation au survol) et la grille filtrable avec compteurs ; `createModelCard()` est réutilisée par l'accueil | Une seule fabrique de cartes pour toutes les pages | Après le chargement de la galerie |
| `frontend/js/views/model-appearance.js` | Remplace le matériau glTF par défaut (100 % métallique) par un matériau mat et recadre la caméra quand la scène change de taille | Les GLB TripoSR n'ont ni matériau ni normales ; correction d'affichage sans modifier le fichier | Au chargement de chaque viewer et en mode Comparer |
| `frontend/js/views/confirm-dialog.js` | Fenêtre modale de confirmation accessible (`<dialog>`), renvoie une promesse ; les boutons concluent directement sans dépendre de l'événement `close` | Remplace `window.confirm()` par un dialogue aux couleurs du Studio | Avant révocation, désactivation ou suppression |
| `frontend/js/views/illustrations.js` | Illustration SVG du cube utilisée par les états vides | Un seul dessin partagé par l'accueil, Mes modèles et le viewer | Quand un état vide est affiché |

## Tests et vérification continue

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/tests/` | Contient la suite pytest du backend | Regroupe les vérifications sans appeler le fournisseur en continu | En local et sur GitHub |
| `backend/tests/test_health.py` | Vérifie `/health`, les états du fournisseur, le message hors ligne et les journaux de démarrage | Protège le contrat et l'absence d'adresse dans les réponses | À chaque suite pytest |
| `backend/tests/test_upload_validator.py` | Couvre formats, taille, signatures et erreurs | Empêche les uploads mal formés sans réseau | À chaque suite pytest |
| backend/tests/test_huggingface_provider.py | Simule view_api et client.config pour tester la découverte d'endpoints, les vrais défauts lus dans config et la validation GLB | Aucun réseau ni GPU dans les tests | À chaque suite pytest |
| backend/tests/test_generation_service.py | Vérifie les transitions d'état et le masquage du jeton et de l'URL dans les logs d'erreur | Protège le diagnostic des secrets locaux | À chaque suite pytest |
| `backend/tests/test_generation_repository.py` | Vérifie schéma, catégories initiales, connexions indépendantes, persistance après redémarrage et récupération des tâches interrompues | Utilise la base PostgreSQL de test et un fournisseur simulé, sans réseau | À chaque suite pytest |
| `backend/tests/test_repository_factory.py` | Vérifie le choix du moteur selon `DATABASE_URL`, le refus d'une URL inconnue et le masquage du mot de passe | Tests sans base ni réseau | À chaque suite pytest |
| `backend/tests/test_postgres_repository.py` | Vérifie le dépôt PostgreSQL : cycle de vie, catégories, clés API, quotas et un test de concurrence sur la limite de débit | Prouve l'atomicité du verrou `FOR UPDATE` | À chaque suite pytest |
| `backend/tests/pg_support.py` | Outils des tests : URL de la base de test (refus si son nom ne contient pas « test »), remise à zéro par `TRUNCATE`, requêtes d'inspection | Un seul endroit pour accéder à la base de test, comme DBeaver | Importé par `conftest.py` et les tests |
| `backend/tests/test_category_repository.py` | Vérifie le CRUD en base PostgreSQL, les conflits et les catégories utilisées | Protège les contraintes relationnelles | À chaque suite pytest |
| `backend/tests/test_category_service.py` | Vérifie validation, normalisation et renommage des catégories | Teste les règles métier sans HTTP | À chaque suite pytest |
| `backend/tests/test_categories_api.py` | Vérifie les routes CRUD, les conflits, l'inactivation et le refus d'upload | Stabilise l'API sans réseau | À chaque suite pytest |
| `backend/tests/test_image_preparer.py` | Vérifie carré, agrandissement, avertissements flou/petite image et erreurs de décodage | Utilise des images déterministes générées localement | À chaque suite pytest |
| `backend/tests/test_local_storage.py` | Contrôle écritures atomiques, noms et garde-fous de chemin | Protège le stockage local contre un chemin client | À chaque suite pytest |
| `backend/tests/test_model_deletion.py` | Vérifie la suppression définitive d'un modèle (ligne en base, GLB, photo source), la fin de l'accès public et les refus (inconnu, exemple, création en cours, identifiant non UUID) | Prouve qu'aucun fichier ni ligne ne reste, avec la base PostgreSQL de test et un stockage temporaire | À chaque suite pytest |
| `backend/tests/test_model_rename.py` | Vérifie le renommage (`PATCH /models/{id}/name`) et le changement de catégorie (`PATCH /models/{id}/category`) d'un modèle : nom visible dans la galerie, extension conservée, persistance en base et refus (nom vide, trop long, `/` ou `\`, catégorie inconnue ou désactivée, modèle inconnu) | Prouve que seul le nom affiché change, avec la base PostgreSQL de test et un stockage temporaire | À chaque suite pytest |
| `backend/tests/test_models_api.py` | Vérifie les réponses d'upload, de suivi, les erreurs et le refus de téléchargement prématuré | Stabilise le contrat HTTP sans appeler le fournisseur | À chaque suite pytest |
| `backend/tests/test_frontend.py` | Vérifie les ressources, catégories dynamiques, santé, blocage hors ligne, import, layout et contrat du widget | Protège les contrats statiques sans navigateur | À chaque suite pytest |
| `backend/tests/test_embed.py` | Vérifie l'activation, les erreurs 404, la vue du modèle, les en-têtes CSP et les limites de contenu | Utilise la base PostgreSQL de test et un stockage temporaire sans navigateur ni fournisseur | À chaque suite pytest |
| `backend/tests/test_demo_gallery.py` | Vérifie les modèles autorisés et les photos source facultatives sans réseau | Protège la galerie et sa comparaison photo/GLB | À chaque suite pytest |
| `backend/tests/test_model_library.py` | Vérifie l'import GLB, limites, catégories, copie d'exemple et migration de modèle | Couvre les cas de bibliothèque avec la base PostgreSQL de test et sans fournisseur | À chaque suite pytest |
| `backend/tests/test_glb_finisher.py` | Vérifie la finition d'un GLB brut, les cas laissés intacts et le branchement dans GenerationService | Prouve que la géométrie n'est pas modifiée | À chaque suite pytest |
| `backend/tests/test_trial_tools.py` | Teste les mesures automatiques et les aides des outils d'essai (chemins de sortie Gradio, contrat incomplet) | Les chiffres de la grille doivent être fiables | À chaque suite pytest |
| `backend/tests/test_trellis_provider.py` | Teste l'enchaînement TRELLIS, le contrat, le quota, le jeton masqué, la configuration et la santé | Prouve l'adaptateur sans réseau | À chaque suite pytest |
| `backend/tests/conftest.py` | Ouvre la session propriétaire par surcharge de `require_owner`, sauf pour les tests marqués `real_auth` | Garde les tests métier existants centrés sur leur logique | À chaque suite pytest |
| `backend/tests/test_auth.py` | Vérifie 401 sans cookie, connexion réussie/refusée, mot de passe absent, limite de tentatives, jeton falsifié ou expiré et routes publiques ouvertes | Prouve la protection sans navigateur ni réseau externe | À chaque suite pytest |
| `backend/tests/test_api_keys.py` | Vérifie empreinte seule, révélation unique, révocation, comparaison et compteurs par clé | Couvre le contrôle d’accès et les quotas sans réseau externe | À chaque suite pytest |
| `backend/tests/test_api_settings.py` | Vérifie les valeurs par défaut, la lecture des variables et le refus du joker CORS | Évite un CORS ou des limites ouverts par erreur | À chaque suite pytest |
| `backend/tests/test_api_v1.py` | Vérifie l’API versionnée, création simulée, suivi, GLB, codes iframe/widget, erreurs, quota, débit et CORS | Appelle TestClient en local et n’utilise pas le vrai fournisseur | À chaque suite pytest |
| `.github/workflows/ci.yml` | Vérifie les documents puis installe les dépendances et exécute pytest | Donne un contrôle répétable sur GitHub | À chaque push ou pull request |

## Documentation et historique

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `docs/` | Regroupe l'état, la structure et les guides | Sépare les explications du code exécutable | Tout au long du projet |
| `docs/etapes/` | Contient un guide par étape de chaque sprint | Permet de comprendre l'évolution sans mélanger les étapes | Pour apprendre et préparer la soutenance |
| `docs/ETAT.md` | Résume les sprints, les étapes prouvées et les points encore ouverts | Distingue les preuves passées du travail non réalisé | Au début et à la fin d'une session |
| `docs/STRUCTURE.md` | Explique chaque élément du dépôt | Aide l'étudiante à défendre les choix | À chaque ajout ou changement de structure |
| `docs/STOCKAGE.md` | Explique la persistance (historique SQLite, remplacé par PostgreSQL le 16/11/2026), migration d'origine, imports et copie de modèles | Rend les choix de persistance et la provenance présentables à la soutenance | À chaque évolution de la bibliothèque |
| `docs/ALTERNATIVES-3D.md` | Compare les fournisseurs image-vers-3D gratuits et propose une migration vers TRELLIS en 3 étapes | Prépare une décision du Sprint 6 sans changer le fournisseur actuel | Avant toute discussion sur la qualité des modèles |
| `docs/etapes/etape-01.md` | Explique FastAPI et GET `/health` | Garde une trace pédagogique du premier socle | Pour réviser l'étape 1 |
| `docs/etapes/etape-02.md` | Explique le validateur et le contrat d'upload historique | Documente l'évolution de POST `/models` au fil du sprint | Pour réviser l'étape 2 |
| `docs/etapes/etape-03.md` | Décrit l'API Hugging Face inspectée, les photos, la licence et les erreurs observées | Distingue l'implémentation de sa faisabilité non démontrée | Pour revoir le fournisseur ou expliquer l'essai au jury |
| `docs/etapes/etape-04.md` | Explique statuts, service, stockage et routes | Rend le cycle de génération explicable fichier par fichier | Pour réviser l'étape 4 |
| `docs/etapes/etape-05.md` | Explique les modules, le suivi réel, le viewer, la galerie et les limites de test | Relie l'interface et ses ressources aux routes backend | Pour présenter ou modifier l'étape 5 |
| docs/etapes/etape-06.md | Consigne le contrat observé, les cinq appels, les temps, les tailles et les limites de visualisation | Fournit une trace exacte et pédagogique pour reproduire la soutenance | Pour analyser les résultats et attribuer les notes visuelles |
| docs/etapes/etape-06-colab.md | Explique l'essai historique, l'échec actuel d'attribution et la restriction de Colab sur les services web | Ne confond pas le succès d'octobre avec une disponibilité actuelle | Pour comprendre pourquoi le serveur est suspendu |
| docs/etapes/etape-07.md | Explique le contrôle de santé, les réglages qualité, les essais vides et les limites des fournisseurs | Garde les notes visuelles et résultats à compléter par l'étudiante | Pour réviser l'étape et planifier une preuve autorisée |
| `docs/etapes/etape-08.md` | Décrit le dépôt SQLite, les catégories initiales, le redémarrage et la galerie | Documente un seul incrément du Sprint 2 et ses tests | Pour expliquer ou vérifier l'étape 8 |
| `docs/etapes/etape-09.md` | Explique le CRUD catégories backend/frontend, les règles de suppression et les tests | Permet de justifier le cycle de vie et la source SQLite | Pour réviser l'étape 9 |
| `docs/etapes/etape-10.md` | Explique Pillow, le cadrage, les avertissements, la conservation de la source et les limites | Rend la préparation d'image défendable sans boîte noire lourde | Pour réviser l'étape 10 |
| `docs/etapes/etape-11.md` | Documente les routes, le schéma, le focus, le menu et les vérifications manuelles | Explique la navigation frontend comme amélioration du Studio avant le Sprint 5 | Pour présenter ou faire évoluer le Studio à pages |
| `docs/etapes/etape-11b.md` | Explique le schéma horizontal Créer, le stepper, le suivi et les limites de vérification visuelle | Documente le layout sans toucher au backend, avant le Sprint 5 | Pour expliquer ou vérifier la page Créer |
| `docs/etapes/etape-12.md` | Explique l'import, la validation GLB, la copie d'exemples, l'origine et les tests | Documente l'ajout à la bibliothèque avant le démarrage du Sprint 5 | Pour réviser l'étape 12 |
| `docs/etapes/etape-13.md` | Explique l'UUID public, l'activation explicite d'un modèle et les routes publiques | Documente les limites de visibilité et la migration SQLite du Sprint 5a | Pour comprendre ou vérifier l'intégration d'un modèle |
| `docs/etapes/etape-14.md` | Explique les clés API, leur empreinte, leur révocation, l’écran Studio et le contrôle `X-API-Key` | Distingue le secret affiché une fois des métadonnées conservées | Pour administrer ou expliquer la sécurité du Sprint 5b |
| `docs/etapes/etape-15.md` | Explique les routes `/api/v1`, erreurs, quota, débit et CORS fermé par défaut | Documente le premier contrat intégrateur et ses limites prouvées | Pour intégrer ou déboguer l’API externe |
| `docs/etapes/etape-16.md` | Explique la route viewer intégrable, les extraits iframe/widget, la CSP et les limites non vérifiées | Sépare le site marchand du Studio et fixe ce qui est réellement testé | Pour intégrer un modèle activé ou préparer l'étape 5e |
| `docs/etapes/etape-16b.md` | Explique la refonte visuelle du Studio (connexion, accueil, guides, cartes), les tests modifiés et les limites | Justifie les choix d'interface pour la soutenance | Pour présenter ou reprendre l'interface |
| `docs/etapes/.gitkeep` | Marqueur ancien du dossier de guides | Conservé sans rôle d'exécution | Au clonage du dépôt |
| `docs/archive/` et `docs/archive/v1/` | Isolent les documents remplacés | Préservent l'historique tout en gardant les instructions v2 à la racine | Pour consulter l'ancienne vision |
| `docs/archive/v1/etapes/` | Contient les guides des étapes v1 archivés | Évite de les confondre avec le Sprint 1 v2 | Consultation historique |
| `docs/archive/v1/AGENTS-ancien.md` | Ancienne instruction permanente v1 | Préserve l'historique sans remplacer la v2 | Consultation de l'ancien cadrage |
| `docs/archive/v1/PROMPT-1-v1.md` | Ancien prompt de session v1 | Préserve le texte remplacé | Consultation historique |
| `docs/archive/v1/etapes/etape-01-v1.md` | Guide v1 de l'étape 1 | Conserve la documentation remplacée | Consultation historique |
| `docs/archive/v1/etapes/etape-02-v1.md` | Guide v1 de l'étape 2 | Conserve la documentation remplacée | Consultation historique |

## Données locales ignorées par Git (certaines destinations sont créées au runtime)

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/.venv/` | Environnement Python local et ses paquets | Évite les dépendances globales ; ne se partage pas dans Git | Au lancement et aux tests locaux |
| backend/.env | Configuration locale, dont la cible d'un serveur Gradio autorisé | Fichier ignoré par Git ; ne jamais copier son contenu dans un document, un journal ou un commit | Pour configurer un fournisseur disponible |
| `backend/data/` | Stocke les données locales de faisabilité (GLB de démonstration) ; l'ancienne base SQLite locale éventuelle n'est plus lue | Garde les médias et la base hors de Git | Pendant les essais et l'exécution locale |
| `backend/data/feasibility-inputs/` | Photos libres choisies pour les essais ; trois autres photos écartées ne doivent pas être envoyées car elles montrent des personnes | Garde une provenance et protège les personnes visibles | Pendant les essais réels |
| backend/data/feasibility-results/ | Contient les cinq GLB du catalogue d'exemples, validés GLB 2.0 : deux TripoSR (étape 6) et, depuis le 11/11/2026, trois TRELLIS finis (chaise cintrée, tabouret, table d'appoint) | Les sorties ne sont pas versionnées ; aucune n'est simulée ; le fournisseur est affiché sur chaque fiche | Pour examiner les résultats ou les ouvrir dans un viewer |
| backend/data/feasibility-results-triposr/ | Sauvegarde des trois GLB TripoSR remplacés par TRELLIS | Garde la preuve de l'étape 6 ; non versionnée | Pour revenir aux versions TripoSR |
| backend/data/trials/ | GLB bruts des essais de fournisseurs (sous-étape C) | Résultats d'essais, non versionnés | Pour comparer les fournisseurs |
| `backend/storage/` | Dossier de runtime pour les photos et modèles des demandes | Conserve les uploads en dehors des sources | Créé automatiquement au premier upload |
| `backend/storage/images/` | Photos reçues à l'exécution | Conserve les entrées hors du dépôt | Après un vrai upload |
| `backend/storage/models/` | GLB générés, importés ou copiés depuis les exemples | Conserve chaque modèle local sous un UUID et hors du dépôt | Après une génération, un import ou une copie |
| `extension-debug.log` | Journal auxiliaire local de l'environnement de développement | N'est pas une entrée de l'application et est exclu de Git | Seulement si l'outil local le recrée |
| `__pycache__/`, `.pytest_cache/` | Bytecode et cache de collecte | Ces fichiers se régénèrent automatiquement | Après imports et tests |

Le registre des métadonnées, les empreintes de clés, les quotas journaliers et les événements de débit API sont persistés dans PostgreSQL (service `db` de Docker Compose, volume `pgdata`) ; les photos sources et GLB restent dans `backend/storage/`. Le dépôt d'étape 12 conserve l'origine `generated`, `imported` ou `example` ; les imports/copies ne possèdent pas de photo source et ne reçoivent pas de durée de génération. L'étape 11b change uniquement le frontend. Le Sprint 2 reste terminé ; les Sprints 3 et 4 sont retirés ; le Sprint 5 est actif depuis le 10 novembre 2026, avec 5a à 5c terminés ; le Sprint 6 attend un OK explicite.

## Ajouts de la dernière étape du Sprint 5 (travail local non encore validé)

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `docs/INTEGRATION.md` | Guide la création d'une clé et les requêtes d'intégration, les erreurs, quotas, CORS et CSP | Donne à une personne externe un parcours basé sur les routes réellement existantes | Lors du branchement d'une boutique |
| `docs/COMPRENDRE-FORMA3D.md` | Guide pédagogique complet du projet : architecture, base, fournisseurs, pages, sécurité, tests, dépannage du serveur 3D, Git, passage au SaaS, glossaire, avec exemples concrets et analogies | Permet d'expliquer tout le site à la professeure et au jury | Pour réviser la soutenance |
| `docs/ARCHITECTURE-CIBLE.md` | Architecture cible SaaS multi-clients (rôles, `owner_id`, options Supabase/PostgreSQL/statu quo, schéma, goulot GPU, RGPD, plan) — rien n'est codé | Option C choisie : le produit reste mono-propriétaire, la suite est conçue et documentée | Pour préparer la soutenance ou une suite du projet |
| `examples/integration.html` | Page de démonstration pour saisir une origine serveur et un UUID public puis charger le widget | Montre le composant avec un modèle réel activé, sans intégrer de faux GLB ni clé | Pour un test local d'intégration |
| `docs/QUALITE-3D.md` | Grille de qualité 3D, contrats observés, résultats d'essais et licences | Juge les fournisseurs sur des critères écrits avant les essais | Avant tout changement de fournisseur |
| `docs/etapes/etape-22.md` | Sous-étape C3 : branchement de TRELLIS, activation, sécurité et vérification réelle | Explique comment changer de fournisseur sans casser TripoSR | Pour activer ou présenter TRELLIS |
| `docs/etapes/etape-23.md` | Étape 23 : suppression confirmée d'un modèle (route, service, stockage, bouton de la fiche) | Explique pourquoi la suppression est définitive, protégée et refusée pendant la création | Pour présenter ou tester la suppression |
| `docs/etapes/etape-24.md` | Étape 24 : clé de session fixe facultative (`FORMA3D_SESSION_SECRET`) pour rester connectée après un redémarrage | Explique le cookie signé, le compromis sécurité/confort et l'activation | Pour configurer ou présenter la session du Studio |
| `docs/etapes/etape-25.md` | Étape 25 : bouton « Renommer » sur la fiche d'un modèle et route `PATCH /models/{id}/name` | Explique pourquoi on modifie la colonne `filename` sans migration, les validations et le test | Pour présenter ou vérifier le renommage |
| `docs/etapes/etape-26.md` | Étape 26 : changer la catégorie d'un modèle depuis sa fiche (`PATCH /models/{id}/category`) et avertissement de `dev.ps1` quand un ancien serveur est réutilisé | Explique la cause du « Not Found » observé, le formulaire « Modifier » et les tests | Pour présenter ou vérifier la modification d'un modèle |
| `docs/etapes/etape-21.md` | Sous-étape C : grille, essais TRELLIS, échecs et blocage par quota | Trace honnêtement ce qui a été tenté | Pour reprendre les essais |
| `docs/etapes/etape-20.md` | Sous-étape B : finition serveur des GLB, mesures sur 5 fichiers réels et limites | Explique pourquoi corriger le fichier en plus de l'affichage | Pour présenter la qualité des fichiers livrés |
| `docs/etapes/etape-19.md` | Sous-étape A : diagnostic mesuré des GLB, correction du matériau par défaut et du cadrage, preuve et limites | Sépare clairement rendu et géométrie pour la soutenance | Pour expliquer la qualité visuelle |
| `docs/etapes/etape-18.md` | Explique la connexion serveur (5f) : routes, cookie, jeton, limite, routes publiques et limites de sécurité | Justifie le remplacement du verrou navigateur pour la soutenance | Pour configurer ou présenter la connexion |
| `docs/etapes/etape-17.md` | Explique le guide, la page `#/guide`, l'exemple HTML et les vérifications réellement faites | Clôture le Sprint 5e avec une preuve honnête | Pour présenter l'intégration à la soutenance |
| `docs/devops/CAHIER-DEVOPS.md` | Cahier des charges du projet DevOps : état de départ, phases P0 à P9, bonus, barème et pièges du dépôt | Traduit les ateliers 1 à 5 et le guide de projet en plan concret pour Forma3D | Avant et pendant chaque phase DevOps |
| `docs/devops/PROMPT-LANCEMENT.md` | Prompt à donner à Claude pour démarrer le projet DevOps, avec messages de relance | Garantit un démarrage cadré, phase par phase, sans secret | Au lancement de la session de travail DevOps |
| `docs/devops/README.md` | Sommaire du projet DevOps : phases, branches, état et décisions D1 à D4 | Donne au jury et à l'étudiante une vue d'ensemble traçable | Au début de chaque phase DevOps et en soutenance |
| `docs/devops/phase-00.md` | Compte rendu de P0 : diagnostic d'entrée, contrôle de secrets, décisions | Prouve qu'on est parti d'un état observé et sans secret | Pour la preuve du point 1 et en soutenance |
| `docs/devops/phase-03a.md` | Compte rendu de P3a : dépôt PostgreSQL, différences avec SQLite, tests, DBeaver | Justifie la migration vers une vraie base pour le jury | Pour le point 4 et en soutenance |
| `docs/devops/phase-01.md` | Compte rendu de P1 : script de contrôle, codes de sortie, piège CRLF | Justifie le point 2 du barème | Pour la preuve du point 2 et en soutenance |
| `docs/devops/phase-02.md` | Compte rendu de P2 : Dockerfile expliqué, vérifications, incident `Exited (3)` | Justifie le point 3 du barème | Pour la preuve du point 3 et en soutenance |
| `docs/devops/phase-03b.md` | Compte rendu de P3b : Compose expliqué, persistance, DBeaver, incident `localhost` | Justifie le point 4 du barème | Pour la preuve du point 4 et en soutenance |
| `docs/devops/phase-03c.md` | Compte rendu de la suppression de SQLite : PostgreSQL seule base, tests, dev.ps1, CI | Trace et justifie la décision D5 | Pour le point 4 et en soutenance |
| `docs/devops/phase-03d.md` | Compte rendu de la migration des données, du test complet de l'application et de la visualisation (DBeaver, Adminer, psql) | Prouve que les données existantes ont survécu au changement de base | Pour le point 4 et en soutenance |
| `docs/devops/phase-04.md` | Compte rendu de P4 : workflow CI expliqué, PR rouge de démonstration | Justifie le point 5 du barème | Pour la preuve du point 5 et en soutenance |
| `docs/devops/phase-05.md` | Compte rendu de P5 : release, immuabilité des tags, procédure de livraison | Justifie le point 6 (partie publication) | Avant de taguer une version et en soutenance |
| `docs/devops/phase-06.md` | Compte rendu de P6 : staging, santé, répétition hors ligne | Justifie le point 6 (partie mise en service) | Avant un déploiement et en soutenance |
| `docs/devops/phase-07.md` | Compte rendu de P7 : panne v1.1.0 (port 8000), retour arrière, v1.1.1, prévention | Justifie le point 7 du barème | Pour la preuve du point 7 et en soutenance |
| `docs/devops/INCIDENT-v1.1.0.md` | Compte rendu d'incident en cinq lignes (quoi, quand, action, durée, prévention) | Format exigé par le cahier ; lu en soutenance | Après l'incident et en soutenance |
| `docs/devops/FICHE-PROJET.md` | Fiche d'une page : architecture, briques, version en service, déroulé du rollback | Résumé à montrer en premier au jury | En soutenance (minute 1) |
| `docs/devops/PREUVES.md` | Tableau des preuves par point du barème : observées ✅ ou à produire ⏳ | Sépare honnêtement le vérifié de ce qui reste à faire | Pendant la préparation du rendu |
| `docs/devops/QUIZ.md` | Questions probables des ateliers 1 à 5 et réponses appuyées sur le projet | Révision orale | Avant la soutenance |
| `docs/devops/SOUTENANCE.md` | Scénario minuté de 10 minutes, préparation, commandes de secours (P9) | Démonstration répétée et sans dépendance réseau | La veille et le jour de la soutenance |
| `docs/devops/PLAN-LECTURE.md` | Ordre de lecture du projet DevOps sur 5 jours, avec fichiers à ouvrir et exercices | Permet à l'étudiante de tout comprendre et justifier seule | Avant de préparer la soutenance |
| `docs/devops/GUIDE-BAREME.md` | Relie chaque exigence du guide étudiant (7 points, bonus, livrables, soutenance) à son explication, sa commande de vérification et le résultat attendu | Savoir en un coup d'œil ce qui est fait, comment le prouver et quoi faire si quelque chose manque | Avant le rendu et pour préparer la soutenance |
