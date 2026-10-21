# Structure expliquée — Forma3D Studio

Mis à jour le 21 octobre 2026. Les tableaux décrivent les fichiers du projet qui existent et les dossiers locaux ignorés par Git. L'étape 6 a été testée partiellement sur Colab : trois essais de l'image récente ont échoué ; dans le runtime Python 3.12, la commande de secours torchmcubes a aussi échoué au code 1 sans afficher son stderr interne. Le runtime historique 2025.10 a été contrôlé (Python 3.12.12, T4, CUDA 12.6). La cellule de secours a été mise à jour d'après le README officiel actuel de torchmcubes et reste à tester. Le serveur n'a pas démarré et aucun GLB n'a été obtenu.

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
| `tools/colab/triposr_server.ipynb` | Vérifie un GPU T4, clone le dépôt officiel, installe ses dépendances dans Colab et lance gradio_app.py avec un lien public | Évite toute installation PyTorch, CUDA ou TripoSR sur le PC ; toutes les cellules de code sont commentées en français. Le contrôle T4/Python 3.12 du runtime 2025.10 est réussi ; une capture montre une commande d'installation personnalisée en échec, mais la runtime et la cause ne sont pas identifiés | Après vérification du runtime et de l'erreur pip, avant de fournir l'URL Gradio au backend |

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
| `backend/app/main.py` | Construit FastAPI, sert la page `/`, configure le service et branche les routes | Fournit un point d'entrée unique | Quand Uvicorn démarre ou TestClient importe l'application |
| `backend/app/config.py` | Charge d'abord `backend/.env`, puis `.env` racine, et vérifie le Space, le jeton facultatif et les délais | Garde les secrets hors du code et permet le fichier local demandé pour les essais | Au démarrage du service de génération |
| `backend/app/models.py` | Définit états et fiche de génération en mémoire | Représente le cycle sans installer une base au Sprint 1 | Pendant la vie du serveur |
| `backend/app/schemas.py` | Fixe le JSON public de l'état de génération | Stabilise les réponses et la documentation OpenAPI | Sur POST et GET `/models` |
| `backend/app/routers/__init__.py` | Marque le paquet des routes | Clarifie l'organisation Python | À l'import des routes |
| `backend/app/routers/models.py` | Valide la photo, crée la tâche, donne l'état et sert le GLB terminé | Sépare HTTP de l'orchestration métier | À l'envoi, au suivi et au téléchargement |
| `backend/app/services/__init__.py` | Marque le paquet métier | Clarifie les imports de services | À l'import du validateur et du service |
| `backend/app/services/upload_validator.py` | Contrôle extension, MIME, signature et plafond de 10 Mo | Le nom ou le type annoncé seul ne suffit pas | Avant d'enregistrer une photo |
| `backend/app/services/generation_service.py` | Orchestre états, appel du fournisseur et stockage | Centralise un cycle testable en dehors des routes | Après un téléversement valide |
| `backend/app/providers/__init__.py` | Marque le paquet d'adaptateurs | Isole les fournisseurs externes | À l'import fournisseur |
| `backend/app/providers/base.py` | Définit `Image3DProvider.generate(Path) -> bytes` et l'erreur commune | Permet de remplacer Hugging Face sans réécrire le service | Dans GenerationService et les adaptateurs |
| `backend/app/providers/huggingface.py` | Appelle `view_api()` à chaque génération, lit les paramètres publiés, exécute une chaîne Gradio TripoSR ou l'endpoint observé Stable Fast 3D et valide le conteneur GLB 2.0 | N'invente pas les fonctions, index, défauts ou sorties ; garde les fournisseurs derrière Image3DProvider | Pour une génération distante via identifiant de Space ou URL Gradio |
| `backend/app/storage/__init__.py` | Marque le paquet des adaptateurs de stockage | Sépare les fichiers de persistance du métier | À l'import du stockage |
| `backend/app/storage/base.py` | Définit le contrat `Storage` pour photos et GLB | Permet de changer la persistance derrière une interface | Dans GenerationService et ses tests |
| `backend/app/storage/local_storage.py` | Écrit de façon atomique avec des noms UUID créés par le serveur | Démarre sans service payant et évite les chemins du client | À l'acceptation et à la fin d'une génération |

## Interface

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `frontend/` | Contient la page web du Sprint 1 | Offre une interface sans deuxième serveur ni build | Quand une personne visite `/` |
| `frontend/README.md` | Explique le rôle de la page et sa dépendance CDN | Rend visible que cette interface existe réellement et ses limites | Avant de la lancer ou de la modifier |
| `frontend/index.html` | Formulaire photo, statuts, viewer, commandes caméra, téléchargement et ouverture d'un GLB local par URL `blob:` | Garde un seul serveur ; le fichier local ne passe pas par l'API et n'est pas présenté comme généré | Quand le vendeur visite `/` ou vérifie le viewer avec un fichier `.glb` existant |

