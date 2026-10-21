# État du projet — Forma3D Studio

Dernière mise à jour : 21 octobre 2026.

## Résumé

Sprint 1 v2 : le flux réel photo vers GLB est maintenant prouvé avec le serveur TripoSR officiel lancé dans Google Colab. Les cinq photos libres de droits ont été soumises au vrai endpoint POST /models de Forma3D ; chacune a atteint PENDING, RUNNING puis DONE. Les cinq fichiers téléchargés sont valides en GLB 2.0. Aucune génération ni aucun fichier n'est simulé.

L'US3, dont le critère est que l'application obtienne un vrai GLB par ce serveur, est satisfaite. Les essais antérieurs de Stable Fast 3D ont échoué et restent consignés séparément. Les appréciations bon/moyen/mauvais des cinq résultats visuels doivent être données par l'étudiante ; elles ne sont pas inférées ici.

## Fait et vérifié

- Les étapes 1 à 5 sont implémentées : API FastAPI, validation et stockage local, suivi de génération, viewer model-viewer, contrôles caméra et téléchargement.
- Le notebook Colab a installé TripoSR et ses dépendances sur un runtime Tesla T4, a lancé le serveur Gradio public et est resté actif pendant les essais.
- Le fournisseur a inspecté le contrat réel par view_api(). Les étapes observées sont /check_input_image, /preprocess et /generate. Le code utilise aussi les valeurs réelles du composant publiées dans client.config ; les valeurs example_input ne sont pas des valeurs par défaut.
- Le prétraitement applique les valeurs publiées par l'interface TripoSR : retrait de fond activé, ratio de premier plan 0,85 et résolution marching-cubes 256. La sortie GLB de generate est choisie après la sortie OBJ.
- L'application a renvoyé PENDING, RUNNING et DONE pour chacune des cinq photos. Les cinq résultats du dossier backend/data/feasibility-results/ passent le validateur local GLB 2.0.
- Une première génération de chair-bentwood.jpg a rencontré un délai d'écriture Gradio. Une relance unique a réussi en 215,0 s ; aucun échec n'a été présenté comme succès.
- Le viewer a déjà affiché un GLB effectivement produit par l'application ; rotation, déplacement, zoom et téléchargement ont été observés sur ce flux initial. Celui-ci utilisait les valeurs d'exemple basses avant la correction des valeurs par défaut. Les cinq nouveaux fichiers aux paramètres officiels ont été vérifiés côté API et sur disque ; l'activation d'Edge a échoué pendant cette dernière vérification visuelle, donc leur nouvel affichage dans Edge reste à revoir.
- Aucun entraînement, PyTorch, CUDA ni TripoSR local. Aucune dépendance n'a été ajoutée à backend/requirements.txt.

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

- Stable Fast 3D : cinq essais antérieurs sur des photos libres ont rencontré la même exception interne générique. Aucun GLB n'a été reçu de ces essais.
- Space Hugging Face officiel stabilityai/TripoSR : son état runtime empêchait la lecture de l'API à l'époque. L'adaptateur actuel vise le serveur Gradio officiel autonome, dont le contrat a ensuite été réellement lu.
- L'installation Colab a d'abord échoué dans torchmcubes, puis la commande de secours a échoué. Le notebook a été ajusté avec les outils de build du README torchmcubes et --no-build-isolation ; cette installation a ensuite réussi sur le runtime T4 Python 3.12.12. onnxruntime a été ajouté au runtime Colab et huggingface-hub fixé à 0.34.0 pour résoudre deux erreurs de démarrage. Rien de cela n'a modifié l'environnement local.
- Le journal des générations est en mémoire et disparaît quand FastAPI redémarre. Les GLB de faisabilité restent dans le dossier local ignoré par Git.
- Le lien Gradio est public, sans authentification, temporaire et absent du notebook versionné et des documents. Garder le runtime et la cellule du serveur actifs pendant une démonstration.
- Le GPU gratuit, sa disponibilité, sa durée et le temps d'inactivité ne sont pas garantis. Le modèle est une approximation visuelle, pas une reconstruction dimensionnelle pour fabriquer un meuble.
- Les droits des photos doivent être vérifiés indépendamment de la licence MIT du code et des poids pré-entraînés.

## Vérifications de code

- Les tests ciblés du fournisseur et du service passent : 20 tests sans réseau, avec client simulé.
- La suite pytest complète passe : 38 tests en 1,12 s. Elle a été lancée avec l'accès local nécessaire aux tests TestClient ; les tests ne contactent aucun fournisseur distant.
- La CI GitHub après le prochain push reste à vérifier. Ne pas annoncer une CI verte avant l'observation de son résultat.
- Vérifier avant commit que backend/.env, les cinq GLB, les photos et le cahier des charges DOCX utilisateur restent hors de l'index Git.

## Prochaine action recommandée

Attribuer une note bon, moyen ou mauvais à chacun des cinq GLB après les avoir examinés, puis relire le diff et vérifier la CI après push.