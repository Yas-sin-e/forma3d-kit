# État du projet — Forma3D Studio

Dernière mise à jour : 2 novembre 2026.

## Étape 7 — fiabilité et qualité (en cours)

- Ajout d'une sonde `GET /health/provider` avec délai de 5 secondes. Elle ne renvoie que `ONLINE`, `OFFLINE` ou `UNCONFIGURED`, jamais la cible distante.
- L'interface vérifie le fournisseur au chargement puis toutes les 30 secondes. Hors ligne, la génération est bloquée et le bouton de secours ouvre un modèle réel de la galerie.
- Les conseils photo, la phrase d'approximation et la photo source éventuelle ont été ajoutés. Aucun nom de modèle `Chaise métal 01/02` n'a été changé.
- Le formulaire exige maintenant une catégorie (chaise, tabouret ou table d'appoint). Après une génération réussie, le modèle et sa photo source rejoignent la galerie dans le filtre choisi ; cette liste de session est en mémoire et se réinitialise au redémarrage.
- Le lancement local passe par `scripts/dev.ps1`, qui crée le venv s'il manque, lance pytest, démarre Uvicorn puis ouvre Edge.
- Les réglages facultatifs `FOREGROUND_RATIO` et `MC_RESOLUTION` ne sont validés qu'avec des noms et bornes tirés du contrat Gradio observé ; aucune plage n'est codée en dur.
- Historique : le 1 novembre, Edge/Colab a affiché « Échec : backend non attribué ». Le 2 novembre, l'étudiante a fourni le lien d'une session déjà active et accepté l'usage personnel de démonstration à ses risques. L'API locale a répondu `ONLINE`, puis une photo libre de tabouret a été traitée par l'application et a produit un GLB valide.
- Preuve de la génération de l'étape 7 : `stool-met-01.jpg`, catégorie `stool`, état final `DONE`, environ 105 s, GLB de 2 619 760 octets, validé GLB 2.0. Le viewer a rendu le modèle et affiché la photo source ainsi que le bouton de téléchargement. L'événement de téléchargement du navigateur n'a pas été confirmé ; le fichier GLB a bien été renvoyé et validé par l'application. La note de qualité visuelle appartient à l'étudiante.
- Contrôle après le lancement local : le script a terminé ses vérifications et l'API a répondu, mais `GET /health/provider` renvoie maintenant `OFFLINE`. Aucune nouvelle photo n'a été envoyée après ce contrôle. La galerie renvoie sept GLB, dont le résultat `stool-met-01` classé dans `stool`.
- L'étudiante a accepté l'usage du serveur pour une démonstration et un développement personnels, à ses risques, sans en faire un service de production. Aucun maintien en vie ni contournement des limites Colab n'est utilisé. La section Limites et la FAQ officielle restent applicables.
- Les tests de l'étape 7 passent : 57 réussis en 1,21 s, avec transports simulés et sans réseau fournisseur. `scripts/dev.ps1 -Port 8003` a terminé les tests et affiché l'API prête. `/health/provider` avait répondu `ONLINE` avant l'envoi, puis `OFFLINE` au contrôle suivant ; le lien actuellement configuré n'est donc pas joignable.
- La catégorie est requise pour chaque envoi ; la nouvelle génération apparaît dans le filtre choisi. Les comparaisons de 15 configurations restent en attente ; aucune génération qualité n'est présentée comme réalisée.

## Résumé de l'étape 6 (historique vérifié)

Sprint 1 v2 : le flux réel photo vers GLB est maintenant prouvé avec le serveur TripoSR officiel lancé dans Google Colab. Les cinq photos libres de droits ont été soumises au vrai endpoint POST /models de Forma3D ; chacune a atteint PENDING, RUNNING puis DONE. Les cinq fichiers téléchargés sont valides en GLB 2.0. Aucune génération ni aucun fichier n'est simulé.

L'US3, dont le critère est que l'application obtienne un vrai GLB par ce serveur, est satisfaite. Les essais antérieurs de Stable Fast 3D ont échoué et restent consignés séparément. Les appréciations bon/moyen/mauvais des cinq résultats visuels doivent être données par l'étudiante ; elles ne sont pas inférées ici.

La page de studio a été refaite en modules CSS/JavaScript sans framework, avec une palette sombre à fort contraste, une scène 3D centrale, un suivi sans pourcentage et les commandes caméra demandées. La galerie interroge une route bornée aux cinq vrais GLB locaux et ne présente aucun objet de remplacement. L'étape 7 a depuis ajouté un contrôle fournisseur, des photos sources autorisées et des réglages qualité validés dynamiquement.

## Fait et vérifié

- Les étapes 1 à 5 sont implémentées : API FastAPI, validation et stockage local, suivi de génération, viewer model-viewer, contrôles caméra et téléchargement.
- Le notebook Colab a installé TripoSR et ses dépendances sur un runtime Tesla T4, a lancé le serveur Gradio public et est resté actif pendant les essais.
- Le fournisseur a inspecté le contrat réel par view_api(). Les étapes observées sont /check_input_image, /preprocess et /generate. Le code utilise aussi les valeurs réelles du composant publiées dans client.config ; les valeurs example_input ne sont pas des valeurs par défaut.
- Le prétraitement applique les valeurs publiées par l'interface TripoSR : retrait de fond activé, ratio de premier plan 0,85 et résolution marching-cubes 256. La sortie GLB de generate est choisie après la sortie OBJ.
- L'application a renvoyé PENDING, RUNNING et DONE pour chacune des cinq photos. Les cinq résultats du dossier backend/data/feasibility-results/ passent le validateur local GLB 2.0.
- Une première génération de chair-bentwood.jpg a rencontré un délai d'écriture Gradio. Une relance unique a réussi en 215,0 s ; aucun échec n'a été présenté comme succès.
- Le viewer a déjà affiché un GLB effectivement produit par l'application ; rotation, déplacement, zoom et téléchargement ont été observés sur ce flux initial. Celui-ci utilisait les valeurs d'exemple basses avant la correction des valeurs par défaut. Les cinq nouveaux fichiers aux paramètres officiels ont été vérifiés côté API et sur disque ; l'activation d'Edge a échoué pendant cette dernière vérification visuelle, donc leur nouvel affichage dans Edge reste à revoir.
- Aucun entraînement, PyTorch, CUDA ni TripoSR local. Aucune dépendance n'a été ajoutée à backend/requirements.txt.
- Le frontend est maintenant séparé en fichiers de thème, composants, API, état, vues et orchestration. Le backend sert ces ressources sous /static/.
- La galerie locale vérifie le GLB 2.0, limite les chemins à cinq identifiants connus et indique clairement l'origine de chaque modèle.
- Le contrôle HTTP de l'instance locale existante a renvoyé 200 pour /, la feuille de thème et le module principal ; GET /models/gallery a renvoyé cinq entrées et un GLB a été servi en model/gltf-binary sans appeler TripoSR.
- Le rendu pixel par pixel et l'interaction dans Edge n'ont pas été validés ; cette vérification couvre le serveur, les ressources et le téléchargement seulement.

## Résultats réels — 21 octobre 2026

| Photo | Entrée (octets) | Durée | Résultat | GLB téléchargé (octets) | Version | Note visuelle |
|---|---:|---:|---|---:|---|---|
| stool-met-01.jpg | 150 163 | 83,1 s | DONE | 2 619 760 | GLB 2.0 | À noter par l'étudiante |
| chair-bentwood.jpg | 2 508 211 | 215,0 s (relance après délai) | DONE | 1 236 604 | GLB 2.0 | À noter par l'étudiante |
| chair-met-01.jpg | 131 046 | 99,0 s | DONE | 865 856 | GLB 2.0 | À noter par l'étudiante |
| chair-met-02.jpg | 80 266 | 204,0 s | DONE | 2 050 148 | GLB 2.0 | À noter par l'étudiante |
| side-table-met.jpg | 252 423 | 83,8 s | DONE | 1 035 632 | GLB 2.0 | À noter par l'étudiante |

Les tailles ont été mesurées sur les photos et GLB présents localement. Les durées correspondent au suivi PENDING/RUNNING/DONE par l'application, et non à une estimation du fournisseur. Les résultats sont ignorés par Git. Les notes qualitatives sont laissées à l'étudiante après examen de chaque modèle.

## Historique et limites

- Décision de l'étudiante : usage personnel de démonstration et de développement accepté à ses propres risques, sans prétention de service de production. Cette acceptation n'autorise ni maintien en vie, ni contournement de quota/limite, ni demande payante. Arrêt obligatoire si Colab exige une connexion, validation ou captcha. La [FAQ officielle Colab](https://research.google.com/colaboratory/faq.html), consultée le 1 novembre 2026, reste la référence des limites des runtimes gérés.

- Stable Fast 3D : cinq essais antérieurs sur des photos libres ont rencontré la même exception interne générique. Aucun GLB n'a été reçu de ces essais.
- Space Hugging Face officiel stabilityai/TripoSR : son état runtime empêchait la lecture de l'API à l'époque. L'adaptateur actuel vise le serveur Gradio officiel autonome, dont le contrat a ensuite été réellement lu.
- L'installation Colab a d'abord échoué dans torchmcubes, puis la commande de secours a échoué. Le notebook a été ajusté avec les outils de build du README torchmcubes et --no-build-isolation ; cette installation a ensuite réussi sur le runtime T4 Python 3.12.12. onnxruntime a été ajouté au runtime Colab et huggingface-hub fixé à 0.34.0 pour résoudre deux erreurs de démarrage. Rien de cela n'a modifié l'environnement local.
- Le journal des générations est en mémoire et disparaît quand FastAPI redémarre. Les GLB de faisabilité restent dans le dossier local ignoré par Git.
- Le lien Gradio utilisé lors de la génération est historique, public et sans authentification ; aucun lien utilisable n'est enregistré dans le dépôt. Les règles actuelles de Colab géré gratuit suspendent son redémarrage par notebook ; voir `docs/etapes/etape-06-colab.md`.
- Le GPU gratuit, sa disponibilité, sa durée et le temps d'inactivité ne sont pas garantis. Le modèle est une approximation visuelle, pas une reconstruction dimensionnelle pour fabriquer un meuble.
- Les droits des photos doivent être vérifiés indépendamment de la licence MIT du code et des poids pré-entraînés.

## Vérifications de code

- Les tests ciblés du fournisseur et du service passent : 20 tests sans réseau, avec client simulé.
- Avant l'étape 7, les 43 tests existants passaient. Après les nouveaux contrôles simulés, la suite complète passe : 55 tests en 1,49 s ; aucun test ne contacte un fournisseur distant.
- Les commits ont été poussés sur main. Le résultat de la CI déclenchée par le push n'est pas visible depuis cette session : le CLI gh est absent et la page publique ne peut pas lire ce dépôt privé. Consulter Actions dans GitHub avant d'annoncer la CI verte.
- Vérifier avant commit que backend/.env, les cinq GLB, les photos et le cahier des charges DOCX utilisateur restent hors de l'index Git.

## Prochaine action recommandée

Après validation d'un environnement d'inférence autorisé, relire son contrat `view_api()` et reprendre les essais qualité laissés en attente ; les étiquettes visuelles et la CI doivent ensuite être vérifiées séparément.
