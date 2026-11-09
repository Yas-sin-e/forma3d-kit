# Structure expliquée — Forma3D Studio

Mis à jour le 9 novembre 2026. L'étape 6 a produit cinq GLB 2.0 réels via le backend Forma3D et TripoSR. L'étape 7 ajoute le contrôle de disponibilité, les catégories obligatoires pour les nouvelles photos, les réglages qualité et les photos source. L'interface du studio est compacte, son viewer est limité en hauteur et la galerie défile en bande de vignettes. L'étape 8 persiste l'historique dans SQLite, sous `backend/data/forma3d.sqlite3`, derrière une interface de dépôt.

## Racine et documents de cadrage

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `AGENTS.md` | Instructions de travail, vision et périmètre du sprint | Garde les règles partagées entre les sessions | Avant toute intervention |
| `PRODUCT.md` | Vision, utilisateurs, parcours et limites du SaaS | Évite d'ajouter au sprint une fonction hors sujet | Pendant le cadrage et la soutenance |
| `DESIGN.md` | Source de vérité des couleurs, du texte, des composants et du mouvement | Maintient la cohérence visuelle | Avant de créer ou modifier l'interface |
| `README.md` | Démarrage du dépôt, état et commandes Windows | Point d'entrée pour l'étudiante et le jury | Au clonage et au lancement |
| `PROMPT-1.md` | Prompt local de démarrage de session v2 | Rappelle les règles au travail quotidien | Au début d'une session Codex ; ignoré par Git |
| `.gitignore` | Exclut secrets, environnements, caches, uploads et sorties générées | Évite de versionner les données locales ou sensibles | Avant chaque commit |
| `.env.example` | Variables fournisseur et réglages TripoSR facultatifs, sans cible ni secret | Rend la configuration explicite sans inventer de valeurs de plage ni exposer de lien | Avant un essai autorisé du fournisseur |
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
| `backend/requirements.txt` | Déclare FastAPI, Uvicorn, HTTPX2, pytest, multipart, Gradio Client et python-dotenv | Recrée les dépendances dans le venv | À l'installation et en CI |
| `backend/app/__init__.py` | Marque `app` comme paquet Python | Rend les imports déterministes | Au démarrage et pendant les tests |
| `backend/app/main.py` | Construit FastAPI, choisit le chemin SQLite fixe, initialise le dépôt et journalise `.env`/HF_SPACE_ID absents sans exposer la cible | Configure l'adaptateur une fois tout en gardant les variables fournisseur inchangées | À l'import et au démarrage d'Uvicorn |
| backend/.env | Configuration locale, dont la cible d'un serveur Gradio autorisé | Fichier ignoré par Git ; ne jamais copier son contenu dans un document, un journal ou un commit | Pour configurer un fournisseur disponible |
| `backend/app/models.py` | Définit les états, la fiche de génération et sa durée mesurée | Sépare les données métier du format de stockage | Pendant le suivi et la relecture d'une génération |
| `backend/app/repositories/` | Regroupe le contrat de dépôt et les adaptateurs de persistance | Isole SQL des règles métier | Quand le service lit ou écrit l'historique |
| `backend/app/repositories/__init__.py` | Marque le paquet Python des dépôts | Rend leur rôle d'accès aux données explicite | À l'import du service ou de l'adaptateur |
| `backend/app/repositories/base.py` | Définit `GenerationRepository` sans imposer SQLite au service | Permet de tester ou remplacer l'adaptateur indépendamment | Dans `GenerationService` et ses tests |
| `backend/app/repositories/sqlite_repository.py` | Crée les tables et gère catégories, générations, connexions courtes et récupération après redémarrage | Utilise `sqlite3` standard et une connexion par opération | Au démarrage, à chaque transition et à la lecture de la galerie |
| `backend/app/config.py` | Charge la cible, les délais et les réglages TripoSR facultatifs sans valeur par défaut de cible | Le projet peut démarrer et signaler proprement un fournisseur non configuré | À la création du fournisseur et au démarrage |
| `backend/app/providers/huggingface.py` | Sonde la cible sous 5 secondes, découvre les appels et bornes de TripoSR et valide le GLB 2.0 | Évite les noms/plages inventés et n'affiche pas d'adresse dans l'état de santé | Au badge de santé et à chaque génération |
| `backend/app/schemas.py` | Fixe les réponses JSON, dont la catégorie choisie et la photo source facultative | Stabilise les réponses et empêche les catégories hors MVP | Sur les routes /models |
| `backend/app/routers/__init__.py` | Marque le paquet des routes | Clarifie l'organisation Python | À l'import des routes |
| `backend/app/routers/models.py` | Reçoit la photo et sa catégorie, expose les états, puis sert les GLB et photos source par identifiant | Sépare HTTP du métier et place chaque génération réussie dans le bon filtre de galerie | À l'envoi, au suivi et à la consultation de la galerie |
| `backend/app/services/__init__.py` | Marque le paquet métier | Clarifie les imports de services | À l'import du validateur et du service |
| `backend/app/services/upload_validator.py` | Contrôle extension, MIME, signature et plafond de 10 Mo | Le nom ou le type annoncé seul ne suffit pas | Avant d'enregistrer une photo |
| `backend/app/services/demo_gallery.py` | Liste seulement cinq GLB autorisés, valide leur structure 2.0 et ajoute la photo source seulement si elle existe | N'expose aucun chemin fourni par le client et exclut les fichiers absents ou invalides | À l'ouverture de la galerie ou d'un modèle d'essai |
| `backend/app/services/generation_service.py` | Orchestre les états, le fournisseur, le stockage des fichiers et le dépôt de métadonnées | Garde les règles métier indépendantes de SQLite | Après un upload, pendant le traitement et à la lecture de l'historique |
| `backend/app/providers/__init__.py` | Marque le paquet d'adaptateurs | Isole les fournisseurs externes | À l'import fournisseur |
| `backend/app/providers/base.py` | Définit `Image3DProvider.generate(Path) -> bytes` et l'erreur commune | Permet de remplacer Hugging Face sans réécrire le service | Dans GenerationService et les adaptateurs |
| backend/app/providers/huggingface.py | Découvre le contrat avec view_api, lit les valeurs courantes de client.config, exécute les étapes TripoSR et valide GLB 2.0 | Évite d'interpréter les exemples comme des valeurs par défaut et prend la vraie sortie GLB | À chaque génération distante |
| `backend/app/storage/__init__.py` | Marque le paquet des adaptateurs de stockage | Sépare les fichiers de persistance du métier | À l'import du stockage |
| `backend/app/storage/base.py` | Définit le contrat `Storage` pour photos et GLB | Permet de changer la persistance derrière une interface | Dans GenerationService et ses tests |
| `backend/app/storage/local_storage.py` | Écrit de façon atomique avec des noms UUID créés par le serveur | Démarre sans service payant et évite les chemins du client | À l'acceptation et à la fin d'une génération |
| `backend/data/forma3d.sqlite3` | Contient les métadonnées locales des catégories et générations | Base fixe, sans configuration ni dépendance serveur ; ignorée par Git | Créée et ouverte au démarrage et lors des opérations du dépôt |