## Tests et vérification continue

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `backend/tests/` | Contient la suite pytest du backend | Regroupe les vérifications sans appeler le fournisseur en continu | En local et sur GitHub |
| `backend/tests/test_health.py` | Vérifie le résultat HTTP de `/health` | Protège le premier contrat du serveur | À chaque suite pytest |
| `backend/tests/test_upload_validator.py` | Couvre formats, taille, signatures et erreurs | Empêche les uploads mal formés sans réseau | À chaque suite pytest |
| `backend/tests/test_huggingface_provider.py` | Vérifie les contrats Stable Fast 3D et TripoSR, l'ordre de la chaîne, la sécurité du jeton et la lecture GLB avec un client simulé et une fixture de conteneur | Ne consomme pas de quota et ne prétend pas générer un vrai modèle en CI | À chaque suite pytest |
| `backend/tests/test_generation_service.py` | Vérifie la création et les transitions d'état sans prétendre créer un vrai modèle | Isole le métier du Space | À chaque suite pytest |
| `backend/tests/test_local_storage.py` | Contrôle écritures atomiques, noms et garde-fous de chemin | Protège le stockage local contre un chemin client | À chaque suite pytest |
| `backend/tests/test_models_api.py` | Vérifie les réponses d'upload, de suivi, les erreurs et le refus de téléchargement prématuré | Stabilise le contrat HTTP sans appeler le fournisseur | À chaque suite pytest |
| `backend/tests/test_frontend.py` | Vérifie la page, le contrôle GLB local et l'absence d'envoi réseau depuis son gestionnaire | Protège le parcours local sans fournisseur et sans navigateur externe | À chaque suite pytest |
| `.github/workflows/ci.yml` | Vérifie les documents puis installe les dépendances et exécute pytest | Donne un contrôle répétable sur GitHub | À chaque push ou pull request |

## Documentation et historique

| Chemin | À quoi ça sert | Pourquoi ce choix | Quand on l'utilise |
|---|---|---|---|
| `docs/` | Regroupe l'état, la structure et les guides | Sépare les explications du code exécutable | Tout au long du projet |
| `docs/etapes/` | Contient un guide par étape du Sprint 1 | Permet de comprendre l'évolution sans mélanger les étapes | Pour apprendre et préparer la soutenance |
| `docs/ETAT.md` | Résume fait, en cours, blocages et prochaine action | Transmet l'état réel d'une session à l'autre | Avant de reprendre et après une étape |
| `docs/STRUCTURE.md` | Explique chaque élément du dépôt | Aide l'étudiante à défendre les choix | À chaque ajout ou changement de structure |
| `docs/etapes/etape-01.md` | Explique FastAPI et GET `/health` | Garde une trace pédagogique du premier socle | Pour réviser l'étape 1 |
| `docs/etapes/etape-02.md` | Explique le validateur et le contrat d'upload historique | Documente l'évolution de POST `/models` au fil du sprint | Pour réviser l'étape 2 |
| `docs/etapes/etape-03.md` | Décrit l'API Hugging Face inspectée, les photos, la licence et les erreurs observées | Distingue l'implémentation de sa faisabilité non démontrée | Pour revoir le fournisseur ou expliquer l'essai au jury |
| `docs/etapes/etape-04.md` | Explique statuts, service, stockage et routes | Rend le cycle de génération explicable fichier par fichier | Pour réviser l'étape 4 |
| `docs/etapes/etape-05.md` | Explique le formulaire, le suivi, le viewer et ses limites de test | Relie l'interface aux routes backend | Pour présenter ou modifier l'étape 5 |
| `docs/etapes/etape-06.md` | Consigne les essais précédents, la préparation Colab et les critères non satisfaits | Évite de déclarer le sprint terminé sans GLB réel | Pour suivre les essais et préparer la soutenance |
| `docs/etapes/etape-06-colab.md` | Explique le démarrage Colab, les options vérifiées, les risques du GPU gratuit et le parcours après réception du lien | Rend l'installation distante reproductible et consigne le test réel partiel ainsi que le blocage des dépendances | Avant de reprendre l'installation TripoSR ou pour expliquer les limites au jury |
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
| `backend/.env` | Réglages secrets locaux du backend, notamment `HF_TOKEN` ; absent lors du dernier contrôle | Le fournisseur public ne reçoit aucun jeton commité | Lorsqu'un essai authentifié est explicitement nécessaire |
| `backend/data/` | Stocke les entrées et sorties locales des essais | Garde les médias hors de Git | Pendant la faisabilité |
| `backend/data/feasibility-inputs/` | Photos libres choisies pour les essais ; trois autres photos écartées ne doivent pas être envoyées car elles montrent des personnes | Garde une provenance et protège les personnes visibles | Pendant les essais réels |
| `backend/data/feasibility-results/` | Destination locale des résultats de faisabilité réellement obtenus | Un GLB n'y est conservé qu'après retour réel et vérification ; aucun résultat n'est présent actuellement | Après une génération réussie ; le sélecteur du viewer peut ouvrir le fichier depuis le navigateur |
| `backend/storage/` | Dossier de runtime pour les photos et modèles des demandes | Conserve les uploads en dehors des sources | Créé automatiquement au premier upload |
| `backend/storage/images/` | Photos reçues à l'exécution | Conserve les entrées hors du dépôt | Après un vrai upload |
| `backend/storage/models/` | GLB reçus du fournisseur | Conserve les modèles générés hors du dépôt | Après une vraie génération réussie |
| `extension-debug.log` | Journal auxiliaire local de l'environnement de développement | N'est pas une entrée de l'application et est exclu de Git | Seulement si l'outil local le recrée |
| `__pycache__/`, `.pytest_cache/` | Bytecode et cache de collecte | Ces fichiers se régénèrent automatiquement | Après imports et tests |

Le registre de générations est actuellement en mémoire et se vide au redémarrage. Le dossier `frontend/` n'est donc plus un emplacement futur : la page Sprint 1 y est présente. Sont toujours hors Sprint 1 : authentification, base de données, OpenCV, rembg, Next.js, comptes vendeurs, catalogue commercial complet, widget distribuable, Docker, Celery, Redis et MinIO.
