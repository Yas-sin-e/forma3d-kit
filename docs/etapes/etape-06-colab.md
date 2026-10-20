# Guide — lancer le serveur TripoSR dans Colab

Dernière vérification des sources : 20 octobre 2026.

## Statut

Le notebook est préparé, mais il est **non testé sur Colab**. Il n'a encore ni lancé le modèle ni obtenu de lien. L'étudiante doit démarrer elle-même le runtime avec son compte Google et nous transmettre l'URL annoncée. Aucun GLB n'est présent ou prétendu généré.

## Pourquoi ce choix

Le Space officiel TripoSR était en erreur runtime. Ce guide lance le code officiel du dépôt VAST-AI-Research dans un runtime Colab temporaire. Le backend Forma3D appelle ensuite le serveur par Gradio Client. TripoSR est pré-entraîné : ce parcours n'entraîne aucun modèle.

Le README officiel demande Python 3.8 ou plus, PyTorch adapté au système et à CUDA, une version CUDA compatible avec celle de PyTorch, puis la mise à niveau de setuptools et l'installation de requirements.txt. Il indique environ 6 Go de VRAM par image en configuration par défaut. Le notebook contrôle le GPU T4 et la version CUDA de PyTorch fournie par Colab ; il n'installe pas PyTorch sur le PC.

Le requirements.txt officiel contient OmegaConf, Pillow, einops, torchmcubes, Transformers, trimesh, rembg, huggingface-hub, imageio avec ffmpeg, Gradio, xatlas et moderngl. Il ne fixe pas PyTorch : le README demande de choisir la version PyTorch correspondant à la plateforme et à CUDA. Le runtime Colab fournit cette partie ; les autres paquets sont installés seulement dans le runtime temporaire.

Le script run.py est l'outil d'inférence en ligne de commande, et non le serveur web utilisé ici. Il prend une ou plusieurs images, peut choisir le périphérique, le modèle pré-entraîné, la taille de chunk, la résolution marching-cubes, le retrait de fond et le ratio du premier plan, le dossier de sortie, le format OBJ ou GLB, la cuisson de texture et le rendu vidéo. Son format par défaut est OBJ ; le notebook lance gradio_app.py, dont le code retourne dans l'ordre un OBJ puis un GLB.

## Démarrage pas à pas

1. Ouvrir tools/colab/triposr_server.ipynb dans Google Colab.
2. Dans Exécution, choisir Modifier le type d'exécution, puis T4 GPU. Les GPU gratuits ne sont pas garantis : le notebook arrête l'exécution si aucun T4 n'est détecté.
3. Lancer les cellules dans l'ordre. Elles vérifient le GPU, clonent le dépôt officiel si nécessaire, mettent à jour setuptools et installent son requirements.txt dans le runtime Colab.
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
- Le notebook est actuellement non testé sur Colab. Les commandes, le démarrage du GPU, la création effective du lien, le contrat Gradio réel et une génération de modèle restent à vérifier.

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
- Application Gradio et options de lancement : https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/gradio_app.py
- Inférence en ligne de commande : https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/run.py
- FAQ officielle Colab sur ressources non garanties et limites variables : https://research.google.com/colaboratory/faq.html
