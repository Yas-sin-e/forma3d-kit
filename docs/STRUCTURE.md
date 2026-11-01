# Structure expliquée — Forma3D Studio

Mis à jour le 1 novembre 2026. L'étape 6 a produit cinq GLB 2.0 réels via le backend Forma3D et le serveur TripoSR dans Colab. L'interface a ensuite été séparée en modules accessibles ; les notes qualitatives des résultats restent à faire par l'étudiante.

## Racine et documents de cadrage

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `AGENTS.md` | Instructions de travail, vision et périmètre du sprint | Garde les règles partagées entre les sessions | Avant toute intervention |
| `PRODUCT.md` | Vision, utilisateurs, parcours et limites du SaaS | Évite d'ajouter au sprint une fonction hors sujet | Pendant le cadrage et la soutenance |
| `DESIGN.md` | Source de vérité des couleurs, du texte, des composants et du mouvement | Maintient la cohérence visuelle | Avant de créer ou modifier l'interface |
| `README.md` | Démarrage du dépôt, état et commandes Windows | Point d'entrée pour l'étudiante et le jury | Au clonage et au lancement |
| `PROMPT-1.md` | Prompt local de démarrage de session v2 | Rappelle les règles au travail quotidien | Au début d'une session Codex ; ignoré par Git |
| `.gitignore` | Exclut secrets, environnements, caches, uploads et sorties générées | Évite de versionner les données locales ou sensibles | Avant chaque commit |
| `.env.example` | Noms des variables de fournisseur sans secret ; HF_SPACE_ID accepte un identifiant de Space ou une URL Gradio | Rend la configuration explicite sans exposer l'URL privée ni le jeton | Avant un essai du fournisseur |
| `sprint-1-v2-saas-3d-ecommerce.docx` | Cahier des charges remis pour le sprint | Conserve la référence de départ et ses exigences | Au cadrage et à la soutenance |
| `.github/` | Configuration destinée au dépôt GitHub | Sépare l'automatisation distante des sources | Sur GitHub |
| `.github/workflows/` | Répertoire des workflows CI | Range les vérifications reproductibles | À chaque push ou pull request |
| `.agents/.ai/` et `.agents/.ai/rules/` | Emplacement local des règles d'assistance | Sépare le contexte d'agent du code livré | Pendant les sessions locales ; règles actuellement vides |
| `.agents/` | Configuration locale de l'assistant, exclue de Git | Sépare les paramètres de Codex des sources applicatives | Pendant le travail local ; pas requis à l'exécution |
| `.agents/skills/` | Emplacement local des skills | N'ajoute pas de dépendance au produit | Quand une skill locale est installée |
| `.agents/skills/.gitkeep` | Marqueur local du répertoire de skills | Rend visible l'emplacement réservé même s'il est vide | Dans le dossier de travail local |
| `.github/workflows/ci.yml` | Vérifie les documents et exécute pytest en CI | Détecte une régression avant la soutenance | Lors d'un push ou d'une pull request |

