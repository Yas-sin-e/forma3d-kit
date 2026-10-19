# Sprint 1 — Étape 6 : essais réels et validation du viewer

## Objectif et livrable attendu

Tester la conversion réelle sur des photos libres de droits de petit mobilier, sans personne ni donnée personnelle, puis vérifier un vrai GLB dans le viewer. Le livrable est un relevé reproductible qui indique le fournisseur, le contrat réellement inspecté, chaque résultat, la présence ou l'absence d'un GLB et les limites de gratuité et de licence. Aucun modèle ne peut être inventé ou présenté comme généré.

## Essais déjà effectués avec Stable Fast 3D

L'API de `stabilityai/stable-fast-3d` a été inspectée avec `Client(space).view_api()` avant les appels. Cinq photos libres sans personne visible ont été envoyées. Le tableau ci-dessous conserve le résultat observé.

| Photo | Durée observée | Résultat |
|---|---:|---|
| `stool-met-01.jpg` | 13,4 s | Exception interne Gradio générique ; aucun GLB |
| `chair-bentwood.jpg` | 41,1 s | Même exception ; aucun GLB |
| `side-table-met.jpg` | 11,6 s | Même exception ; aucun GLB |
| `chair-met-01.jpg` | 12,4 s | Même exception ; aucun GLB |
| `chair-met-02.jpg` | 9,2 s | Même exception ; aucun GLB |

Les cinq requêtes ont échoué avec le message Gradio indiquant que l'application amont a levé une exception sans détail. Ni le quota ni la file d'attente ne sont identifiés comme cause. Les photos et paramètres observés sont décrits dans `docs/etapes/etape-03.md` ; les photos restent ignorées par Git sous `backend/data/feasibility-inputs/`.

## Essai de disponibilité de TripoSR

Le candidat suivant est le Space officiel `stabilityai/TripoSR`. Son dépôt de Space et sa page du modèle indiquent une licence MIT. Cela décrit la licence du modèle et du Space ; cela ne garantit ni la disponibilité du calcul gratuit, ni l'absence de quota, ni un droit automatique sur les photos de tiers.

Le code source officiel courant `app.py` a été consulté. Il chaîne `check_input_image`, `preprocess`, puis `generate`. Le code retourne le chemin OBJ puis le chemin GLB. Le client installé est `gradio_client` 2.7.2 ; `inspect.signature(Client)` confirme un argument `token` (pas `hf_token`).

L'appel demandé `Client("stabilityai/TripoSR", token=False).view_api(return_format="dict")` n'a pas pu lire le contrat : le constructeur `Client` s'arrête avant `view_api()` parce que le Space est signalé en erreur runtime. Trois inspections réseau ont abouti au même résultat. Aucun nom d'endpoint ni paramètre de requête n'a été inventé et aucune photo n'a été envoyée.

Erreur relevée lors de la seconde inspection :

- Type : `ValueError`
- `repr` : `ValueError('The current space is in the invalid state: RUNTIME_ERROR. Please contact the owner to fix this.')`
- `__cause__` : `None`

Aucun `HF_TOKEN` n'est configuré : `backend/.env`, le `.env` racine et la variable du processus sont absents. Il n'y a donc pas eu de tentative authentifiée. `backend/app/config.py` charge désormais `backend/.env` en premier, puis `.env` à la racine, sans remplacer une variable d'environnement déjà définie.

Le contrat `view_api()` reste à inspecter lorsque le Space redevient disponible. L'adaptateur TripoSR dédié et l'appel sur une photo restent à faire après cette inspection ; l'adaptateur Stable Fast 3D existant ne doit pas être réutilisé en supposant que les APIs se ressemblent.

## Ouverture d'un GLB local dans le viewer

La page possède maintenant le bouton « Ouvrir un GLB local ». Il crée une URL `blob:` dans le navigateur à partir du fichier choisi, ne l'envoie pas à `/models`, et affiche « Fichier local, non généré par l'application ». Le lien de téléchargement de la génération reste masqué pour ce parcours. L'URL temporaire est révoquée lors du remplacement du modèle et à la fermeture de la page.

