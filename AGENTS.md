# SaaS 3D pour l'e-commerce — Instructions permanentes du projet

## Mission
Forma3D Studio aide un vendeur à partir d'une photo de produit pour obtenir un modèle 3D interactif. Le SaaS complet prévoit trois composants :
1. Le service API : génère et conserve le modèle.
2. Le widget intégrable : affiche le modèle dans une boutique existante.
3. La boutique vitrine : démontre le parcours dans un catalogue de produits.

## Contraintes décidées par l'étudiante
1. 100 % gratuit : aucune API payante, carte bancaire ou abonnement.
2. Aucun entraînement : modèles image-vers-3D pré-entraînés uniquement.
3. Projet de soutenance : chaque fichier et chaque dossier doivent être compréhensibles.
4. Répondre toujours en français ; code, noms de fichiers et commandes en anglais.
5. Signaler clairement les quotas, files d'attente, périodes de veille et instabilités des offres gratuites.

## Règle d'explication de chaque fichier et dossier
Pour chaque fichier ou dossier créé :
1. Ajouter une ligne à docs/STRUCTURE.md : chemin, rôle, raison du choix et moment d'utilisation.
2. Ajouter un commentaire d'en-tête en français dans chaque fichier de code, indiquant son rôle et son exécution.
3. Avant d'écrire du code, annoncer la liste des fichiers et leur intérêt, puis attendre l'accord de l'étudiante.

