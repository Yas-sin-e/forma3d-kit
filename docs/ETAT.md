# État du projet — Forma3D Studio

Dernière mise à jour : 10 novembre 2026.

## Avenant au cahier des charges v1.0

Les Sprints 3 (comptes publics) et 4 (vitrine/catalogue public) sont retirés du périmètre. L'objectif prioritaire est un module 3D intégrable partout, composé d'une API avec clé et d'un widget ; le Studio est la console privée mono-propriétaire. Limite connue : le Studio n'a pas d'authentification, donc usage local ou démonstration uniquement ; ne pas l'exposer publiquement tel quel.

## Sprint 5 — Module intégrable (actif)

- Objectif : exposer de façon contrôlée les modèles terminés par une API avec clé et un widget intégrable.
- Livrable vérifiable : modèle activable individuellement, clé révocable non stockée en clair, routes versionnées authentifiées, iframe/widget intégrable et guide d'intégration.
- Étapes 0 et 5a (étape 13) terminées le 11 novembre 2026. Prochaine sous-étape : 5b / étape 14.
- Le Sprint 6 reste non démarré et nécessite un OK explicite.

## Sprint 2 — Qualité et fiabilité (terminé)

- Objectif : rendre l'historique persistant après redémarrage, gérer les catégories partagées et préparer les photos avec des outils légers.
- Livrable vérifiable de l'étape 8 : un GLB terminé et ses métadonnées sont encore consultables après redémarrage du backend, et la galerie les lit depuis SQLite.
- Livrable vérifiable de l'étape 9 : CRUD des catégories persisté et utilisé par le formulaire et les filtres de galerie. Livrable vérifiable de l'étape 10 : une copie carrée préparée est envoyée au fournisseur, avec avertissement de netteté/taille, tandis que l'original reste intact.
- Fichier de suivi : `docs/ETAT.md` ; structure expliquée dans `docs/STRUCTURE.md` et détails dans `docs/etapes/etape-08.md`, `etape-09.md` et `etape-10.md`.
- Étape 8 : SQLite local derrière `GenerationRepository`, catégories initiales, historique relu par la galerie et récupération des travaux interrompus sont implémentés. Chemin fixe : `backend/data/forma3d.sqlite3` ; aucun changement à `config.py` ou `.env.example`. Suite complète : 61 tests réussis en 2,52 s ; tests isolés du fournisseur et de `backend/.env`.
- Étape 9a : routes GET/POST/PATCH/DELETE `/categories`, validations de slug/libellé et gestion de conflit ; suppression utilisée refusée en 409. Une catégorie inactive n'est plus proposée aux uploads, mais reste liée aux générations existantes. Commit `cb82ece` ; suite complète : 68 tests réussis.
- Étape 9b : écran de gestion, formulaire et filtres de galerie alimentés par l'API ; les erreurs API sont présentées dans l'interface. Interface non vérifiée manuellement dans le navigateur durant cette session. Commit `1c3f1ac` ; suite complète : 68 tests réussis.
- Étape 10 : `ImagePreparer` s'appuie sur Pillow 13.0.0, ajouté à `backend/requirements.txt` (Pillow n'était pas installé dans le venv avant cette étape). La copie envoyée est carrée, conserve 12 % de marge, a un côté de sortie d'au moins 512 px et utilise LANCZOS ; la photo source n'est pas modifiée. Les images petites/floues reçoivent un avertissement non bloquant. En cas de décodage impossible, le service conserve le comportement existant et envoie l'original avec un avertissement. Aucune dépendance `rembg`, OpenCV ou PyTorch n'a été ajoutée.
- Vérification finale étape 10 : 74 tests pytest réussis, sans réseau fournisseur, avec `backend/.env` protégé contre la lecture. Les tests couvrent les avertissements, le cadrage, la conservation de la source, la migration SQLite, l'envoi de la copie préparée et le contrat HTTP/UI de l'avertissement. Pas de test de génération réelle ni de vérification visuelle navigateur pour cette étape. Sprints 3 et 4 retirés du périmètre.
- Étape 11 (refonte UX du Studio, avant le Sprint 5) : navigation hash et cinq pages du Studio ajoutées au frontend uniquement. Aucun endpoint, modèle, fournisseur ou configuration n'a changé. Vérification finale : suite pytest complète de 75 tests, sans fournisseur distant ; 15 fichiers JavaScript vérifiés syntaxiquement. Pas de vérification visuelle navigateur. Commit et push sur `main`.
- Le choix du fournisseur et du modèle reste inchangé. `backend/.env` n'est ni lu ni modifié. Toute base de données prévue sera locale, dans `backend/data/`, ignorée par Git.

