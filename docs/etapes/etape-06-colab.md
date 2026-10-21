# Guide — lancer le serveur TripoSR dans Colab

Dernière vérification des sources et de la session : 21 octobre 2026.

## Statut

Le notebook a été **testé partiellement sur Colab le 21 octobre 2026** : dans l'image récente, Tesla T4 et clonage officiel réussissent, puis trois essais d'installation échouent ; le dernier s'arrête pendant la préparation du wheel de `Pillow==10.1.0`. Le runtime historique Colab `2025.10` a été contrôlé avec Python 3.12.12, Tesla T4 et PyTorch CUDA 12.6. Une installation personnalisée sans `torchmcubes` et la commande de secours simple de TripoSR ont échoué avec le code 1 ; aucune capture ne contient le stderr interne de pip. La cellule de secours est mise à jour d'après le README actuel de `tatsy/torchmcubes` et imprime désormais ses diagnostics, mais cette modification reste non testée sur Colab. Le serveur ne fonctionne pas, aucun lien n'a été obtenu et aucun GLB n'est présent ou prétendu généré.

## Pourquoi ce choix

Le Space officiel TripoSR était en erreur runtime. Ce guide lance le code officiel du dépôt VAST-AI-Research dans un runtime Colab temporaire. Le backend Forma3D appelle ensuite le serveur par Gradio Client. TripoSR est pré-entraîné : ce parcours n'entraîne aucun modèle.

Le README officiel demande Python 3.8 ou plus, PyTorch adapté au système et à CUDA, une version CUDA compatible avec celle de PyTorch, puis la mise à niveau de setuptools et l'installation de requirements.txt. Il indique environ 6 Go de VRAM par image en configuration par défaut. Le notebook contrôle le GPU T4 et la version CUDA de PyTorch fournie par Colab ; il n'installe pas PyTorch sur le PC.

Le requirements.txt officiel contient OmegaConf, Pillow, einops, torchmcubes, Transformers, trimesh, rembg, huggingface-hub, imageio avec ffmpeg, Gradio, xatlas et moderngl. Il ne fixe pas PyTorch : le README demande de choisir la version PyTorch correspondant à la plateforme et à CUDA. Le runtime Colab fournit cette partie ; les autres paquets sont installés seulement dans le runtime temporaire.

Le README actuel de `torchmcubes` précise aussi le compilateur : Python et PyTorch doivent être déjà disponibles, un compilateur C++20 et CMake 3.24 ou plus sont requis, et CUDA Toolkit 12 ou plus est nécessaire pour compiler le support GPU. Sans CUDA Toolkit, le projet décrit une compilation CPU. Sa procédure pip installe `scikit-build-core` et `pybind11`, puis utilise `--no-build-isolation` pour lier l'extension au PyTorch du runtime.

Le script run.py est l'outil d'inférence en ligne de commande, et non le serveur web utilisé ici. Il prend une ou plusieurs images, peut choisir le périphérique, le modèle pré-entraîné, la taille de chunk, la résolution marching-cubes, le retrait de fond et le ratio du premier plan, le dossier de sortie, le format OBJ ou GLB, la cuisson de texture et le rendu vidéo. Son format par défaut est OBJ ; le notebook lance gradio_app.py, dont le code retourne dans l'ordre un OBJ puis un GLB.

## Démarrage pas à pas

1. Ouvrir tools/colab/triposr_server.ipynb dans Google Colab.
2. Dans Exécution, choisir Modifier le type d'exécution, puis T4 GPU. Les GPU gratuits ne sont pas garantis : le notebook arrête l'exécution si aucun T4 n'est détecté.
3. Sur l'image Colab récente, le contrôle T4 et le clonage ont réussi, mais trois essais d'installation ont échoué. N'y relance pas l'installation. Le runtime historique `2025.10` a Python 3.12.12, T4 et CUDA 12.6 ; son contrôle GPU a réussi. Les erreurs de la variante et de l'ancienne commande de secours n'ont pas leur stderr détaillé. La cellule de secours versionnée suit maintenant le README actuel de `tatsy/torchmcubes` et conserve la sortie complète ; exécute-la au plus une fois dans ce runtime, puis arrête les essais si elle échoue.
4. En cas d'erreur CUDA torchmcubes explicitement indiquée par le README, exécuter uniquement la cellule de dépannage. Elle désinstalle le paquet de ce runtime, puis reprend la commande de réinstallation proposée dans le README.
5. Lancer la dernière cellule. Elle exécute gradio_app.py avec --share, --port 7860 et --queuesize 1. Le code officiel a le port 7860 par défaut. La sortie affiche le lien gradio.live à copier.
6. Garder cette cellule en cours d'exécution pendant les appels de Forma3D et pendant une éventuelle démonstration.
7. Quand le lien apparaît, l'envoyer dans la conversation sous la forme URL : https://....gradio.live. Ne pas le publier dans un dépôt ou dans un document public.
8. Avant de versionner le notebook après un essai, effacer toutes ses sorties dans Colab et vérifier que le lien temporaire ne reste pas enregistré dans le fichier.

