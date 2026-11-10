# Structure expliquée — Forma3D Studio

Mis à jour le 10 novembre 2026. Le Sprint 2 est terminé. Les étapes 11 et 11b sont des refontes UX indépendantes du Sprint 3. L'étape 12 ajoute l'import GLB et la provenance unifiée ; le Sprint 5 n'est pas démarré.

## Racine et documents de cadrage

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `AGENTS.md` | Instructions de travail, vision et périmètre du sprint | Garde les règles partagées entre les sessions | Avant toute intervention |
| `PRODUCT.md` | Vision, utilisateurs, parcours et limites du SaaS | Évite d'ajouter au sprint une fonction hors sujet | Pendant le cadrage et la soutenance |
| `DESIGN.md` | Source de vérité des couleurs, du texte, des composants et du mouvement | Maintient la cohérence visuelle | Avant de créer ou modifier l'interface |
| `README.md` | Démarrage du dépôt, état et commandes Windows | Point d'entrée pour l'étudiante et le jury | Au clonage et au lancement |
| `PROMPT-1.md` | Prompt local de démarrage de session v2 | Rappelle les règles au travail quotidien | Au début d'une session Codex ; ignoré par Git |
| `.gitignore` | Exclut secrets, environnements, caches, uploads et sorties générées | Évite de versionner les données locales ou sensibles | Avant chaque commit |
| `.env.example` | Variables fournisseur, réglages TripoSR facultatifs et plafond GLB `MAX_GLB_UPLOAD_MB` (30 par défaut) | Rend la configuration explicite sans cible ni secret | Avant le lancement ou l'import d'un modèle |
| `sprint-1-v2-saas-3d-ecommerce.docx` | Cahier des charges remis pour le sprint | Conserve la référence de départ et ses exigences | Au cadrage et à la soutenance |
| `.github/` | Configuration destinée au dépôt GitHub | Sépare l'automatisation distante des sources | Sur GitHub |
| `.github/workflows/` | Répertoire des workflows CI | Range les vérifications reproductibles | À chaque push ou pull request |
| `.agents/.ai/` et `.agents/.ai/rules/` | Emplacement local des règles d'assistance | Sépare le contexte d'agent du code livré | Pendant les sessions locales ; règles actuellement vides |
| `.agents/` | Configuration locale de l'assistant, exclue de Git | Sépare les paramètres de Codex des sources applicatives | Pendant le travail local ; pas requis à l'exécution |
| `.agents/skills/` | Emplacement local des skills | N'ajoute pas de dépendance au produit | Quand une skill locale est installée |
| `.agents/skills/.gitkeep` | Marqueur local du répertoire de skills | Rend visible l'emplacement réservé même s'il est vide | Dans le dossier de travail local |
| `.github/workflows/ci.yml` | Vérifie les documents et exécute pytest en CI | Détecte une régression avant la soutenance | Lors d'un push ou d'une pull request |
| `scripts/` | Regroupe les commandes de développement Windows | Évite de mémoriser les étapes venv/tests/serveur | Au démarrage local |
| `scripts/dev.ps1` | Crée le venv absent, installe les dépendances si nécessaire, exécute pytest, démarre Uvicorn et ouvre Edge | Donne un seul parcours reproductible au projet | Depuis PowerShell à la racine |

