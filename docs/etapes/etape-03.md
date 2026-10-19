# Sprint 1 — Étape 3 : contrat image-vers-3D et fournisseur Hugging Face

## Objectif et livrable vérifiable

Isoler l'appel à un modèle image-vers-3D pré-entraîné derrière `Image3DProvider`, puis inspecter le contrat courant du Space avant tout envoi d'image. Le livrable de code est un adaptateur qui n'invente ni nom de paramètre ni sortie, applique un délai maximal et refuse les réponses qui ne sont pas des fichiers GLB 2.0 cohérents.

L'inspection `Client("stabilityai/stable-fast-3d").view_api()` a décrit le bouton `/run_button`. Paramètres observés : `input_image`, `foreground_ratio` (0,85), `remesh_option` (choix `None`, `Triangle`, `Quad`), `vertex_count` (-1) et `texture_size` (1024). Les sorties observées sont `Preview Background Removal` et `3D Model`, de type fichier. Le code relit cette description juste avant chaque génération et s'arrête si le contrat a changé.

Les tests automatiques de cette étape sont locaux et n'appellent pas Hugging Face. Ils protègent l'interprétation d'une description de l'API et les contrôles du fichier. Les trois essais photo réels ont été exécutés, mais se sont terminés par une exception interne du Space sans renvoyer de GLB ; le détail figure dans la section « Essais avec photos ».

## Fichiers de code

### `backend/app/config.py`

La classe immuable `Settings` regroupe l'identifiant du Space, le jeton facultatif, le délai maximal, le nombre d'essais (au plus deux) et le délai de relance. `get_settings()` lit `.env` à la racine et masque l'absence de jeton en gardant un mode anonyme. La validation bloque les valeurs incohérentes avant une requête.

### `backend/app/providers/base.py`

`Image3DProvider` est un protocole Python : tout fournisseur doit exposer `generate(image_path) -> bytes`. Le service de l'étape 4 dépendra de cette interface et non du SDK Hugging Face, ce qui rend le changement de fournisseur possible sans coupler les routes.

### `backend/app/providers/huggingface.py`

`HuggingFaceSpaceProvider` vérifie que l'image existe, consulte l'état du Space avec une échéance, construit le client sans journaliser de jeton, puis appelle `view_api()` avant de soumettre `/run_button`. Il utilise uniquement les paramètres et valeurs par défaut décrits par cette inspection. Une sortie nommée `3D Model` doit fournir un chemin local en `.glb`. Le contrôle final vérifie la signature `glTF`, la version 2 et la longueur déclarée ; il ne remplace pas le chargement visuel du modèle dans le viewer de l'étape 5.

Une panne temporaire reconnue peut être retentée une seule fois. Le délai total reste borné. Les erreurs indiquent que le Space ou son contrat est indisponible, et le jeton est retiré du texte d'erreur.

### `backend/tests/test_huggingface_provider.py`

Les tests utilisent une description locale de la forme de réponse observée par `view_api()`. Ce fixture teste le code d'interprétation ; ce n'est ni un Space simulé utilisé par l'application ni un modèle fabriqué. Les tests vérifient les paramètres, le choix de la bonne sortie, les changements incompatibles et le contrôle de base du GLB. Aucun test automatique ne dépense de quota GPU.

### `.env.example` et `backend/requirements.txt`

`.env.example` documente le Space, le jeton facultatif et les délais sans contenir de secret. `gradio_client` appelle le Space ; `python-dotenv` lit le fichier local ; `httpx2` consulte l'état du Space et reste aussi le transport utilisé par TestClient dans la version de Starlette installée.

## Limites gratuites et licence

La documentation Hugging Face publiée au moment de l'étape indique un quota ZeroGPU journalier de 2 minutes sans authentification et de 5 minutes pour un compte gratuit, avec une priorité de file qui dépend du quota restant. Un Space public peut aussi être en veille, saturé ou indisponible. Ces limites empêchent de promettre un SaaS gratuit à disponibilité constante ; l'API d'un Space public ne constitue pas un SLA.

Stable Fast 3D est sous Stability AI Community License. Pour un service commercial hébergé ou une API, le texte de licence demande une inscription auprès de Stability AI ; il prévoit également une attribution « Powered by Stability AI » pour les produits ou services concernés et des règles distinctes au-delà d'un million de dollars de revenus annuels. Le prototype de soutenance ne constitue pas une autorisation de lancer un SaaS commercial. Revalider la licence et le fournisseur avant tout lancement public.

