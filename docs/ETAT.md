# État du projet — Forma3D Studio

Dernière mise à jour : 21 octobre 2026.

## Résumé d'avancement

Sprint 1 — SaaS e-commerce : photo vers GLB affiché et téléchargeable. Les étapes 1 à 5 sont implémentées. L'étape 6 reste bloquée à l'installation Colab : une capture montre un `pip install` d'une liste sans `torchmcubes` en échec (code 1), puis une trace Python 3.12 confirme que la commande de secours `pip install git+...torchmcubes.git` échoue aussi (code 1). Dans les deux cas, le message pip interne manque. Le runtime historique `2025.10` a été vérifié avec Python 3.12.12, Tesla T4 et CUDA 12.6. Aucun serveur, lien public ni GLB réel n'a été obtenu. Le Sprint 1 et l'US3 ne sont pas déclarés terminés.

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
- Le 21 octobre 2026, le vrai runtime Colab a détecté Tesla T4 et a cloné le dépôt officiel dans /content/TripoSR. Trois essais d'installation ont échoué avant le démarrage de Gradio : les deux premiers sur la préparation de métadonnées de torchmcubes ; le troisième, après séparation de torchmcubes, sur la construction de Pillow==10.1.0 depuis son archive source (« Getting requirements to build wheel » : erreur, code 1). La sortie disponible ne révèle pas l'exception interne de Pillow ; aucune cause plus précise n'est affirmée. La limite de trois tentatives est atteinte.
- Les notes officielles Colab datées du 16 septembre 2026 annoncent Python 3.13.15 sur les images runtime. PyPI publie Pillow 10.1.0 avec des wheels CPython au plus pour 3.12 et aucun wheel cp313. Cela correspond au téléchargement de l'archive source observé, mais la version du noyau de cette session n'a pas été imprimée ; la compatibilité est une hypothèse étayée, pas une cause prouvée.
- Pour tester une image runtime antérieure, la version Colab `2025.10` a été sélectionnée en gardant T4. Après l'arrêt de l'ancienne session, le nouveau runtime s'est connecté le 21 octobre 2026. La cellule GPU y a confirmé Python 3.12.12, Tesla T4 et PyTorch CUDA 12.6. Le clonage et les dépendances doivent être repris dans cette session neuve ; le dossier `/content/TripoSR` de l'ancien runtime n'y est pas considéré comme présent.

## Bloqué : dépendances dans Colab

- Dans l'image Colab récente, le GPU Tesla T4 et le clonage sont vérifiés ; l'installation échoue à Pillow==10.1.0 après trois tentatives. Aucune quatrième tentative n'est lancée dans cette piste.
- Dans le runtime historique Colab `2025.10`, le contrôle GPU est réussi (Python 3.12.12, Tesla T4, PyTorch CUDA 12.6). Une première capture d'installation personnalisée sans `torchmcubes` montre un code 1, sans runtime clairement visible. Une trace ultérieure avec `/usr/lib/python3.12/subprocess.py` confirme que la commande de secours TripoSR `pip install git+https://github.com/tatsy/torchmcubes.git` a aussi échoué avec le code 1 ; `CalledProcessError` ne contient pas le stderr interne de pip.
- La cellule de serveur n'a pas été exécutée : aucune URL Gradio publique n'existe à communiquer et le serveur TripoSR n'est pas disponible.
- Aucun contrat view_api() du serveur Colab n'a été lu ; seuls des tests locaux simulant Client couvrent les deux formes de contrat.
- Aucune photo n'a été envoyée à ce serveur, aucun statut PENDING/RUNNING/DONE n'a été observé et aucun GLB ne se trouve dans backend/data/feasibility-results/.
- Le viewer et le téléchargement n'ont pas été validés avec un GLB réel. Aucun tableau de 5 à 10 résultats TripoSR ni note de qualité de l'étudiante n'existe encore.
- La cellule de secours du notebook versionné a été adaptée au README actuel de `tatsy/torchmcubes` : installer `scikit-build-core`, `pybind11` et `cmake`, puis construire avec `--no-build-isolation`, en affichant stdout/stderr complet. Ce changement est **non testé sur Colab**. Exécuter la cellule corrigée au plus une fois dans le runtime Python 3.12 ; si elle échoue, conserver stdout/stderr et arrêter les tentatives avant de choisir la suite.
- Une fois le serveur démarré et son URL communiquée : l'écrire uniquement dans backend/.env, inspecter le vrai view_api(), envoyer une photo sûre via POST /models, suivre les statuts, valider et afficher le GLB, essayer le téléchargement, puis seulement étendre l'essai à 5–10 photos. L'étudiante attribuera les notes bon/moyen/mauvais.

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

Vérification locale du 21 octobre : les 15 tests de `tests/test_huggingface_provider.py` passent avec `--basetemp=data\.pytest-scratch` (aucun appel réseau). La suite complète a été lancée, mais elle n'a pas produit de résultat dans ce sandbox et a été interrompue ; elle n'est donc pas déclarée verte localement. La CI doit confirmer la suite complète après le push.

## Prochaine action recommandée

Vérifier le runtime de la capture Colab et récupérer l'erreur pip complète avant un nouvel essai d'installation. Ne déclarer l'étape 6 réussie qu'après démarrage du serveur, inspection réelle de `view_api()`, réception d'un vrai GLB par le parcours de l'application, affichage et téléchargement.
