# Forma3D Studio — Instructions permanentes du projet

## Mission

Forma3D Studio transforme la photo d’un objet en modèle 3D GLB, l’affiche dans un viewer interactif avec rotation, déplacement de caméra et zoom, puis permettra de le placer dans un canevas d’aménagement.

## Contraintes du projet

1. **100 % gratuit :** aucune API payante, carte bancaire ou abonnement.
2. **Aucun entraînement :** utiliser uniquement des modèles image-vers-3D pré-entraînés.
3. **Compréhension :** le projet est défendu en soutenance ; expliquer le rôle et le fonctionnement des fichiers réalisés.
4. **Langue :** répondre toujours en français ; code, noms de fichiers et commandes restent en anglais.
5. **Limites :** expliquer clairement les quotas, files d’attente, indisponibilités et autres limites des solutions gratuites.
6. **Périmètre confirmé :** le MVP cible le petit mobilier simple : tabouret, chaise et table d’appoint.
7. **Suivi :** utiliser GitHub Projects pour suivre le travail.
8. **Calendrier :** soutenance prévue dans environ deux semaines à compter du 18 octobre 2026, soit vers le 1er novembre 2026 ; date exacte à confirmer.
9. **Niveau déclaré :** niveau avancé en Python et en React.

## Méthode — 11 étapes

1. **Cadrage et fondations :** cadrage produit, AGENTS.md, PRODUCT.md et DESIGN.md.
2. **Dépôt et structure :** dépôt GitHub, organisation du projet et CI/CD ; Docker est facultatif.
3. **Faisabilité 3D gratuite :** essayer trois photos avec Hugging Face Spaces ou Kaggle/Colab et décider du fournisseur.
4. **Backend socle :** FastAPI, SQLite avec SQLAlchemy, configuration et tests.
5. **Prétraitement :** contrôle de qualité OpenCV et suppression du fond.
6. **Fournisseur 3D :** interface Image3DProvider et nettoyage du maillage avec trimesh.
7. **Jobs et stockage :** traitements en arrière-plan, stockage et progression ; WebSocket seulement si utile.
8. **Base frontend :** Next.js, TypeScript, Tailwind et système visuel décrit dans DESIGN.md.
9. **Viewer 3D :** React Three Fiber, rotation, déplacement de caméra, zoom et objets de démonstration.
10. **Canevas d’aménagement :** TransformControls, inspecteur et export.
11. **Finalisation :** tests E2E, polissage, déploiement gratuit et documentation de soutenance.

Les étapes 1 à 9 constituent le MVP photo-vers-GLB-vers-viewer. L’étape 10 est une extension. L’étape 11 finalise le projet.

**Ne jamais commencer une étape suivante sans le « OK » explicite de l’étudiante.** Avant chaque étape, rappeler l’objectif et le résultat vérifiable attendu. Ne pas dépasser le périmètre de l’étape autorisée.

## Cycle d’une étape

MODE BRAINSTORM → plan validé par l’étudiante → MODE GHOST → MODE REVIEW → MODE EDIT si des corrections sont demandées → validation → mise à jour de docs/ETAT.md.

- **MODE BRAINSTORM :** analyser les besoins et options avant de coder ; aucun fichier de code. Présenter 2 ou 3 options, une recommandation et un plan de tâches de 30 à 90 minutes.
- **MODE GHOST :** écrire les fichiers complets directement dans le projet, sans coller leur contenu dans le chat. Réponse courte avec chemins, rôle, commandes de lancement et de vérification, résultat attendu.
- **MODE REVIEW :** relire sans corriger ; classer les remarques bloquant, important ou mineur.
- **MODE EDIT :** effectuer la modification ciblée la plus petite possible, expliquer le diff et relancer les vérifications pertinentes.
- **MODE ASK :** poser une seule question à la fois, avec 2 à 4 choix et une recommandation lorsque cela s’applique.

## Exigences de livraison