### Étape 8 — SQLite et historique persistant (Sprint 2)

- La persistance utilise le module `sqlite3` standard, derrière l'interface `GenerationRepository`. Les catégories `chair`, `stool` et `side-table` sont créées au premier démarrage sans remplacer une ligne existante.
- Le chemin est fixe : `backend/data/forma3d.sqlite3`. Il n'est donc pas configurable ; `config.py` et `.env.example` restent inchangés. `.gitignore` couvre le dossier et les extensions SQLite.
- Chaque opération du dépôt ouvre et ferme sa propre connexion. Cela évite de partager une connexion SQLite entre les requêtes HTTP et la tâche de génération exécutée en arrière-plan ; aucune transaction ne reste ouverte pendant l'appel au fournisseur.
- Au démarrage, les générations restées `PENDING` ou `RUNNING` sont marquées `FAILED` avec le message « Génération interrompue au redémarrage du serveur. »
- `GET /models/gallery`, défini dans `backend/app/routers/models.py`, garde les modèles de démonstration puis ajoute les générations `DONE` retournées par `GenerationService.list_completed_generations()`. Le service consulte SQLite et filtre les entrées dont le GLB ou la photo a disparu ; le format API et le viewer restent inchangés.
- Le guide de conception du stockage est `docs/STOCKAGE.md` ; l'explication pédagogique et le test de persistance sont dans `docs/etapes/etape-08.md`.
- Aucun appel fournisseur n'est fait par les tests. La preuve de persistance emploie un fournisseur et un GLB minimal de test, qui ne sont pas un résultat réel de génération.
- La suite complète a passé 61 tests en 2,52 s. Elle a été lancée avec `HF_SPACE_ID` vide et un garde-fou qui refuse le chargement de `.env` à la racine ou dans `backend/`, tout en laissant le test de configuration lire ses `.env` temporaires. Le bac à sable bloquait les sockets locales de FastAPI `TestClient` ; pytest a donc été exécuté avec l'autorisation requise pour cette vérification. Aucun fournisseur distant n'a été appelé.
- Vérification visuelle dans le navigateur local sur le port 8012, processus lancé avec `PYTHON_DOTENV_DISABLED=1` et `HF_SPACE_ID` vide : badge « Serveur 3D : hors ligne », bouton de génération désactivé, cinq modèles de démonstration présents ; le clic sur « Chaise en bois cintré » a affiché le viewer, sa photo source et le lien de téléchargement. Cette galerie est celle des résultats de faisabilité, pas une nouvelle génération ; aucun appel fournisseur n'a eu lieu. Edge n'était pas accessible par le pilote de navigateur, la vérification a donc été faite dans le navigateur intégré.
- `git check-ignore -v` confirme que `backend/data/forma3d.sqlite3` et `backend/data/probe.db` sont ignorés par la règle `backend/data/`.

### Étape 9 — Catégories partagées (Sprint 2)