## Serveur temporaire TripoSR

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `tools/` | Regroupe les outils de développement hors de l'application | Le notebook serveur ne fait pas partie du backend livré | Pour lancer le fournisseur dans un environnement GPU distant |
| `tools/colab/` | Range le notebook d'apprentissage et de contrôle du runtime distant | Isole les dépendances TripoSR des sources backend | Pour vérifier le GPU et comprendre l'historique des essais |
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
| `backend/requirements.txt` | Déclare FastAPI, Uvicorn, HTTPX2, pytest, multipart, Gradio Client, python-dotenv et Pillow | Recrée les dépendances du service et de la préparation légère dans le venv | À l'installation et en CI |
| `backend/app/__init__.py` | Marque `app` comme paquet Python | Rend les imports déterministes | Au démarrage et pendant les tests |
| `backend/app/main.py` | Construit FastAPI, choisit le chemin SQLite fixe, initialise le dépôt et journalise `.env`/HF_SPACE_ID absents sans exposer la cible | Configure l'adaptateur une fois tout en gardant les variables fournisseur inchangées | À l'import et au démarrage d'Uvicorn |
| backend/.env | Configuration locale, dont la cible d'un serveur Gradio autorisé | Fichier ignoré par Git ; ne jamais copier son contenu dans un document, un journal ou un commit | Pour configurer un fournisseur disponible |
| `backend/app/models.py` | Définit les catégories, états, origines, fiche de génération et chemins facultatifs de photo | Sépare les données métier du format de stockage et distingue import, exemple et génération | Pendant la gestion, le suivi et la relecture |
| `backend/app/repositories/` | Regroupe le contrat de dépôt et les adaptateurs de persistance | Isole SQL des règles métier | Quand le service lit ou écrit l'historique |
| `backend/app/repositories/__init__.py` | Marque le paquet Python des dépôts | Rend leur rôle d'accès aux données explicite | À l'import du service ou de l'adaptateur |
| `backend/app/repositories/base.py` | Définit `GenerationRepository` sans imposer SQLite au service | Permet de tester ou remplacer l'adaptateur indépendamment | Dans `GenerationService` et ses tests |
| `backend/app/repositories/sqlite_repository.py` | Crée les tables, migre sans perte la colonne `origin` et gère connexions courtes | Utilise `sqlite3` standard et une connexion par opération | Au démarrage, à chaque transition et à la lecture de la galerie |
| `backend/app/config.py` | Charge la cible, délais, réglages TripoSR et taille maximale d'import GLB | Centralise les valeurs configurables, sans valeur de fournisseur inventée | À la création des services et au démarrage |
| `backend/app/providers/huggingface.py` | Sonde la cible sous 5 secondes, découvre les appels et bornes de TripoSR et valide le GLB 2.0 | Évite les noms/plages inventés et n'affiche pas d'adresse dans l'état de santé | Au badge de santé et à chaque génération |
| `backend/app/schemas.py` | Fixe les réponses JSON avec l'origine, l'état, la date et les liens de galerie | Stabilise les contrats HTTP sans exposer les chemins locaux | Sur les routes `/categories` et `/models` |
| `backend/app/routers/__init__.py` | Marque le paquet des routes | Clarifie l'organisation Python | À l'import des routes |
| `backend/app/routers/categories.py` | Expose lister, créer, renommer, activer/désactiver et supprimer les catégories | Garde la validation HTTP distincte des règles métier | Aux actions de gestion et au chargement des choix |
| `backend/app/routers/models.py` | Reçoit les photos, importe les GLB, copie les exemples autorisés, expose les états et réunit la galerie | Sépare HTTP du métier et valide les catégories avant l'enregistrement | À l'envoi, au suivi, à l'import et à la consultation des modèles |
| `backend/app/services/__init__.py` | Marque le paquet métier | Clarifie les imports de services | À l'import du validateur et du service |
| `backend/app/services/category_service.py` | Vérifie les catégories, les slugs et les libellés puis traduit les erreurs de persistance | Centralise les règles réutilisables par les routes et les tests | Lors du CRUD et avant chaque upload |
| `backend/app/services/upload_validator.py` | Contrôle extension, MIME, signature et plafond de 10 Mo | Le nom ou le type annoncé seul ne suffit pas | Avant d'enregistrer une photo |
| `backend/app/services/image_preparer.py` | Redresse, compose une image carrée avec marges et mesure petite taille/netteté via Pillow | Prépare une copie temporaire sans modifier l'original ni ajouter de modèle | Juste avant l'appel du fournisseur |
| `backend/app/services/demo_gallery.py` | Liste les cinq GLB autorisés, valide le GLB 2.0 en fichier ou en mémoire et résout les exemples copiables | Partage un validateur strict sans exposer de chemin arbitraire | À l'ouverture de la galerie, à l'import et à la copie d'exemple |
| `backend/app/services/generation_service.py` | Orchestre génération et enregistrement des modèles importés ou copiés, avec leur origine | Garde la validation métier indépendante de SQLite et du stockage | Après un upload photo, import GLB ou copie d'exemple |
| `backend/app/providers/__init__.py` | Marque le paquet d'adaptateurs | Isole les fournisseurs externes | À l'import fournisseur |
| `backend/app/providers/base.py` | Définit `Image3DProvider.generate(Path) -> bytes` et l'erreur commune | Permet de remplacer Hugging Face sans réécrire le service | Dans GenerationService et les adaptateurs |
| backend/app/providers/huggingface.py | Découvre le contrat avec view_api, lit les valeurs courantes de client.config, exécute les étapes TripoSR et valide GLB 2.0 | Évite d'interpréter les exemples comme des valeurs par défaut et prend la vraie sortie GLB | À chaque génération distante |
| `backend/app/storage/__init__.py` | Marque le paquet des adaptateurs de stockage | Sépare les fichiers de persistance du métier | À l'import du stockage |
| `backend/app/storage/base.py` | Définit le contrat `Storage` pour photos et GLB | Permet de changer la persistance derrière une interface | Dans GenerationService et ses tests |
| `backend/app/storage/local_storage.py` | Écrit les photos et GLB avec des noms UUID serveur et refuse l'écrasement d'un GLB | Évite les chemins client et conserve un stockage atomique sans service payant | À l'import et à la fin d'une génération |
| `backend/data/forma3d.sqlite3` | Contient les métadonnées locales des catégories et générations | Base fixe, sans configuration ni dépendance serveur ; ignorée par Git | Créée et ouverte au démarrage et lors des opérations du dépôt |

