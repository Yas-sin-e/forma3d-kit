# Guide pour comprendre le code de Forma3D Studio (à lire en premier)

Ce dossier explique **chaque fichier du backend, du frontend et des tests**, étape par étape,
avec des mots simples et de vrais extraits du code. Lis les fichiers **dans l'ordre** :
chaque étape s'appuie sur la précédente.

| Fichier | Ce que tu vas comprendre | Fichiers du code expliqués |
|---|---|---|
| `01_idee_generale.md` | Le problème, la solution et l'organisation en couches | — |
| `02_etape1_demarrage_config.md` | Comment le serveur démarre et lit sa configuration | `requirements.txt`, `__init__.py`, `main.py`, `config.py` |
| `03_etape2_objets_metier_schemas.md` | Les « objets » du projet et la forme du JSON | `models.py`, `schemas.py` |
| `04_etape3_photo_et_fichiers.md` | Contrôler la photo, la préparer, l'enregistrer | `upload_validator.py`, `image_preparer.py`, `storage/base.py`, `local_storage.py` |
| `05_etape4_generation_3d.md` | Le cœur : de la photo au GLB, états PENDING → DONE | `generation_service.py`, `providers/base.py`, `trellis.py`, `glb_finisher.py` |
| `06_etape5_base_postgresql.md` | Où et comment les données sont gardées | `repositories/base.py`, `factory.py`, `postgres_repository.py` |
| `07_etape6_routes_studio.md` | Les adresses HTTP du Studio (modèles, catégories, exemples) | `routers/models.py`, `routers/categories.py`, `category_service.py`, `demo_gallery.py` |
| `08_etape7_connexion_et_cles_api.md` | Qui a le droit d'entrer : mot de passe, session, clés API | `routers/auth.py`, `owner_auth.py`, `routers/api_keys.py`, `api_key_service.py` |
| `09_etape8_api_externe_embed_widget.md` | Comment un site partenaire affiche un modèle | `routers/api_v1.py`, `routers/embed.py`, `frontend/widget.js` |
| `10_etape9_frontend_socle.md` | La coque HTML, le routeur, l'unique fichier qui parle au serveur | `index.html`, `css/`, `main.js`, `router.js`, `api.js`, `auth.js`, `state.js`, `format.js` |
| `11_etape10_pages_et_vues.md` | Chaque écran du Studio et ses morceaux réutilisables | `js/pages/*.js`, `js/views/*.js` |
| `12_etape11_tests.md` | Les tests automatiques pytest | `backend/tests/*.py` |
| `13_lancer_le_projet.md` | Les commandes à taper, et quoi faire si ça ne marche pas | — |
| `14_questions_pour_la_soutenance.md` | Les questions possibles du jury, avec des réponses courtes | — |

> Le fournisseur **TripoSR** (`backend/app/providers/huggingface.py`) n'est volontairement **pas détaillé**
> ici : on retient seulement qu'il respecte le même contrat que TRELLIS (« une image entre, un GLB sort »).

## Le projet en une phrase

> La propriétaire envoie **une photo** d'un petit meuble ; un **modèle d'IA déjà entraîné** fabrique
> un fichier 3D **`.glb`** ; elle le vérifie dans le **Studio**, puis peut l'**afficher sur un site
> partenaire** grâce à une balise HTML ou à une **API protégée par clé**.

## Le chemin d'une photo, en image

```
 Navigateur (Studio)                 Serveur FastAPI                         Extérieur
 ───────────────────                 ───────────────                         ─────────
 create.js ─ api.js ── POST /models ─► routers/models.py
                                         │ 1. UploadValidator  (bon format ? ≤ 10 Mo ?)
                                         │ 2. LocalStorage     (photo enregistrée sur le disque)
                                         │ 3. PostgreSQL       (ligne « PENDING »)
       ◄──────── 202 + status_url ───────┘
                                         ▼  tâche de fond : GenerationService.run()
                                         │ 4. ImagePreparer    (copie carrée 512 px minimum)
                                         │ 5. Fournisseur 3D ─────────────────────► Space TRELLIS
                                         │                    ◄──── fichier GLB ── (ou TripoSR)
                                         │ 6. glb_finisher     (matériau mat + normales)
                                         │ 7. LocalStorage     (GLB enregistré)
                                         │ 8. PostgreSQL       (ligne « DONE »)
 progress.js ◄── GET /models/{id} toutes les 1,5 s ── (PENDING → RUNNING → DONE)
 viewer.js   ◄── GET /models/{id}/glb ── le modèle s'affiche dans <model-viewer>
```

- **GLB** = un fichier 3D en un seul morceau (formes + couleurs). C'est le « JPEG de la 3D ».
- **FastAPI** = le framework Python qui transforme des fonctions en adresses HTTP (rôle de Spring Boot).
- **Tâche de fond** = travail lancé **après** la réponse : le navigateur n'attend pas les 1 à 3 minutes de génération.
- **Polling** = le navigateur redemande l'état régulièrement, comme on rafraîchit un suivi de colis.

## Où est quoi dans le code

```
backend/
  requirements.txt          ← les bibliothèques Python à installer
  app/
    main.py                 ← POINT D'ENTRÉE : crée l'application et branche tout
    config.py               ← lit et vérifie les réglages (.env)
    models.py               ← les objets métier (génération, catégorie, clé API)
    schemas.py              ← la forme exacte du JSON envoyé et reçu
    routers/                ← les PORTES : une fonction = une adresse HTTP
    services/               ← les RÈGLES : ce qu'on a le droit de faire, dans quel ordre
    providers/              ← les FOURNISSEURS 3D : TRELLIS ou TripoSR
    repositories/           ← la BASE DE DONNÉES : PostgreSQL
    storage/                ← les FICHIERS : photos et GLB sur le disque
  tests/                    ← les tests automatiques pytest
frontend/
  index.html                ← la coque de la page (menu, en-tête, zone #app)
  widget.js                 ← la balise <forma3d-viewer> pour les sites partenaires
  css/                      ← les couleurs et les styles
  js/
    main.js, router.js      ← démarrage et navigation entre les pages
    api.js                  ← le SEUL fichier qui appelle le serveur
    pages/                  ← un fichier par écran
    views/                  ← des morceaux d'écran réutilisables
```

## Les 3 couches à retenir (la phrase clé pour le jury)

```
  ROUTER  ──►  SERVICE  ──►  PROVIDER / REPOSITORY / STORAGE
  (porte)      (règles)      (outils : IA, base de données, disque)
```

Une route **ne parle jamais directement** à la base ni au disque : elle passe par un service.
Le service ne connaît que des **contrats** (interfaces) : on peut changer de fournisseur 3D
ou de base de données **sans réécrire les règles**. C'est exactement l'organisation
`@RestController` → `@Service` → `@Repository` de Spring Boot.