- `backend/app/services/category_service.py` applique les règles métier ; `backend/app/routers/categories.py` expose la liste et le CRUD. Le dépôt SQLite est la source de vérité. Les doublons de slug et les libellés vides sont refusés avec un message lisible.
- La suppression d'une catégorie référencée par une génération renvoie HTTP 409 ; une catégorie inutilisée peut être supprimée. Désactiver une catégorie la retire des choix de nouvel upload, sans retirer ses anciens modèles de l'historique ni de la galerie.
- `frontend/js/views/categories.js` fournit l'écran de gestion ; `uploader.js` reçoit les catégories actives ; `gallery.js` charge les catégories pour filtrer les modèles. Vérification automatique : la suite complète a réussi après 9a et 9b (68 tests à chaque commit). Pas de vérification manuelle navigateur durant la finalisation.

### Étape 10 — Préparation locale de la photo (Sprint 2)

- `backend/app/services/image_preparer.py` utilise Pillow, sans modèle IA ni dépendance lourde. La photo d'origine reste dans `backend/storage/images/` et sert à l'aperçu ; seul un PNG carré temporaire préparé est transmis au fournisseur.
- Le préparateur ajoute une marge de 12 %, agrandit la sortie à 512 px minimum et émet un avertissement si un côté source est inférieur à 512 px ou si la mesure locale des contours signale un manque de netteté. Ces avertissements ne bloquent pas la tâche. Si Pillow ne peut pas décoder le fichier, l'original est utilisé avec un avertissement.
- Le champ `image_warning` est persisté dans SQLite, ajouté par migration non destructive, retourné par les réponses de génération et affiché dans le panneau de suivi avec un conseil photo.
- Vérifications : 74 tests passent via pytest avec fournisseurs simulés. Aucune photo réelle n'a été générée avec le service 3D dans cette étape ; le navigateur n'a pas été piloté et l'apparence de l'avertissement reste à vérifier manuellement.

## Étape 11 — Refonte UX de la navigation (avant le Sprint 5)

- `frontend/index.html` ne contient plus qu'une coque persistante ; `frontend/js/router.js` résout `#/creer`, `#/modeles`, `#/modeles/{id}`, `#/categories` et `#/exemples`, suit Précédent/Suivant via `hashchange`, met à jour le titre et le lien actif, puis place le focus sur le titre de page.
- `frontend/js/pages/` contient un module par page. Mes modèles filtre les générations UUID provenant de l'API galerie ; Exemples affiche les cinq modèles de démonstration. Les deux vues utilisent les catégories retournées par l'API.
- La fiche réutilise les endpoints existants de galerie, état, téléchargement et photo source. L'API ne communique pas la durée : la page affiche « Non communiquée » au lieu de calculer ou inventer une valeur. Aucun nouvel endpoint backend n'était nécessaire.
- L'en-tête conserve le badge santé, le menu devient repliable sous 640 px, les erreurs courantes sont formulées pour la propriétaire et les informations Colab/.env sont uniquement dans les détails techniques repliables de la page Créer.
- Vérification automatisée : `backend/tests/test_frontend.py` (5 tests ciblés), suite complète (75 tests), puis analyse syntaxique Node.js des 15 modules JavaScript. Aucun parcours interactif navigateur ni génération réelle n'a été fait.
- À vérifier manuellement : routes et historique Précédent/Suivant ; menu actif et burger ; filtres de Mes modèles et Exemples ; création/confirmation de suppression des catégories ; fiche inconnue ; photo source et téléchargement ; affichage à 360 px et 1440 px.

## Étape 11b — Refonte du layout de Créer (frontend uniquement)

- Objectif : rendre le parcours Photo → Création → Résultat visible d'un coup d'œil, puis afficher la carte d'entrée, le viewer et le suivi en lignes compactes.
- `frontend/js/pages/create.js` présente le stepper informatif, la carte unique Photo et catégorie, la ligne hors service et les détails repliables. `frontend/js/views/uploader.js` actualise l'explication visible du bouton désactivé selon la photo, la catégorie, le serveur ou l'état occupé. `frontend/js/views/progress.js` garde les cinq états et rend explicites les étapes à faire, actives, terminées ou en échec. `frontend/css/components.css` règle la grille stretch, les hauteurs adaptatives, les seuils 1024/640 px et le défilement horizontal contenu du suivi mobile.
- Aucun code d'application backend, fournisseur 3D, route API ou fichier local `.env` n'a été modifié. Le Sprint 5 est actif depuis le 10 novembre 2026.
- Vérification : 5 tests ciblés de `backend/tests/test_frontend.py`, suite complète de 83 tests réussie en 2,65 s, `node --check` sur les modules JavaScript et `git diff --check`. Les tests ne contactent aucun fournisseur.
- Non vérifié : rendu visuel et défilement réel à 1366×768, 1920×1080, 360 px, tabulation et lecteur d'écran. Aucun navigateur n'a été piloté conformément à la consigne.
- Guide pédagogique : `docs/etapes/etape-11b.md`. Le Sprint 5 est actif depuis le 10 novembre 2026.