## Serveur temporaire TripoSR

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `tools/` | Regroupe les outils de développement hors de l'application | Le notebook serveur ne fait pas partie du backend livré | Pour lancer le fournisseur dans un environnement GPU distant |
| `tools/colab/` | Range le notebook destiné à Google Colab | Isole les cellules qui installent TripoSR temporairement dans le runtime distant | Quand l'étudiante prépare son serveur pour un essai |
| tools/colab/triposr_server.ipynb | Contrôle un T4, clone TripoSR, installe les dépendances et lance Gradio avec un lien temporaire | Tout s'exécute dans Colab ; le notebook a été réellement lancé, cinq générations ont réussi et les sorties sont effacées du fichier versionné | Au démarrage d'une session Colab ou d'une démonstration |

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
| `backend/app/main.py` | Construit FastAPI, sert la page, publie le frontend sous /static/, configure le service et le catalogue | Fournit un point d'entrée unique pour les ressources et les routes | Quand Uvicorn démarre ou TestClient importe l'application |
| backend/.env | Configuration locale, dont l'URL temporaire du serveur Gradio | Fichier ignoré par Git ; ne jamais copier son contenu dans un document ou un commit | Pour connecter le backend au serveur Colab actif |
| `backend/app/models.py` | Définit états et fiche de génération en mémoire | Représente le cycle sans installer une base au Sprint 1 | Pendant la vie du serveur |
| `backend/app/schemas.py` | Fixe les réponses JSON de génération et de la galerie | Stabilise les réponses et la documentation OpenAPI | Sur les routes /models |
| `backend/app/routers/__init__.py` | Marque le paquet des routes | Clarifie l'organisation Python | À l'import des routes |
| `backend/app/routers/models.py` | Reçoit les photos, expose les états, sert le GLB terminé et les modèles de galerie | Sépare HTTP de l'orchestration métier et limite les fichiers de démo | À l'envoi, au suivi, au téléchargement et au filtrage de la galerie |
| `backend/app/services/__init__.py` | Marque le paquet métier | Clarifie les imports de services | À l'import du validateur et du service |
| `backend/app/services/upload_validator.py` | Contrôle extension, MIME, signature et plafond de 10 Mo | Le nom ou le type annoncé seul ne suffit pas | Avant d'enregistrer une photo |
| `backend/app/services/demo_gallery.py` | Liste seulement cinq GLB autorisés, valide leur structure 2.0 et résout leurs identifiants | N'expose aucun chemin fourni par le client et exclut les fichiers absents ou invalides | À l'ouverture de la galerie ou d'un modèle d'essai |
| backend/app/services/generation_service.py | Orchestre les états, le fournisseur et le stockage ; journalise type/repr/cause et masque les secrets | Facilite le diagnostic sans divulguer le jeton ni l'URL configurée | Après un upload valide ou en cas d'échec fournisseur |
| `backend/app/providers/__init__.py` | Marque le paquet d'adaptateurs | Isole les fournisseurs externes | À l'import fournisseur |
| `backend/app/providers/base.py` | Définit `Image3DProvider.generate(Path) -> bytes` et l'erreur commune | Permet de remplacer Hugging Face sans réécrire le service | Dans GenerationService et les adaptateurs |
| backend/app/providers/huggingface.py | Découvre le contrat avec view_api, lit les valeurs courantes de client.config, exécute les étapes TripoSR et valide GLB 2.0 | Évite d'interpréter les exemples comme des valeurs par défaut et prend la vraie sortie GLB | À chaque génération distante |
| `backend/app/storage/__init__.py` | Marque le paquet des adaptateurs de stockage | Sépare les fichiers de persistance du métier | À l'import du stockage |
| `backend/app/storage/base.py` | Définit le contrat `Storage` pour photos et GLB | Permet de changer la persistance derrière une interface | Dans GenerationService et ses tests |
| `backend/app/storage/local_storage.py` | Écrit de façon atomique avec des noms UUID créés par le serveur | Démarre sans service payant et évite les chemins du client | À l'acceptation et à la fin d'une génération |

