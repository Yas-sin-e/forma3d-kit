# Forma3D Studio — Brief produit v2

## 1. Vision
Forma3D Studio est un SaaS 3D pour le commerce en ligne. Un vendeur transmet la photo d'un produit et reçoit un fichier GLB interactif qu'il peut présenter dans sa boutique. À terme, le produit regroupe un service de génération, un visualiseur intégrable comme widget et un site vitrine qui démontre le parcours dans une boutique.

Le projet est réalisé pour une soutenance. Le code et les décisions d'architecture doivent rester simples à expliquer. Chaque fichier est documenté dans docs/STRUCTURE.md et dans le guide de son étape.

## 2. Utilisateurs et problème
- **Vendeur en ligne :** veut présenter un produit sous plusieurs angles sans créer lui-même un modèle 3D.
- **Acheteur :** veut examiner visuellement un article avant de le considérer.
- **Étudiante et jury :** ont besoin d'un prototype compréhensible, reproductible et honnête sur ses limites.

Le premier jeu d'essai vise le petit mobilier opaque : tabouret, chaise et table d'appoint. Ce choix borne les essais ; il ne signifie pas que le système sait reconstruire toutes les catégories de produits.

## 3. Promesse et limites
À partir d'une photo exploitable, le prototype tente de produire un GLB avec un modèle image-vers-3D pré-entraîné. Le navigateur permet ensuite de tourner le modèle, déplacer le point de vue, zoomer et télécharger le fichier.

Une image unique ne révèle pas les faces cachées et ne garantit ni les dimensions, ni la géométrie exacte, ni un résultat utilisable pour la fabrication. Les résultats dépendent de l'image, du modèle et de la disponibilité du fournisseur.

Le SaaS commercial complet n'est pas livré au Sprint 1. Les comptes vendeurs, le catalogue, l'intégration marchande avec clé API, le widget distribuable et la boutique vitrine complète évoluent dans les sprints suivants. La boutique de démonstration ne sera pas présentée comme une place de marché réelle avec paiement.

## 4. Parcours visé du Sprint 1
1. Le vendeur sélectionne une photo de produit.
2. L'API vérifie le format et la taille du fichier.
3. Un fournisseur pré-entraîné produit un modèle 3D ; son intégration est isolée derrière Image3DProvider.
4. L'API conserve le fichier et communique un état réel du traitement.
5. Une page servie par FastAPI charge le GLB dans le composant model-viewer.
6. Le vendeur manipule le modèle et télécharge le GLB.

L'étape 1 de ce sprint ne met en place que le squelette FastAPI et son vrai endpoint GET /health. Les étapes suivantes ajoutent les fonctions du parcours dans l'ordre défini par AGENTS.md.

## 5. Contraintes et périmètre

### Contraintes permanentes
- Aucun entraînement ni ajustement de modèle : uniquement des modèles pré-entraînés.
- Aucune API payante, carte bancaire ou abonnement.
- Les quotas, files d'attente, périodes de veille et interruptions d'un service gratuit sont expliqués honnêtement.
- Les photos envoyées à un Space public ne contiennent pas de données personnelles.
- Les licences des modèles et services sont vérifiées avant tout usage autre que scolaire.
- Un modèle pré-généré de démonstration est signalé comme pré-généré et ne remplace pas une génération réelle.

### Inclus dans le Sprint 1
- Structure du backend et endpoint de santé.
- Validation JPG, PNG et WebP avec une limite de 10 Mo.
- Interface Image3DProvider et essai d'un Space Hugging Face à partir de ses paramètres réellement documentés.
- Génération, stockage local et état de traitement.
- Page HTML avec viewer interactif et téléchargement.
- Essais réels avec 5 à 10 photos de petit mobilier opaque.

### Hors périmètre du Sprint 1
- OpenCV, rembg, authentification et base de données.
- Next.js, comptes vendeurs, catalogue commercial, widget distribuable, clés API et boutique vitrine complète.
- Docker, Celery, Redis et MinIO.
- Toute garantie de fidélité géométrique ou d'adéquation à la fabrication.

## 6. Critères d'acceptation du produit final visé
- Une photo acceptée suit un parcours réel de validation, génération, stockage et affichage.
- L'application montre des erreurs utiles lorsque l'image ou le fournisseur ne convient pas.
- Le fichier GLB affiché provient d'une génération réelle ; toute démo pré-générée est étiquetée.
- Le viewer fournit rotation, déplacement de caméra, zoom et téléchargement.
- Le modèle, sa licence et les limites du fournisseur sont documentés.
- Aucun parcours ne requiert de paiement ou d'entraînement.
- La documentation explique les fichiers réellement présents et les choix faits pour la soutenance.

## 7. Organisation
Le suivi des tâches utilise GitHub Projects. L'horizon communiqué pour la soutenance est de deux semaines ; la date précise reste à confirmer. Le niveau déclaré en Python et en React est avancé. Le Sprint 1 utilise une page HTML légère servie par FastAPI, sans introduire React avant d'en avoir besoin.