Le dossier `backend/data/feasibility-results/` est vide. Aucun GLB réel n'est disponible ; le bouton peut être utilisé plus tard avec un fichier `.glb` véritable placé dans ce dossier, mais la rotation, le déplacement, le zoom et le chargement 3D n'ont donc pas encore été validés avec un modèle.

## Fichiers modifiés : rôle, lancement et justification

| Fichier | Rôle et logique | Lancer ou vérifier | Pourquoi ce choix |
|---|---|---|---|
| `frontend/index.html` | Ajoute le sélecteur de GLB local, crée une URL `blob:` et la révoque ; distingue visuellement les sources locale et générée | Démarrer Uvicorn depuis `backend`, puis ouvrir `/` et sélectionner un vrai `.glb` | Le test local du viewer ne doit pas dépendre d'une génération ni transmettre le fichier au serveur |
| `backend/app/config.py` | Charge `backend/.env` avant `.env` racine, puis conserve la priorité des variables du processus | `python -m pytest -q` depuis `backend` | Le jeton facultatif se configure au chemin prévu sans l'inscrire dans le dépôt |
| `backend/tests/test_frontend.py` | Vérifie la présence du sélecteur et que son gestionnaire n'utilise ni `fetch` ni `FormData` | `python -m pytest -q` depuis `backend` | Protège le caractère local du parcours sans Space ni modèle simulé |
| `backend/tests/test_huggingface_provider.py` | Vérifie la priorité de `backend/.env` avec des valeurs de test locales non secrètes | `python -m pytest -q` depuis `backend` | Garantit le chargement de configuration sans appeler Hugging Face |
| `frontend/README.md` | Explique le sélecteur et le fait qu'aucun fichier n'est actuellement disponible pour vérifier la caméra | Lecture avant de modifier ou présenter le frontend | Évite de confondre fichier local et génération de l'application |
| `AGENTS.md` | Documente les deux emplacements de configuration ignorés par Git | Lecture au début d'une session | Maintient la règle de secret pour les prochaines sessions |
| `docs/STRUCTURE.md` | Décrit le sélecteur local, les tests et `backend/.env` | Lecture au début ou lors d'un changement d'arborescence | Permet de comprendre chaque élément du projet |
| `docs/ETAT.md` | Consigne l'état réel du Sprint 1 et le blocage TripoSR | Lecture au début de chaque session | Évite de déclarer la génération ou le sprint validés à tort |
| `docs/etapes/etape-06.md` | Conserve les essais, l'exception et le mode d'emploi du test local | Lecture pour refaire la faisabilité et préparer la soutenance | Assure la traçabilité du résultat négatif/non concluant |
| `.env.example` | Indique les variables à copier dans `backend/.env` ou `.env` sans inclure de jeton | Copie locale uniquement ; ne pas commiter le fichier créé `.env` | Rend la configuration reproductible sans secret dans Git |

## Vérifications

Depuis `backend` dans PowerShell :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Puis ouvrir `http://127.0.0.1:8000/`. Une sélection locale valide doit afficher le nom du fichier et l'avertissement de provenance, sans appeler l'API. La validation visuelle du modèle et des contrôles de caméra attend un GLB réel.

## Conclusion de l'étape

L'étape 6 n'est pas validée : Stable Fast 3D a échoué cinq fois ; TripoSR est en `RUNTIME_ERROR` avant inspection de son API ; aucun GLB réel n'a été produit. Le projet ne contient aucun modèle fictif. Le viewer comporte maintenant une voie locale honnête pour pouvoir tester un futur GLB.

La suite consiste à attendre le retour du Space, refaire `view_api(return_format="dict")`, créer l'adaptateur TripoSR uniquement à partir du contrat observé, puis tester une photo sûre. Si le Space reste indisponible, consigner le blocage à la soutenance et décider ensuite si un autre fournisseur gratuit pré-entraîné mérite une étude.
