# État du projet — Forma3D Studio

Dernière mise à jour : 19 octobre 2026.

## Sprint actif et résumé

Sprint 1 — de la photo au GLB affiché et téléchargeable. Les étapes 1 à 5 sont implémentées. L'étape 6 reste bloquée : Stable Fast 3D a échoué cinq fois et le Space officiel TripoSR est en erreur runtime avant l'inspection de son API. Aucun GLB réel n'a été obtenu ; le sprint n'est pas déclaré terminé.

## Fait

- Vision v2 cadrée comme SaaS 3D pour l'e-commerce ; le widget intégrable et la boutique vitrine restent prévus pour des sprints ultérieurs.
- Ancien cadrage v1 et guides archivés dans `docs/archive/v1/`.
- API FastAPI avec GET `/health`, page HTML sur GET `/`, validation d'images, upload, suivi, stockage local et téléchargement après `DONE`.
- Contrat `Image3DProvider` et adaptateur Stable Fast 3D séparés ; cet adaptateur relit `view_api()` et contrôle les GLB 2.0.
- Page HTML avec upload, statut réel, viewer `<model-viewer>`, rotation, déplacement de caméra, zoom et téléchargement après génération réussie.
- Ajout du bouton « Ouvrir un GLB local » : le navigateur utilise une URL `blob:` ; le fichier n'est pas envoyé au serveur et porte la mention « Fichier local, non généré par l'application ».
- Configuration : `backend/.env` est chargé avant `.env` racine, puis les variables déjà définies dans le processus gardent la priorité. Les deux fichiers restent ignorés par Git.
- Guides des étapes, inventaire `docs/STRUCTURE.md` et suite de tests locale sans appel automatique Hugging Face.

## Essais fournisseur et blocage

- `stabilityai/stable-fast-3d` : API inspectée avant usage ; cinq photos libres et sans personne visible ont échoué avec la même exception interne Gradio générique. Aucun GLB.
- `stabilityai/TripoSR` : la source officielle de `app.py` a été lue et la licence MIT du modèle vérifiée. `gradio_client` 2.7.2 accepte `token` dans `Client`.
- Trois tentatives de `Client("stabilityai/TripoSR", token=False).view_api(return_format="dict")` ont été arrêtées par le constructeur : `ValueError('The current space is in the invalid state: RUNTIME_ERROR. Please contact the owner to fix this.')`; `__cause__` vaut `None`. Le Space n'a pas fourni son contrat et aucune photo ne lui a été envoyée.
- `backend/.env`, `.env` racine et variable d'environnement `HF_TOKEN` absents ; aucune tentative authentifiée. La configuration locale accepte désormais le chemin `backend/.env` pour une future tentative, sans afficher le jeton.
- `backend/data/feasibility-results/` est vide. Aucun modèle n'est inventé ou pré-généré. Les mouvements de caméra n'ont pas encore été validés avec un GLB.
- Les essais Stable Fast 3D ne prouvent ni un quota épuisé ni une file d'attente ; le message public ne donne pas la cause. Une offre gratuite peut dormir, être instable ou limiter l'accès.

## En cours / restant pour fermer Sprint 1

- Attendre que le Space TripoSR quitte `RUNTIME_ERROR`, puis refaire l'inspection live de `view_api(return_format="dict")`.
- À partir seulement des noms réellement retournés par `view_api`, créer un adaptateur TripoSR dédié derrière `Image3DProvider` ; ne pas réutiliser l'adaptateur Stable Fast 3D avec des paramètres supposés.
- Si l'API est inspectable, essayer une photo de mobilier libre de droits sans personne. En cas de même exception interne, consigner type, `repr` et `__cause__`; utiliser `HF_TOKEN` de `backend/.env` seulement si nécessaire et après vérification de la signature du client.
- Obtenir et vérifier un GLB réel, le placer localement dans `backend/data/feasibility-results/`, ouvrir ce fichier depuis le navigateur, puis vérifier rotation, déplacement, zoom et téléchargement du parcours généré.
- Si aucun fournisseur public ne produit un modèle, présenter le blocage sans modèle de démonstration inventé.

## Décisions

- SaaS 3D orienté e-commerce ; vendeurs et acheteurs sont les utilisateurs visés à terme.
- MVP de faisabilité limité au tabouret, à la chaise et à la table d'appoint.
- GitHub Projects pour Scrum ; horizon communiqué : deux semaines ; date précise de soutenance non confirmée.
- Python et React : niveau déclaré avancé.
- Stable Fast 3D a été essayé en premier ; TripoSR est le candidat suivant. La licence MIT du modèle n'assure pas la disponibilité gratuite et stable de son Space.
- Le jeton Hugging Face est facultatif ; `backend/.env` est le chemin prévu pour les essais backend. Aucun jeton n'est présent actuellement.
- Aucun entraînement de modèle ; usage de modèles pré-entraînés seulement.
- Pas d'OpenCV, rembg ajouté au projet, comptes, base de données, Next.js, Docker, Celery, Redis ou MinIO dans le Sprint 1.
- Le serveur sert une page HTML ; les métadonnées en mémoire sont perdues au redémarrage et les fichiers restent locaux.

## Vérification

Depuis `backend` dans PowerShell :

    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

La suite doit réussir sans appeler Hugging Face ni créer un GLB. Le chargement d'un fichier local se fait depuis le navigateur et n'envoie pas le fichier à `/models`. Le contrôle réel du viewer et de la caméra reste à faire lorsqu'un GLB authentique sera disponible.

## Prochaine action recommandée

Réessayer l'inspection de TripoSR lorsque le Space officiel revient en état normal ; construire l'adaptateur depuis son contrat réel, puis tester une photo sûre. Ne passer à la suite du sprint qu'après validation du parcours complet avec un GLB réel.