## Interface

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `frontend/` | Contient la page, les styles et les modules JavaScript du Sprint 1 | Offre une interface modulaire sans deuxième serveur ni build | Quand une personne visite / |
| `frontend/README.md` | Explique les modules, le parcours et les limites du navigateur | Rend les responsabilités et dépendances compréhensibles | Avant de lancer ou modifier le frontend |
| `frontend/index.html` | Définit les zones accessibles du studio, du viewer, du suivi et de la galerie | Sépare le document et les libellés de la logique des vues | Quand FastAPI sert la page d'accueil |
| `frontend/css/` | Regroupe le thème et les styles de composants | Sépare les jetons visuels de la mise en page | Au chargement de la page et pour une retouche visuelle |
| `frontend/css/theme.css` | Définit la palette sombre, les fontes, le focus et la réduction du mouvement | Centralise les règles globales et lisibles | Avant les styles des composants |
| `frontend/css/components.css` | Met en page panneaux, upload, suivi, viewer, galerie et adaptations écran | Donne à chaque zone un style cohérent sans CSS intégré dans le HTML | Lors du rendu du studio |
| `frontend/js/` | Regroupe l'état, l'API et les vues ES modules | Permet de suivre une responsabilité par fichier sans framework | Quand le navigateur charge le module principal |
| `frontend/js/api.js` | Centralise fetch pour créer et suivre les générations et charger la galerie | Empêche les vues de disperser les appels serveur | À chaque action nécessitant l'API |
| `frontend/js/state.js` | Garde en mémoire photo, statut, durée et minuteries de la session | Évite une base de données pour cet état temporaire | Pendant l'envoi et le suivi d'une demande |
| `frontend/js/main.js` | Coordonne formulaire, suivi, galerie et viewer | Relie les modules sans placer la logique HTTP dans les vues | À l'ouverture de la page |
| `frontend/js/views/` | Regroupe les vues de l'interface | Isole les responsabilités visibles du studio | Quand une vue est modifiée ou réutilisée |
| `frontend/js/views/uploader.js` | Gère le dépôt, le sélecteur, les erreurs de fichier et l'envoi au callback | Rend les contrôles de fichier testables sans mélanger l'API | À la sélection d'une photo |
| `frontend/js/views/progress.js` | Traduit les états observés et le temps réel en étape accessible | N'invente ni pourcentage ni délai restant | Pendant et après une génération |
| `frontend/js/views/viewer.js` | Charge les modèles et gère caméra, plein écran, auto-rotation, AR conditionnelle et fichier local | Isole les gestes du composant 3D du suivi API | Après sélection ou génération d'un GLB |
| `frontend/js/views/gallery.js` | Crée les aperçus 3D et filtre les résultats de faisabilité par catégorie | N'affiche que les entrées réelles reçues du backend | Quand la galerie est chargée ou filtrée |