Le script accepte également --username et --password ; il n'active auth que si les deux valeurs sont fournies. Le notebook ne les passe pas, conformément au lien public demandé : l'interface est donc sans authentification. Quiconque obtient ce lien temporaire peut joindre le serveur. N'envoyer aucune photo contenant une personne, une information personnelle ou une image dont les droits d'utilisation ne sont pas acquis.

## Limites à connaître

- L'accès gratuit à un GPU T4 n'est pas garanti. La disponibilité, les quotas, les périodes d'inactivité, la durée maximale du runtime et le type de GPU changent selon Colab ; Google ne publie pas de durée fixe.
- Le lien public Gradio est temporaire et disparaît quand le processus ou le runtime s'arrête.
- Colab peut terminer une session après inactivité ou selon ses limites dynamiques. Une démo nécessite le runtime disponible et la cellule du serveur active.
- Le serveur est public sans identifiants dans la configuration de ce notebook. Il ne faut donc pas lui transmettre de données sensibles.
- Le notebook utilise le PyTorch déjà fourni par l'image Colab. Aucun paquet, poids ni compilateur CUDA n'est ajouté à l'environnement Windows local.
- Le README et la licence MIT couvrent le code et les poids publiés par le projet. La licence ne donne pas les droits sur les photos envoyées.
- Sur l'image Colab récente, le notebook a été testé jusqu'au clonage et à l'échec d'installation. La sortie montre `Pillow==10.1.0` téléchargé comme archive source, puis une erreur de préparation du wheel ; elle ne révèle pas l'exception interne, donc la cause racine n'est pas établie.
- Sur le runtime historique `2025.10`, Python 3.12.12, T4 et CUDA 12.6 sont observés, et la cellule GPU réussit.
- Les 15 tests locaux simulés du fournisseur passent (`pytest -q tests/test_huggingface_provider.py --basetemp=data/.pytest-scratch`, depuis `backend`). Le lancement Gradio, la création effective du lien, le contrat Gradio réel et une génération de modèle restent à vérifier.

## Ce que Forma3D vérifiera après réception de l'URL

1. Écrire l'URL uniquement dans backend/.env, ignoré par Git.
2. Construire Client avec cette URL et appeler view_api() pour lire le contrat exposé par ce runtime. Aucun chemin API n'est supposé à l'avance.
3. Utiliser une seule photo de mobilier libre de droits, sans personne, via le vrai POST /models de l'application.
4. Relever PENDING, RUNNING et DONE à partir des réponses HTTP réelles, vérifier les octets GLB 2.0, ouvrir le fichier dans le viewer, tester rotation, déplacement, zoom et téléchargement. Le compte rendu distinguera les contrôles observés de ceux qui auront échoué.
5. Seulement si le parcours unique réussit, passer aux 5 à 10 photos. Les durées et tailles seront mesurées ; la note bon, moyen ou mauvais sera donnée par l'étudiante, jamais inférée par le code.

L'US3 et l'étape 6 resteront non validées tant que Forma3D n'aura pas reçu un vrai GLB par ce serveur et que le parcours réel n'aura pas été vérifié. Les résultats des anciens essais sont conservés dans docs/etapes/etape-06.md.

## Sources officielles consultées

- Dépôt, aperçu du modèle et licence : https://github.com/VAST-AI-Research/TripoSR
- README : https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/README.md
- Dépendances : https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/requirements.txt
- README et instructions pip actuelles de `torchmcubes` : https://github.com/tatsy/torchmcubes#pip-installation
- Application Gradio et options de lancement : https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/gradio_app.py
- Inférence en ligne de commande : https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/run.py
- Instructions de compilation actuelles de `torchmcubes` : https://github.com/tatsy/torchmcubes#pip-installation
- FAQ officielle Colab sur ressources non garanties et limites variables : https://research.google.com/colaboratory/faq.html
- Notes officielles Colab sur les images runtime (Python 3.13.15 depuis le 16 septembre 2026) : https://colab.research.google.com/notebooks/relnotes.ipynb
- Fichiers de la version Pillow 10.1.0 sur PyPI : https://pypi.org/project/Pillow/10.1.0/