## Étape 12 — Import GLB et liste unifiée (terminée avant le Sprint 5)

- Objectif : permettre à la propriétaire d'ajouter un GLB local ou de copier un exemple dans la bibliothèque, avec une origine visible et honnête. Le Sprint 2 reste terminé ; l'étape 12 a préparé la bibliothèque avant le Sprint 5.
- `POST /models/import` vérifie l'extension `.glb`, la taille et la structure GLB 2.0, puis exige une catégorie active. `MAX_GLB_UPLOAD_MB` est configurable dans `.env.example` (30 Mo par défaut ; 1 à 512 Mo). Le nom stocké est un UUID serveur et un fichier existant n'est pas écrasé.
- `POST /models/examples/{example_id}/copy` copie uniquement un GLB de la liste d'exemples autorisés. Les deux routes créent un état `DONE` dans SQLite et un fichier dans `backend/storage/models/`.
- La migration SQLite ajoute `origin` avec `generated` pour les anciennes lignes ; les nouveaux objets ont `generated`, `imported` ou `example`. Les imports/copies n'ont ni photo source ni durée de génération. Le dépôt les relit malgré l'absence de photo ; la galerie et la fiche affichent l'origine.
- `#/modeles` propose l'import, un état vide avec les deux actions attendues, les filtres actifs de l'API, et la date/origine sur les cartes. `#/exemples` permet de choisir une catégorie avant la copie. La fiche détaille l'origine ; l'aperçu local de Créer porte maintenant le libellé « Aperçu d’un fichier GLB (sans enregistrer) ».
- Vérification : suite complète pytest, 83 tests réussis en 5,44 s ; les 31 tests ciblés correspondants avaient également réussi. Node `--check` a accepté les modules JavaScript et `git diff --check` n'a trouvé aucune erreur d'espacement. Les tests utilisent SQLite temporaire et un GLB minimal construit uniquement pour vérifier le format ; aucun fournisseur distant n'a été appelé.
- Non vérifié : navigation et formulaire dans un vrai navigateur, import d'un GLB réel depuis le poste, affichage visuel du nouveau modèle, fonctionnement à 360 px et CI GitHub. Le fournisseur 3D et le modèle choisi n'ont pas été modifiés. `backend/.env` n'a pas été consulté ni modifié.
- Suivi pédagogique : `docs/etapes/etape-12.md`; détail de persistance : `docs/STOCKAGE.md`; structure des fichiers : `docs/STRUCTURE.md`.

## Étape 13 — Sprint 5a : identifiant public et activation

