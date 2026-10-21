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

Lors de l'essai antérieur, le code app.py livré par le Space a été consulté. Il enchaînait check_input_image, preprocess, puis generate et retournait le chemin OBJ puis le chemin GLB. La nouvelle préparation s'appuie sur le dépôt officiel courant, dont gradio_app.py et les options de lancement sont documentés plus bas. Le client installé est gradio_client 2.7.2 ; inspect.signature(Client) confirme un argument token (pas hf_token).

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

## Préparation du serveur TripoSR dans Colab

Le dépôt officiel TripoSR a maintenant été relu dans ses fichiers README.md, requirements.txt, gradio_app.py et run.py. Le dépôt et ses poids pré-entraînés sont sous licence MIT. Le README demande Python 3.8 ou plus, PyTorch/CUDA compatibles, setuptools à jour et les dépendances de requirements.txt ; il donne aussi une procédure de réinstallation de torchmcubes en cas d'erreur CUDA. Le notebook utilise PyTorch fourni par Colab et ne modifie ni l'environnement local ni backend/requirements.txt.

Le lanceur officiel expose réellement --share, --port (7860 par défaut), --username et --password. Il configure auth uniquement si username et password sont tous deux fournis. Le notebook exécute gradio_app.py avec --share, --port 7860 et --queuesize 1 sans identifiants : le serveur est donc accessible à toute personne connaissant le lien temporaire. La cellule reste active pendant le serveur.

La signature installée de gradio_client 2.7.2 est inspectée localement : Client reçoit src et token ; sa documentation accepte un Space ID ou l'URL complète d'une application Gradio. Le fournisseur accepte désormais les deux. Il appelle view_api() à chaque génération, choisit une chaîne complète ou les étapes séparées selon les entrées/sorties observées, puis sélectionne la sortie portant le format GLB. Un jeton Hugging Face ne part jamais vers un serveur Gradio externe.

Le notebook a été essayé sur un vrai runtime Colab le 21 octobre 2026, mais uniquement jusqu'à l'installation des dépendances. Tesla T4 a été détecté et le dépôt officiel a été cloné. Le guide `docs/etapes/etape-06-colab.md` conserve le parcours restant. Google rappelle que la disponibilité GPU, les limites d'utilisation, les types de GPU et les délais d'inactivité de Colab varient et ne sont pas garantis. Les photos doivent être libres de droits et ne contenir personne ni donnée personnelle.

## Test réel Colab — 21 octobre 2026

| Tentative | Action observée | Résultat |
|---|---|---|
| 1 | Mise à jour de setuptools puis installation de `requirements.txt` officiel | Échec pendant la préparation de `torchmcubes`; le processus pip s'est arrêté avec le code 1. |
| 2 | Même installation avec capture séparée de stdout et stderr pour rendre le diagnostic visible | Échec de génération des métadonnées de `torchmcubes` (`metadata-generation-failed`). |
| 3 | Dépendances officielles autres que `torchmcubes`, puis outils de build et installation de `torchmcubes` avec `--no-build-isolation` | Échec antérieur à `torchmcubes` : `Pillow==10.1.0` a été téléchargé en archive source ; « Getting requirements to build wheel » a échoué (code 1). La sortie pip ne montre pas l'exception interne. |

Le runtime réellement connecté a indiqué `Tesla T4` et PyTorch CUDA `13.0`. Le clonage `/content/TripoSR` a réussi. Après ces trois essais d'installation, les tentatives sur cette piste sont arrêtées. La cellule `gradio_app.py` n'a pas été lancée ; aucun lien Gradio, aucun appel `view_api()`, aucune photo, aucun statut de génération et aucun GLB n'ont été observés. Cela ne prouve pas que Pillow seul est la cause racine, seulement que c'est la première dépendance visible qui bloque la troisième tentative. Aucun paquet n'a été installé sur le PC.