1. Fichiers complets, sans coupure, sans points de suspension simulant du contenu et sans TODO incomplet.
2. Aucun code simulé (par exemple setTimeout, faux modèles ou données fictives), sauf accord explicite et indication visible.
3. Pour chaque étape, documenter pas à pas dans docs/etapes/etape-XX.md : rôle des fichiers, logique, exécution, vérification et raison des choix pour la soutenance.
4. Ajouter des tests automatiques aux nouvelles fonctions ; utiliser pytest côté Python. Une étape de documentation seule n’ajoute pas de fonction et ne nécessite pas de test logiciel.
5. À la fin d’une étape, lister les fichiers modifiés, donner les commandes pertinentes et mettre à jour docs/ETAT.md.

## Architecture de génération 3D

L’interface de fournisseur est :

    Image3DProvider.generate(image_path) -> bytes au format GLB

Implémentations prévues :

- **HuggingFaceSpaceProvider :** appelle un Space public via gradio_client. Découvrir les paramètres réels avec Client(space).view_api() ; ne jamais les deviner. Prévoir une relance temporisée pour un Space endormi, une durée maximale, un message d’erreur clair et un cache basé sur le hash de la photo.
- **KaggleProvider (facultatif) :** modèle open source exécuté dans un notebook GPU gratuit et exposé par une petite API.
- **PrecomputedProvider :** vrais GLB pré-générés et conservés pour une démonstration fiable ; les présenter honnêtement comme pré-générés.

Vérifier la licence de chaque modèle avant tout usage autre que scolaire. Ne pas transmettre de photo contenant des données personnelles à un Space public. Aucun fournisseur gratuit ne garantit disponibilité, délai ou quota.

## Stack visée

- **Frontend :** Next.js, TypeScript, Tailwind, React Three Fiber, drei et Zustand.
- **Backend :** FastAPI, SQLAlchemy, Alembic et SQLite au départ ; PostgreSQL seulement si un besoin apparaît.
- **Stockage :** dossier local derrière une interface Storage, remplaçable ultérieurement.
- **Vision :** OpenCV et rembg.
- **Maillage :** trimesh.
- **DevOps :** GitHub et GitHub Actions ; Docker facultatif.
- Pas de Celery, Redis ni MinIO au MVP ; les ajouter uniquement si un besoin réel le justifie.

## Commandes de référence

- API : cd backend && uvicorn app.main:app --reload
- Tests backend : cd backend && pytest -q
- Frontend : cd frontend && npm run dev

Compléter ces commandes au fil des étapes, en conservant des commandes réalisables avec la structure réellement présente.

## Sécurité et autorisations

- Les secrets résident uniquement dans .env, jamais dans Git ; maintenir .env.example à jour.
- Demander confirmation avant toute suppression de fichiers, migration de base de données, installation de dépendances lourdes, commande sur un serveur distant, ajout d’un serveur MCP ou ajout d’une skill tierce.
- Lire le contenu d’une skill ou d’un serveur MCP tiers avant de l’activer.
- Les photos envoyées à un Space public ne doivent contenir aucune donnée personnelle.

## Skills du projet

Skills visées : taste-skill et impeccable pour l’interface, playwright-cli pour les essais navigateur et img2threejs pour des objets de démonstration ou un repli procédural. Elles ne sont pas garanties disponibles dans chaque session. Vérifier le catalogue de la session et signaler celles qui manquent ; ne jamais prétendre avoir utilisé une skill indisponible.

DESIGN.md est la source de vérité du design et doit être lu avant tout changement d’interface. Si taste-skill et impeccable sont disponibles, suivre la demande de critique puis de polish à la fin de l’étape UI. img2threejs n’est pas le pipeline principal de génération.

## Mémoire du projet

Au début de chaque session, lire AGENTS.md et docs/ETAT.md et résumer l’état en cinq lignes. Après chaque étape, actualiser docs/ETAT.md : fait, en cours, bloqué, décisions et prochaine étape.