## Interface

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `frontend/` | Contient la page, les styles et les modules JavaScript du Sprint 1 | Offre une interface modulaire sans deuxième serveur ni build | Quand une personne visite / |
| `frontend/README.md` | Explique les modules, le parcours et les limites du navigateur | Rend les responsabilités et dépendances compréhensibles | Avant de lancer ou modifier le frontend |
| `frontend/index.html` | Définit le studio compact, les conseils repliables, la photo agrandissable, le viewer, le suivi et la galerie | Garde l'interface accessible tout en donnant la priorité à la scène 3D | Quand FastAPI sert la page d'accueil |
| `frontend/css/` | Regroupe le thème et les styles de composants | Sépare les jetons visuels de la mise en page | Au chargement de la page et pour une retouche visuelle |
| `frontend/css/theme.css` | Définit la palette sombre, les fontes, le focus et la réduction du mouvement | Centralise les règles globales et lisibles | Avant les styles des composants |
| `frontend/css/components.css` | Met en page le panneau d'entrée étroit, le viewer limité à 70 vh, sa miniature source, sa barre flottante et la bande de vignettes | Conserve les couleurs DESIGN.md, le focus clavier et le fonctionnement à partir de 360 px | Lors du rendu du studio et aux changements de largeur |
| `frontend/js/` | Regroupe l'état, l'API et les vues ES modules | Permet de suivre une responsabilité par fichier sans framework | Quand le navigateur charge le module principal |
| `frontend/js/api.js` | Centralise fetch pour génération (photo et catégorie), galerie et santé du fournisseur | Empêche les vues de disperser les appels serveur | À chaque action et toutes les 30 secondes pour la disponibilité |
| `frontend/js/state.js` | Garde en mémoire photo, statut, durée et minuteries de la session | Évite une base de données pour cet état temporaire | Pendant l'envoi et le suivi d'une demande |
| `frontend/js/main.js` | Coordonne formulaire, suivi, galerie et viewer ; rafraîchit le filtre après une génération réussie | Montre le résultat dans sa catégorie sans logique HTTP dans les vues | À l'ouverture et aux changements d'état |
| `frontend/js/views/` | Regroupe les vues de l'interface | Isole les responsabilités visibles du studio | Quand une vue est modifiée ou réutilisée |
| `frontend/js/views/uploader.js` | Gère dépôt, validation photo et choix obligatoire parmi les trois catégories | Évite les générations sans type d'objet clair ou avec fournisseur hors ligne | Avant toute soumission |
| `frontend/js/views/progress.js` | Traduit les états observés et le temps réel en étape accessible | N'invente ni pourcentage ni délai restant | Pendant et après une génération |
| `frontend/js/views/viewer.js` | Charge le GLB, applique l'éclairage PBR documenté et ouvre la photo source dans une boîte de dialogue accessible | Améliore le rendu et permet de comparer la source sans rétrécir la scène | Après une génération ou une sélection de galerie |
| `frontend/js/views/gallery.js` | Crée la bande de vignettes 3D filtrable et permet l'ouverture au clic ou au clavier | Garde les étiquettes réelles et rend chaque résultat directement sélectionnable | Après le chargement de galerie et une génération terminée |