## Découpage en six sprints de deux semaines
1. De la photo au modèle 3D — terminé (contrôle CI GitHub laissé à l'étudiante).
2. Qualité et fiabilité : qualité d'image, arrière-plan, base de données, historique — sprint actif depuis le 9 novembre 2026.
3. Comptes vendeurs et produits.
4. Boutique vitrine : catalogue et fiches produits 3D.
5. Intégration : widget, code à copier, API avec clé.
6. Finalisation : tests E2E, déploiement gratuit, soutenance.

Ne jamais passer à une étape ou à un sprint suivant sans « OK » explicite.
Avant chaque étape, rappeler l'objectif et le livrable vérifiable.

## Sprint 1 — périmètre essentiel
État : terminé par décision de l'étudiante, sauf la vérification de la CI GitHub, qu'elle traite elle-même.

Objectif : le vendeur envoie une photo, obtient un GLB via un fournisseur gratuit de modèle pré-entraîné, l'examine dans un viewer et peut le télécharger.

Étapes, une à la fois :
1. Structure, Git, premier test GET /health et documentation de structure.
2. UploadValidator et POST /models : JPG, PNG ou WebP, 10 Mo maximum, avec tests.
3. Interface Image3DProvider et fournisseur Hugging Face ; découvrir d'abord l'API réelle avec Client(space).view_api().
4. GenerationService, stockage local et états PENDING/RUNNING/DONE/FAILED.
5. Page HTML avec model-viewer, rotation, déplacement de caméra, zoom et téléchargement, servie par FastAPI.
6. Essais réels sur 5 à 10 photos de petit mobilier opaque ; conserver des modèles de démonstration si les licences l'autorisent.
7. Fiabilité et qualité : contrôle fournisseur sans divulgation d'URL, comportement hors ligne, conseils photo, comparaison à l'image source, réglages validés par le contrat courant et documentation des limites.

Pour toute nouvelle génération, l'étudiante choisit une catégorie parmi chaise, tabouret et table d'appoint. Un GLB terminé apparaît dans le filtre correspondant avec sa photo source. Au Sprint 1, les métadonnées restaient en mémoire ; depuis l'étape 8 du Sprint 2, elles sont conservées dans SQLite et relues par la même route de galerie.

Ne pas faire au Sprint 1 : OpenCV, rembg, comptes, base de données, Next.js, Docker, Celery, Redis ou MinIO.

## Sprint 2 — qualité et fiabilité
Objectif : conserver l'historique des générations après redémarrage, gérer les catégories partagées et préparer les photos avec des contrôles légers.

Étapes, une à la fois et seulement après l'OK de l'étudiante :
8. SQLite et historique persistant derrière une interface de dépôt ; tables `categories` et `generations`, catégories initiales chaise/tabouret/table d'appoint, galerie inchangée côté API/viewer ; test de persistance après redémarrage ; écrire `docs/STOCKAGE.md`.
9. CRUD des catégories partagées : créer, renommer, désactiver et refuser la suppression d'une catégorie utilisée ; routes et interface de gestion.
10. Préparation de la photo : recadrage carré, agrandissement des petites images, contrôle de taille et de netteté avec les outils légers déjà présents ou ajoutés après validation.

Ne pas changer le fournisseur 3D ni le modèle retenu au Sprint 2. Ne pas ajouter `rembg`, OpenCV ou PyTorch sans confirmation explicite de l'étudiante. Le fichier SQLite local reste dans `backend/data/`, ignoré par Git.

## Hugging Face
- Appeler un Space public avec gradio_client uniquement après inspection de son API réelle.
- HF_SPACE_ID accepte un identifiant de Space ou une URL HTTP(S) complète d'application Gradio ; appeler view_api() au moment de la génération et sélectionner uniquement les fonctions, paramètres et sorties présents dans le contrat renvoyé.
- Ne jamais transmettre HF_TOKEN à une URL Gradio externe ; il est destiné à l'accès Hugging Face.
- Le backend charge les secrets de `backend/.env` en priorité, puis ceux du `.env` racine ; les deux restent ignorés par Git.
- Ne jamais inventer de nom de paramètre ou de chemin de sortie.
- Prévoir délai maximal, relance limitée si le Space dort, erreurs explicites et isolation dans Image3DProvider.
- Ne pas envoyer de photo contenant des données personnelles à un Space public.
- Vérifier les licences avant tout usage autre que scolaire.
- Expliquer les quotas et files d'attente gratuits observés ; ils peuvent rendre une démo non fiable.
- Décision de l'étudiante : usage personnel de démonstration et de développement accepté à ses propres risques ; ce n'est pas un service de production. Cette décision n'autorise aucun contournement des limites, captcha, demande de connexion ou quota de Colab. Arrêter si Colab affiche un blocage. La FAQ de Colab ne garantit pas le GPU ni la durée et avertit que les services web non liés au calcul interactif sur les runtimes gérés peuvent être interrompus.
- Une URL publique Gradio est temporaire et accessible à quiconque la connaît. Garder la configuration uniquement dans un `.env` ignoré par Git ; le contrôle de santé ne renvoie jamais cette URL.
- Un GLB pré-généré est identifié honnêtement et ne compte pas comme génération en direct.

## Modes de travail
- MODE BRAINSTORM : analyser avant le code ; proposer 2 ou 3 options, une recommandation et un plan de 30 à 90 minutes.
- MODE GHOST : écrire les fichiers complets directement ; expliquer les fichiers, les commandes et le résultat.
- MODE REVIEW : rechercher les défauts, classés bloquant / important / mineur, sans corriger.
- MODE EDIT : réaliser le plus petit changement ciblé puis relancer les vérifications concernées.
- MODE ASK : une question à la fois, avec 2 à 4 choix.

## Exigences de livraison
1. Aucun fichier incomplet, aucun TODO non résolu et aucun faux résultat de génération.
2. Documenter chaque étape dans docs/etapes/etape-XX.md : rôle des fichiers, logique, lancement, test et justification pour la soutenance.
3. Ajouter des tests pytest pour toute nouvelle fonction Python.
4. À la fin d'une étape, lister les fichiers créés ou modifiés, donner les commandes de vérification et mettre à jour docs/ETAT.md.

## Stack Sprint 1
- Python 3.11 ou plus récent, FastAPI, Uvicorn, gradio_client, HTTPX et pytest.
- Page HTML modulaire sans framework, avec model-viewer et une galerie limitée aux GLB réels de faisabilité ; FastAPI sert la page et ses ressources.
- Stockage local derrière LocalStorage ; métadonnées sans base de données.
- Dépendances payantes interdites. Ajouter une bibliothèque seulement quand une étape l'exige.

## Sécurité
- Secrets seulement dans .env, jamais dans Git ; garder .env.example à jour lorsque du code lit une variable.
- Demander confirmation avant suppression de fichiers, migration de données, installation de dépendances lourdes, action réseau inhabituelle, ajout d'une skill ou d'un serveur MCP.
- Lire le contenu d'une skill ou d'un serveur tiers avant de l'activer.

## État de référence au 19 octobre 2026
- Vision active : service de génération SaaS, futur widget et boutique vitrine de démonstration.
- Produit MVP initial : petit mobilier opaque, notamment tabouret, chaise et table d'appoint.
- Outil de suivi choisi : GitHub Projects.
- Horizon de soutenance communiqué : deux semaines ; la date exacte reste à confirmer.
- Niveau déclaré : avancé en Python et React.
- Hugging Face est un fournisseur candidat dont la faisabilité et les limites doivent encore être vérifiées.
- La vision v1 est conservée dans docs/archive/v1/ ; elle ne définit plus le produit actif.
- L'état de travail courant est résumé dans docs/ETAT.md.

## Mémoire du projet
Au début de chaque session, lire AGENTS.md, docs/ETAT.md et docs/STRUCTURE.md, puis résumer l'avancement en cinq lignes. Après chaque étape, mettre à jour docs/ETAT.md.

## État historique au 2 novembre 2026
- L'étape 6 a prouvé cinq générations TripoSR dans une session passée ; ces cinq résultats sont des fichiers locaux réels, et ne sont pas de nouvelles générations de cette session.
- L'étape 7 ajoute le contrôle fournisseur hors ligne et des réglages dont les noms/bornes doivent provenir du contrat réel à chaque génération.
- La reconnexion Colab du 1 novembre 2026 a affiché « Échec : backend non attribué ». Lors d'une session ultérieure, l'étudiante a fourni le lien d'une session déjà active et a accepté le risque pour une démonstration personnelle ; aucun lien n'est conservé dans les documents ou le dépôt.
- Aucun mécanisme de maintien en vie ni contournement des limites Colab n'est autorisé. Si une limite, demande de connexion, validation ou captcha apparaît, arrêter et demander à l'étudiante.
- Une génération de démonstration du tabouret a réussi le 2 novembre et apparaît dans la galerie sous `stool`. Après le lancement local suivant, `/health/provider` a renvoyé `OFFLINE` ; ne pas envoyer d'autre photo tant qu'un serveur valide n'est pas joignable.
- Les étiquettes `Chaise métal 01/02` ne changent qu'après validation de l'étudiante.

## État au 9 novembre 2026
- Sprint actif : 2 — Qualité et fiabilité. L'étape 8 est implémentée ; consulter `docs/ETAT.md` pour les résultats des vérifications et ne commencer l'étape 9 qu'après un « OK » distinct.
- Sprint 1 considéré terminé par l'étudiante ; la vérification de la CI GitHub reste à sa charge.
- Livrable vérifiable de l'étape 8 : une génération terminée reste consultable après redémarrage du backend et apparaît dans la galerie depuis SQLite. Suivi : `docs/ETAT.md`, `docs/STRUCTURE.md` et `docs/etapes/etape-08.md`.
- Aucun changement au fournisseur ou au choix du modèle n'est autorisé au Sprint 2. Aucun secret n'est requis ni consulté pour le travail prévu.