## Interface

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `frontend/` | Contient la page, les styles et les modules JavaScript du Sprint 1 | Offre une interface modulaire sans deuxième serveur ni build | Quand une personne visite / |
| `frontend/README.md` | Explique les modules, le parcours et les limites du navigateur | Rend les responsabilités et dépendances compréhensibles | Avant de lancer ou modifier le frontend |
| `frontend/index.html` | Définit la coque commune, l'en-tête, le menu responsive, le badge santé et le point de montage `#app` | Sépare la navigation persistante des pages chargées au hash | À chaque visite du Studio |
| `frontend/css/` | Regroupe le thème et les styles de composants | Sépare les jetons visuels de la mise en page | Au chargement de la page et pour une retouche visuelle |
| `frontend/css/theme.css` | Définit la palette sombre, les fontes, le focus et la réduction du mouvement | Centralise les règles globales et lisibles | Avant les styles des composants |
| `frontend/css/components.css` | Met en page le studio, dont le parcours Créer en grille stretch adaptative et le suivi horizontal mobile | Conserve la palette DESIGN.md, le focus clavier et le repli sous 1024 px | Au rendu et quand la fenêtre change de largeur/hauteur |
| `frontend/js/` | Regroupe l'état, l'API et les vues ES modules | Permet de suivre une responsabilité par fichier sans framework | Quand le navigateur charge le module principal |
| `frontend/js/api.js` | Centralise fetch pour génération, import GLB, copie d'exemple, galerie, catégories et santé | Empêche les vues de disperser les appels serveur | À chaque action et toutes les 30 secondes pour la disponibilité |
| `frontend/js/router.js` | Résout les routes hash, conserve la page Créer pendant une navigation, active le lien courant et focalise le titre | Gère plusieurs pages sans framework et respecte le clavier et l'historique du navigateur | À l'ouverture, au clic dans le menu et lors de Précédent/Suivant |
| `frontend/js/pages/` | Contient un module par page visible du vendeur | Isole le balisage et le montage de chaque route | Lorsqu'une route hash est ouverte |
| `frontend/js/pages/create.js` | Présente le parcours Photo/Création/Résultat, une carte Photo et catégorie, viewer, suivi et états hors ligne | Rend le chemin utilisateur immédiatement lisible sans modifier le traitement | Sur `#/creer` |
| `frontend/js/pages/models.js` | Affiche les modèles persistés, le formulaire d'import GLB, catégories et état vide | Réunit créations, imports et exemples copiés avec la même fiche | Sur `#/modeles` |
| `frontend/js/pages/model-detail.js` | Charge état, origine, modèle, photo source facultative, date et téléchargement | Réutilise les routes d'état existantes et distingue un import d'une génération | Sur `#/modeles/{id}` |
| `frontend/js/pages/categories.js` | Place la gestion existante dans une page séparée | Évite d'encombrer l'accueil et rend les actions de catalogue plus claires | Sur `#/categories` |
| `frontend/js/pages/examples.js` | Présente les exemples autorisés et propose de les copier dans Mes modèles avec une catégorie | Conserve les originaux dans la galerie d'exemples et crée une entrée locale séparée | Sur `#/exemples` |
| `frontend/js/pages/viewer-markup.js` | Fournit le balisage du viewer utilisé par la page Créer | Évite de dupliquer les commandes accessibles | Au montage du parcours de création |
| `frontend/js/state.js` | Garde en mémoire photo, statut, durée et minuteries de la session | Évite une base de données pour cet état temporaire | Pendant l'envoi et le suivi d'une demande |
| `frontend/js/main.js` | Démarre le routeur et diffuse l'état de disponibilité | Garde le contrôle santé unique et indépendant des pages | Au chargement et toutes les 30 secondes |
| `frontend/js/views/` | Regroupe les vues de l'interface | Isole les responsabilités visibles du studio | Quand une vue est modifiée ou réutilisée |
| `frontend/js/views/uploader.js` | Gère dépôt, validation photo, catégorie et explication visible du bouton désactivé | Évite une action bloquée sans raison compréhensible | À chaque changement de photo, catégorie, santé ou activité |
| `frontend/js/views/categories.js` | Gère le CRUD et demande confirmation avant suppression | Protège les actions destructives et traduit les erreurs en mots simples | Sur `#/categories` |
| `frontend/js/views/progress.js` | Traduit les états observés en cinq étapes horizontales, avec état à faire, actif, terminé ou en échec | N'invente ni pourcentage ni délai restant et conserve une annonce aria-live polie | Pendant et après une génération |
| `frontend/js/views/viewer.js` | Charge le GLB, applique l'éclairage PBR documenté et ouvre la photo source dans une boîte de dialogue accessible | Améliore le rendu et permet de comparer la source sans rétrécir la scène | Après une génération ou une sélection de galerie |
| `frontend/js/views/gallery.js` | Crée les cartes 3D, filtres, dates et badges d'origine issus de l'API | Rend visibles les différences entre génération, import et exemple | Après le chargement de la galerie |

