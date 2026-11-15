# Comprendre Forma3D Studio — le guide complet

> Document pédagogique pour comprendre **tout** le projet et l'expliquer à un jury.
> Il décrit uniquement ce qui existe dans le dépôt au 15 novembre 2026 (dernier commit lu : `95f2d86`, après l'ajout de la suppression des modèles, de la session persistante facultative et de l'architecture cible).
> Quand une information n'a pas pu être vérifiée dans le code, elle est marquée **« à vérifier »**.

---

## 0. Comment lire ce document

**En une phrase :** chaque section commence par un résumé « En une phrase », puis détaille avec des tableaux, des schémas et des exemples.

- **Si vous avez 10 minutes :** lisez les sections 1, 3 et 11 (le projet, l'architecture, les parcours).
- **Pour la soutenance :** ajoutez les sections 10 (le site page par page) et 12 (la sécurité).
- **Pour comprendre le code :** sections 4, 5, 6 et 8.
- **Si le badge « Serveur 3D » est rouge :** section 17.
- **Pour la suite du projet (SaaS) :** section 18 et `docs/ARCHITECTURE-CIBLE.md`.
- **Pour Git, les branches et les pull requests :** section 19.
- Les sections importantes se terminent par trois encadrés : **Un exemple concret**, **Une analogie** et **Ce que je réponds si on me demande pourquoi**.
- Les schémas sont écrits en **Mermaid** (un langage texte que GitHub transforme en dessin). Sur GitHub, ils s'affichent automatiquement.
- Des **analogies** avec ce que vous connaissez déjà (Angular, Spring Boot, Keycloak, Oracle PL/SQL, Symfony) sont signalées par 🔁.

Légende :

| Symbole | Sens |
|---|---|
| 🔁 | Analogie avec une technologie que vous connaissez |
| ⚠️ | Piège, limite ou point temporaire |
| ✅ | Vérifié dans le code ou par un test |
| **à vérifier** | Information non confirmée par le code |

---

## 1. Le projet en 5 minutes

**En une phrase :** Forma3D Studio transforme une photo de petit meuble en modèle 3D, permet de le vérifier, puis de l'afficher sur le site d'une boutique en ligne.

### Le problème

Une boutique en ligne montre ses produits avec des photos plates. Un modèle 3D (que l'on fait tourner à la souris) aide l'acheteur, mais il coûte cher à fabriquer : il faut un logiciel 3D et une personne formée.

### La solution

1. La propriétaire du Studio envoie **une photo** d'un meuble (chaise, tabouret, table d'appoint).
2. Un **modèle d'intelligence artificielle déjà entraîné** (TripoSR ou TRELLIS) fabrique un fichier 3D `.glb`.
3. Le Studio affiche ce modèle, le compare à la photo et permet de le télécharger.
4. La propriétaire **active l'intégration** : un site partenaire peut alors afficher le modèle avec une simple balise HTML.
5. Un développeur partenaire peut aussi piloter Forma3D par une **API** protégée par une **clé API**.

### Pour qui ?

| Personne | Ce qu'elle fait |
|---|---|
| **La propriétaire** (vous) | Utilise le Studio : crée, importe, vérifie et publie les modèles. Seule personne qui se connecte. |
| **Le développeur d'une boutique** | Utilise une clé API et le code d'intégration (iframe ou widget). |
| **Le visiteur final** | Voit et fait tourner le modèle 3D sur la page produit de la boutique. |
| **Le jury** | Doit comprendre un prototype honnête sur ses limites. |

### Ce que le projet n'est PAS

- ❌ **Aucun entraînement de modèle** : le projet utilise uniquement des modèles **pré-entraînés** (déjà appris par d'autres équipes). Aucun réseau de neurones n'est entraîné ou ajusté.
- ❌ **Aucune API payante** : tout est gratuit. Les services gratuits ont des **quotas** (limites journalières) et peuvent être hors ligne.
- ❌ **Pas un service de production** : c'est un prototype de soutenance, à utiliser en local tant qu'il n'est pas déployé en HTTPS.
- ❌ **Pas de comptes multiples** : un seul mot de passe, celui de la propriétaire. Le passage à un SaaS multi-clients est **conçu mais pas codé** (section 18 et `docs/ARCHITECTURE-CIBLE.md`).
- ❌ **Pas une reconstruction exacte** : une seule photo ne montre pas l'arrière de l'objet ; le modèle est une **estimation**, pas un plan de fabrication.

---

## 2. Le format `.glb`

**En une phrase :** un fichier `.glb` est un objet 3D complet (forme, couleurs, matériaux) rangé dans un seul fichier binaire que les navigateurs savent afficher.

### Ce que c'est

- **glTF** (GL Transmission Format) est le format 3D standard du web, publié par le Khronos Group. On le surnomme « le JPEG de la 3D ».
- **GLB** est la version **binaire** de glTF : tout tient dans **un seul fichier**.
- Un fichier GLB contient deux parties appelées **chunks** (morceaux) :

```mermaid
flowchart LR
    A["En-tête 12 octets<br/>magic glTF, version 2, longueur"] --> B["Chunk JSON<br/>description de la scène :<br/>maillages, matériaux, accesseurs"]
    B --> C["Chunk BIN<br/>données brutes :<br/>positions, couleurs, indices, textures"]
```

| Partie | Contenu | 🔁 Analogie |
|---|---|---|
| En-tête | Le mot `glTF`, la version `2`, la longueur totale | La signature d'un fichier |
| Chunk JSON | La **description** : quels maillages, quels matériaux, où lire les nombres | Le schéma d'une table Oracle |
| Chunk BIN | Les **nombres** : coordonnées des sommets, triangles, image de texture | Les lignes de la table |

Le code du projet vérifie cette structure dans `DemoGallery.is_valid_glb_2()` (`backend/app/services/demo_gallery.py`) et `HuggingFaceSpaceProvider._read_glb()` (`backend/app/providers/huggingface.py`). ✅

### Vocabulaire de la 3D

| Terme | Définition simple |
|---|---|
| **Sommet** (vertex) | Un point dans l'espace (x, y, z) |
| **Triangle** | Trois sommets reliés ; la surface d'un objet est faite de milliers de triangles |
| **Maillage** (mesh) | L'ensemble des triangles d'un objet |
| **Normale** | Une flèche perpendiculaire à la surface ; elle sert à calculer la lumière |
| **Matériau** | Comment la surface réagit à la lumière : couleur, aspect **métallique**, **rugosité** |
| **Texture** | Une image collée sur la surface (comme un papier peint) |

### Couleurs de sommets contre textures

| | Couleurs de sommets (TripoSR) | Texture (TRELLIS) |
|---|---|---|
| Principe | Chaque sommet porte une couleur ; entre deux sommets, la couleur est mélangée | Une image PNG est plaquée sur la surface grâce à des coordonnées UV |
| Précision | Faible : les détails fins disparaissent | Bonne : motifs, cannage de l'assise visibles |
| Mesuré dans le projet | 20 000 à 65 000 sommets, aucun matériau, aucune normale | Texture PNG d'environ 1 Mo, un matériau, pas de normales |

⚠️ **Piège découvert dans le projet** : quand un GLB n'a pas de matériau, ou qu'il oublie la valeur `metallicFactor`, la norme glTF le considère **100 % métallique**. Le modèle paraît alors presque noir. Le projet corrige cela à deux endroits (voir section 7) : à l'affichage (`frontend/js/views/model-appearance.js`) et dans le fichier lui-même (`backend/app/services/glb_finisher.py`).

### Comment un navigateur l'affiche

Le navigateur utilise **WebGL** (la carte graphique depuis JavaScript). Le projet n'écrit pas de WebGL à la main : il utilise le composant **`<model-viewer>`** de Google, chargé depuis un CDN dans `frontend/index.html`. On écrit simplement :

```html
<model-viewer src="/models/gallery/chair-bentwood" camera-controls auto-rotate></model-viewer>
```

### Où les GLB sont stockés

| Dossier | Contenu | Suivi par Git ? |
|---|---|---|
| `backend/storage/models/` | GLB générés, importés ou copiés depuis les exemples (nommés par un UUID) | ❌ non (ignoré) |
| `backend/storage/images/` | Photos sources envoyées | ❌ non |
| `backend/data/feasibility-results/` | Les 5 GLB du catalogue d'exemples | ❌ non |
| `backend/data/feasibility-results-triposr/` | Sauvegarde des 3 anciens exemples TripoSR remplacés par TRELLIS | ❌ non |
| `backend/data/trials/` | GLB bruts des essais de fournisseurs | ❌ non |

Les fichiers 3D et la base sont **locaux** : ils ne partent jamais sur GitHub.

### Comment un GLB entre dans le projet

1. **Génération** : une photo est envoyée au fournisseur (TripoSR ou TRELLIS), qui renvoie un GLB ; le service le **finit** (matériau, normales) puis l'enregistre.
2. **Import** : la propriétaire importe un `.glb` existant depuis « Mes modèles ».
3. **Copie d'exemple** : un exemple du catalogue est copié dans « Mes modèles ».

### Ouvrir un GLB sur votre PC

- **Windows** : double-cliquez sur le fichier ; il s'ouvre dans la **Visionneuse 3D** de Windows (application « 3D Viewer », à installer depuis le Microsoft Store si elle n'est pas présente — **à vérifier** sur votre version de Windows).
- **Blender** (gratuit) : menu *File → Import → glTF 2.0 (.glb/.gltf)*.
- **Dans le Studio** : page Créer, bouton « Aperçu d'un fichier GLB (sans enregistrer) » ; le fichier est lu par le navigateur et n'est pas envoyé au serveur.

---

## 3. Architecture

**En une phrase :** un navigateur parle à un serveur FastAPI, qui range les informations dans SQLite, les fichiers sur le disque, et demande les modèles 3D à un service d'IA externe.

### 3.1 Les composants

```mermaid
flowchart LR
    subgraph Navigateur
        UI["Studio<br/>HTML + CSS + modules JS"]
        MV["model-viewer<br/>affichage 3D"]
    end
    subgraph Serveur["Serveur FastAPI (uvicorn)"]
        R["Routeurs<br/>routes HTTP"]
        S["Services<br/>logique métier"]
        P["Fournisseurs 3D<br/>TripoSR ou TRELLIS"]
    end
    DB[("SQLite<br/>backend/data/forma3d.sqlite3")]
    FS[("Disque<br/>backend/storage/")]
    HF["Service IA externe<br/>Hugging Face Space ou Colab"]
    Site["Site d'une boutique<br/>iframe ou widget"]

    UI -->|fetch JSON| R
    MV -->|télécharge le GLB| R
    R --> S
    S --> DB
    S --> FS
    S --> P
    P -->|gradio_client| HF
    Site -->|/embed et /public| R
```

🔁 **Analogie Spring Boot** : les **routeurs** sont les `@RestController`, les **services** sont les `@Service`, les **dépôts** (repositories) sont les `@Repository`. FastAPI joue le rôle de Spring Boot, uvicorn celui de Tomcat.

🔁 **Analogie Angular** : le frontend n'utilise **pas** Angular. C'est du JavaScript « vanille » organisé en modules : `router.js` joue le rôle du `RouterModule`, chaque fichier de `pages/` est comme un composant, `api.js` est comme un `HttpClient` centralisé dans un service.

### 3.2 Le parcours complet d'un modèle

```mermaid
flowchart LR
    A["1. Photo<br/>JPG, PNG ou WebP"] --> B["2. Validation<br/>format, 10 Mo max"]
    B --> C["3. Préparation<br/>carré, marges, 512 px min"]
    C --> D["4. Génération<br/>TripoSR ou TRELLIS"]
    D --> E["5. Finition GLB<br/>matériau mat + normales"]
    E --> F["6. Stockage<br/>disque + SQLite"]
    F --> G["7. Viewer<br/>fiche du modèle"]
    G --> H["8. Activation<br/>de l'intégration"]
    H --> I["9. Site client<br/>iframe ou widget"]
```

### 3.3 Séquence d'une génération

```mermaid
sequenceDiagram
    actor P as Propriétaire
    participant N as Navigateur
    participant A as FastAPI
    participant G as GenerationService
    participant F as Fournisseur 3D
    participant D as SQLite et disque

    P->>N: dépose une photo et clique « Créer le modèle 3D »
    N->>A: POST /models (photo + catégorie)
    A->>A: valide le fichier (UploadValidator)
    A->>G: create_generation()
    G->>D: enregistre la photo, statut PENDING
    A-->>N: 202 Accepted + status_url
    A->>G: run() en tâche de fond
    G->>D: statut RUNNING
    G->>G: prépare une copie carrée (ImagePreparer)
    G->>F: generate(photo préparée)
    F-->>G: octets GLB
    G->>G: finit le GLB (glb_finisher)
    G->>D: enregistre le GLB, statut DONE
    loop toutes les 1,5 s
        N->>A: GET /models/{id}
        A-->>N: PENDING, RUNNING puis DONE
    end
    N->>A: GET /models/{id}/glb
    A-->>N: fichier GLB affiché dans model-viewer
```

⚠️ Le statut terminé s'appelle **`DONE`** dans le code (pas `COMPLETED`). ✅


### 3.4 Un exemple concret : la photo du fauteuil vert, de bout en bout

Le 15 novembre 2026, la propriétaire a envoyé `fauteuil-retro-sur-fond-blanc….webp` (fauteuil vert, fond blanc uni) dans la catégorie « Chaise ».

| Étape | Ce qui s'est passé réellement | Où dans le code |
|---|---|---|
| 1 | Le navigateur envoie la photo : `POST /models` | `frontend/js/api.js` → `createGeneration()` |
| 2 | Le serveur vérifie extension, type, **signature** (premiers octets) et taille ≤ 10 Mo | `services/upload_validator.py` |
| 3 | La photo est rangée dans `backend/storage/images/{uuid}.webp` ; une ligne `PENDING` est créée dans SQLite | `generation_service.create_generation()` |
| 4 | Réponse immédiate `202 Accepted` ; la génération continue en tâche de fond (`RUNNING`) | `routers/models.py`, `BackgroundTasks` |
| 5 | Une copie carrée à marges est préparée (512 px minimum) | `services/image_preparer.py` |
| 6 | TRELLIS : connexion au Space, `/start_session`, détourage `/preprocess_image`, puis `/generate_and_extract_glb` | `providers/trellis.py` |
| 7 | Le GLB reçu est vérifié, fini (matériau mat, normales) et écrit dans `backend/storage/models/{uuid}.glb` ; statut `DONE` | `glb_finisher.py`, `local_storage.py` |
| 8 | La page, qui interrogeait `GET /models/{id}` toutes les 1,5 s, affiche le modèle | `pages/create.js` |
| 9 | Sur la fiche, l'intégration est activée : le modèle reçoit une adresse publique `/embed/{public_id}` | `PATCH /models/{id}/integration` |
| 10 | Une page servie sur le port 8081 (« site vitrine » de test) affiche le fauteuil grâce au widget | `frontend/widget.js`, `EMBED_ALLOWED_ORIGINS` |

> **Une analogie.** 🔁 C'est une application Spring Boot classique : un `@RestController` reçoit le fichier, un `@Service` orchestre, un `@Repository` écrit en base, et une méthode `@Async` fait le travail long. La différence : le « gros calcul » (l'IA) est délégué à un service externe, comme un microservice appelé par HTTP.

