# État du projet — Forma3D Studio

Dernière mise à jour : 20 octobre 2026.

## Résumé d'avancement

Sprint 1 — photo vers GLB affiché et téléchargeable. Les étapes 1 à 5 sont implémentées. L'étape 6 est en cours de préparation : un serveur TripoSR officiel sera démarré par l'étudiante sur Colab, puis appelé par Forma3D via une URL Gradio publique. Le notebook est non testé sur Colab. Aucun GLB réel n'a encore été obtenu ; le Sprint 1 et l'US3 ne sont pas déclarés terminés.

## Fait

- Vision v2 cadrée comme SaaS 3D pour l'e-commerce ; widget intégrable et boutique vitrine planifiés pour des sprints ultérieurs.
- Ancien cadrage v1 et guides archivés dans docs/archive/v1/.
- API FastAPI avec GET /health, page HTML, validation d'images, POST /models, suivi de génération, stockage local et téléchargement après DONE.
- Contrat Image3DProvider et adaptateur Gradio séparé du service métier.
- Viewer model-viewer avec rotation, déplacement de caméra, zoom, génération suivie par statut et téléchargement.
- Bouton « Ouvrir un GLB local » : le navigateur utilise une URL blob ; le fichier ne passe pas par le serveur et est identifié comme non généré par l'application.
- Configuration charge backend/.env avant le .env racine. HF_SPACE_ID accepte un identifiant de Space ou une URL HTTP(S) complète.
- Signature locale inspectée : gradio_client 2.7.2 expose Client(src, token=...). Sa documentation de signature accepte une URL complète d'application Gradio. Un jeton HF n'est pas transmis à un serveur Gradio tiers.
- Notebook tools/colab/triposr_server.ipynb et guide docs/etapes/etape-06-colab.md créés pour le serveur TripoSR.
- Le fournisseur appelle view_api() à chaque génération, lit les valeurs par défaut exposées et trouve la sortie GLB selon la description réelle. Il prend en charge le clic complet ou les étapes Gradio séparées si elles sont publiées.
- Le validateur du fournisseur contrôle l'en-tête GLB 2.0, le chunk JSON, l'asset et les limites de chunks.
- Aucun paquet n'a été ajouté à backend/requirements.txt ; aucun PyTorch, CUDA ou TripoSR n'a été installé en local.

## Historique des essais réels

- Stable Fast 3D : API inspectée avant usage ; cinq photos de mobilier libres et sans personne visible ont échoué avec la même exception interne Gradio générique. Aucun GLB n'a été reçu.
- Space officiel stabilityai/TripoSR : trois tentatives de constructeur se sont arrêtées avant view_api() sur RUNTIME_ERROR ; aucune photo ne lui a été envoyée. L'erreur et sa repr sont conservées dans docs/etapes/etape-06.md.
- Ces échecs ne prouvent ni un quota épuisé ni une file d'attente ; les messages n'en donnaient pas la cause.
- Le code officiel TripoSR a été consulté dans README.md, requirements.txt, gradio_app.py et run.py. Le dépôt et les poids sont sous licence MIT.
- gradio_app.py expose --share, --port (7860 par défaut), --username et --password. auth est activé uniquement quand les deux identifiants sont donnés. Le notebook démarre sans authentification et demande un lien temporaire public.

## En cours et bloqué par l'URL Colab

- La disponibilité du GPU T4, l'installation dans Colab, le lancement Gradio et la création effective du lien n'ont pas été vérifiés. Le notebook est explicitement marqué « non testé sur Colab ».
- Aucun contrat view_api() du serveur Colab n'a été lu ; seuls des tests locaux simulant Client couvrent les deux formes de contrat.
- Aucune photo n'a été envoyée à ce serveur, aucun statut PENDING/RUNNING/DONE n'a été observé et aucun GLB ne se trouve dans backend/data/feasibility-results/.
- Le viewer et le téléchargement n'ont pas été validés avec un GLB réel. Aucun tableau de 5 à 10 résultats TripoSR ni note de qualité de l'étudiante n'existe encore.
- Il faut attendre l'URL publique que l'étudiante communiquera. Elle sera écrite uniquement dans backend/.env et restera ignorée par Git.
- Après réception de l'URL : inspecter le vrai view_api(), envoyer une photo sûre via POST /models, suivre les statuts, valider et afficher le GLB, essayer le téléchargement, puis seulement étendre l'essai à 5–10 photos. L'étudiante attribuera les notes bon/moyen/mauvais.

## Décisions et limites

- MVP initial limité au petit mobilier opaque : tabouret, chaise, table d'appoint.
- Aucun entraînement de modèle ; TripoSR pré-entraîné seulement.
- GitHub Projects pour Scrum ; horizon de soutenance de deux semaines communiqué, date précise non connue ; niveau Python et React déclaré avancé.
- Colab gratuit ne garantit pas GPU T4, durée de session, disponibilité ni période d'inactivité fixe. Le lien Gradio est public et temporaire ; la cellule doit tourner pendant les essais et la démonstration.
- Ne jamais envoyer au serveur public une photo personnelle, contenant une personne ou sans droits d'utilisation.
- Pas d'OpenCV, de rembg ajouté au projet, comptes, base de données, Next.js, Docker, Celery, Redis ou MinIO au Sprint 1.
- Le registre des statuts est en mémoire et disparaît au redémarrage. Les fichiers restent sur le disque local.

## Commandes locales de vérification

Depuis le dossier backend sous PowerShell :

    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Les tests locaux doivent simuler le client et ne pas appeler de fournisseur distant. Les tests complets du dépôt sont également exécutés en CI GitHub. L'environnement Windows actuel a présenté un blocage dans la création du socket local de Starlette TestClient ; le diagnostic et le résultat final local sont à consigner dans la session de travail.

Lors de la préparation de l'étape 6, 31 tests locaux hors des trois modules qui démarrent TestClient ont réussi. Ces modules ne peuvent pas être exécutés dans le sandbox Windows actuel : la boucle asyncio attend un socket local pendant le démarrage de TestClient. Ce blocage de l'environnement n'est pas déclaré comme une régression du code. La CI GitHub « Project checks » a exécuté la suite complète avec succès sur le commit 59033ebffaf3fa6f5cd5b8c6177293cae7a816e3 le 20 octobre 2026.

## Prochaine action recommandée

Ouvrir le guide docs/etapes/etape-06-colab.md, lancer le notebook avec le GPU T4 si Colab le propose, puis transmettre le lien sous la forme URL : https://....gradio.live. Ne déclarer l'étape 6 réussie qu'après réception et vérification d'un vrai GLB par le parcours de l'application.
