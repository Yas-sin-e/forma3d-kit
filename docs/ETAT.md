# État du projet Forma3D Studio

## Étape en cours

Étape 2 terminée. Le dépôt privé est publié et la CI documentaire a réussi. L’étape 3 attend l’« OK » explicite de l’étudiante.

## Fait

- Étape 1 validée par l’étudiante (« OK ») le 18 octobre 2026.
- Catégorie MVP : petit mobilier simple (tabouret, chaise, table d’appoint).
- Suivi des tâches : GitHub Projects.
- Niveau déclaré : avancé en Python et en React.
- Soutenance estimée vers le 1er novembre 2026 ; date exacte à confirmer.
- Copie de travail créée sous OneDrive/Bureau/forma3d-studio/forma3d-kit-codex et huit fichiers d’origine vérifiés par SHA-256.
- Le dossier de travail complet se trouve à la destination demandée. Windows a bloqué le déplacement/nettoyage de la source ; seul Downloads/forma3d-kit-codex/.agents/skills/.gitkeep y reste.
- Dépôt Git local initialisé sur main ; commit initial créé.
- README, .gitignore, répertoires backend et frontend, guides de rôle et workflow de CI documentaire ajoutés.
- Vérifications locales : neuf fichiers requis présents, aucun espace de fin dans les nouveaux fichiers.
- Artefacts locaux .agents/ et PROMPT-1.md exclus du suivi Git.
- Dépôt GitHub privé créé : https://github.com/Yas-sin-e/forma3d-kit-codex.
- Branche main poussée vers origin ; le commit initial 21e8869 est publié.
- Le workflow « Project documentation » a réussi pour le commit 21e8869 (exécution #1).

## En cours

- Aucun travail d’implémentation en cours ; attendre l’« OK » explicite avant l’étape 3.

## Bloqué

- Aucun blocage technique sur les fichiers locaux.
- Le dossier source de Downloads n’a pas pu être supprimé entièrement : Windows bloque son répertoire .agents et le dossier racine. Tous les fichiers d’origine, y compris .agents/skills/.gitkeep, sont présents à la destination de travail.
- Aucun blocage restant pour l’étape 2 ; le dossier source résiduel n’est pas utilisé.

## Décisions

- Dossier de travail visé : forma3d-studio/forma3d-kit-codex.
- Dépôt distant : dépôt privé GitHub Yas-sin-e/forma3d-kit-codex, branche main.
- CI initiale limitée à vérifier la présence des documents ; les tests applicatifs viendront avec le backend et le frontend.
- La CI GitHub Actions est limitée au contrôle documentaire. Pour rester sans frais, surveiller le quota de minutes applicable aux dépôts privés et ne pas activer de dépassement payant.
- Aucun déploiement continu avant l’étape 11, quand une application exécutable existera.
- Génération 3D gratuite derrière Image3DProvider ; Hugging Face Spaces reste à évaluer à l’étape 3.
- Pas de Celery, Redis ni MinIO au MVP.
- Le canevas d’aménagement est prévu à l’étape 10 ; un modèle pré-généré doit être clairement étiqueté.

## Prochaine étape

Étape 3 — tester la faisabilité d’une génération 3D gratuite sur trois photos, comparer les fournisseurs pré-entraînés et retenir une option réaliste. Ne commencer qu’après l’« OK » explicite de l’étudiante. Les limites gratuites, files d’attente, licences et risques pour la soutenance devront être vérifiés avant le choix.