> **Ce que je réponds si on me demande pourquoi.** « J'ai séparé routes, services, dépôts et fournisseurs pour que chaque couche soit testable seule et remplaçable : je peux changer de fournisseur 3D ou de base de données sans réécrire le reste. La génération est asynchrone parce qu'elle dure une à deux minutes : on ne bloque pas la requête HTTP pendant ce temps. »

---

## 4. Technologies

**En une phrase :** le projet utilise volontairement peu de technologies, toutes gratuites, pour rester explicable.

### 4.1 Tableau récapitulatif

| Technologie | Rôle | Pourquoi ce choix | Alternative possible | Où dans le code |
|---|---|---|---|---|
| **Python 3** | Langage du serveur | Écosystème IA (gradio_client) | Java | `backend/` |
| **FastAPI** | Framework web | Simple, rapide, documentation automatique | Spring Boot, Symfony, Flask | `backend/app/main.py`, `routers/` |
| **uvicorn** | Serveur HTTP qui exécute FastAPI | Standard pour FastAPI | Tomcat (Java), gunicorn | commande de lancement |
| **Pydantic** | Validation des données JSON | Intégré à FastAPI | Bean Validation (Java) | `backend/app/schemas.py` |
| **python-multipart** | Lecture des formulaires avec fichier | Nécessaire pour l'upload | — | upload `POST /models` |
| **python-dotenv** | Lecture du fichier `.env` | Garde les secrets hors du code | variables système | `backend/app/config.py` |
| **SQLite** | Base de données | Un seul fichier, aucun serveur à installer | PostgreSQL, Oracle | `repositories/sqlite_repository.py` |
| **Pillow** | Traitement d'image | Léger, sans IA | OpenCV | `services/image_preparer.py` |
| **gradio_client** | Appel des services IA Gradio | Bibliothèque officielle | requêtes HTTP à la main | `providers/huggingface.py`, `providers/trellis.py` |
| **httpx2** | Requêtes HTTP (contrôle de santé du fournisseur) | Client HTTP moderne | requests | `providers/huggingface.py`, `providers/trellis.py` |
| **Hugging Face Spaces** | Hébergement gratuit de démonstrations IA | Gratuit avec quota | Replicate (payant) | configuration `TRELLIS_SPACE_ID` |
| **Google Colab** | GPU gratuit temporaire pour TripoSR | Gratuit, sans carte | serveur GPU payant | `tools/colab/triposr_server.ipynb` |
| **TripoSR** | Modèle image→3D (couleurs de sommets) | Premier modèle qui a fonctionné | — | fournisseur par défaut |
| **TRELLIS** | Modèle image→3D (texture) | Meilleures couleurs mesurées | Hunyuan3D (licence exclut l'UE) | `providers/trellis.py` |
| **model-viewer** | Composant web d'affichage 3D | Une balise HTML suffit | Three.js | `frontend/index.html`, `pages/` |
| **Modules ES** | Découpage du JavaScript en fichiers | Natif, sans outil de build | Angular, webpack | `frontend/js/` |
| **Web Components** | Balise HTML personnalisée `<forma3d-viewer>` | Fonctionne sur tout site | iframe seule | `frontend/widget.js` |
| **pytest** | Tests automatiques | Standard Python | JUnit | `backend/tests/` |
| **GitHub Actions** | Intégration continue | Gratuit pour un dépôt GitHub | GitLab CI, Jenkins | `.github/workflows/ci.yml` |

### 4.2 Explications simples

- **FastAPI** : on écrit une fonction Python et on la décore avec `@router.get("/chemin")`. FastAPI la transforme en route HTTP, vérifie les données et génère une documentation interactive sur `/docs`. 🔁 C'est un `@GetMapping` de Spring Boot.
- **uvicorn** : le programme qui écoute sur un port (ex. 8000) et transmet les requêtes à FastAPI. 🔁 Tomcat pour Spring Boot.
- **Pydantic** : des classes qui décrivent la forme d'un JSON (`class LoginRequest(BaseModel): password: str`). Si le JSON reçu ne correspond pas, FastAPI répond 422. 🔁 DTO + `@Valid`.
- **SQLite** : une base SQL complète dans **un seul fichier**. Pas de serveur à installer. 🔁 Comme Oracle, mais sans instance ni utilisateur.
- **Pillow** : ouvre une image, la redimensionne, ajoute des marges, mesure la netteté.
- **gradio_client** : **Gradio** est une bibliothèque qui crée une page web autour d'un modèle IA. `gradio_client` permet d'appeler cette page **depuis un programme**. Le projet appelle toujours `view_api()` d'abord pour lire les fonctions réellement disponibles (le « contrat »).
- **Hugging Face Spaces** : un site qui héberge gratuitement des démonstrations IA. Le GPU gratuit (**ZeroGPU**) a un **quota par jour**.
- **TripoSR** : modèle de Stability AI et Tripo AI, qui produit une forme fidèle mais des couleurs approximatives.
- **TRELLIS** : modèle de Microsoft, qui produit un maillage avec une **texture** (meilleures couleurs), mais qui peut inventer des parties cachées.
- **model-viewer** : une balise HTML fournie par Google qui affiche un GLB avec rotation, zoom et éclairage.
- **Modules ES** : `import { x } from "./api.js?v=..."`. Le navigateur charge les fichiers à la demande. Le paramètre `?v=20261112-d1` est une **clé de cache** : on la change quand le code change, pour que le navigateur ne garde pas l'ancienne version.
- **Web Components** : on définit une nouvelle balise (`customElements.define("forma3d-viewer", ...)`) utilisable dans n'importe quelle page HTML, même sans framework.
- **pytest** : chaque fonction `test_...` est exécutée ; si une ligne `assert` échoue, le test échoue.
- **GitHub Actions** : à chaque `git push`, GitHub lance les tests sur une machine virtuelle (voir section 14).

---

## 5. Arborescence et relations entre fichiers

**En une phrase :** le dépôt est découpé en `backend/` (serveur Python), `frontend/` (interface servie par le serveur), `docs/` (documentation) et quelques outils, chaque fichier ayant un seul rôle.

### 5.1 Tous les fichiers suivis par Git

#### Racine

| Fichier | Rôle |
|---|---|
| `.env.example` | Modèle des variables d'environnement, **sans secret** (voir section 9) |
| `.github/workflows/ci.yml` | Intégration continue : tests à chaque push |
| `.gitignore` | Liste de ce que Git ne doit pas suivre (`.env`, base, GLB, photos…) |
| `AGENTS.md` | Règles permanentes du projet pour les assistants IA |
| `DESIGN.md` | Règles visuelles : couleurs, typographie, composants |
| `PRODUCT.md` | Vision produit, utilisateurs, limites |
| `README.md` | Présentation et démarrage du dépôt |

#### Backend — application (`backend/app/`)

| Fichier | Rôle |
|---|---|
| `backend/README.md` | Explications du backend |
| `backend/requirements.txt` | Dépendances Python (FastAPI, uvicorn, Pillow…) |
| `backend/app/__init__.py` | Fait de `app` un paquet Python (vide) |
| `backend/app/main.py` | **Point d'entrée** : crée l'application, choisit le fournisseur, branche les routeurs, sert la page `/` |
| `backend/app/config.py` | Lit les variables d'environnement et les valide (`Settings`) |
| `backend/app/models.py` | Objets métier : `GenerationRecord`, `CategoryRecord`, `APIKeyRecord`, statuts, origines |
| `backend/app/schemas.py` | Formes des réponses et requêtes JSON (Pydantic) |
| `backend/app/providers/__init__.py` | Paquet des fournisseurs (vide) |
| `backend/app/providers/base.py` | Contrat `Image3DProvider` : « une image entre, des octets GLB sortent » |
| `backend/app/providers/huggingface.py` | Fournisseur **TripoSR** (Space Hugging Face ou URL Gradio Colab) |
| `backend/app/providers/trellis.py` | Fournisseur **TRELLIS** (Space public, détourage puis GLB texturé) |
| `backend/app/repositories/__init__.py` | Paquet des dépôts (vide) |
| `backend/app/repositories/base.py` | Contrat `GenerationRepository` : toutes les opérations de base de données |
| `backend/app/repositories/sqlite_repository.py` | Implémentation SQLite : tables, migrations, requêtes |
| `backend/app/routers/__init__.py` | Paquet des routeurs (vide) |
| `backend/app/routers/auth.py` | Connexion : `/auth/login`, `/auth/logout`, `/auth/me`, dépendance `require_owner` |
| `backend/app/routers/models.py` | Modèles du Studio : création, galerie, import, copie, intégration, fichiers ; routes `/public` |
| `backend/app/routers/categories.py` | CRUD des catégories |
| `backend/app/routers/api_keys.py` | Gestion des clés API et dépendance `require_api_key` |
| `backend/app/routers/api_v1.py` | API externe versionnée `/api/v1` (protégée par clé) |
| `backend/app/routers/embed.py` | Page publique `/embed/{public_id}` affichée dans une iframe |
| `backend/app/services/__init__.py` | Paquet des services (vide) |
| `backend/app/services/generation_service.py` | Orchestration : états, préparation, fournisseur, finition, stockage |
| `backend/app/services/upload_validator.py` | Vérifie format et taille de la photo |
| `backend/app/services/image_preparer.py` | Prépare une copie carrée de la photo et signale flou ou petite taille |
| `backend/app/services/glb_finisher.py` | Ajoute matériau mat et normales aux GLB générés |
| `backend/app/services/category_service.py` | Règles métier des catégories |
| `backend/app/services/api_key_service.py` | Création, empreinte, vérification, quotas des clés |
| `backend/app/services/demo_gallery.py` | Liste fixe des 5 exemples du catalogue |
| `backend/app/services/owner_auth.py` | Mot de passe, jetons de session signés, limite de tentatives |
| `backend/app/storage/__init__.py` | Paquet du stockage (vide) |
| `backend/app/storage/base.py` | Contrat `Storage` (enregistrer photo et GLB) |
| `backend/app/storage/local_storage.py` | Stockage sur le disque local, écriture atomique |

#### Backend — tests (`backend/tests/`)

| Fichier | Ce qu'il vérifie |
|---|---|
| `conftest.py` | Ouvre la session propriétaire pour les tests, sauf ceux marqués `real_auth` |
| `test_api_keys.py` | Empreinte seule, secret affiché une fois, révocation, suppression définitive, quotas |
| `test_api_settings.py` | Validation des quotas et des origines CORS/iframe |
| `test_api_v1.py` | API externe : clé, statuts, erreurs, quota |
| `test_auth.py` | Connexion : 401 sans cookie, mot de passe faux, limite, routes publiques ouvertes, clé de session fixe facultative |
| `test_categories_api.py` | Routes des catégories |
| `test_category_repository.py` | Catégories dans SQLite |
| `test_category_service.py` | Règles des catégories |
| `test_demo_gallery.py` | Catalogue d'exemples : seuls les fichiers connus et valides (isolé de la vraie base SQLite) |
| `test_embed.py` | Page `/embed` et politique de sécurité CSP |
| `test_frontend.py` | Fichiers du frontend : présence des éléments, `fetch` seulement dans `api.js` |
| `test_generation_repository.py` | Historique des générations dans SQLite, redémarrage |
| `test_generation_service.py` | États PENDING → DONE ou FAILED, photo préparée |
| `test_glb_finisher.py` | Finition des GLB sans modifier la géométrie |
| `test_health.py` | Routes `/health` et `/health/provider` (indépendant de `backend/.env`) |
| `test_huggingface_provider.py` | Fournisseur TripoSR avec client simulé |
| `test_image_preparer.py` | Préparation de la photo |
| `test_local_storage.py` | Écriture des fichiers |
| `test_model_library.py` | Import GLB et copie d'exemple |
| `test_models_api.py` | Routes `/models` |
| `test_model_deletion.py` | Suppression d'un modèle : ligne, GLB et photo effacés ; refus pendant la création, pour un exemple ou sans connexion |
| `test_trellis_provider.py` | Fournisseur TRELLIS avec client simulé |
| `test_trial_tools.py` | Outils d'essai de fournisseurs |
| `test_upload_validator.py` | Validation des photos |

#### Frontend (`frontend/`)

| Fichier | Rôle |
|---|---|
| `frontend/README.md` | Explications du frontend |
| `frontend/index.html` | **Coque** : en-tête, menu, pied de page, point de montage `#app` |
| `frontend/favicon.svg` | Icône d'onglet |
| `frontend/widget.js` | Balise `<forma3d-viewer>` pour les sites partenaires |
| `frontend/css/theme.css` | Couleurs, espacements, animations |
| `frontend/css/components.css` | Styles de tous les composants (14 sections) |
| `frontend/js/main.js` | Démarrage : vérifie la session, lance le routeur, surveille le serveur 3D |
| `frontend/js/router.js` | Routes `#/...`, protection par connexion, changement de page |
| `frontend/js/api.js` | **Seul fichier qui appelle le serveur** (`fetch`) |
| `frontend/js/auth.js` | État de connexion (lu sur `/auth/me`) |
| `frontend/js/state.js` | État temporaire d'une génération en cours |
| `frontend/js/format.js` | Dates relatives, tailles, durées, fournisseur des exemples |
| `frontend/js/pages/login.js` | Page Connexion |
| `frontend/js/pages/dashboard.js` | Page Accueil |
| `frontend/js/pages/create.js` | Page Créer |
| `frontend/js/pages/viewer-markup.js` | HTML du viewer de la page Créer |
| `frontend/js/pages/models.js` | Page Mes modèles |
| `frontend/js/pages/model-detail.js` | Fiche d'un modèle |
| `frontend/js/pages/examples.js` | Page Exemples |
| `frontend/js/pages/categories.js` | Page Catégories |
| `frontend/js/pages/api-keys.js` | Page Clés API |
| `frontend/js/pages/guide.js` | Page Guide d'intégration |
| `frontend/js/views/uploader.js` | Dépôt et validation de la photo |
| `frontend/js/views/progress.js` | Les 5 étapes du suivi de création |
| `frontend/js/views/viewer.js` | Viewer 3D de la page Créer |
| `frontend/js/views/gallery.js` | Cartes de modèles et filtres |
| `frontend/js/views/categories.js` | Gestion des catégories |
| `frontend/js/views/confirm-dialog.js` | Fenêtre de confirmation |
| `frontend/js/views/illustrations.js` | Dessin SVG du cube (états vides) |
| `frontend/js/views/model-appearance.js` | Correction du matériau et recadrage de la caméra |

#### Documentation (`docs/`)

| Fichier | Rôle |
|---|---|
| `docs/COMPRENDRE-FORMA3D.md` | Ce guide |
| `docs/ARCHITECTURE-CIBLE.md` | Conception du futur SaaS multi-clients (rien n'est codé) |
| `docs/ETAT.md` | État d'avancement, étape par étape |
| `docs/STRUCTURE.md` | Rôle de chaque fichier et dossier |
| `docs/STOCKAGE.md` | Base SQLite, fichiers, intégration |
| `docs/INTEGRATION.md` | Guide pour le développeur d'une boutique |
| `docs/ALTERNATIVES-3D.md` | Comparaison des fournisseurs 3D gratuits |
| `docs/QUALITE-3D.md` | Grille de qualité et résultats d'essais |
| `docs/etapes/.gitkeep` | Garde le dossier dans Git |
| `docs/etapes/etape-01.md` | Structure et contrôle de santé |
| `docs/etapes/etape-02.md` | Validation de l'upload |
| `docs/etapes/etape-03.md` | Contrat image→3D et fournisseur Hugging Face |
| `docs/etapes/etape-04.md` | Génération, états et stockage local |
| `docs/etapes/etape-05.md` | Interface modulaire et viewer |
| `docs/etapes/etape-06.md` | Essais TripoSR réels |
| `docs/etapes/etape-06-colab.md` | TripoSR, Colab et limites du serveur public |
| `docs/etapes/etape-07.md` | Fiabilité et qualité |
| `docs/etapes/etape-08.md` | SQLite et historique persistant |
| `docs/etapes/etape-09.md` | CRUD des catégories |
| `docs/etapes/etape-10.md` | Préparation locale de la photo |
| `docs/etapes/etape-11.md` | Refonte de la navigation |
| `docs/etapes/etape-11b.md` | Refonte de la page Créer |
| `docs/etapes/etape-12.md` | Import GLB et bibliothèque unifiée |
| `docs/etapes/etape-13.md` | Identifiant public et activation (Sprint 5a) |
| `docs/etapes/etape-14.md` | Clés API (Sprint 5b) |
| `docs/etapes/etape-15.md` | API versionnée (Sprint 5c) |
| `docs/etapes/etape-16.md` | Intégration dans une boutique (Sprint 5d) |
| `docs/etapes/etape-16b.md` | Refonte visuelle du Studio |
| `docs/etapes/etape-17.md` | Guide intégrateur et preuve sur un autre site (Sprint 5e) |
| `docs/etapes/etape-18.md` | Connexion côté serveur (Sprint 5f) |
| `docs/etapes/etape-19.md` | Rendu fidèle des GLB (sous-étape A) |
| `docs/etapes/etape-20.md` | Finition serveur des GLB (sous-étape B) |
| `docs/etapes/etape-21.md` | Grille de qualité et essais de fournisseurs (sous-étape C) |
| `docs/etapes/etape-22.md` | TRELLIS branché dans Forma3D (sous-étape C3) |
| `docs/etapes/etape-23.md` | Suppression d'un modèle depuis sa fiche |
| `docs/etapes/etape-24.md` | Clé de session fixe facultative (`FORMA3D_SESSION_SECRET`) |
| `docs/archive/v1/AGENTS-ancien.md` | Ancienne version des règles (historique) |
| `docs/archive/v1/PROMPT-1-v1.md` | Ancienne consigne de démarrage (historique) |
| `docs/archive/v1/etapes/etape-01-v1.md` | Ancienne étape 1 (historique) |
| `docs/archive/v1/etapes/etape-02-v1.md` | Ancienne étape 2 (historique) |

#### Outils et exemples

| Fichier | Rôle |
|---|---|
| `examples/integration.html` | Faux « site de boutique » pour tester le widget |
| `scripts/dev.ps1` | Script Windows : crée l'environnement, lance les tests **isolés de `backend/.env`**, puis démarre le serveur sur le port 8001 (avec `backend/.env`) |
| `tools/colab/triposr_server.ipynb` | Notebook Colab historique de TripoSR (hors application) |
| `tools/trials/trial_trellis.py` | Essai TRELLIS reproductible (hors application) |
| `tools/trials/trial_models.py` | Essai de plusieurs modèles (hors application) |

### 5.2 Qui importe qui — backend

```mermaid
flowchart TD
    main["main.py"] --> config["config.py"]
    main --> hf["providers/huggingface.py"]
    main --> tr["providers/trellis.py"]
    main --> repo["repositories/sqlite_repository.py"]
    main --> rauth["routers/auth.py"]
    main --> rmodels["routers/models.py"]
    main --> rcat["routers/categories.py"]
    main --> rkeys["routers/api_keys.py"]
    main --> rv1["routers/api_v1.py"]
    main --> rembed["routers/embed.py"]
    main --> gen["services/generation_service.py"]
    main --> keys["services/api_key_service.py"]
    main --> cat["services/category_service.py"]
    main --> demo["services/demo_gallery.py"]
    main --> owner["services/owner_auth.py"]
    main --> store["storage/local_storage.py"]
    tr --> hf
    hf --> base["providers/base.py"]
    tr --> base
    rauth --> owner
    rv1 --> rkeys
    rv1 --> gen
    rmodels --> gen
    rmodels --> val["services/upload_validator.py"]
    gen --> prep["services/image_preparer.py"]
    gen --> fin["services/glb_finisher.py"]
    gen --> demo
    gen --> repo
    gen --> store
    keys --> repo
    cat --> repo
    repo --> models["models.py"]
```

### 5.3 Qui importe qui — frontend

```mermaid
flowchart TD
    index["index.html"] --> main["main.js"]
    main --> auth["auth.js"]
    main --> router["router.js"]
    main --> api["api.js"]
    auth --> api
    router --> pages["pages/*.js"]
    pages --> api
    pages --> views["views/*.js"]
    pages --> format["format.js"]
    views --> api
    views --> appearance["views/model-appearance.js"]
    views --> state["state.js"]
    api --> serveur[("Serveur FastAPI")]
```

Règle vérifiée par un test (`test_frontend.py`) : **seul `api.js` contient `fetch(`**. ✅ 🔁 Comme un service Angular unique qui centralise tous les appels `HttpClient`.

### 5.4 La chaîne complète sur un exemple réel : « Créer le modèle 3D »

| # | Couche | Fichier et fonction | Ce qui se passe |
|---|---|---|---|
| 1 | Page | `frontend/js/views/uploader.js` → écouteur `submit` du formulaire `#upload-form` | Vérifie qu'une photo et une catégorie sont choisies, puis appelle `startGeneration` |
| 2 | Page | `frontend/js/pages/create.js` → `startGeneration()` | Passe en mode « occupé », lance le chronomètre |
| 3 | Appel HTTP | `frontend/js/api.js` → `createGeneration(photo, category)` | `POST /models` avec un `FormData` |
| 4 | Route | `backend/app/routers/models.py` → route `POST /models` | Protégée par `require_owner` ; valide le fichier avec `UploadValidator` |
| 5 | Service | `GenerationService.create_generation()` | Enregistre la photo, crée l'enregistrement `PENDING` |
| 6 | Dépôt | `SQLiteGenerationRepository.save_generation()` | Insère la ligne dans `generations` |
| 7 | Tâche de fond | `GenerationService.run()` | Passe en `RUNNING`, prépare la photo (`ImagePreparer`) |
| 8 | Fournisseur | `HuggingFaceSpaceProvider.generate()` ou `TrellisSpaceProvider.generate()` | Appelle le service IA et vérifie le GLB reçu |
| 9 | Service | `_finish_generated_model()` → `glb_finisher.finish_glb()` | Ajoute matériau mat et normales |
| 10 | Stockage | `LocalStorage.save_model()` | Écrit `backend/storage/models/{id}.glb` |
| 11 | Dépôt | `save_generation()` | Statut `DONE`, chemin du GLB, durée |
| 12 | Page | `create.js` → `refreshStatus()` toutes les 1,5 s | `GET /models/{id}` jusqu'à `DONE`, puis affiche le modèle dans le viewer |


---

## 6. Base de données

**En une phrase :** une base SQLite (un seul fichier, `backend/data/forma3d.sqlite3`) garde les catégories, l'historique des modèles et les clés API ; les fichiers eux-mêmes restent sur le disque.

### 6.1 Schéma entité-relation

```mermaid
erDiagram
    CATEGORIES ||--o{ GENERATIONS : "classe"
    API_KEYS ||--o{ API_USAGE_DAILY : "compte par jour"
    API_KEYS ||--o{ API_RATE_EVENTS : "trace les appels"

    CATEGORIES {
        INTEGER id PK
        TEXT slug UK
        TEXT label
        INTEGER is_active
        TEXT created_at
    }
    GENERATIONS {
        TEXT id PK
        INTEGER category_id FK
        TEXT status
        TEXT filename
        TEXT content_type
        TEXT source_photo_path
        TEXT glb_path
        REAL duration_seconds
        TEXT error_message
        TEXT image_warning
        TEXT origin
        TEXT public_id
        INTEGER embed_enabled
        TEXT created_at
        TEXT updated_at
    }
    API_KEYS {
        TEXT id PK
        TEXT name
        TEXT prefix
        TEXT fingerprint UK
        TEXT created_at
        INTEGER revoked
    }
    API_USAGE_DAILY {
        TEXT api_key_id FK
        TEXT usage_date
        INTEGER generation_count
    }
    API_RATE_EVENTS {
        INTEGER id PK
        TEXT api_key_id FK
        TEXT occurred_at
    }
```

### 6.2 Les tables et leurs colonnes

**`categories`** — les catégories de produits.

| Colonne | Sens |
|---|---|
| `id` | Numéro automatique |
| `slug` | Identifiant technique unique (`chair`, `stool`, `side-table`) |
| `label` | Nom affiché (« Chaise », « Tabouret », « Table d'appoint ») |
| `is_active` | 1 = proposée pour les nouvelles créations ; 0 = désactivée |
| `created_at` | Date de création |

Au premier démarrage, les trois catégories initiales sont créées si elles n'existent pas. ✅

**`generations`** — chaque modèle : généré, importé ou copié depuis un exemple.

| Colonne | Sens |
|---|---|
| `id` | UUID (identifiant unique) interne, utilisé par le Studio |
| `category_id` | Lien vers `categories` (clé étrangère) |
| `status` | `PENDING`, `RUNNING`, `DONE` ou `FAILED` (contrôle `CHECK`) |
| `filename` | Nom affiché du fichier ou titre |
| `content_type` | Type de la photo (`image/jpeg`…) |
| `source_photo_path` | Chemin de la photo source sur le disque |
| `glb_path` | Chemin du GLB (vide tant que le modèle n'est pas terminé) |
| `duration_seconds` | Durée de génération mesurée |
| `error_message` | Cause d'un échec, sans secret |
| `image_warning` | Avertissement non bloquant (photo petite ou floue) |
| `origin` | `generated`, `imported` ou `example` |
| `public_id` | UUID **public**, utilisé par `/embed` et le widget (différent de `id`) |
| `embed_enabled` | 1 = intégration autorisée sur un site ; 0 par défaut |
| `created_at`, `updated_at` | Dates |

**`api_keys`** — les clés API. ⚠️ La clé complète n'est **jamais** enregistrée : seule son **empreinte** (`fingerprint`, un hachage SHA-256) l'est, plus un `prefix` lisible (`f3d_live_xxx…`).

**`api_usage_daily`** — nombre de créations par clé et par jour (quota quotidien).

**`api_rate_events`** — horodatage des appels récents de chaque clé (limite par minute ; les événements de plus de 60 s sont nettoyés).

Les exemples du catalogue ne sont **pas** dans la base : ils sont décrits par une liste fixe dans `demo_gallery.py`.

### 6.3 Pourquoi SQLite ?

- Un seul fichier, aucun serveur à installer : parfait pour un prototype local.
- SQL standard : 🔁 vous retrouvez `CREATE TABLE`, `REFERENCES`, `CHECK` comme dans Oracle.
- Limite : un seul écrivain à la fois, pas de comptes utilisateurs de base de données, pas adapté à plusieurs serveurs.

### 6.4 Migrations

**Une migration** est une modification de la structure d'une base existante sans perdre les données. Le projet utilise des migrations **simples et non destructives** dans `SQLiteGenerationRepository.initialize()` :

1. `CREATE TABLE IF NOT EXISTS …` crée les tables absentes.
2. Le code lit les colonnes existantes (`PRAGMA table_info(generations)`).
3. Il ajoute les colonnes manquantes avec `ALTER TABLE … ADD COLUMN` : `image_warning`, `origin`, `public_id`, `embed_enabled`.

🔁 C'est l'équivalent très simplifié de Flyway (Spring) ou des migrations Doctrine (Symfony), sans numéro de version. ⚠️ Il n'existe pas de retour arrière automatique.

### 6.5 Au redémarrage du serveur

Les générations restées `PENDING` ou `RUNNING` (le serveur s'est arrêté au milieu) passent à `FAILED` avec le message « Génération interrompue au redémarrage du serveur. » ✅ Une génération n'est donc jamais bloquée pour toujours en « en cours ».

### 6.6 Passer plus tard à PostgreSQL (sans le faire)

Les services ne parlent jamais à SQLite directement : ils utilisent le **contrat** `GenerationRepository` (`backend/app/repositories/base.py`). Ce contrat liste les opérations : `initialize`, `save_generation`, `get_generation`, `get_generation_by_public_id`, `set_embed_enabled`, `delete_generation`, `list_completed_generations`, `list_categories`, `create_category`, `update_category`, `delete_category`, `create_api_key`, `list_api_keys`, `find_api_keys_by_prefix`, `revoke_api_key`, `delete_revoked_api_key`, `consume_api_rate_limit`, `consume_api_daily_quota`…

🔁 C'est une **interface Java** : pour passer à PostgreSQL, il suffirait d'écrire une classe `PostgreSQLGenerationRepository` qui implémente les mêmes méthodes, puis de la choisir dans `main.py`. Les routes et services ne changeraient pas. Il faudrait aussi un script qui copie les données et des migrations versionnées. **Ce n'est pas fait.** Détails, avec le vrai code et la question de l'`owner_id` : `docs/ARCHITECTURE-CIBLE.md`, section 9.


### 6.7 Encadrés

> **Un exemple concret.** Après la génération du fauteuil vert, la table `generations` contient une ligne : `status = DONE`, `category_id` = celui de « chair », `source_photo_path` et `glb_path` vers les fichiers du disque, `embed_enabled = 0`. Quand la propriétaire active l'intégration, seule la colonne `embed_enabled` passe à 1 ; le `public_id` ne change pas. Quand elle supprime le modèle (étape 23), la ligne est effacée, puis le GLB et la photo.

> **Une analogie.** 🔁 Le schéma ressemble à ce que vous écririez en Oracle : clés primaires, clé étrangère `category_id`, contrainte `CHECK` sur le statut. La différence : pas d'instance, pas d'utilisateur de base, pas de PL/SQL ; la logique est dans les services Python, et l'accès passe par un dépôt comme un `@Repository` Spring.

> **Ce que je réponds si on me demande pourquoi.** « SQLite est un vrai moteur SQL, suffisant pour une console mono-propriétaire en local, et il ne demande aucune installation. J'ai isolé tout l'accès derrière l'interface `GenerationRepository` pour pouvoir passer à PostgreSQL le jour où il faudra plusieurs serveurs ou un hébergement : c'est décrit dans `docs/ARCHITECTURE-CIBLE.md`. »

---

## 7. Fournisseurs 3D

**En une phrase :** un « fournisseur » est la classe qui envoie la photo à un service d'IA et rapporte un GLB ; le projet en contient deux, TripoSR (par défaut) et TRELLIS.

### 7.1 Le contrat commun

```python
class Image3DProvider(Protocol):
    def generate(self, image_path: Path) -> bytes: ...
```

Une image entre, des octets GLB sortent. 🔁 Comme une interface Spring avec deux implémentations, choisies au démarrage.

### 7.2 Les deux fournisseurs

| | TripoSR — `HuggingFaceSpaceProvider` | TRELLIS — `TrellisSpaceProvider` |
|---|---|---|
| Fichier | `backend/app/providers/huggingface.py` | `backend/app/providers/trellis.py` |
| Où tourne l'IA | Un Space Hugging Face **ou** un serveur Gradio temporaire sur Google Colab (`HF_SPACE_ID`) | Le Space public `trellis-community/TRELLIS` (`TRELLIS_SPACE_ID`) |
| Enchaînement | Lit le contrat (`view_api()`), choisit la fonction disponible, envoie la photo | `view_api()` → `/start_session` → `/preprocess_image` (détourage du fond) → `/generate_and_extract_glb` |
| Résultat | GLB à couleurs de sommets | GLB texturé |
| Relance | Oui si le Space démarre (`HF_MAX_ATTEMPTS`, 1 ou 2) | Non |
| Délai maximal | `HF_TIMEOUT_SECONDS` (300 s par défaut) | Même délai global, plus **120 s par requête HTTP** (`_HTTP_REQUEST_TIMEOUT_SECONDS`) |
| Compatibilité en plus | Sait aussi lire le contrat de Stable Fast 3D (`/run_button`) | — |

Après le fournisseur, **le même traitement** s'applique : vérification GLB 2.0, puis finition (`glb_finisher.py`) qui ajoute un matériau mat et des normales. ✅

### 7.3 Lequel est utilisé par défaut ?

**TripoSR**, car `IMAGE3D_PROVIDER` vaut `triposr` par défaut (`backend/app/config.py`). ✅ Dans la configuration de démonstration de l'étudiante, `IMAGE3D_PROVIDER=trellis` est défini dans `backend/.env` : c'est **TRELLIS** qui génère (une génération complète depuis le Studio a réussi le 15 novembre 2026).

```mermaid
flowchart LR
    A["Démarrage de main.py"] --> B{"IMAGE3D_PROVIDER ?"}
    B -->|"triposr (défaut)"| C["HuggingFaceSpaceProvider<br/>utilise HF_SPACE_ID"]
    B -->|trellis| D["TrellisSpaceProvider<br/>utilise TRELLIS_SPACE_ID"]
```

**Comment vérifier :** ouvrez `http://127.0.0.1:8001/health/provider` (serveur lancé par `dev.ps1` ; `8000` si uvicorn est lancé à la main). Quand le service est hors ligne, le message parle de « Colab » pour TripoSR et de « Space TRELLIS » pour TRELLIS (section 17).

**Comment changer :** dans `backend/.env`, mettez `IMAGE3D_PROVIDER=trellis`, puis redémarrez le serveur. Ou lancez le serveur depuis un terminal où la variable est définie (elle a alors priorité sur `.env`).

### 7.4 Le jeton `HF_TOKEN`

- C'est un **mot de passe pour programme** fourni gratuitement par Hugging Face (*Settings → Access Tokens*, type « Read »).
- Il augmente le **quota GPU gratuit** de TRELLIS. Ordre de grandeur : environ **2 minutes** de GPU par jour sans jeton et **5 minutes** avec un compte gratuit — **à vérifier** sur https://huggingface.co/docs/hub/spaces-zerogpu. Une génération TRELLIS a pris environ 1 min 30 à 2 min pendant les essais.
- ⚠️ Le quota est attaché au **compte**, pas au jeton : créer un nouveau jeton sur le même compte ne redonne **aucun** quota. Multiplier les comptes serait un contournement, interdit par les conditions d'utilisation et par les règles du projet.
- Où le ranger : **uniquement** dans `backend/.env` (ignoré par Git) ou dans la variable d'un terminal. **Jamais** dans `.env.example`, dans le code ou dans une conversation.
- Sécurité : le code ne l'envoie qu'à Hugging Face. `TRELLIS_SPACE_ID` doit être un identifiant `propriétaire/nom`, jamais une URL, et le fournisseur TripoSR refuse d'envoyer le jeton à une URL Gradio externe. Il est masqué dans les messages d'erreur. ✅

### 7.5 Quotas, erreurs et mode hors ligne

| Situation | Ce que voit la propriétaire |
|---|---|
| `HF_SPACE_ID` vide (TripoSR) | Badge « Serveur 3D : hors ligne » ; bouton « Créer » désactivé ; statut `UNCONFIGURED` |
| Lien Colab expiré (72 h maximum) | Badge hors ligne ; message « Le serveur 3D (Colab) est arrêté ou son lien a expiré » |
| Quota TRELLIS épuisé | La création échoue avec « Quota GPU gratuit du Space TRELLIS atteint pour aujourd'hui… » |
| Space TRELLIS en veille | « Le Space TRELLIS est en veille, en panne ou indisponible » |
| Contrat du Space modifié | La génération s'arrête avant l'envoi de la photo (« Le contrat … a changé ») |
| Space très lent | Avant le 15 novembre 2026, « The read operation timed out » (délai HTTP de 5 s par défaut) ; corrigé avec 120 s par requête |

Quand le fournisseur est hors ligne, le reste du Studio fonctionne : exemples, import GLB, fiches, intégration.

### 7.6 Les notebooks Google Colab

- Le dépôt contient **un seul** notebook : `tools/colab/triposr_server.ipynb`. Il vérifie le GPU, installe TripoSR et documente le dépannage. Sa dernière cellule **empêche** de lancer un service web public sur un Colab gratuit géré (règle de la FAQ Colab).
- Vos notebooks de test **TRELLIS v1, SF3D et comparaison** ne sont **pas** dans le dépôt Git (**à vérifier** : probablement sur votre Google Drive).
- **Ils ne font pas partie de l'application** : le serveur ne les lit jamais.
- **Quand les garder** : comme preuves d'expérimentation pour la soutenance (captures, résultats). **Quand les supprimer** : quand leurs résultats sont recopiés dans `docs/QUALITE-3D.md` et qu'ils ne servent plus. N'y laissez jamais un jeton en clair.

### 7.7 Licences à vérifier

| Élément | Licence | À vérifier |
|---|---|---|
| TripoSR | MIT | Droits des photos utilisées |
| TRELLIS (code et poids) | MIT | Usage commercial des modèles générés via le Space (question ouverte) |
| Stable Fast 3D | Stability AI Community License | Gratuit sous un seuil de chiffre d'affaires |
| Hunyuan3D-2 | Licence Tencent | Exclut l'Union européenne, le Royaume-Uni et la Corée du Sud : non retenu |
| model-viewer | Apache 2.0 | — |

Détails et essais : `docs/ALTERNATIVES-3D.md` et `docs/QUALITE-3D.md`.


### 7.8 Encadrés

> **Un exemple concret.** Le 15 novembre 2026, plusieurs créations échouaient avec « The read operation timed out ». Diagnostic : `gradio_client` coupait chaque requête HTTP après 5 s (valeur par défaut de httpx), alors que la simple connexion au Space chargé prenait 26 s. Avec un délai de 120 s par requête, une photo du fauteuil a produit un GLB en 117 s : connexion 26 s, détourage 14 s, génération 73 s.

> **Une analogie.** 🔁 `Image3DProvider` est une interface Java avec deux implémentations (`HuggingFaceSpaceProvider`, `TrellisSpaceProvider`), et `main.py` choisit laquelle injecter selon une propriété de configuration, comme un `@ConditionalOnProperty` de Spring Boot.

> **Ce que je réponds si on me demande pourquoi.** « Je n'entraîne aucun modèle : j'appelle des modèles pré-entraînés gratuits. Je lis toujours le contrat réel du service (`view_api()`) avant d'envoyer la photo, pour ne jamais inventer un nom de paramètre. Et j'isole le fournisseur derrière une interface, parce que les services gratuits changent, ferment ou atteignent leur quota. »

---

## 8. Cycle de vie d'un modèle

**En une phrase :** un modèle généré passe par quatre états, enregistrés dans SQLite et lus par la page toutes les 1,5 seconde.

```mermaid
stateDiagram-v2
    [*] --> PENDING : POST /models (photo acceptée)
    PENDING --> RUNNING : la tâche de fond démarre
    RUNNING --> DONE : GLB reçu, vérifié, fini et enregistré
    RUNNING --> FAILED : erreur, quota ou délai dépassé
    PENDING --> FAILED : redémarrage du serveur
    DONE --> [*]
    FAILED --> [*]
```

| État | Sens | Ce que montre la page Créer |
|---|---|---|
| `PENDING` | Photo reçue, en attente | Étape « En file » active |
| `RUNNING` | Le fournisseur travaille | Étape « Création du modèle » active, chronomètre |
| `DONE` | GLB prêt | Modèle affiché, lien « Ouvrir la fiche du modèle → » |
| `FAILED` | Échec | Message renvoyé par le serveur, bouton « Réessayer avec cette photo » |

- **Tâche de fond** : FastAPI répond tout de suite `202 Accepted`, puis exécute `GenerationService.run()` avec `BackgroundTasks`. 🔁 Comme une méthode `@Async` de Spring.
- **Aucun pourcentage inventé** : la page n'affiche que les états réellement renvoyés.
- **Reprise après redémarrage** : pas de reprise automatique ; une génération `PENDING` ou `RUNNING` passe en `FAILED` (section 6.5) et il faut la relancer.
- Les modèles **importés** ou **copiés** sont créés directement en `DONE`.


> **Un exemple concret.** Le fauteuil blanc photographié sur fond gris est passé par `PENDING` → `RUNNING` → `DONE` en 1 min 33 s, avec un `image_warning` (« La photo est petite… ») : l'avertissement n'a pas bloqué la création. Une tentative pendant que le Space était trop lent est passée de `RUNNING` à `FAILED` avec le message réel du serveur.

> **Une analogie.** 🔁 C'est une machine à états comme le statut d'une commande dans une application Symfony ou Spring : chaque transition est écrite en base, et l'interface Angular ne ferait que lire l'état courant (ici, par interrogation régulière plutôt que par WebSocket).

> **Ce que je réponds si on me demande pourquoi.** « Les quatre états sont enregistrés dans SQLite pour qu'un rechargement de page ou un redémarrage ne perde pas le suivi. Je n'affiche aucun pourcentage inventé : seulement l'état réellement renvoyé par le serveur. »

---

## 9. Variables d'environnement

**En une phrase :** les réglages et secrets sont lus dans des variables d'environnement, rangées dans un fichier `.env` local que Git ignore.

### 9.1 `.env` contre `.env.example`

| | `.env.example` | `backend/.env` (ou `.env` à la racine) |
|---|---|---|
| Contient | La **liste** des variables, avec des valeurs vides ou par défaut | Vos **vraies** valeurs (mot de passe, jeton) |
| Suivi par Git ? | ✅ oui | ❌ non (ignoré) |
| Qui le lit ? | Les humains | Le serveur, au démarrage |

Ordre de lecture (`config.py`) : `backend/.env` d'abord, puis `.env` à la racine, **sans écraser** une variable déjà définie dans le terminal. 🔁 Comme `application.properties` de Spring, avec les variables système prioritaires.

```mermaid
flowchart LR
    T["Variable du terminal<br/>(prioritaire)"] --> V{"Déjà définie ?"}
    V -->|non| B["backend/.env"]
    B --> R[".env à la racine"]
    R --> D["Valeur par défaut<br/>de config.py"]
    V -->|oui| U["Utilisée telle quelle"]
```

⚠️ Le fichier `.env` n'est lu qu'**au démarrage** du serveur : après une modification, il faut arrêter puis relancer le serveur (section 15.2).

### 9.2 Toutes les variables

Les exemples de valeurs ci-dessous sont **faux** et servent seulement à montrer le format.

| Variable | Rôle | Défaut | Lue par | Effet si absente | Exemple (faux) |
|---|---|---|---|---|---|
| `HF_SPACE_ID` | Adresse du serveur TripoSR : identifiant de Space ou URL Gradio | vide | `config.py` → `huggingface.py` | TripoSR non configuré, statut `UNCONFIGURED` | `https://exemple-faux.gradio.live` |
| `HF_TOKEN` | Jeton Hugging Face (quota plus élevé, Space privé) | vide | `config.py`, outils `tools/trials/` | Accès anonyme, quota plus faible | `hf_EXEMPLEFAUX123` |
| `HF_TIMEOUT_SECONDS` | Délai maximal d'une génération | `300` | `config.py` | 300 s | `300` |
| `HF_MAX_ATTEMPTS` | Nombre de tentatives TripoSR (1 ou 2) | `2` | `config.py` | 2 | `2` |
| `HF_RETRY_DELAY_SECONDS` | Attente avant relance | `5` | `config.py` | 5 s | `5` |
| `FOREGROUND_RATIO` | Réglage TripoSR, utilisé seulement s'il existe dans le contrat du serveur | vide | `config.py` | Valeur du serveur | `0.85` |
| `MC_RESOLUTION` | Résolution TripoSR, même règle | vide | `config.py` | Valeur du serveur | `256` |
| `MAX_GLB_UPLOAD_MB` | Taille maximale d'un GLB importé (1 à 512) | `30` | `config.py` | 30 Mo | `30` |
| `API_DAILY_GENERATION_LIMIT` | Créations par clé et par jour | `20` | `config.py` | 20 | `20` |
| `API_RATE_LIMIT_PER_MINUTE` | Requêtes `/api/v1` par clé et par minute | `10` | `config.py` | 10 | `10` |
| `API_CORS_ORIGINS` | Sites autorisés à appeler l'API en JavaScript (`*` refusé) | vide | `config.py` → `main.py` | Aucun site tiers | `http://boutique-exemple.test` |
| `EMBED_ALLOWED_ORIGINS` | Sites autorisés à afficher `/embed` dans une iframe (`*` refusé) | vide | `config.py` → `embed.py` | Seul le Studio lui-même | `http://127.0.0.1:8081` |
| `FORMA3D_OWNER_PASSWORD` | Mot de passe unique de la propriétaire | vide | `services/owner_auth.py` | **Connexion refusée** (503) | `mot-de-passe-exemple-long` |
| `FORMA3D_SESSION_SECRET` | Clé fixe de signature des sessions (32 caractères minimum) | vide | `owner_auth.py` → `main.py` | Clé aléatoire à chaque démarrage : reconnexion après redémarrage | `exemple-faux-0123456789abcdefghijklmnop` |
| `IMAGE3D_PROVIDER` | Fournisseur 3D : `triposr` ou `trellis` | `triposr` | `config.py` → `main.py` | TripoSR | `trellis` |
| `TRELLIS_SPACE_ID` | Space TRELLIS (`propriétaire/nom`, jamais une URL) | `trellis-community/TRELLIS` | `config.py` → `trellis.py` | Space communautaire par défaut | `trellis-community/TRELLIS` |

⚠️ Une valeur invalide (par exemple `IMAGE3D_PROVIDER=meshy`, une origine `*` ou un `FORMA3D_SESSION_SECRET` trop court) empêche le serveur de démarrer, avec un message clair. ✅

`PYTHON_DOTENV_DISABLED=true` n'est pas une variable du projet mais de la bibliothèque python-dotenv : `scripts/dev.ps1` la pose **seulement pendant pytest** (avec `HF_SPACE_ID` vide) pour que les tests ne lisent jamais `backend/.env`, puis la retire avant de démarrer le serveur.

---

## 10. Le site page par page

**En une phrase :** le Studio est une seule page HTML (`index.html`) dont le contenu change selon l'adresse après le `#` (exemple : `#/creer`), sans recharger la page.

🔁 **Angular** : c'est le principe d'une SPA (Single Page Application, application à page unique) avec un routeur, mais écrit à la main dans `router.js`.

### 10.0 La coque commune (présente sur toutes les pages après connexion)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [cube] Forma3D Studio  Accueil  Créer  Mes modèles  Exemples  Administration ▾│
│                                        ● Serveur 3D : hors ligne  ⇥ Déconnexion│
├──────────────────────────────────────────────────────────────────────────────┤
│                         (contenu de la page, dans #app)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│ Forma3D Studio v1.0   Documentation   Guide d'intégration   GitHub           │
│                                   Prototype de soutenance · Aucun entraînement │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Élément | Emplacement | Au clic | Fichier |
|---|---|---|---|
| Logo « Forma3D Studio » | En haut à gauche | Va à `#/accueil` | `index.html` |
| « Accueil », « Créer », « Mes modèles », « Exemples » | Menu | Change la page ; le lien actif a un fond vert pâle | `router.js` → `updateNavigation()` |
| « Administration » ▾ | Menu | Ouvre un sous-menu : « Catégories », « Clés API », « Guide d'intégration » | `index.html` (élément `<details>`) |
| Badge « Serveur 3D : en ligne / hors ligne » | En haut à droite | Aucun clic ; mis à jour toutes les 30 s par `GET /health/provider` | `main.js` → `refreshProviderHealth()` |
| « Déconnexion » | En haut à droite | `POST /auth/logout`, efface le cookie, retour à `#/login` | `auth.js` → `logout()` |
| Bouton ☰ | Sur mobile seulement | Ouvre ou ferme le menu | `router.js` |
| « Documentation », « GitHub » | Pied de page | Ouvre le dépôt GitHub (privé : visible seulement par un compte autorisé) | `index.html` |
| « Guide d'intégration » | Pied de page | Va à `#/guide` | `index.html` |

Sur l'écran de connexion, le menu, le badge et le pied de page sont **masqués**.

### 10.1 Connexion — `#/login`

**But :** protéger le Studio par le mot de passe de la propriétaire.

```
┌───────────────────────────────────┐
│            [cube vert]            │
│          CONSOLE PRIVÉE           │
│          Forma3D Studio           │
│ Saisissez le mot de passe de la   │
│ propriétaire pour accéder au      │
│ Studio.                           │
│ Mot de passe                      │
│ [••••••••••••••••]   [Afficher]   │
│ [   Accéder au Studio →        ]  │
│ Session protégée par le serveur…  │
└───────────────────────────────────┘
```

| Élément | Ce qui se passe | Fichier, fonction, route |
|---|---|---|
| Champ « Mot de passe » | Saisie masquée | `pages/login.js` |
| « Afficher » / « Masquer » | Montre ou cache le texte saisi | `login.js` |
| « Accéder au Studio → » | Le bouton passe à « Vérification… » ; envoi du mot de passe | `auth.js` → `login()` → `api.js` → `loginOwner()` → `POST /auth/login` |

| État | Message affiché |
|---|---|
| Champ vide | « Saisissez le mot de passe. » |
| Mot de passe faux | « Mot de passe incorrect. » (réponse 401) |
| 6e tentative en moins d'une minute | « Trop de tentatives. Patientez une minute avant de réessayer. » (429) |
| Mot de passe non configuré sur le serveur | « Connexion impossible : définissez FORMA3D_OWNER_PASSWORD dans backend/.env, puis redémarrez le serveur. » |
| Succès | Cookie de session posé ; retour à la page demandée, sinon `#/accueil` |

⚠️ **Piège** : mettre le mot de passe dans `.env.example` ne marche pas ; le serveur lit seulement `backend/.env` (ou `.env` à la racine).

### 10.2 Accueil — `#/accueil`

**But :** une vue d'ensemble et des raccourcis.

```
┌────────────────────────────────────────────────────────────────┐
│ ● Serveur 3D hors ligne · exemples disponibles                  │
│ Transformez vos photos en modèles 3D            [chaise 3D qui  │
│ Créez, gérez et intégrez vos modèles 3D…         tourne]        │
│ [Créer un modèle 3D →]  [Voir les exemples]                     │
├──────────────────┬──────────────────┬──────────────────────────┤
│ 3 Modèles  Voir  │ 1 Clés API  Gérer│ 3 Catégories   Organiser │
├──────────────────┴──────────────────┴──────────────────────────┤
│ Vos modèles récents                                 Tout voir → │
│ [carte] [carte] [carte]   ou   « Votre bibliothèque est vide » │
│ Exemples du catalogue                               Explorer →  │
│ [carte] [carte] [carte] [carte] [carte]  (défilement horizontal)│
│ Raccourcis                                                      │
│ [Créer un modèle] [Importer un GLB] [Gérer les clés API] [Guide]│
└────────────────────────────────────────────────────────────────┘
```

| Élément | Au clic | Données |
|---|---|---|
| « Créer un modèle 3D → » | Va à `#/creer` | — |
| « Voir les exemples » | Va à `#/exemples` | — |
| Carte « Modèles enregistrés » → « Voir » | Va à `#/modeles` | Nombre lu par `GET /models/gallery` (modèles UUID seulement) |
| Carte « Clés API actives » → « Gérer » | Va à `#/cles-api` | `GET /api-keys`, clés non révoquées |
| Carte « Catégories disponibles » → « Organiser » | Va à `#/categories` | `GET /categories` |
| « Tout voir → » | Va à `#/modeles` | 3 derniers modèles par date |
| Une carte de modèle | Ouvre la fiche `#/modeles/{id}` | La miniature tourne au survol |
| « Créer mon premier modèle » (état vide) | Va à `#/creer` | — |
| « Explorer → » | Va à `#/exemples` | — |
| Raccourci « Importer un GLB » | Va à `#/modeles?import=1`, qui ouvre directement le formulaire d'import | — |
| Raccourci « Guide d'intégration » | Va à `#/guide` | — |

Fichier : `pages/dashboard.js`. États : cartes grises animées (« squelettes ») pendant le chargement ; message rouge si le serveur ne répond pas.

### 10.3 Créer — `#/creer`

**But :** transformer une photo en modèle 3D.

```
┌──────────────────────────────┬─────────────────────────────────────────┐
│ Photo et catégorie           │ ESPACE DE TRAVAIL       [Aperçu d'un    │
│ ┌──────────────────────────┐ │ Aperçu du modèle         fichier GLB…]  │
│ │  (+) Glissez une photo   │ │ ┌─────────────────────────────────────┐ │
│ │  ici ou [Choisir une     │ │ │                                     │ │
│ │  photo]                  │ │ │       Votre modèle apparaîtra ici   │ │
│ └──────────────────────────┘ │ │                                     │ │
│ Catégorie du produit [▼]     │ └─────────────────────────────────────┘ │
│ [   Créer le modèle 3D →   ] │ [↶][↷] [←][→][↑][↓] [−][+] Rotation auto │
│ Choisissez une photo…        │ Plein écran  Réinitialiser              │
│ + Conseils photo             │ ⓘ Aperçu 3D généré automatiquement…     │
│ + Détails techniques         │                                         │
├──────────────────────────────┴─────────────────────────────────────────┤
│ Suivi de création  ①Photo envoyée ②En file ③Création ④Validation ⑤Terminé│
└────────────────────────────────────────────────────────────────────────┘
```

| Élément | Ce qui se passe | Fichier, fonction, route |
|---|---|---|
| Zone « Glissez une photo ici » / « Choisir une photo » | Choix ou glisser-déposer ; aperçu de la photo dans la zone ; contrôle JPG, PNG ou WebP, 10 Mo maximum | `views/uploader.js` → `setSelectedPhoto()` |
| « Catégorie du produit » | Liste des catégories **actives** | `GET /categories?include_inactive=true` puis filtre |
| « Créer le modèle 3D → » | Désactivé tant que photo, catégorie ou serveur 3D manquent ; sinon `POST /models` | `uploader.js` → `create.js` → `startGeneration()` → `api.js` → `createGeneration()` |
| Texte sous le bouton | Explique pourquoi le bouton est désactivé (« Choisissez une photo pour activer la création. », « Le serveur 3D est hors ligne. Consultez les exemples en attendant. », « Tout est prêt pour créer le modèle. ») | `uploader.js` → `syncState()` |
| « Voir les exemples » (bandeau jaune) | Va à `#/exemples` ; visible si le serveur 3D est hors ligne | `create.js` |
| « Conseils photo » | Déplie 4 conseils (un objet, fond uni, lumière douce, 70 % de l'image) | `create.js` |
| « Détails techniques » | Déplie l'état du serveur et comment relancer Colab | `create.js` |
| « Aperçu d'un fichier GLB (sans enregistrer) » | Ouvre un GLB local **dans le navigateur seulement** (rien n'est envoyé) | `views/viewer.js` |
| « Vue 3D / Photo source / Comparer » | Change l'affichage (visible quand une photo source existe) ; en « Comparer », la rotation s'arrête et la caméra se recadre | `viewer.js` → `setView()` → `model-appearance.js` → `refitCamera()` |
| ↶ ↷ | Tourne de 15° | `viewer.js` → `rotateCamera()` |
| ← → ↑ ↓ | Déplace la vue | `viewer.js` → `panCamera()` |
| − + | Zoom | `viewer.js` |
| « Rotation auto » | Active ou arrête la rotation | `viewer.js` |
| « Plein écran » | Plein écran du viewer | `viewer.js` |
| « Réinitialiser » | Remet la caméra par défaut | `viewer.js` |
| « Télécharger » | Télécharge le GLB | lien vers `/models/{id}/glb` |
| Vignette « Agrandir » | Ouvre la photo source en grand | `viewer.js` |
| « Réessayer avec cette photo » | Relance après un échec | `create.js` |
| « Ouvrir la fiche du modèle → » | Va à la fiche après `DONE` | `create.js` |

| État | Ce qu'on voit |
|---|---|
| Vide | Cube dessiné, « Votre modèle apparaîtra ici » |
| Envoi / en file / création | Étapes du suivi colorées, chronomètre, roue de chargement |
| Avertissement photo | Bandeau jaune « La photo est petite… » ou « …floue… » (n'empêche pas la création) |
| Succès | Modèle affiché, « Votre modèle est prêt » |
| Échec | Cause réelle renvoyée par le serveur (exemple : quota TRELLIS) |

⚠️ **Pièges** : le bouton reste gris si le badge est « hors ligne » ; un échec dû au quota n'est pas un problème de photo.

### 10.4 Mes modèles — `#/modeles`

**But :** la bibliothèque des modèles enregistrés (générés, importés, copiés).

```
┌──────────────────────────────────────────────────────────────────┐
│ Mes modèles                          [Importer un modèle (.glb)] │
│ Modèles enregistrés                                  [3 modèles] │
│ [Tous 3] [Chaise 2] [Tabouret 1] [Table d'appoint 0]             │
│ ┌────────┐ ┌────────┐ ┌────────┐                                 │
│ │Généré  │ │Importé │ │Exemple │   badge d'origine                │
│ │ (3D)   │ │ (3D)   │ │ (3D)   │                                 │
│ │Titre   │ │Titre   │ │Titre   │                                 │
│ │Chaise · il y a 2 jours · 1,2 Mo                                │
│ └────────┘ └────────┘ └────────┘                                 │
└──────────────────────────────────────────────────────────────────┘
```

| Élément | Ce qui se passe | Route |
|---|---|---|
| « Importer un modèle (.glb) » | Ouvre le formulaire d'import | — |
| Champs « Fichier .glb », « Titre », « Catégorie » | Le titre se remplit avec le nom du fichier | — |
| « Importer dans Mes modèles » | Envoie le fichier ; message « Modèle importé… » et lien « Ouvrir sa fiche » | `POST /models/import` |
| « Annuler » | Ferme le formulaire | — |
| Filtres « Tous », catégories avec compteur | Filtrent les cartes | local (aucun appel) |
| Une carte | Ouvre la fiche | — |
| État vide : « Créer à partir d'une photo », « Importer un modèle » | Va à Créer / ouvre l'import | — |

Fichiers : `pages/models.js`, `views/gallery.js`. Le GLB importé est vérifié (format GLB 2.0, taille `MAX_GLB_UPLOAD_MB`) et marqué « Importé ».

### 10.5 Fiche du modèle — `#/modeles/{id}`

**But :** examiner un modèle, le télécharger et l'intégrer à un site.

```
┌───────────────────────────────────────────┬─────────────────────────┐
│ Aperçu 3D      [Vue 3D|Photo source|Comparer]│ Chaise en bois cintré   │
│ ┌───────────────────┬───────────────────┐ │ État        Prêt        │
│ │  modèle 3D        │  photo source     │ │ Catégorie   Chaise      │
│ │  (mode Comparer)  │                   │ │ Origine     Exemple · TRELLIS│
│ └───────────────────┴───────────────────┘ │ Date        …           │
│ ⓘ Aperçu 3D généré automatiquement…       │ Durée       1 min 16 s  │
│                                           │ [Télécharger le modèle] │
├───────────────────────────────────────────┴─────────────────────────┤
│ Afficher ce modèle sur un site                                      │
│ ① Activez l'intégration            [○—]  interrupteur               │
│ ② Choisissez votre méthode         [IFrame][Widget Forma3D]         │
│ ③ Copiez le code                   <iframe src=…>        [Copier]   │
│ ④ Aperçu                           [cadre de navigateur avec /embed]│
└─────────────────────────────────────────────────────────────────────┘
```

| Élément | Ce qui se passe | Route |
|---|---|---|
| « ← Retour à Mes modèles » / « ← Retour aux exemples » | Retour à la liste | — |
| « Vue 3D », « Photo source », « Comparer » | Changent l'affichage ; « Comparer » met le modèle et la photo côte à côte | local |
| « Télécharger le modèle (.glb) » | Télécharge le fichier | `/models/{id}/glb` ou `/models/gallery/{id}` |
| ① Interrupteur « Intégration publique de ce modèle » | Active ou désactive la publication (désactivée par défaut) | `PATCH /models/{id}/integration` |
| ② Onglets « IFrame » / « Widget Forma3D » | Choisissent le code affiché ; bloqués tant que l'étape 1 n'est pas faite | local |
| ③ « Copier » | Copie le code ; « Code copié. Collez-le dans la page produit de votre site. » | presse-papiers |
| ④ Aperçu | Affiche la vraie page `/embed/{public_id}` dans un cadre | `/embed/...` |
| « Supprimer ce modèle » (rouge, sous « Télécharger ») | Fenêtre de confirmation (« Cette action est irréversible », avec un avertissement si l'intégration est active), puis suppression de la ligne, du GLB et de la photo, et retour à « Mes modèles ». Caché pour les exemples et pendant une création | `DELETE /models/{id}` |

| État | Ce qu'on voit |
|---|---|
| Chargement | « Chargement des informations… », roue sur le modèle |
| Modèle en cours | « Le modèle est encore en cours de création. » ; la page se met à jour toutes les 2 s |
| Échec | « La création n'a pas abouti. Aucun fichier n'est disponible. » |
| Identifiant inconnu | « Ce modèle est introuvable. Il a peut-être été supprimé. » |
| Suppression refusée | Message sous le bouton (par exemple 409 : « Ce modèle est encore en cours de création… ») |

⚠️ Les **exemples du catalogue** n'ont pas de section d'intégration : il faut d'abord les copier dans « Mes modèles ». Fichier : `pages/model-detail.js`.

### 10.6 Exemples — `#/exemples`

**But :** montrer les 5 modèles de démonstration, réellement générés pendant les essais.

| Élément | Ce qui se passe | Route |
|---|---|---|
| Filtres par catégorie avec compteur | Filtrent | local |
| Une carte | Ouvre la fiche de l'exemple | — |
| Texte sous la carte | « Généré avec TRELLIS à partir d'une seule photo en 1 min 16 s. » (fournisseur et durée réellement mesurés) | `format.js` |
| « Ajouter à mes modèles » | Ouvre le panneau « Ajouter l'exemple à Mes modèles » | — |
| « Ajouter à Mes modèles » (panneau) | Copie l'exemple ; « Exemple ajouté à Mes modèles. » + « Ouvrir sa fiche » | `POST /models/examples/{id}/copy` |
| « Annuler » | Ferme le panneau | — |

Depuis le 11 novembre 2026, 3 exemples (chaise cintrée, tabouret, table d'appoint) viennent de **TRELLIS** et 2 (chaises métal) de **TripoSR**. Fichier : `pages/examples.js`.

### 10.7 Catégories — `#/categories` (menu Administration)

| Élément | Ce qui se passe | Route |
|---|---|---|
| « Nouvelle catégorie » + « Ajouter la catégorie » | Crée une catégorie (le slug est calculé à partir du nom) | `POST /categories` |
| Champ du nom + « Renommer » | Change le nom affiché | `PATCH /categories/{slug}` |
| Badge « Active » / « Désactivée » | État de la catégorie | — |
| Badge « N modèles » | Nombre de modèles enregistrés dans cette catégorie | calculé depuis `GET /models/gallery` |
| « Désactiver » / « Réactiver » | Fenêtre de confirmation, puis la catégorie n'est plus proposée à la création | `PATCH /categories/{slug}` |
| « Supprimer » | Grisé si la catégorie est utilisée ; sinon confirmation puis suppression | `DELETE /categories/{slug}` |

Message d'erreur si le nom existe déjà : « Ce nom de catégorie est déjà utilisé… ». Fichiers : `pages/categories.js`, `views/categories.js`.

### 10.8 Clés API — `#/cles-api` (menu Administration)

```
┌───────────────────────────────────────────────────────────────┐
│ Comment utiliser l'API                       Guide complet →  │
│ ①Créez une clé → ②Copiez le secret → ③Ajoutez l'en-tête → ④Testez│
│ [exemple curl]                                       [Copier] │
├───────────────────────────────────────────────────────────────┤
│ Créer une clé   Nom pour la reconnaître [______] [Créer une clé API]│
│ ⚠ Copiez votre clé maintenant  f3d_live_…      [Copier la clé]│
├───────────────────────────────────────────────────────────────┤
│ Clés existantes                          [1 active · 2 clés]  │
│ ┌ Boutique ● Active ┐  ┌ dd ○ Révoquée ───────────┐           │
│ │ f3d_live_abc…     │  │ f3d_live_xyz…            │           │
│ │ [Révoquer]        │  │ [Supprimer définitivement]│           │
└───────────────────────────────────────────────────────────────┘
```

| Élément | Ce qui se passe | Route |
|---|---|---|
| « Guide complet → » | Va à `#/guide` | — |
| « Copier » (exemple curl) | Copie la commande d'exemple | — |
| « Nom pour la reconnaître » + « Créer une clé API » | Crée la clé ; affiche le secret **une seule fois** | `POST /api-keys` |
| « Copier la clé » | Copie le secret | — |
| « Révoquer » (clé active) | Confirmation, puis la clé est refusée par l'API ; le secret affiché disparaît | `DELETE /api-keys/{id}` |
| « Supprimer définitivement » (clé révoquée) | Confirmation, puis la clé et ses compteurs sont effacés | `DELETE /api-keys/{id}/permanent` |

⚠️ Une clé active ne peut pas être supprimée directement (le serveur répond 409) : il faut d'abord la révoquer. Fichier : `pages/api-keys.js`.

### 10.9 Guide d'intégration — `#/guide` (menu Administration)

Page de lecture : sommaire (« Créer une clé », « Envoyer une photo », « Suivre le modèle », « Activer et intégrer », « Quotas et origines », « Sécurité »), 6 sections et des blocs de code avec un bouton « Copier ». Les adresses des exemples utilisent l'adresse réelle du serveur. Aucun appel au serveur. Fichier : `pages/guide.js`.

### 10.10 Page introuvable

Toute adresse inconnue affiche « Cette page n'existe pas » et un bouton « Retour à l'accueil ». Fichier : `router.js` → `makeNotFoundPage()`.

---

## 11. Utiliser le site de bout en bout

**En une phrase :** trois personnes utilisent Forma3D, chacune avec un chemin différent.

### 11 a. La propriétaire : de la connexion à un modèle intégré

```mermaid
flowchart LR
    A["Connexion<br/>#/login"] --> B["Créer<br/>photo + catégorie"]
    B --> C["Suivi<br/>PENDING → DONE"]
    C --> D["Fiche du modèle<br/>vérifier, comparer"]
    D --> E["Activer l'intégration"]
    E --> F["Copier le code<br/>iframe ou widget"]
    F --> G["Créer une clé API<br/>si un serveur doit appeler l'API"]
```

1. Lancer `.\scripts\dev.ps1`, ouvrir `http://127.0.0.1:8001` (ou `8000` si uvicorn est lancé à la main), se connecter.
2. Aller dans **Créer**, déposer une photo nette, choisir la catégorie, cliquer sur « Créer le modèle 3D → ».
3. Attendre l'étape « Terminé », puis cliquer sur « Ouvrir la fiche du modèle → ».
4. Vérifier le modèle avec « Comparer » ; le télécharger si besoin.
5. Activer l'interrupteur « Intégration publique de ce modèle ».
6. Choisir « IFrame » ou « Widget Forma3D », cliquer sur « Copier », envoyer le code au développeur de la boutique.
7. Si le développeur doit appeler l'API, créer une clé dans **Clés API** et la lui transmettre de façon sûre.

Sans serveur 3D en ligne : remplacer l'étape 2 par **Exemples → « Ajouter à mes modèles »** ou **Mes modèles → « Importer un modèle (.glb) »**.

### 11 b. Le développeur d'une boutique : de la clé API à l'affichage

```mermaid
sequenceDiagram
    participant S as Serveur de la boutique
    participant F as Forma3D
    participant P as Page produit
    S->>F: POST /api/v1/models (X-API-Key, photo)
    F-->>S: 202 + id
    S->>F: GET /api/v1/models/{id} (répété)
    F-->>S: DONE
    Note over F: La propriétaire active l'intégration
    S->>F: GET /api/v1/models/{id}/integration-code
    F-->>S: iframe_html, widget_html, public_id
    S->>P: insère le code dans la page
```

1. Recevoir une clé API de la propriétaire et la ranger **côté serveur** (jamais dans le JavaScript public).
2. Envoyer une photo : `POST /api/v1/models` avec l'en-tête `X-API-Key`.
3. Suivre l'état : `GET /api/v1/models/{id}` jusqu'à `DONE`.
4. Après activation par la propriétaire, récupérer le code : `GET /api/v1/models/{id}/integration-code`.
5. Insérer l'iframe ou le widget dans la page produit.
6. Faire autoriser l'adresse du site dans `EMBED_ALLOWED_ORIGINS`.

### 11 c. Le visiteur final

```mermaid
flowchart LR
    A["Ouvre la page produit<br/>de la boutique"] --> B["La page charge<br/>widget.js ou l'iframe"]
    B --> C["/embed/{public_id}<br/>servi par Forma3D"]
    C --> D["model-viewer télécharge<br/>/public/models/{public_id}/glb"]
    D --> E["Le visiteur fait tourner<br/>et zoome le meuble"]
```

1. Le visiteur ouvre la page produit de la boutique.
2. Le navigateur charge l'iframe `/embed/{public_id}` depuis Forma3D.
3. Forma3D vérifie que le modèle existe, est terminé et que son intégration est activée ; sinon, il affiche « Ce modèle 3D n'est pas disponible… ».
4. Le visiteur fait tourner le modèle à la souris ou au doigt. Il ne voit **jamais** de clé API.

---

## 12. Sécurité

**En une phrase :** le Studio est protégé par un mot de passe vérifié par le serveur, l'API par des clés dont seule l'empreinte est gardée, et l'affichage public par une liste de sites autorisés.

### 12.1 Ce qui protège quoi

```mermaid
flowchart TD
    subgraph Studio["Routes du Studio : /models, /categories, /api-keys"]
        S1["Cookie de session<br/>require_owner"]
    end
    subgraph API["API externe : /api/v1"]
        A1["En-tête X-API-Key<br/>require_api_key + quotas"]
    end
    subgraph Public["Public : /embed, /public, /static, /, /health"]
        P1["Aucun mot de passe<br/>mais modèle activé obligatoire<br/>+ CSP frame-ancestors"]
    end
```

### 12.2 Connexion de la propriétaire

- Le mot de passe vient de `FORMA3D_OWNER_PASSWORD` ; il n'est jamais dans le code ni dans le navigateur.
- Comparaison avec `hmac.compare_digest` : le temps de réponse ne révèle pas la longueur des caractères corrects (protection contre les attaques par mesure du temps).
- Après connexion, le serveur pose un **cookie** `forma3d_session` :
  - **HttpOnly** : JavaScript ne peut pas le lire (protège contre le vol par script) ;
  - **SameSite=Lax** : il n'est pas envoyé par les formulaires d'autres sites ;
  - **Secure** en HTTPS ;
  - durée **8 heures**.
- Le contenu du cookie est un **jeton signé HMAC-SHA256** : `owner.<expiration>.<signature>`. Sans la clé secrète du serveur, impossible d'en fabriquer un faux. Par défaut, la clé est tirée au hasard à chaque démarrage : un redémarrage déconnecte la propriétaire. Si `FORMA3D_SESSION_SECRET` (32 caractères minimum) est défini dans `backend/.env`, la clé est fixe et la session survit aux redémarrages, toujours 8 h au plus ; changer cette valeur déconnecte tout le monde (étape 24).
- Limite : **5 tentatives par minute et par adresse IP** (en mémoire).

🔁 **Keycloak** fait la même chose en plus complet (jetons JWT signés, sessions, rôles). Ici, il n'y a qu'un utilisateur et un seul rôle.

### 12.3 Clés API

- Format : `f3d_live_…` (un préfixe lisible + un secret aléatoire).
- Le secret est montré **une seule fois**, à la création (réponse avec `Cache-Control: no-store`).
- La base garde seulement l'**empreinte SHA-256** du secret. Un **hachage** est une fonction à sens unique : on peut vérifier une clé, mais pas retrouver la clé à partir de l'empreinte.
- **Révoquer** : la clé est refusée immédiatement (401), la ligne reste comme trace. **Supprimer définitivement** : seulement après révocation.
- **Quotas par clé** : `API_DAILY_GENERATION_LIMIT` créations par jour, `API_RATE_LIMIT_PER_MINUTE` requêtes par minute (429 avec `Retry-After`).

### 12.4 CORS et CSP

| Mécanisme | Question à laquelle il répond | Réglage | Par défaut |
|---|---|---|---|
| **CORS** (Cross-Origin Resource Sharing) | « Le JavaScript d'un autre site peut-il appeler l'API ? » | `API_CORS_ORIGINS` | Aucun site |
| **CSP `frame-ancestors`** (Content Security Policy) | « Un autre site peut-il afficher `/embed` dans une iframe ? » | `EMBED_ALLOWED_ORIGINS` | Seulement le Studio (`'self'`) |

Les deux refusent `*`. Le test d'intégration du 12 novembre 2026 l'a vérifié : la page s'affiche sur le site autorisé et elle est bloquée sur un site non autorisé (voir `docs/etapes/etape-17.md`). ✅

### 12.5 Ce qui n'est pas encore protégé

- ⚠️ **HTTP en local** : sans HTTPS, le cookie et les clés circulent en clair sur le réseau. Usage local uniquement tant qu'il n'y a pas de déploiement HTTPS.
- ⚠️ Pas de jeton anti-CSRF dédié (seulement `SameSite=Lax`).
- ⚠️ Pas de comptes multiples ni de rôles : un seul mot de passe (conception de la suite : section 18).
- ✅ La suppression d'un modèle n'existe que dans le Studio (session propriétaire) ; l'API `/api/v1` n'en propose pas : une clé API volée ne peut rien effacer.
- ⚠️ La limite de tentatives est en mémoire : elle repart à zéro au redémarrage.
- ⚠️ `/health/provider` est public (il ne donne qu'un statut, jamais l'adresse du serveur).
- ⚠️ Tout le monde qui connaît le `public_id` d'un modèle activé peut le voir ; désactiver l'intégration coupe l'accès.


### 12.6 Encadrés

> **Un exemple concret.** Trois essais avec PowerShell montrent le rôle de la clé API : sans en-tête `X-API-Key` → **401** ; avec une fausse clé → **401** ; avec la vraie clé → **200** et l'état du modèle. Après révocation dans « Clés API », le même appel repasse à **401**. Côté Studio, si le serveur redémarre sans `FORMA3D_SESSION_SECRET`, le cookie n'est plus reconnu et l'écran de connexion réapparaît.

> **Une analogie.** 🔁 Keycloak émet des jetons JWT signés et gère utilisateurs et rôles ; ici, un seul utilisateur, un jeton signé HMAC dans un cookie HttpOnly, et une dépendance FastAPI `require_owner` qui joue le rôle d'un filtre Spring Security sur les routes du Studio. Les clés API ressemblent aux « client credentials » d'un client OAuth, stockées seulement sous forme d'empreinte, comme un mot de passe haché.

> **Ce que je réponds si on me demande pourquoi.** « J'ai séparé trois portes : la session de la propriétaire pour le Studio, une clé API pour les programmes, et un accès public limité aux modèles explicitement activés sur des sites autorisés. Aucun secret n'est stocké en clair, et tout est fermé par défaut. »

---

## 13. Intégration chez un client

**En une phrase :** un site partenaire affiche un modèle activé avec une iframe ou une balise `<forma3d-viewer>`, et peut piloter les créations par l'API `/api/v1`.

### 13.1 Trois façons d'intégrer

| Méthode | Pour qui | Clé API ? | Exemple |
|---|---|---|---|
| **iframe** | N'importe quel site | Non | `<iframe src="https://SERVICE/embed/PUBLIC_ID" width="100%" height="480">` |
| **Widget** `<forma3d-viewer>` | Site qui accepte un script | Non | voir ci-dessous |
| **API `/api/v1`** | Le **serveur** de la boutique | Oui (`X-API-Key`) | `curl -H "X-API-Key: …" …/api/v1/models/ID` |

### 13.2 Le widget pas à pas

```html
<script src="https://SERVICE/static/widget.js" defer></script>
<forma3d-viewer model="PUBLIC_ID" height="480" auto-rotate></forma3d-viewer>
```

1. `widget.js` définit la balise `forma3d-viewer` (Web Component).
2. La balise lit `model` (le `public_id`, contrôlé : format UUID), `height` (bornée entre 240 et 1200 px) et `auto-rotate`.
3. Elle crée une iframe vers `/embed/{public_id}` sur le même serveur que le script.
4. La clé API n'est **jamais** utilisée par le widget.

### 13.3 Les routes de l'API externe

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/v1/models` | Envoyer une photo (`file`, `category`) ; réponse 202 |
| `GET` | `/api/v1/models/{id}` | Lire l'état |
| `GET` | `/api/v1/models/{id}/glb` | Télécharger le GLB (409 si pas prêt) |
| `GET` | `/api/v1/models/{id}/integration-code` | Obtenir `iframe_html`, `widget_html`, `public_id` (403 si l'intégration n'est pas activée) |

Les erreurs ont toujours la forme `{"error": {"code": "...", "message": "..."}}`.

### 13.4 Exemple de test fourni

`examples/integration.html` est un faux site de boutique : on y saisit l'adresse de Forma3D et un `public_id`, puis la page charge le widget. Mode d'emploi complet : `docs/INTEGRATION.md` et la page `#/guide`.


### 13.5 Ce qui se passe quand un visiteur ouvre la page produit

```mermaid
sequenceDiagram
    participant V as Navigateur du visiteur
    participant B as Site vitrine (port 8081)
    participant F as Forma3D (port 8001)
    V->>B: GET /ma-vitrine.html
    B-->>V: page HTML avec iframe ou widget
    V->>F: GET /embed/{public_id}
    F->>F: modèle DONE et embed_enabled ? origine autorisée ?
    F-->>V: page du viewer + en-tête CSP frame-ancestors
    V->>F: GET /public/models/{public_id}/glb
    F-->>V: fichier GLB affiché par model-viewer
```

> **Un exemple concret.** Sur le PC de l'étudiante : terminal 1, `dev.ps1` (Forma3D sur 8001) ; terminal 2, `python -m http.server 8081` (le « site vitrine »). Avec `EMBED_ALLOWED_ORIGINS=http://127.0.0.1:8081` dans `backend/.env`, la page `examples/integration.html` affiche le fauteuil vert. Le port fait partie de l'origine : pour le navigateur, 8001 et 8081 sont deux sites différents.

> **Une analogie.** 🔁 C'est comme intégrer une vidéo YouTube : on colle une balise, la vidéo reste hébergée chez YouTube, et YouTube décide quels sites ont le droit de l'afficher. Le widget `<forma3d-viewer>` est un Web Component, comparable à un composant Angular exporté en « Angular Elements » utilisable dans n'importe quelle page.

> **Ce que je réponds si on me demande pourquoi.** « L'intégration n'a besoin d'aucune clé : le visiteur ne voit jamais de secret. La clé API sert seulement au serveur de la boutique. L'adresse `127.0.0.1` ne fonctionne que sur mon PC ; un vrai site en ligne demanderait un hébergement HTTPS, prévu dans l'architecture cible. »

---

## 14. Tests et CI/CD

**En une phrase :** 159 tests automatiques (au 15 novembre 2026) vérifient le backend et les fichiers du frontend, et GitHub les relance à chaque envoi de code.

### 14.1 Ce que prouvent les tests

- Ils prouvent que les **règles du code** sont respectées : validation des photos, états des générations, sécurité des clés, protection des routes, structure des GLB, présence des éléments d'interface.
- Ils utilisent des **faux fournisseurs** : aucun test n'appelle vraiment un service d'IA.
- Ils **ne prouvent pas** la qualité visuelle d'un modèle, ni le rendu réel dans un navigateur, ni la disponibilité des services gratuits.

Lancer les tests (Windows, depuis la racine du dépôt) :

```powershell
cd backend
$env:PYTHON_DOTENV_DISABLED = "true"; $env:HF_SPACE_ID = ""
.venv\Scripts\python.exe -m pytest -q
```

**Isolation des tests** (corrigée le 15 novembre 2026) : un test ne doit jamais dépendre de la machine de la développeuse.

| Problème rencontré | Cause | Correction |
|---|---|---|
| Avec `IMAGE3D_PROVIDER=trellis` et `HF_TOKEN` dans `backend/.env`, deux tests de `test_health.py` recevaient « ONLINE » | Le test remplaçait `main_module.provider`, mais la route lit `app.state.generation_provider` (TRELLIS), qui interrogeait le vrai Space | Le test remplace l'objet réellement lu par la route |
| Après une vraie génération, deux tests de `test_demo_gallery.py` échouaient | Ils lisaient la vraie base `backend/data/forma3d.sqlite3` | Le service est remplacé par un faux service vide pendant ces tests |
| `dev.ps1` dépendait du `.env` réel pendant pytest | python-dotenv chargeait `backend/.env` | pytest tourne avec `PYTHON_DOTENV_DISABLED=true` et `HF_SPACE_ID` vide ; le serveur, lui, lit toujours `.env` |

### 14.2 CI et CD en mots simples

- **CI (intégration continue)** : à chaque envoi de code, un robot récupère le projet, installe les dépendances et lance les tests. Si un test échoue, on le voit tout de suite.
- **CD (déploiement continu)** : après des tests réussis, un robot met automatiquement le site en ligne.
- ✅ Le projet a la **CI**. ❌ Il n'a **pas de CD** : aucun déploiement automatique n'existe.

```mermaid
flowchart LR
    A["git push"] --> B["GitHub Actions<br/>machine Ubuntu"]
    B --> C["Installe Python 3.14<br/>et les dépendances"]
    C --> D["pytest -q"]
    D --> E["Vérifie la présence<br/>des fichiers requis"]
    E --> F{"Tout est vert ?"}
    F -->|oui| G["Coche verte sur GitHub"]
    F -->|non| H["Croix rouge + journal d'erreur"]
```

### 14.3 `.github/workflows/ci.yml` ligne par ligne

| Ligne(s) | Sens |
|---|---|
| `name: Project checks` | Nom affiché dans l'onglet « Actions » de GitHub |
| `on: push` et `pull_request` | Se lance à chaque envoi de code et à chaque demande de fusion |
| `permissions: contents: read` | Le robot peut seulement **lire** le dépôt (sécurité) |
| `jobs: project-checks:` | Une seule tâche nommée « Documents and backend tests » |
| `runs-on: ubuntu-latest` | Machine virtuelle Linux fournie par GitHub |
| `uses: actions/checkout@v7` | Récupère le code du dépôt |
| `uses: actions/setup-python@v7` avec `python-version: "3.14"` | Installe Python 3.14 |
| `run: python -m pip install -r requirements.txt` (dans `backend`) | Installe les dépendances |
| `run: python -m pytest -q` (dans `backend`) | Lance tous les tests |
| `test -f README.md` … `test -f frontend/README.md` | Vérifie que les documents obligatoires existent (`set -euo pipefail` arrête au premier fichier manquant) |

⚠️ Le résultat de la CI se lit dans l'onglet **Actions** du dépôt GitHub ; il n'a pas été vérifié pour ce document (**à vérifier**).


### 14.4 Encadrés

> **Un exemple concret.** Le 15 novembre 2026, `dev.ps1` refusait de démarrer : « Les tests ont échoué ». Les tests de santé lisaient le vrai `.env` de l'étudiante (TRELLIS + jeton) et interrogeaient le vrai Space. Correction : le test remplace l'objet que la route utilise vraiment, et pytest tourne sans `.env`. Preuve : les tests passent avec l'environnement par défaut **et** avec des variables factices (`IMAGE3D_PROVIDER=trellis`, `HF_TOKEN=jeton-factice-pour-test`).

> **Une analogie.** 🔁 C'est l'équivalent de JUnit avec Mockito : les fournisseurs 3D sont remplacés par des faux objets (`FakeClient`, `SuccessfulProvider`), et `app.dependency_overrides` de FastAPI joue le rôle de `@MockBean` dans un test Spring Boot.

> **Ce que je réponds si on me demande pourquoi.** « Un test doit donner le même résultat sur toutes les machines. Mes tests n'appellent jamais un service d'IA, n'utilisent pas ma vraie base et ne lisent pas mon `.env` ; ils prouvent les règles du code, pas la qualité visuelle, que je vérifie à la main. »

---

## 15. Installer, configurer, lancer, dépanner

**En une phrase :** on installe Python, on crée un environnement virtuel, on renseigne `backend/.env`, puis on lance uvicorn depuis la racine du dépôt principal.

### 15.1 Installation (Windows, une seule fois)

```powershell
cd C:\chemin\vers\forma3d-kit-codex
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
copy .env.example backend\.env
```

Puis ouvrez `backend\.env` et renseignez au minimum `FORMA3D_OWNER_PASSWORD`.

### 15.2 Lancer

```powershell
cd C:\chemin\vers\forma3d-kit-codex
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000
```

Ouvrez `http://127.0.0.1:8000`. Variante automatique, recommandée : `.\scripts\dev.ps1` (lance d'abord les tests isolés, puis le serveur sur le port **8001**, et ouvre Edge).

| Lancement | Port | Lit `backend/.env` ? |
|---|---|---|
| `.\scripts\dev.ps1` | **8001** | Oui pour le serveur, non pour les tests |
| `uvicorn … --port 8000` à la main | **8000** (ou le port choisi) | Oui |

⚠️ Si un serveur répond déjà sur le port, `dev.ps1` affiche « API prête » **sans le redémarrer** : après une modification de `backend/.env`, arrêtez d'abord l'ancien serveur. Le serveur tourne en arrière-plan et ne s'arrête pas quand on ferme le terminal :

```powershell
Get-NetTCPConnection -LocalPort 8001 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess }
```

### 15.3 Erreurs fréquentes

| Symptôme | Cause probable | Solution |
|---|---|---|
| La page affiche encore l'ancienne version | Cache du navigateur | Recharger avec **Ctrl+F5** |
| Mes modèles ou mes réglages ont « disparu » | Serveur lancé depuis le mauvais dossier (une copie de travail au lieu du dépôt principal) | Lancer depuis la racine du dépôt principal, celle qui contient votre `backend/.env` et `backend/data/` |
| « Connexion impossible : définissez FORMA3D_OWNER_PASSWORD… » | Mot de passe absent de `backend/.env` (ou mis par erreur dans `.env.example`) | L'ajouter dans `backend/.env`, redémarrer |
| `error while attempting to bind on address … 8000` | Port déjà utilisé par un autre serveur | Arrêter l'autre serveur (Ctrl+C) ou utiliser `--port 8001` |
| Badge « Serveur 3D : hors ligne » | Voir la section 17 (fournisseur non configuré, ancien serveur, quota, Colab expiré…) | Lire `/health/provider`, puis suivre la section 17 |
| « Les tests ont échoué ; le serveur n'a pas été démarré » | Un test a échoué : `dev.ps1` refuse alors de démarrer le serveur | Lire le nom du test en rouge ; mettre le dépôt à jour (`git pull`) |
| « API prête » mais l'ancienne configuration reste active | Un ancien serveur occupait déjà le port | Arrêter l'ancien serveur (commande ci-dessus), relancer |
| « The read operation timed out » | Space TRELLIS très lent (ancien délai de 5 s) | Corrigé (120 s par requête) ; mettre le dépôt à jour |
| Le bouton « Supprimer ce modèle » n'apparaît pas | Ancienne version de `model-detail.js` en cache | **Ctrl+F5**, ou F12 puis « Vider le cache et effectuer une actualisation forcée » |
| « Quota GPU gratuit du Space TRELLIS atteint » | Quota journalier épuisé | Réessayer plus tard ; ajouter un jeton gratuit `HF_TOKEN` |
| Le modèle paraît noir | Matériau métallique par défaut (ancien fichier) | Déjà corrigé à l'affichage et pour les nouveaux fichiers ; recharger avec Ctrl+F5 |
| Un site partenaire n'affiche rien | Origine absente de `EMBED_ALLOWED_ORIGINS`, ou intégration non activée | Ajouter l'origine exacte, redémarrer, activer l'interrupteur sur la fiche |

---

## 16. Limites, travail restant et perspectives

**En une phrase :** le prototype fonctionne de bout en bout en local, mais il reste mono-propriétaire, dépendant de services gratuits instables, et non déployé.

### 16.1 Limites honnêtes

- **Qualité 3D** : une seule photo ne montre pas l'arrière ; TripoSR a des couleurs approximatives, TRELLIS invente parfois des parties (exemple observé : une table en demi-lune devenue ovale).
- **Fiabilité** : Colab expire, les Spaces gratuits ont des quotas journaliers et des mises en veille.
- **Génération TRELLIS depuis le Studio** : obtenue le 15 novembre 2026 (fauteuil rétro vert : GLB affiché, intégré et visible sur une page de test), après la correction du délai HTTP. Elle reste dépendante du quota quotidien et de la disponibilité du Space.
- **Qualité selon la photo** : un fauteuil blanc sur fond gris clair, en petite capture d'écran, a donné un modèle posé sur une « dalle » : le détourage n'a pas séparé l'objet du sol (contraste trop faible, ombre, image de moins de 512 px).
- **Sécurité** : usage local, HTTP, un seul mot de passe (section 12.5).
- **Données** : SQLite et disque local, sans sauvegarde automatique.
- **Pas de déploiement** ni de CD.

### 16.2 La deuxième partie du projet (proposée, non commencée)

Décision du 15 novembre 2026 : option C (rester mono-propriétaire pour la soutenance). L'architecture détaillée est dans `docs/ARCHITECTURE-CIBLE.md` et résumée en section 18. La suppression d'un modèle existe désormais, en version définitive avec confirmation (étape 23).

| Étape | Contenu |
|---|---|
| D | Comptes vendeurs et inscription ; données séparées par boutique ; tests d'isolation |
| E | Rôle `superadmin`, journal d'audit, suppression réversible |
| F | Passage à PostgreSQL grâce à l'interface `GenerationRepository` ; sauvegardes |
| G | Récupération de mot de passe par courriel (service d'envoi à choisir) |
| Plus tard | Plusieurs vues d'un même produit (face, côté, arrière) si le modèle le permet ; application pour une plateforme e-commerce ; déploiement HTTPS |

---

## 17. Pourquoi le serveur 3D affiche « hors ligne »

**En une phrase :** le badge rouge signifie que Forma3D ne peut pas joindre son fournisseur 3D ; la cause se lit sur `/health/provider`, et tout le reste du Studio continue de fonctionner.

### 17.1 Lire le diagnostic

Ouvrez `http://127.0.0.1:8001/health/provider` (ou `8000` si uvicorn est lancé à la main). La réponse ne contient jamais l'adresse du serveur ni le jeton :

```json
{"status": "OFFLINE", "message": "Le serveur 3D (Colab) est arrêté ou son lien a expiré (72 h)…"}
```

| `status` | Message | Ce que ça veut dire |
|---|---|---|
| `ONLINE` | « Le serveur 3D est joignable. » | Tout va bien |
| `UNCONFIGURED` | « HF_SPACE_ID est vide… » | Fournisseur TripoSR sans adresse : `IMAGE3D_PROVIDER` n'est pas `trellis` et `HF_SPACE_ID` est vide |
| `OFFLINE` + « Colab » | « Le serveur 3D (Colab) est arrêté ou son lien a expiré… » | Le serveur utilise **TripoSR** : soit le lien Colab a expiré, soit `IMAGE3D_PROVIDER=trellis` n'a pas été pris en compte |
| `OFFLINE` + « TRELLIS » | « Le Space TRELLIS est en veille, en panne ou indisponible… » | TRELLIS est bien configuré, mais le Space ne répond pas « RUNNING » |

### 17.2 Les causes, dans l'ordre où les chercher

```mermaid
flowchart TD
    A["Badge rouge"] --> B{"/health/provider"}
    B -->|UNCONFIGURED| C["Fournisseur non configuré :<br/>IMAGE3D_PROVIDER ou HF_SPACE_ID"]
    B -->|OFFLINE + Colab| D{"Le serveur a-t-il été<br/>relancé après la<br/>modification de .env ?"}
    D -->|non| E["Arrêter l'ancien serveur<br/>puis relancer dev.ps1"]
    D -->|oui| F["Lancé depuis le bon dossier ?<br/>Ligne IMAGE3D_PROVIDER correcte ?<br/>Sinon : lien Colab expiré"]
    B -->|OFFLINE + TRELLIS| G["Space en veille ou en panne :<br/>réessayer plus tard"]
    B -->|ONLINE mais création en échec| H["Lire le message d'échec :<br/>quota épuisé, délai, contrat changé"]
```

| Cause | Comment la reconnaître | Que faire |
|---|---|---|
| **Fournisseur non configuré** | `UNCONFIGURED` | Dans `backend/.env` : `IMAGE3D_PROVIDER=trellis` (ou une adresse `HF_SPACE_ID` pour TripoSR), puis redémarrer |
| **Ancien serveur encore actif** | Message « Colab » alors que `.env` dit `trellis` ; `dev.ps1` affiche « API prête » sans redémarrer | Arrêter le serveur sur le port 8001 (section 15.2), relancer |
| **Serveur lancé depuis le mauvais dossier** | Par exemple depuis `.claude\worktrees\…`, qui n'a pas de `backend/.env` | Lancer depuis la racine du dépôt principal |
| **Jeton absent** | Pas d'erreur immédiate, mais quota anonyme très petit | Ajouter `HF_TOKEN` (gratuit) dans `backend/.env` |
| **Quota épuisé** | Badge parfois vert, mais création en échec : « Quota GPU gratuit du Space TRELLIS atteint… » | Attendre la recharge quotidienne ; ne pas relancer en boucle |
| **Lien Colab expiré** (TripoSR) | `OFFLINE` + « Colab » | Relancer le notebook, copier la nouvelle adresse dans `HF_SPACE_ID`, redémarrer |
| **Space lent ou en veille** | `OFFLINE` + « TRELLIS », ou création longue | Réessayer plus tard |

⚠️ Le badge est rafraîchi toutes les 30 s (`main.js`) ; au chargement il peut être jaune quelques secondes (vérification en cours).

### 17.3 Ce qui reste utilisable sans fournisseur

- ✅ Exemples du catalogue, et « Ajouter à mes modèles »
- ✅ Import d'un `.glb` existant
- ✅ Fiches, comparaison photo/modèle, téléchargement, suppression
- ✅ Activation de l'intégration, iframe, widget, page `/embed`
- ✅ Clés API et routes `/api/v1` de lecture
- ❌ Seule la **création à partir d'une photo** est bloquée (bouton désactivé)

> **Ce que je réponds si on me demande pourquoi.** « Le fournisseur est un service gratuit externe : il peut dormir ou atteindre son quota. J'ai donc rendu son état visible, sans jamais exposer d'adresse ni de jeton, et j'ai gardé tout le reste du Studio utilisable hors ligne. »

---

## 18. Du Studio privé au SaaS

**En une phrase :** pour la soutenance, Forma3D reste une console privée (option C) ; le passage à un SaaS multi-clients est conçu en détail dans `docs/ARCHITECTURE-CIBLE.md`, mais pas codé.

| Thème | Aujourd'hui | Demain (cible) |
|---|---|---|
| Rôles | Propriétaire seule | Visiteur, client inscrit, administrateur |
| Isolation | Sans objet | `owner_id` sur modèles, clés API et sites autorisés ; chaque requête vérifie le propriétaire (sinon : faille IDOR) |
| Base | SQLite local | PostgreSQL hébergé, avec Row Level Security |
| Fichiers | `backend/storage/` | Stockage d'objets séparé |
| Authentification | Mot de passe unique | Supabase Auth recommandé (option A) plutôt qu'une authentification maison (option B) |
| Goulot | Quota GPU gratuit | Le même quota, partagé par tous les clients : c'est la vraie limite |
| Données personnelles | Aucune inscription | RGPD : consentement, export, suppression de compte |

```mermaid
flowchart LR
    C["Option C<br/>soutenance<br/>(choisie)"] --> A["Option A<br/>Supabase<br/>(recommandée ensuite)"]
    C -.-> B["Option B<br/>PostgreSQL + auth maison<br/>(déconseillée)"]
```

Pourquoi la migration est possible : le service dépend de l'interface `GenerationRepository`, pas de SQLite (section 6.6). Le vrai travail serait d'ajouter l'`owner_id` à chaque méthode et à chaque route.

👉 Lire `docs/ARCHITECTURE-CIBLE.md` : schéma des tables, comparaison des options avec les liens officiels, plan en étapes, et dix phrases prêtes pour l'oral.

---

## 19. Comment travailler avec Git sur ce projet

**En une phrase :** chaque changement est fait sur une branche, proposé dans une pull request, fusionné dans `main` sur GitHub, puis récupéré sur le PC avec `git pull`.

```mermaid
sequenceDiagram
    participant W as Copie de travail (branche)
    participant G as GitHub
    participant M as Dossier principal (main)
    W->>W: modifications + tests + commit
    W->>G: git push (nouvelle branche)
    G->>G: pull request, relecture, CI
    G->>G: Merge dans main
    M->>G: git pull
    G-->>M: main à jour
    M->>M: arrêter l'ancien serveur, relancer dev.ps1
```

| Mot | Sens | Commande |
|---|---|---|
| **Branche** | Une ligne de travail séparée de `main` | `git switch -c ma-branche` |
| **Commit** | Une photo enregistrée des modifications | `git commit -m "message"` |
| **Push** | Envoyer ses commits sur GitHub | `git push -u origin ma-branche` |
| **Pull request (PR)** | Demande de fusion d'une branche dans `main`, avec relecture et CI | bouton « Create pull request » sur GitHub |
| **Merge** | Fusionner la PR dans `main` | bouton « Merge » sur GitHub |
| **Pull** | Récupérer sur son PC ce qui a été fusionné | `git pull` |

**Pourquoi un assistant peut travailler dans un worktree séparé.** Un *worktree* est un **deuxième dossier** relié au même dépôt Git, sur une autre branche (ici sous `.claude\worktrees\…`). L'assistant y travaille sans toucher au dossier où la propriétaire lance le site. Conséquences vécues le 15 novembre 2026 :

- une correction faite dans le worktree n'est **pas** active chez soi tant que la PR n'est pas fusionnée et que `git pull` n'est pas fait ;
- le worktree n'a **pas** de `backend/.env` ni de base `backend/data/` : un serveur lancé depuis ce dossier affiche « hors ligne » et une bibliothèque vide ;
- après `git pull`, il faut **redémarrer** le serveur, et parfois faire **Ctrl+F5** dans le navigateur (fichiers JavaScript en cache).

> **Une analogie.** 🔁 C'est le même flux que sur GitLab ou GitHub avec un projet Angular ou Spring Boot en équipe : une branche par fonctionnalité, une *merge request*, la CI, puis la fusion.

> **Ce que je réponds si on me demande pourquoi.** « Chaque changement passe par une pull request : il est relu et testé par la CI avant d'arriver dans `main`. L'historique montre exactement quand et pourquoi chaque fonctionnalité a été ajoutée. »

---

## 20. Glossaire A–Z

| Terme | Définition |
|---|---|
| **API** | Interface qui permet à un programme d'en appeler un autre par des requêtes |
| **Clé API** | Secret qui identifie un programme client ; ici `f3d_live_…` |
| **CI / CD** | Intégration continue (tests automatiques) / déploiement continu (mise en ligne automatique) |
| **Colab** | Service Google qui prête un GPU gratuitement, pour une durée limitée |
| **Cookie HttpOnly** | Petit fichier du navigateur, illisible par JavaScript, qui garde la session |
| **CORS** | Règle qui autorise ou non le JavaScript d'un autre site à appeler une API |
| **CSP** | Politique de sécurité envoyée par le serveur ; `frame-ancestors` dit qui peut afficher la page dans une iframe |
| **Détourage** | Suppression du fond d'une photo pour ne garder que l'objet |
| **Empreinte (hachage)** | Résultat d'une fonction à sens unique (SHA-256) : sert à vérifier un secret sans le stocker |
| **FastAPI** | Framework Python qui transforme des fonctions en routes HTTP |
| **GLB / glTF** | Format standard de fichier 3D pour le web ; GLB est la version binaire en un seul fichier |
| **Gradio** | Bibliothèque qui crée une page web autour d'un modèle d'IA |
| **HMAC** | Signature calculée avec une clé secrète ; prouve qu'un jeton n'a pas été modifié |
| **Hugging Face Space** | Démonstration d'IA hébergée gratuitement sur huggingface.co |
| **IDOR** | Faille où l'on accède à la ressource d'un autre en changeant un identifiant, faute de vérifier le propriétaire |
| **iframe** | Cadre qui affiche une page web à l'intérieur d'une autre page |
| **Maillage (mesh)** | Ensemble des triangles qui forment la surface d'un objet 3D |
| **Matériau** | Description de la réaction d'une surface à la lumière (couleur, métal, rugosité) |
| **Migration** | Modification de la structure d'une base de données sans perdre les données |
| **model-viewer** | Composant HTML de Google qui affiche un fichier 3D |
| **Module ES** | Fichier JavaScript qui exporte et importe des fonctions (`import` / `export`) |
| **Multi-tenant** | Une seule application et une seule base servent plusieurs clients, dont les données sont séparées |
| **Normale** | Direction perpendiculaire à une surface, utilisée pour l'éclairage |
| **owner_id** | Colonne qui indique à quel client appartient une ligne (modèle, clé API, site autorisé) |
| **Pré-entraîné** | Modèle d'IA déjà appris par une autre équipe ; on l'utilise sans l'entraîner |
| **Pull request (PR)** | Demande de fusion d'une branche dans `main`, relue et testée avant la fusion |
| **Pydantic** | Bibliothèque Python qui valide la forme des données JSON |
| **Quota** | Limite d'utilisation (par jour ou par minute) |
| **RGPD** | Règlement européen sur la protection des données personnelles (consentement, accès, effacement) |
| **Révoquer** | Désactiver définitivement une clé tout en gardant sa trace |
| **RLS (Row Level Security)** | Règle PostgreSQL qui filtre les lignes selon l'utilisateur, même si le code oublie le filtre |
| **Routeur** | Code qui associe une adresse à une page (frontend) ou une route à une fonction (backend) |
| **SPA** | Application à page unique : le contenu change sans recharger la page |
| **SQLite** | Base de données SQL contenue dans un seul fichier |
| **Tâche de fond** | Travail exécuté après la réponse HTTP (ici, la génération) |
| **Texture** | Image plaquée sur la surface d'un objet 3D |
| **TRELLIS** | Modèle d'IA de Microsoft qui produit un modèle 3D texturé à partir d'une image |
| **TripoSR** | Modèle d'IA de Stability AI et Tripo qui produit un modèle 3D à couleurs de sommets |
| **UUID** | Identifiant unique de 36 caractères, impossible à deviner en pratique |
| **uvicorn** | Serveur qui exécute une application FastAPI |
| **Worktree** | Deuxième dossier de travail relié au même dépôt Git, sur une autre branche |
| **Web Component** | Balise HTML personnalisée créée en JavaScript (`<forma3d-viewer>`) |
| **Widget** | Petit composant intégrable dans un autre site |
| **ZeroGPU** | GPU gratuit partagé des Spaces Hugging Face, limité par un quota journalier attaché au compte (environ 2 min sans compte, 5 min avec un compte gratuit : à vérifier) |