- Chaque génération terminée, import et exemple copié possède un UUID public de version 4, attribué lors de la fin ou de la migration. L'indicateur embed_enabled est désactivé par défaut.
- La migration SQLite ajoute public_id et embed_enabled sans reconstruire ni perdre les lignes existantes. Elle attribue une seule fois un UUID4 aux lignes DONE existantes et conserve ensuite cet identifiant.
- PATCH /models/{id}/integration permet d'activer ou désactiver un modèle DONE dont le GLB existe. La fiche du modèle du Studio expose ce bouton uniquement aux modèles persistés.
- GET /public/models/{public_id} et GET /public/models/{public_id}/glb répondent 404 tant que le modèle n'est pas explicitement activé. Le JSON public ne révèle ni identifiant interne, ni chemin local, ni photo source.
- Les exemples fixes de la galerie restent inactivables ; leur copie dans Mes modèles reçoit un UUID public désactivé, comme un import ou une génération.
- Vérification : 87 tests pytest réussis en 4,02 s avec HF_SPACE_ID vide, dotenv désactivé et accès localhost autorisé pour TestClient ; tous les modules JavaScript passent node --check ; git diff --check passe. Aucun fournisseur n'a été appelé.
- Non vérifié : parcours visuel dans un navigateur et génération 3D réelle. Le Studio n'a pas d'authentification ; il reste réservé au local ou à une démonstration et ne doit pas être exposé publiquement tel quel.
- Guide pédagogique : docs/etapes/etape-13.md. Aucun fournisseur, modèle, dépendance ou variable d'environnement n'a changé.

## Sprint 1 — terminé (état documenté au 3 novembre)

L'étudiante considère le Sprint 1 terminé. Elle prend en charge elle-même la vérification de la CI GitHub ; celle-ci n'est pas déclarée verte ici.

### Étape 7 — fiabilité et qualité

