# État du projet Forma3D Studio

## Étape en cours

Étape 2 — dépôt, structure et CI/CD. La préparation locale est terminée ; la création du dépôt distant reste en attente de confirmation.

## Fait

- Étape 1 validée par l’étudiante (« OK ») le 18 octobre 2026.
- Catégorie MVP : petit mobilier simple (tabouret, chaise, table d’appoint).
- Suivi des tâches : GitHub Projects.
- Niveau déclaré : avancé en Python et en React.
- Soutenance estimée vers le 1er novembre 2026 ; date exacte à confirmer.
- Copie de travail créée sous OneDrive/Bureau/forma3d-studio/forma3d-kit-codex et huit fichiers d’origine vérifiés par SHA-256.
- La source dans Downloads reste intacte, car Windows a refusé son déplacement pendant que la session Codex l’utilisait.
- Dépôt Git local initialisé sur main ; commit initial créé.
- README, .gitignore, répertoires backend et frontend, guides de rôle et workflow de CI documentaire ajoutés.
- Vérifications locales : neuf fichiers requis présents, aucun espace de fin dans les nouveaux fichiers.
- Artefacts locaux .agents/ et PROMPT-1.md exclus du suivi Git.

## En cours

- Choisir la visibilité du dépôt GitHub.
- Obtenir la confirmation avant la création du dépôt distant et le premier push.

## Bloqué

- Aucun blocage technique sur les fichiers locaux.
- Le déplacement physique du dossier source est bloqué par un verrou Windows ; la copie vérifiée dans le nouvel emplacement permet de travailler à la destination choisie.
- La création du dépôt distant et le premier push attendent la confirmation de l’étudiante.

## Décisions

- Dossier de travail visé : forma3d-studio/forma3d-kit-codex.
- CI initiale limitée à vérifier la présence des documents ; les tests applicatifs viendront avec le backend et le frontend.
- Aucun déploiement continu avant l’étape 11, quand une application exécutable existera.
- Génération 3D gratuite derrière Image3DProvider ; Hugging Face Spaces reste à évaluer à l’étape 3.
- Pas de Celery, Redis ni MinIO au MVP.
- Le canevas d’aménagement est prévu à l’étape 10 ; un modèle pré-généré doit être clairement étiqueté.

## Prochaine étape

Après confirmation de la visibilité et de l’action distante : créer le dépôt GitHub Forma3D Studio et envoyer le commit initial, puis vérifier que le workflow de CI s’exécute. La CI utilise un runner GitHub Actions standard ; la gratuité et les limites dépendent de la visibilité du dépôt.
