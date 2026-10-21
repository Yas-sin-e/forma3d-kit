# Sprint 1 — Étape 6 : essais TripoSR et validation de l'application

## Objectif

Vérifier qu'une photo libre de droits de petit mobilier passe par Forma3D jusqu'à un vrai modèle GLB 2.0. Les essais utilisent exclusivement le modèle pré-entraîné officiel TripoSR. Aucun poids n'est entraîné, aucun modèle fictif n'est présenté et aucune image contenant une personne n'est envoyée.

## État final

Le serveur officiel TripoSR fonctionne dans un runtime Google Colab Tesla T4. Le contrat Gradio a été lu à l'exécution et le fournisseur a utilisé les paramètres réellement configurés dans l'interface. Le vrai endpoint POST /models de Forma3D a donné PENDING, RUNNING puis DONE pour cinq photos. Cinq fichiers GLB ont été téléchargés depuis l'application et passent le validateur GLB 2.0.

L'US3 est satisfaite au sens de son critère technique : l'application elle-même reçoit un vrai GLB via le serveur TripoSR. Les fichiers de résultats sont dans backend/data/feasibility-results/ ; ils sont locaux et ignorés par Git.

## Contrat réellement observé

Avec le client gradio_client 2.7.2, la signature installée de Client accepte src et token ; src peut être un identifiant ou l'URL complète d'un serveur Gradio. Un jeton Hugging Face n'est pas transmis à l'URL publique externe.

view_api() a réellement exposé les fonctions /check_input_image, /preprocess et /generate. L'application officielle enchaîne contrôle de l'image, prétraitement et génération. generate renvoie l'OBJ puis le GLB ; l'adaptateur sélectionne la sortie identifiée comme GLB.

view_api() donne notamment des example_input pour décrire les champs. Ceux-ci ne sont pas les valeurs initiales de l'interface. Le fournisseur lit donc client.config et les composants de l'application ; il a observé retrait de fond activé, ratio 0,85 et résolution marching-cubes 256. Cette correction évite de lancer une génération à la résolution d'exemple minimale.

## Résultats mesurés

| Photo libre | Taille d'entrée | Durée de l'application | États observés | Taille du GLB | Validation | Note qualité |
|---|---:|---:|---|---:|---|---|
| stool-met-01.jpg | 150 163 octets | 83,1 s | PENDING → RUNNING → DONE | 2 619 760 octets | GLB 2.0 valide | À remplir par l'étudiante |
| chair-bentwood.jpg | 2 508 211 octets | 215,0 s | PENDING → RUNNING → DONE | 1 236 604 octets | GLB 2.0 valide | À remplir par l'étudiante |
| chair-met-01.jpg | 131 046 octets | 99,0 s | PENDING → RUNNING → DONE | 865 856 octets | GLB 2.0 valide | À remplir par l'étudiante |
| chair-met-02.jpg | 80 266 octets | 204,0 s | PENDING → RUNNING → DONE | 2 050 148 octets | GLB 2.0 valide | À remplir par l'étudiante |
| side-table-met.jpg | 252 423 octets | 83,8 s | PENDING → RUNNING → DONE | 1 035 632 octets | GLB 2.0 valide | À remplir par l'étudiante |

Le premier appel sur chair-bentwood.jpg a échoué avec un délai d'écriture Gradio. Une seule relance a ensuite terminé en DONE et fourni le GLB indiqué. La première sortie basse résolution de cet objet n'est pas utilisée dans le tableau des résultats définitifs.

Aucun score bon/moyen/mauvais n'est rempli par le système : cette appréciation visuelle appartient à l'étudiante. L'image du modèle doit être jugée par comparaison avec sa photo et en faisant tourner le viewer.

## Vérification du viewer

Lors d'un essai antérieur via l'interface, un GLB réellement généré a été affiché. Le contrôle de rotation, le déplacement de la caméra, le zoom et le lien de téléchargement ont été observés. Cet affichage précédent utilisait les petites valeurs example_input de l'API ; il a révélé que le résultat était trop grossier pour juger les paramètres normaux.