- Ajout d'une sonde `GET /health/provider` avec délai de 5 secondes. Elle ne renvoie que `ONLINE`, `OFFLINE` ou `UNCONFIGURED`, jamais la cible distante.
- L'interface vérifie le fournisseur au chargement puis toutes les 30 secondes. Hors ligne, la génération est bloquée et le bouton de secours ouvre un modèle réel de la galerie.
- Les conseils photo, la phrase d'approximation et la photo source éventuelle ont été ajoutés. Aucun nom de modèle `Chaise métal 01/02` n'a été changé.
- Le formulaire exige maintenant une catégorie (chaise, tabouret ou table d'appoint). Après une génération réussie, le modèle et sa photo source rejoignent la galerie dans le filtre choisi. À l'étape 7, cette liste était en mémoire ; l'étape 8 la persiste désormais dans SQLite.
- Le lancement local passe par `scripts/dev.ps1`, qui crée le venv s'il manque, lance pytest, démarre Uvicorn puis ouvre Edge.
- Les réglages facultatifs `FOREGROUND_RATIO` et `MC_RESOLUTION` ne sont validés qu'avec des noms et bornes tirés du contrat Gradio observé ; aucune plage n'est codée en dur.
- Historique : le 1 novembre, Edge/Colab a affiché « Échec : backend non attribué ». Le 2 novembre, l'étudiante a fourni le lien d'une session déjà active et accepté l'usage personnel de démonstration à ses risques. L'API locale a répondu `ONLINE`, puis une photo libre de tabouret a été traitée par l'application et a produit un GLB valide.
- Preuve de la génération de l'étape 7 : `stool-met-01.jpg`, catégorie `stool`, état final `DONE`, environ 105 s, GLB de 2 619 760 octets, validé GLB 2.0. Le viewer a rendu le modèle et affiché la photo source ainsi que le bouton de téléchargement. L'événement de téléchargement du navigateur n'a pas été confirmé ; le fichier GLB a bien été renvoyé et validé par l'application. La note de qualité visuelle appartient à l'étudiante.
- Contrôle après le lancement local : le script a terminé ses vérifications et l'API a répondu, mais `GET /health/provider` renvoie maintenant `OFFLINE`. Aucune nouvelle photo n'a été envoyée après ce contrôle. La galerie renvoie sept GLB, dont le résultat `stool-met-01` classé dans `stool`.
- L'étudiante a accepté l'usage du serveur pour une démonstration et un développement personnels, à ses risques, sans en faire un service de production. Aucun maintien en vie ni contournement des limites Colab n'est utilisé. La section Limites et la FAQ officielle restent applicables.
- Les tests de l'étape 7 passent : 57 réussis en 1,21 s, avec transports simulés et sans réseau fournisseur. `scripts/dev.ps1 -Port 8003` a terminé les tests et affiché l'API prête. `/health/provider` avait répondu `ONLINE` avant l'envoi, puis `OFFLINE` au contrôle suivant ; le lien actuellement configuré n'est donc pas joignable.
- La catégorie est requise pour chaque envoi ; la nouvelle génération apparaît dans le filtre choisi. Les comparaisons de 15 configurations restent en attente ; aucune génération qualité n'est présentée comme réalisée.
- Présentation du studio compactée : conseils photo repliables, panneau d'entrée plus étroit sur grand écran, viewer limité à 70 vh, miniature source agrandissable, barre caméra flottante et galerie horizontale de vignettes sélectionnables au clic ou au clavier. Les noms existants, dont « Chaise métal 01 » et « Chaise métal 02 », sont conservés.
- Éclairage du viewer réglé avec les attributs documentés pour model-viewer 4.4.0 (`environment-image`, `tone-mapping`, `exposure`, `shadow-intensity`, `shadow-softness`). La documentation officielle décrit le tonemapping Neutral comme adapté à la fidélité des couleurs e-commerce : [documentation v4.4.0](https://raw.githubusercontent.com/google/model-viewer/v4.4.0/packages/modelviewer.dev/data/docs.json), [exemple éclairage et environnement](https://modelviewer.dev/examples/lightingandenv/). La valeur d'exposition est un réglage visuel à réévaluer après comparaison sur plusieurs modèles.
- Vérification visuelle locale sans fournisseur : le processus Uvicorn de test a reçu `HF_SPACE_ID` vide par variable d'environnement, sans lecture, modification ni affichage de `backend/.env`. La page a affiché « Serveur 3D : hors ligne » et désactivé la génération. Dans le navigateur, un GLB existant « Chaise métal 01 » s'est chargé dans le viewer ; la miniature de la photo source était visible et son clic a ouvert la photo en grand ; la galerie apparaissait en bande horizontale avec ses cinq modèles. Le rendu paraissait clair et les tons bruns visibles, sans comparaison côte à côte avec l'ancien éclairage. La largeur réelle de 360 px n'a pas été vérifiée visuellement ; aucune génération ni requête au fournisseur n'a été lancée.

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
- Avant l'étape 8, le journal des générations était en mémoire et disparaissait au redémarrage ; il est maintenant persisté dans SQLite. Les GLB de faisabilité et la base restent dans les dossiers locaux ignorés par Git.
- Le lien Gradio utilisé lors de la génération est historique, public et sans authentification ; aucun lien utilisable n'est enregistré dans le dépôt. Les règles actuelles de Colab géré gratuit suspendent son redémarrage par notebook ; voir `docs/etapes/etape-06-colab.md`.
- Le GPU gratuit, sa disponibilité, sa durée et le temps d'inactivité ne sont pas garantis. Le modèle est une approximation visuelle, pas une reconstruction dimensionnelle pour fabriquer un meuble.
- Les droits des photos doivent être vérifiés indépendamment de la licence MIT du code et des poids pré-entraînés.

## Vérifications de code

- Les tests ciblés du fournisseur et du service passent : 20 tests sans réseau, avec client simulé.
- Avant l'étape 7, les 43 tests existants passaient. Après les nouveaux contrôles simulés, la suite complète passe : 55 tests en 1,49 s ; aucun test ne contacte un fournisseur distant.
- Les commits ont été poussés sur main. Le résultat de la CI déclenchée par le push n'est pas visible depuis cette session : le CLI gh est absent et la page publique ne peut pas lire ce dépôt privé. Consulter Actions dans GitHub avant d'annoncer la CI verte.
- Vérifier avant commit que backend/.env, les cinq GLB, les photos et le cahier des charges DOCX utilisateur restent hors de l'index Git.

## Prochaine action recommandée

Continuer avec l'étape 14 (Sprint 5b) : clés API affichées une seule fois, empreinte SHA-256 persistée et révocation ; ne jamais stocker ni journaliser une clé en clair. La CI GitHub reste à vérifier par l'étudiante.
