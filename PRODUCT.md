# Forma3D Studio — Brief produit v2

## 1. Vision
Forma3D Studio est un module de génération et d'affichage 3D intégrable dans tout site. La propriétaire utilise le Studio, console privée mono-propriétaire, pour générer ou importer un GLB, puis l'autoriser pour une API et un widget intégrables.

Le projet est réalisé pour une soutenance. Le code et les décisions d'architecture doivent rester simples à expliquer. Chaque fichier est documenté dans docs/STRUCTURE.md et dans le guide de son étape.

## 2. Utilisateurs et problème
- **Propriétaire du Studio :** gère seule les modèles et leur activation pour l'intégration.
- **Développeur intégrateur :** utilise une clé API et le widget dans un site existant.
- **Visiteur du site intégrateur :** consulte le modèle 3D.
- **Étudiante et jury :** ont besoin d'un prototype compréhensible, reproductible et honnête sur ses limites.

Le premier jeu d'essai vise le petit mobilier opaque : tabouret, chaise et table d'appoint. Ce choix borne les essais ; il ne signifie pas que le système sait reconstruire toutes les catégories de produits.

## 3. Promesse et limites
À partir d'une photo exploitable, le prototype tente de produire un GLB avec un modèle image-vers-3D pré-entraîné. Le navigateur permet ensuite de tourner le modèle, déplacer le point de vue, zoomer et télécharger le fichier.

Une image unique ne révèle pas les faces cachées et ne garantit ni les dimensions, ni la géométrie exacte, ni un résultat utilisable pour la fabrication. Les résultats dépendent de l'image, du modèle et de la disponibilité du fournisseur.

Les Sprints 3 (comptes publics) et 4 (vitrine/catalogue public) sont retirés du périmètre. Le Sprint 5 construit le module intégrable : API avec clé et widget d'affichage. Le Studio n'a pas d'authentification et reste destiné à un usage local ou de démonstration ; il ne doit pas être exposé tel quel sur Internet.

## 4. Parcours visé du Sprint 1
1. La propriétaire sélectionne une photo de produit.
2. L'API vérifie le format et la taille du fichier.
3. Un fournisseur pré-entraîné produit un modèle 3D ; son intégration est isolée derrière Image3DProvider.
4. L'API conserve le fichier et communique un état réel du traitement.
5. Une page modulaire servie par FastAPI charge le GLB dans le composant model-viewer et montre une galerie locale des cinq résultats réels de faisabilité pour la démonstration.
6. La propriétaire manipule le modèle et télécharge le GLB. La galerie du Studio est une bibliothèque locale, pas un catalogue public.

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
- Page de studio modulaire avec une galerie de démonstration limitée aux résultats réels présents sur le poste ; elle ne devient pas un catalogue produit partagé.

### Hors périmètre du Sprint 1
- OpenCV, rembg, authentification et base de données.
- Comptes publics, vitrine, catalogue public et boutique : retirés du périmètre.
- Next.js, Docker, Celery, Redis et MinIO.
- Le Sprint 5 porte l'API avec clé et le widget intégrable, sans changer le fournisseur ou le modèle.
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
