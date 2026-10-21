# Guide — serveur TripoSR dans Google Colab

Dernière vérification : 21 octobre 2026. Le notebook a été exécuté sur un runtime Google Colab Tesla T4 ; le serveur Gradio officiel a démarré et a produit cinq modèles utilisés par l'application Forma3D.

## Ce que fait le notebook

tools/colab/triposr_server.ipynb clone le dépôt officiel VAST-AI-Research/TripoSR, installe ses dépendances dans l'environnement temporaire de Colab et lance gradio_app.py. Il ne configure ni PyTorch, ni CUDA, ni TripoSR sur l'ordinateur local. Le modèle est pré-entraîné ; le parcours n'entraîne rien.

Le runtime testé a fourni Python 3.12.12, Tesla T4 et PyTorch/CUDA 12.6. L'installation officielle de requirements.txt a d'abord échoué à torchmcubes. Le README de torchmcubes a servi à compiler son extension en installant scikit-build-core, pybind11 et CMake, puis en utilisant --no-build-isolation. Cette installation a réussi.

Le premier lancement a révélé que le runtime n'avait pas onnxruntime ; son installation dans Colab a résolu l'erreur. Une incompatibilité de huggingface-hub a ensuite été corrigée par une version 0.34.0 dans le même runtime. Ces corrections sont décrites dans le notebook. Aucun changement n'a été fait aux dépendances du backend local.

## Contrat et résultats vérifiés

Le code du dépôt officiel a été consulté dans README.md, requirements.txt, gradio_app.py et run.py. Le contrat réel lu avec view_api() expose /check_input_image, /preprocess et /generate. generate renvoie les sorties OBJ et GLB dans cet ordre ; le fournisseur conserve le GLB.

Le notebook démarre gradio_app.py avec --share, --port 7860 et --queuesize 1. Le code officiel accepte --share, --port, --username et --password, et n'ajoute l'authentification que si les deux identifiants sont fournis. Le notebook n'en fournit pas : quiconque connaît le lien public temporaire peut appeler le serveur.

La chaîne complète a été utilisée par Forma3D : cinq photos libres ont atteint PENDING, RUNNING puis DONE via POST /models. Les cinq GLB téléchargés sont valides au format 2.0. Mesures et photos sont consignées dans docs/etapes/etape-06.md. Aucune URL temporaire n'est inscrite dans ce guide ni dans le notebook versionné.

## Reprendre une session

1. Ouvrir tools/colab/triposr_server.ipynb dans Google Colab.
2. Dans Exécution, choisir Modifier le type d'exécution puis T4 GPU, si Colab le propose.
3. Exécuter les cellules dans l'ordre. Le notebook vérifie le GPU, clone le dépôt officiel, installe les dépendances puis démarre le serveur.
4. Si une cellule échoue, conserver son erreur complète et ne pas prétendre que le serveur est disponible. Les problèmes de torchmcubes, onnxruntime et huggingface-hub sont explicitement traités dans les cellules du notebook.
5. Copier le nouveau lien affiché par Gradio uniquement dans la configuration locale backend/.env. Le lien n'est pas permanent ; ne pas le coller dans un fichier versionné ou un message public.
6. Garder la cellule de démarrage en cours pendant les générations et la démonstration. Arrêter la cellule ou perdre le runtime coupe le serveur.
7. Avant de versionner le notebook après une session, effacer ses sorties et vérifier qu'aucun lien temporaire n'y reste enregistré.

## Limites et données

- L'accès gratuit à un GPU T4 n'est jamais garanti ; Colab décide de la disponibilité, des quotas, des périodes d'inactivité et de la durée de session.
- Le lien Gradio est public et temporaire. Le serveur configuré ici n'a pas d'authentification.
- Une démonstration nécessite que la session Colab, le GPU et la cellule du serveur restent actifs.
- N'envoyer que des photos libres de droits, sans personne ni donnée personnelle. Le serveur public reçoit les images.
- La licence MIT couvre le code et les poids publiés par TripoSR ; elle ne transfère pas les droits d'une image.
- La reconstruction est visuelle ; elle ne garantit pas les dimensions ou l'aptitude à fabriquer le meuble.
- Le statut du test est réel : installation, démarrage, lecture API, cinq générations et validation GLB ont été observés le 21 octobre 2026. Cela ne garantit pas que le service public temporaire soit encore actif lors d'une prochaine session.