Les notes officielles Colab indiquent qu'au 16 septembre 2026 les images CPU/GPU utilisent Python 3.13.15. Les fichiers PyPI de Pillow 10.1.0 comprennent des wheels CPython 3.12, mais aucune wheel cp313. Cela rend plausible une incompatibilité avec le runtime le plus récent ; toutefois, la version du noyau de la session récente n'a pas été capturée et la sortie pip ne contient pas la cause racine complète. Pour tester cette hypothèse sans quatrième tentative sur la même installation, la version d'exécution Colab `2025.10` a été sélectionnée avec T4. Le 21 octobre, sa nouvelle session a affiché Python 3.12.12, Tesla T4 et PyTorch CUDA 12.6 ; la cellule de contrôle GPU a réussi.

Une capture transmise ensuite montre l'échec (code 1) de la première commande d'installation d'une variante séparant `torchmcubes` (`requirements_without_torchmcubes`). Les lignes visibles ne contiennent pas l'exception pip d'origine. Une trace fournie après montre que la cellule de secours a également échoué sur `pip install git+https://github.com/tatsy/torchmcubes.git`; elle situe l'interpréteur sous `/usr/lib/python3.12`, mais ne contient toujours pas le stderr qui expliquerait l'échec. Le README actuel de `tatsy/torchmcubes` demande un compilateur C++20, CMake 3.24 ou plus et CUDA Toolkit 12 ou plus pour compiler le support GPU ; il recommande `scikit-build-core`, `pybind11` et `--no-build-isolation`. La cellule versionnée a été corrigée pour installer ces outils, réutiliser le PyTorch de Colab et afficher stdout/stderr complet ; cette correction n'a pas encore été exécutée sur Colab.

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

## Fichiers de préparation Colab et fournisseur

| Fichier | Rôle et logique | Lancer ou vérifier | Pourquoi ce choix |
|---|---|---|---|
| `tools/colab/triposr_server.ipynb` | Vérifie T4, récupère le dépôt officiel, installe dans Colab et lance le serveur Gradio public | Test partiel sur Colab : T4 et clonage réussis ; installation bloquée après trois tentatives à Pillow 10.1.0 ; ne pas relancer avant correction | Le modèle pré-entraîné tourne dans un GPU distant temporaire sans PyTorch local |
| backend/app/providers/huggingface.py | Inspecte view_api à l'exécution, gère les IDs et URLs Gradio, prend la sortie GLB et contrôle la structure GLB 2.0 | Les tests simulés sont lancés par pytest depuis backend ; l'essai réseau attend l'URL | L'interface métier reste indépendante des détails du fournisseur et des chemins API supposés |
| backend/tests/test_huggingface_provider.py | Simule les contrats Gradio combiné et séparé, l'ordre des appels, la protection du jeton et le format GLB | pytest depuis backend, sans réseau | Vérifie l'adaptateur sans faire passer une fixture de test pour une génération réelle |
| docs/etapes/etape-06-colab.md | Explique le notebook, les options exactes, les risques gratuits et les prochaines validations réelles | À consulter avant de lancer Colab | Rend le serveur reproductible tout en décrivant ses limites |

## Vérifications

Depuis `backend` dans PowerShell :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Puis ouvrir `http://127.0.0.1:8000/`. Une sélection locale valide doit afficher le nom du fichier et l'avertissement de provenance, sans appeler l'API. La validation visuelle du modèle et des contrôles de caméra attend un GLB réel.

## Conclusion de l'étape

L'étape 6 n'est pas validée : Stable Fast 3D a échoué cinq fois ; le Space TripoSR précédent était en `RUNTIME_ERROR` ; le serveur TripoSR autonome n'a pas pu dépasser l'installation des dépendances après trois tentatives. Aucun GLB réel n'a été produit. Le projet ne contient aucun modèle fictif. Le viewer comporte maintenant une voie locale honnête pour pouvoir tester un futur GLB.

La prochaine action est d'exécuter une seule fois la cellule de secours corrigée dans le runtime Python 3.12 et de transmettre tout stdout/stderr produit. Si la commande échoue encore, arrêter les essais et consigner le blocage exact. Après un démarrage réussi du serveur, son API réelle devra être inspectée avec `view_api()`, puis une photo sûre devra être envoyée par POST `/models`. L'étape 6 ne sera validée qu'après les statuts réels, la réception d'un GLB valide, l'affichage contrôlé dans le viewer et le téléchargement ; les 5 à 10 photos et les notes de qualité viendront après cette preuve initiale.