## Tests et vérification continue

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/tests/` | Contient la suite pytest du backend | Regroupe les vérifications sans appeler le fournisseur en continu | En local et sur GitHub |
| `backend/tests/test_health.py` | Vérifie `/health`, les états du fournisseur, le message hors ligne et les journaux de démarrage | Protège le contrat et l'absence d'adresse dans les réponses | À chaque suite pytest |
| `backend/tests/test_upload_validator.py` | Couvre formats, taille, signatures et erreurs | Empêche les uploads mal formés sans réseau | À chaque suite pytest |
| backend/tests/test_huggingface_provider.py | Simule view_api et client.config pour tester la découverte d'endpoints, les vrais défauts lus dans config et la validation GLB | Aucun réseau ni GPU dans les tests | À chaque suite pytest |
| backend/tests/test_generation_service.py | Vérifie les transitions d'état et le masquage du jeton et de l'URL dans les logs d'erreur | Protège le diagnostic des secrets locaux | À chaque suite pytest |
| `backend/tests/test_generation_repository.py` | Vérifie schéma, catégories initiales, connexions indépendantes, persistance après redémarrage et récupération des tâches interrompues | Utilise un SQLite temporaire et un fournisseur simulé, sans réseau | À chaque suite pytest |
| `backend/tests/test_category_repository.py` | Vérifie le CRUD SQLite, les conflits et les catégories utilisées | Protège les contraintes relationnelles | À chaque suite pytest |
| `backend/tests/test_category_service.py` | Vérifie validation, normalisation et renommage des catégories | Teste les règles métier sans HTTP | À chaque suite pytest |
| `backend/tests/test_categories_api.py` | Vérifie les routes CRUD, les conflits, l'inactivation et le refus d'upload | Stabilise l'API sans réseau | À chaque suite pytest |
| `backend/tests/test_image_preparer.py` | Vérifie carré, agrandissement, avertissements flou/petite image et erreurs de décodage | Utilise des images déterministes générées localement | À chaque suite pytest |
| `backend/tests/test_local_storage.py` | Contrôle écritures atomiques, noms et garde-fous de chemin | Protège le stockage local contre un chemin client | À chaque suite pytest |
| `backend/tests/test_models_api.py` | Vérifie les réponses d'upload, de suivi, les erreurs et le refus de téléchargement prématuré | Stabilise le contrat HTTP sans appeler le fournisseur | À chaque suite pytest |
| `backend/tests/test_frontend.py` | Vérifie les ressources, catégories dynamiques, santé, blocage hors ligne, import et contrat du nouveau layout | Protège les contrats statiques sans navigateur | À chaque suite pytest |
| `backend/tests/test_demo_gallery.py` | Vérifie les modèles autorisés et les photos source facultatives sans réseau | Protège la galerie et sa comparaison photo/GLB | À chaque suite pytest |
| `backend/tests/test_model_library.py` | Vérifie l'import GLB, limites, catégories, copie d'exemple et migration de `origin` | Couvre les cas de bibliothèque avec SQLite temporaire et sans fournisseur | À chaque suite pytest |
| `.github/workflows/ci.yml` | Vérifie les documents puis installe les dépendances et exécute pytest | Donne un contrôle répétable sur GitHub | À chaque push ou pull request |

## Documentation et historique

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `docs/` | Regroupe l'état, la structure et les guides | Sépare les explications du code exécutable | Tout au long du projet |
| `docs/etapes/` | Contient un guide par étape de chaque sprint | Permet de comprendre l'évolution sans mélanger les étapes | Pour apprendre et préparer la soutenance |
| `docs/ETAT.md` | Résume les sprints, les étapes prouvées et les points encore ouverts | Distingue les preuves passées du travail non réalisé | Au début et à la fin d'une session |
| `docs/STRUCTURE.md` | Explique chaque élément du dépôt | Aide l'étudiante à défendre les choix | À chaque ajout ou changement de structure |
| `docs/STOCKAGE.md` | Explique SQLite, migration d'origine, imports et copie de modèles | Rend les choix de persistance et la provenance présentables à la soutenance | À chaque évolution de la bibliothèque |
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
| `docs/etapes/etape-11.md` | Documente les routes, le schéma, le focus, le menu et les vérifications manuelles | Explique la navigation frontend sans confondre l'étape avec le Sprint 3 | Pour présenter ou faire évoluer le Studio à pages |
| `docs/etapes/etape-11b.md` | Explique le schéma horizontal Créer, le stepper, le suivi et les limites de vérification visuelle | Documente le layout sans toucher au backend ni démarrer Sprint 5 | Pour expliquer ou vérifier la page Créer |
| `docs/etapes/etape-12.md` | Explique l'import, la validation GLB, la copie d'exemples, l'origine et les tests | Documente l'ajout à la bibliothèque sans démarrer le Sprint 5 | Pour réviser l'étape 12 |
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
| `backend/data/` | Stocke les données locales de faisabilité et l'historique SQLite | Garde les médias et la base hors de Git | Pendant les essais et l'exécution locale |
| `backend/data/forma3d.sqlite3` | Contient les catégories et métadonnées des générations | Chemin fixe ; ignoré par `backend/data/` et les motifs d'extensions SQLite | À chaque opération de persistance |
| `backend/data/feasibility-inputs/` | Photos libres choisies pour les essais ; trois autres photos écartées ne doivent pas être envoyées car elles montrent des personnes | Garde une provenance et protège les personnes visibles | Pendant les essais réels |
| backend/data/feasibility-results/ | Contient les cinq GLB réellement téléchargés par l'application et validés GLB 2.0 | Les sorties de faisabilité ne sont pas versionnées ; aucune n'est simulée | Pour examiner les résultats ou les ouvrir dans un viewer |
| `backend/storage/` | Dossier de runtime pour les photos et modèles des demandes | Conserve les uploads en dehors des sources | Créé automatiquement au premier upload |
| `backend/storage/images/` | Photos reçues à l'exécution | Conserve les entrées hors du dépôt | Après un vrai upload |
| `backend/storage/models/` | GLB générés, importés ou copiés depuis les exemples | Conserve chaque modèle local sous un UUID et hors du dépôt | Après une génération, un import ou une copie |
| `extension-debug.log` | Journal auxiliaire local de l'environnement de développement | N'est pas une entrée de l'application et est exclu de Git | Seulement si l'outil local le recrée |
| `__pycache__/`, `.pytest_cache/` | Bytecode et cache de collecte | Ces fichiers se régénèrent automatiquement | Après imports et tests |

Le registre des métadonnées est persisté dans `backend/data/forma3d.sqlite3` ; les photos sources et GLB restent dans `backend/storage/`. Le dépôt d'étape 12 conserve l'origine `generated`, `imported` ou `example` ; les imports/copies ne possèdent pas de photo source et ne reçoivent pas de durée de génération. L'étape 11b change uniquement le frontend. Le Sprint 2 reste terminé, le Sprint 3 n'est pas démarré et les étapes 11b/12 ne démarrent pas le Sprint 5.