Sources officielles consultées : [quota ZeroGPU Hugging Face](https://huggingface.co/docs/hub/en/spaces-zerogpu), [API des Spaces](https://huggingface.co/docs/hub/en/spaces-api-endpoints), [licence Stable Fast 3D](https://github.com/Stability-AI/stable-fast-3d/blob/main/LICENSE.md).

## Installer, configurer et vérifier

Depuis la racine du dépôt sous PowerShell :

    Copy-Item .env.example .env

Un jeton HF gratuit est facultatif. Si on en ajoute un, il reste uniquement dans `.env`, qui est ignoré par Git. Depuis `backend` :

    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m pytest -q

La commande pytest ne contacte aucun Space. Son résultat mesuré après l'étape 3 est consigné dans `docs/ETAT.md`.

## Essais avec photos

Les cinq photos d'essai viennent de sources ouvertes et montrent chacune un seul meuble sans personne. Elles restent dans `backend/data/feasibility-inputs/`, dossier local ignoré par Git. Trois premiers candidats Wikimedia (deux tabourets photographiés dans un marché et une chaise en placage prise dans un musée) ont été téléchargés puis écartés après inspection car des personnes étaient visibles dans l'arrière-plan ; ils ne seront pas envoyés à un Space public.

| Fichier local | Objet | Auteur / collection | Source et licence vérifiée |
|---|---|---|---|
| `stool-met-01.jpg` | Tabouret en chêne | The Metropolitan Museum of Art, objet 64.101.896 | [Fiche Met — Public Domain](https://www.metmuseum.org/art/collection/search/203700) |
| `chair-met-01.jpg` | Chaise suisse en bois | The Metropolitan Museum of Art, objet 08.181.16 | [Fiche Met — Public Domain](https://www.metmuseum.org/art/collection/search/190814) |
| `chair-met-02.jpg` | Chaise Savonarola | The Metropolitan Museum of Art, objet 37.80.18 | [Fiche Met — Public Domain](https://www.metmuseum.org/art/collection/search/471206) |
| `chair-bentwood.jpg` | Chaise courbe en bois | Antonio Borrillo | [Commons — CC0](https://commons.wikimedia.org/wiki/File:Chair.JPG) |
| `side-table-met.jpg` | Table d'appoint | Metropolitan Museum of Art / Wikimedia Commons | [Commons — CC0](https://commons.wikimedia.org/wiki/File:Side_table_MET_160176.jpg) |

Fichiers présents mais exclus de l'essai et à ne pas téléverser : `stool-01.jpg`, `stool-03.jpg` et `chair-veneer.jpg`. Ils sont conservés localement pour tracer la sélection, mais montrent des personnes.

La décision d'envoyer ces fichiers au Space public est distincte de la licence des images : utiliser uniquement ces photos libres, sans visages ni données privées. Le 19 octobre 2026, trois appels réels ont été tentés sans jeton HF, après `view_api()` et avec les paramètres qu'il décrivait :

| Photo | Résultat observé | Durée | GLB |
|---|---|---:|---|
| `stool-met-01.jpg` | Échec : « The upstream Gradio app has raised an exception but has not enabled verbose error reporting. » | 13,4 s | Aucun |
| `chair-bentwood.jpg` | Même exception interne générique | 41,1 s | Aucun |
| `side-table-met.jpg` | Même exception interne générique | 11,6 s | Aucun |

Les trois photos et leurs sources étaient différentes ; l'erreur répétée pointe vers l'application Space ou son inférence, mais son message public ne permet pas d'en connaître la cause. Le Space affichait « Running on Zero » ; aucun message de quota ou de file d'attente n'a été reçu. Aucun fichier GLB n'a été écrit. Le test live est donc **non concluant et bloqué** ; il ne prouve ni la qualité de Stable Fast 3D ni le bon fonctionnement complet de la génération. Ne pas présenter cet essai comme une réussite.

## Pourquoi cette conception

- Le protocole `Image3DProvider` permet au service et au viewer de ne pas dépendre du SDK d'un seul fournisseur.
- La relecture de `view_api()` protège contre une interface de Space qui évolue.
- Le délai total et la relance limitée évitent une requête qui bloque l'application indéfiniment.
- La vérification des octets empêche de confondre une image d'aperçu ou une erreur HTML avec un modèle GLB.
- Les tests hors réseau sont reproductibles et ne consomment pas le quota gratuit.
- Le statut de génération, la persistance et l'endpoint de conversion ne sont pas inclus ici ; ils appartiennent à l'étape 4.
