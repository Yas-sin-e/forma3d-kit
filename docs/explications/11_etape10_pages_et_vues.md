# 11. Étape 10 — Les pages et les vues du Studio

Fichiers : `frontend/js/pages/*.js` (un fichier par écran) et `frontend/js/views/*.js`
(des morceaux d'écran réutilisés par plusieurs pages).

```
pages/  = UN écran complet       (render + mount, appelé par router.js)
views/  = UN morceau réutilisable (appelé par les pages)
```

## Étape 10.1 — Les pages

### `login.js` — Connexion

Écran plein, un seul champ « mot de passe » avec un bouton Afficher/Masquer. À l'envoi :
`login(password)` → `POST /auth/login`. En cas de refus, la page affiche **le message du serveur**
(« Mot de passe incorrect. », « Trop de tentatives. Patientez une minute… »). Elle prévient aussi quand
la session a expiré ou quand `FORMA3D_OWNER_PASSWORD` n'est pas configuré. Après succès : retour à la page demandée.

### `dashboard.js` — Accueil

Présentation, **chiffres réels** (nombre de modèles, de catégories, de clés actives), modèles récents,
aperçu des exemples et raccourcis. Les chiffres viennent des routes existantes : **rien n'est inventé**.

### `create.js` — Créer un modèle (la page la plus importante)

Deux colonnes : la photo à gauche (40 %), le viewer à droite (60 %), le suivi en dessous.

```javascript
async function startGeneration(photo, category) {
  beginGeneration(photo);
  uploader.setBusy(true);
  progress.render("SENDING", { elapsedSeconds: 0 });
  appState.clockTimer = window.setInterval(() => updateProgress(appState.generationStatus), 1000);
  const data = await createGeneration(photo, category);                 // POST /models → 202
  appState.currentStatusUrl = sameOriginPath(data.status_url);
  const terminal = await applyStatus(data);
  if (!terminal) appState.pollingTimer = window.setInterval(() => void refreshStatus(), 1500);
}
```

```javascript
async function applyStatus(data) {
  warning.hidden = !data.image_warning;                                 // « photo floue », etc.
  if (data.status === "PENDING" || data.status === "RUNNING") { updateProgress(data.status); return false; }
  if (data.status === "FAILED") { showFailure(data.error_message || "..."); return true; }
  viewer.showModel({ url: modelUrl, downloadUrl: modelUrl, sourcePhoto: appState.selectedPhoto, ... });
  resultLink.href = `#/modeles/${encodeURIComponent(data.id)}`;          // lien vers la fiche
  return true;
}
```

- **Polling** toutes les 1,5 s jusqu'à DONE ou FAILED ; le chronomètre avance chaque seconde.
- `pollingInFlight` empêche d'envoyer une 2e demande tant que la 1re n'a pas répondu.
- `sameOriginPath()` refuse une adresse de suivi qui pointerait vers un autre site.
- `describeUploadError()` traduit 413, 415, 422, 429 en phrases claires.
- Si le serveur 3D est hors ligne (événement `forma3d:health`), le bouton d'envoi est désactivé avec une explication.
- Bouton **Réessayer** après un échec, avec la même photo.

### `models.js` — Mes modèles

Grille des modèles enregistrés (créés, importés, copiés), filtres par catégorie avec compteurs, état vide
illustré. Bouton **Importer un GLB** (`#/modeles?import=1` l'ouvre directement) → `POST /models/import`.

### `model-detail.js` — Fiche d'un modèle

- Bascule **Vue 3D / Photo source / Comparer** (côte à côte).
- Informations : origine, catégorie, date, taille, durée de génération.
- **✎ Modifier** : formulaire en ligne pour le nom et la catégorie (`PATCH .../name` et `.../category`).
- **Intégration guidée en 4 étapes** : interrupteur d'activation → choix iframe ou widget → code à copier → aperçu réel via `/embed`.
- **Supprimer ce modèle** avec fenêtre de confirmation, puis retour à « Mes modèles ».
- Un identifiant inconnu affiche un message clair (pas une page blanche).

### `examples.js` — Exemples

Les 5 modèles de démonstration, avec une description et la **durée réellement mesurée** pendant les essais.
Bouton « Ajouter à mes modèles » → `POST /models/examples/{id}/copy`.

### `categories.js` — Catégories