## Tests et vérification continue

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/tests/` | Contient la suite pytest du backend | Regroupe les vérifications sans appeler le fournisseur en continu | En local et sur GitHub |
| `backend/tests/test_health.py` | Vérifie le résultat HTTP de `/health` | Protège le premier contrat du serveur | À chaque suite pytest |
| `backend/tests/test_upload_validator.py` | Couvre formats, taille, signatures et erreurs | Empêche les uploads mal formés sans réseau | À chaque suite pytest |
| backend/tests/test_huggingface_provider.py | Simule view_api et client.config pour tester la découverte d'endpoints, les vrais défauts lus dans config et la validation GLB | Aucun réseau ni GPU dans les tests | À chaque suite pytest |
| backend/tests/test_generation_service.py | Vérifie les transitions d'état et le masquage du jeton et de l'URL dans les logs d'erreur | Protège le diagnostic des secrets locaux | À chaque suite pytest |
| `backend/tests/test_local_storage.py` | Contrôle écritures atomiques, noms et garde-fous de chemin | Protège le stockage local contre un chemin client | À chaque suite pytest |
| `backend/tests/test_models_api.py` | Vérifie les réponses d'upload, de suivi, les erreurs et le refus de téléchargement prématuré | Stabilise le contrat HTTP sans appeler le fournisseur | À chaque suite pytest |
| `backend/tests/test_frontend.py` | Vérifie les ressources statiques, l'isolation HTTP dans api.js et l'absence d'envoi du fichier local | Protège les limites du frontend sans fournisseur | À chaque suite pytest |
| `backend/tests/test_demo_gallery.py` | Vérifie l'allowlist, la validation GLB, les erreurs et le téléchargement temporaire | Protège la galerie sans dépendre des médias ignorés du poste | À chaque suite pytest |
| `.github/workflows/ci.yml` | Vérifie les documents puis installe les dépendances et exécute pytest | Donne un contrôle répétable sur GitHub | À chaque push ou pull request |

## Documentation et historique

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `docs/` | Regroupe l'état, la structure et les guides | Sépare les explications du code exécutable | Tout au long du projet |
| `docs/etapes/` | Contient un guide par étape du Sprint 1 | Permet de comprendre l'évolution sans mélanger les étapes | Pour apprendre et préparer la soutenance |
| docs/ETAT.md | Résume l'étape 6, les cinq résultats réels, les contrôles effectués et les points encore à valider | Évite de perdre la distinction entre preuve technique et note de qualité | Au début et à la fin d'une session |
| `docs/STRUCTURE.md` | Explique chaque élément du dépôt | Aide l'étudiante à défendre les choix | À chaque ajout ou changement de structure |
| `docs/etapes/etape-01.md` | Explique FastAPI et GET `/health` | Garde une trace pédagogique du premier socle | Pour réviser l'étape 1 |
| `docs/etapes/etape-02.md` | Explique le validateur et le contrat d'upload historique | Documente l'évolution de POST `/models` au fil du sprint | Pour réviser l'étape 2 |
| `docs/etapes/etape-03.md` | Décrit l'API Hugging Face inspectée, les photos, la licence et les erreurs observées | Distingue l'implémentation de sa faisabilité non démontrée | Pour revoir le fournisseur ou expliquer l'essai au jury |
| `docs/etapes/etape-04.md` | Explique statuts, service, stockage et routes | Rend le cycle de génération explicable fichier par fichier | Pour réviser l'étape 4 |
| `docs/etapes/etape-05.md` | Explique les modules, le suivi réel, le viewer, la galerie et les limites de test | Relie l'interface et ses ressources aux routes backend | Pour présenter ou modifier l'étape 5 |
| docs/etapes/etape-06.md | Consigne le contrat observé, les cinq appels, les temps, les tailles et les limites de visualisation | Fournit une trace exacte et pédagogique pour reproduire la soutenance | Pour analyser les résultats et attribuer les notes visuelles |
| docs/etapes/etape-06-colab.md | Explique l'installation testée, le démarrage Gradio et les limites du runtime gratuit | Permet de redémarrer le service sans PyTorch local et sans divulguer le lien temporaire | Avant de préparer une autre démonstration |
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
| backend/.env | Configuration locale, dont l'URL temporaire du serveur Gradio | Fichier ignoré par Git ; ne jamais copier son contenu dans un document ou un commit | Pour connecter le backend au serveur Colab actif |
| `backend/data/` | Stocke les entrées et sorties locales des essais | Garde les médias hors de Git | Pendant la faisabilité |
| `backend/data/feasibility-inputs/` | Photos libres choisies pour les essais ; trois autres photos écartées ne doivent pas être envoyées car elles montrent des personnes | Garde une provenance et protège les personnes visibles | Pendant les essais réels |
| backend/data/feasibility-results/ | Contient les cinq GLB réellement téléchargés par l'application et validés GLB 2.0 | Les sorties de faisabilité ne sont pas versionnées ; aucune n'est simulée | Pour examiner les résultats ou les ouvrir dans un viewer |
| `backend/storage/` | Dossier de runtime pour les photos et modèles des demandes | Conserve les uploads en dehors des sources | Créé automatiquement au premier upload |
| `backend/storage/images/` | Photos reçues à l'exécution | Conserve les entrées hors du dépôt | Après un vrai upload |
| `backend/storage/models/` | GLB reçus du fournisseur | Conserve les modèles générés hors du dépôt | Après une vraie génération réussie |
| `extension-debug.log` | Journal auxiliaire local de l'environnement de développement | N'est pas une entrée de l'application et est exclu de Git | Seulement si l'outil local le recrée |
| `__pycache__/`, `.pytest_cache/` | Bytecode et cache de collecte | Ces fichiers se régénèrent automatiquement | Après imports et tests |

Le registre de générations est actuellement en mémoire et se vide au redémarrage. Le dossier `frontend/` n'est donc plus un emplacement futur : la page Sprint 1 y est présente. Sont toujours hors Sprint 1 : authentification, base de données, OpenCV, rembg, Next.js, comptes vendeurs, catalogue commercial complet, widget distribuable, Docker, Celery, Redis et MinIO.