Les cinq nouvelles générations utilisent les valeurs officielles 0,85 et 256 ; l'API a renvoyé DONE et leurs GLB téléchargés sont valides. Leur ouverture finale dans Edge n'a pas pu être confirmée pendant cette vérification, car l'outil de contrôle Windows n'a pas réussi à activer la fenêtre Edge. Ne pas confondre cette limite d'observation avec un échec de génération.

## Préparation et lancement Colab

Le notebook tools/colab/triposr_server.ipynb utilise le dépôt officiel VAST-AI-Research/TripoSR, son README, requirements.txt, gradio_app.py et run.py. Le runtime fournit PyTorch et CUDA ; aucun paquet lourd n'est installé sur le PC.

Les premiers échecs de torchmcubes ont été résolus en suivant son README de compilation : scikit-build-core, pybind11 et CMake, puis installation avec --no-build-isolation. Le démarrage officiel a ensuite signalé l'absence d'onnxruntime ; son installation dans Colab a corrigé cette erreur. Une incompatibilité de huggingface-hub a ensuite été corrigée dans le runtime avec la version 0.34.0. Le serveur Gradio a finalement démarré.

gradio_app.py expose les options --share, --port, --username et --password ; le port par défaut observé dans le code est 7860. Le lanceur n'active l'authentification que lorsque les deux paramètres username et password sont fournis. Le notebook passe --share, --port 7860 et --queuesize 1 sans identifiants : le lien est public et temporaire. Les instructions reproductibles et les limites figurent dans docs/etapes/etape-06-colab.md.

## Résultats antérieurs conservés

Stable Fast 3D a échoué sur cinq photos avec une exception interne Gradio non détaillée. Le Space Hugging Face hébergé de TripoSR était auparavant en RUNTIME_ERROR. Ces échecs restent historiques : ils ne changent pas les cinq succès obtenus avec le serveur autonome officiel.

## Fichiers, exécution et apprentissage

| Fichier | Rôle | Quand le lire ou l'utiliser |
|---|---|---|
| tools/colab/triposr_server.ipynb | Prépare les dépendances, vérifie le T4 et lance Gradio dans Colab | Avant une nouvelle session GPU ou une démonstration |
| backend/app/providers/huggingface.py | Lit view_api et client.config, suit la chaîne TripoSR et vérifie le GLB | À chaque génération distante |
| backend/app/services/generation_service.py | Enregistre les états et journalise les erreurs avec leur type et leur cause | Pour suivre une génération ou diagnostiquer un blocage |
| backend/tests/test_huggingface_provider.py | Simule le contrat afin de vérifier l'adaptateur sans réseau | Pendant pytest |
| backend/tests/test_generation_service.py | Vérifie les états et le masquage de secrets dans les journaux | Pendant pytest |
| backend/data/feasibility-inputs/ | Conserve localement les photos ouvertes retenues | Pour reproduire les essais autorisés |
| backend/data/feasibility-results/ | Conserve les cinq GLB réellement téléchargés et validés | Pour examiner ou présenter les modèles |
| docs/etapes/etape-06-colab.md | Donne le mode d'emploi du runtime et de ses limites | Avant de démarrer Colab |

## Limites

- Un GPU T4 gratuit n'est pas garanti. Disponibilité et durée du runtime dépendent de Colab.
- Le serveur est public et le lien temporaire cesse de fonctionner quand le runtime ou le processus s'arrête.
- Garder la cellule du serveur active pendant une démonstration.
- Envoyer uniquement des photos dont l'usage est autorisé, sans personne ni donnée personnelle.
- La licence MIT du projet TripoSR ne confère pas de droits sur les photos de tiers.
- La reconstruction est une approximation visuelle et ne garantit ni les dimensions ni une géométrie prête à fabriquer.
- Le registre applicatif des statuts disparaît au redémarrage ; les GLB de faisabilité locaux restent disponibles.

## Conclusion

La preuve technique US3 est obtenue : cinq photos ont traversé le backend Forma3D vers le serveur TripoSR et cinq GLB 2.0 ont été vérifiés. Les contrôles du viewer avaient été observés sur la première génération réelle, à résolution basse. Le nouvel affichage à résolution normale reste à revoir dans Edge ; les notes de qualité sont à compléter par l'étudiante. Le notebook et les résultats ne contiennent pas de lien Colab/Gradio utilisable ou de secret.