Page d'administration ; elle compte les modèles par catégorie et confie la gestion à `views/categories.js`.

### `api-keys.js` — Clés API

Guide en 4 étapes, exemple `curl` réel avec l'adresse du serveur, liste des clés avec badge de statut.
À la création, le secret est affiché **une seule fois** avec un bouton Copier, puis oublié.
Révocation puis suppression définitive, chacune avec confirmation.

### `guide.js` — Guide d'intégration

Version lisible de `docs/INTEGRATION.md` dans le Studio (le dossier `docs/` n'est pas servi par FastAPI).
Les exemples utilisent l'adresse réelle du service.

### `viewer-markup.js` — Le HTML du viewer de Créer

Contient seulement le balisage (scène avec dégradé, grille, squelette de chargement, boutons).
`views/viewer.js` y branche ensuite les actions.

## Étape 10.2 — Les vues réutilisables

### `uploader.js` — Choisir et vérifier la photo

```javascript
function validatePhoto(file) {
  if (!acceptedExtensions.has(extension) || (file.type && !acceptedTypes.has(file.type))) {
    return "Choisissez une photo JPG, PNG ou WebP.";
  }
  if (file.size === 0) return "Le fichier photo est vide.";
  if (file.size > maxUploadBytes) return "La limite de taille est de 10 Mo.";
  return null;
}
```

Glisser-déposer ou clic, vignette de la photo (adresse locale : rien n'est envoyé avant le clic),
choix de la catégorie. Ce contrôle est un **confort** ; le serveur revérifie tout (étape 3).

### `progress.js` — Le suivi en 5 étapes

```javascript
const statusCopy = {
  SENDING: ["Envoi de la photo…", "..."],
  PENDING: ["Photo reçue · demande en file", "..."],
  RUNNING: ["Création du modèle 3D en cours", "..."],
  DONE:    ["Modèle prêt", "..."],
  FAILED:  ["La création a échoué", "..."],
};
```

On affiche **seulement les états renvoyés par le serveur**, avec le temps écoulé :
**aucun faux pourcentage**, car on ne sait pas combien de temps l'IA va prendre.

### `viewer.js` — Afficher un GLB

Place le GLB dans `<model-viewer>`, gère le squelette de chargement, la rotation douce à l'ouverture,
le téléchargement, la bascule Vue 3D / Photo source / Comparer et les erreurs de chargement.

### `model-appearance.js` — Corriger l'apparence

```javascript
export const PRODUCT_METALLIC = 0;
export const PRODUCT_ROUGHNESS = 0.8;
export function applyProductAppearance(viewer) { ... }
export function refitCamera(viewer) { ... }
```

Même idée que `glb_finisher.py`, mais côté navigateur, pour les anciens GLB : remplace le matériau
« 100 % métallique » par défaut par un matériau mat. `refitCamera` recadre la caméra quand la zone change de taille
(par exemple en passant au mode Comparer).

### `gallery.js` — Cartes et filtres

```javascript
export function createModelCard(model, options = {}) { ... }    // une carte : aperçu 3D, badge d'origine, date
export function setupGallery(onOpenModel, options = {}) { ... } // la grille + les filtres par catégorie
```

Utilisée par Mes modèles, Exemples et l'Accueil.

### `categories.js` (vue) — Gérer les catégories

Créer, renommer, activer/désactiver et supprimer. Chaque ligne affiche son statut et son nombre de modèles.
Une suppression refusée (409, catégorie utilisée) affiche le message du serveur.

### `confirm-dialog.js` — Fenêtre de confirmation

```javascript
const ok = await confirmDialog({ title: "Supprimer ce modèle ?", message: "...", confirmLabel: "Supprimer", danger: true });
if (!ok) return;
```

Remplace `window.confirm()` par une fenêtre `<dialog>` accessible aux couleurs du Studio.
La **promesse** renvoie `true` (confirmé) ou `false` (annulé, Échap).

### `illustrations.js` — Le dessin du cube

Renvoie un petit dessin SVG (cube 3D) affiché quand une liste est vide.

## À retenir

> Une page = un écran (`render` + `mount`). Une vue = une brique réutilisable. Toutes passent par
> `api.js`, et l'interface n'affiche **que des données réelles** (aucun chiffre ni pourcentage inventé).