## Tests et vérification continue

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/tests/` | Contient la suite pytest du backend | Regroupe les vérifications sans appeler le fournisseur en continu | En local et sur GitHub |
| `backend/tests/test_health.py` | Vérifie `/health`, les états du fournisseur, le message hors ligne et les journaux de démarrage | Protège le contrat et l'absence d'adresse dans les réponses | À chaque suite pytest |
| `backend/tests/test_upload_validator.py` | Couvre formats, taille, signatures et erreurs | Empêche les uploads mal formés sans réseau | À chaque suite pytest |
| backend/tests/test_huggingface_provider.py | Simule view_api et client.config pour tester la découverte d'endpoints, les vrais défauts lus dans config et la validation GLB | Aucun réseau ni GPU dans les tests | À chaque suite pytest |
| backend/tests/test_generation_service.py | Vérifie les transitions d'état et le masquage du jeton et de l'URL dans les logs d'erreur | Protège le diagnostic des secrets locaux | À chaque suite pytest |
| `backend/tests/test_generation_repository.py` | Vérifie schéma, catégories initiales, connexions indépendantes, persistance après redémarrage et récupération des tâches interrompues | Utilise un SQLite temporaire et un fournisseur simulé, sans réseau | À chaque suite pytest |
| `backend/tests/test_local_storage.py` | Contrôle écritures atomiques, noms et garde-fous de chemin | Protège le stockage local contre un chemin client | À chaque suite pytest |
| `backend/tests/test_models_api.py` | Vérifie les réponses d'upload, de suivi, les erreurs et le refus de téléchargement prématuré | Stabilise le contrat HTTP sans appeler le fournisseur | À chaque suite pytest |
| `backend/tests/test_frontend.py` | Vérifie les ressources, le polling santé, le blocage hors ligne et les conseils | Protège la structure du frontend sans navigateur | À chaque suite pytest |
| `backend/tests/test_demo_gallery.py` | Vérifie les modèles autorisés et les photos source facultatives sans réseau | Protège la galerie et sa comparaison photo/GLB | À chaque suite pytest |
| `.github/workflows/ci.yml` | Vérifie les documents puis installe les dépendances et exécute pytest | Donne un contrôle répétable sur GitHub | À chaque push ou pull request |

## Documentation et historique

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `docs/` | Regroupe l'état, la structure et les guides | Sépare les explications du code exécutable | Tout au long du projet |
| `docs/etapes/` | Contient un guide par étape de chaque sprint | Permet de comprendre l'évolution sans mélanger les étapes | Pour apprendre et préparer la soutenance |
| `docs/ETAT.md` | Résume les sprints, les étapes prouvées et les points encore ouverts | Distingue les preuves passées du travail non réalisé | Au début et à la fin d'une session |
| `docs/STRUCTURE.md` | Explique chaque élément du dépôt | Aide l'étudiante à défendre les choix | À chaque ajout ou changement de structure |
| `docs/STOCKAGE.md` | Explique le schéma SQLite, le chemin fixe, les connexions et la lecture de l'historique | Rend les choix de persistance présentables à la soutenance | À l'étape 8 et lors d'une évolution du stockage |
| `docs/etapes/etape-01.md` | Explique FastAPI et GET `/health` | Garde une trace pédagogique du premier socle | Pour réviser l'étape 1 |
| `docs/etapes/etape-02.md` | Explique le validateur et le contrat d'upload historique | Documente l'évolution de POST `/models` au fil du sprint | Pour réviser l'étape 2 |
| `docs/etapes/etape-03.md` | Décrit l'API Hugging Face inspectée, les photos, la licence et les erreurs observées | Distingue l'implémentation de sa faisabilité non démontrée | Pour revoir le fournisseur ou expliquer l'essai au jury |
| `docs/etapes/etape-04.md` | Explique statuts, service, stockage et routes | Rend le cycle de génération explicable fichier par fichier | Pour réviser l'étape 4 |
| `docs/etapes/etape-05.md` | Explique les modules, le suivi réel, le viewer, la galerie et les limites de test | Relie l'interface et ses ressources aux routes backend | Pour présenter ou modifier l'étape 5 |
| docs/etapes/etape-06.md | Consigne le contrat observé, les cinq appels, les temps, les tailles et les limites de visualisation | Fournit une trace exacte et pédagogique pour reproduire la soutenance | Pour analyser les résultats et attribuer les notes visuelles |
| docs/etapes/etape-06-colab.md | Explique l'essai historique, l'échec actuel d'attribution et la restriction de Colab sur les services web | Ne confond pas le succès d'octobre avec une disponibilité actuelle | Pour comprendre pourquoi le serveur est suspendu |
| docs/etapes/etape-07.md | Explique le contrôle de santé, les réglages qualité, les essais vides et les limites des fournisseurs | Garde les notes visuelles et résultats à compléter par l'étudiante | Pour réviser l'étape et planifier une preuve autorisée |
| `docs/etapes/etape-08.md` | Décrit le dépôt SQLite, les catégories initiales, le redémarrage et la galerie | Documente un seul incrément du Sprint 2 et ses tests | Pour expliquer ou vérifier l'étape 8 |
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
| `backend/storage/models/` | GLB reçus du fournisseur | Conserve les modèles générés hors du dépôt | Après une vraie génération réussie |
| `extension-debug.log` | Journal auxiliaire local de l'environnement de développement | N'est pas une entrée de l'application et est exclu de Git | Seulement si l'outil local le recrée |
| `__pycache__/`, `.pytest_cache/` | Bytecode et cache de collecte | Ces fichiers se régénèrent automatiquement | Après imports et tests |

Le registre des métadonnées est persisté dans `backend/data/forma3d.sqlite3` ; les photos et GLB restent dans `backend/storage/`. Les travaux PENDING/RUNNING du processus précédent deviennent FAILED au redémarrage, car une tâche de fond n'est pas reprise. Le dossier `frontend/` contient la page actuelle. Les étapes 9 et 10 restent hors de l'étape 8 : CRUD des catégories et préparation d'image.
