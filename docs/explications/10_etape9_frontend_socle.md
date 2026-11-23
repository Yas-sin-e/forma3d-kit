# 10. Étape 9 — Le socle du frontend

Fichiers : `frontend/README.md`, `frontend/index.html`, `frontend/favicon.svg`, `frontend/css/theme.css`,
`frontend/css/components.css`, `frontend/js/main.js`, `frontend/js/router.js`, `frontend/js/api.js`,
`frontend/js/auth.js`, `frontend/js/state.js`, `frontend/js/format.js`.

## Le principe : une seule page, plusieurs écrans

Le Studio est une **SPA** (*Single Page Application*) écrite en JavaScript **sans framework**
(ni Angular, ni React). Le navigateur charge `index.html` **une seule fois** ; ensuite, changer
d'écran remplace seulement le contenu de la zone `#app`.

```
index.html  (coque fixe : en-tête, menu, badge serveur 3D, pied de page)
   └── <main id="app">  ← router.js y place la page demandée
```

Les fichiers sont des **modules ES** (`import` / `export`), servis par FastAPI sous `/static/`.
Le `?v=20261117-r2` à la fin des adresses force le navigateur à recharger la nouvelle version après une mise à jour.

## Étape 9.1 — La coque (`index.html`)

```html
<link rel="stylesheet" href="/static/css/theme.css?v=20261117-r2">
<link rel="stylesheet" href="/static/css/components.css?v=20261117-r2">
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.4.0/model-viewer.min.js"></script>
<script type="module" src="/static/js/main.js?v=20261117-r2"></script>
...
<nav class="header-nav" id="main-nav">
  <a class="nav-link" href="#/accueil"  data-nav="dashboard">…</a>
  <a class="nav-link" href="#/creer"    data-nav="create">…</a>
  <a class="nav-link" href="#/modeles"  data-nav="models">…</a>
  <a class="nav-link" href="#/exemples" data-nav="examples">…</a>
  <details class="nav-group" id="admin-nav-group">  <!-- menu Administration -->
     Catégories · Clés API · Guide
  </details>
</nav>
<span class="provider-badge" id="provider-badge" role="status" aria-live="polite">Serveur 3D : vérification…</span>
<button class="logout-button" id="logout-button">…</button>
<main id="app" tabindex="-1"></main>
```

- **`<model-viewer>`** : composant web de Google qui affiche un GLB et permet de le faire tourner, zoomer, déplacer.
- **`#/creer`** : la partie après `#` (le *hash*) change sans recharger la page.
- **`role="status"` + `aria-live`** : un lecteur d'écran annonce le changement d'état du serveur 3D (accessibilité).
- `favicon.svg` : l'icône de l'onglet.

## Étape 9.2 — Les styles (`css/`)

| Fichier | Contenu |
|---|---|
| `theme.css` | Les **variables** : couleurs, espacements, rayons, ombres, animations (`--color-accent`, `--space-4`…) |
| `components.css` | Le style de chaque composant (14 sections : en-tête, boutons, cartes, viewer, formulaires…) |

On change une couleur une fois dans `theme.css`, et tout le Studio suit.

## Étape 9.3 — Le démarrage (`main.js`)

```javascript
await refreshSession();          // 1. demande au serveur : suis-je connectée ? (GET /auth/me)
startRouter();                   // 2. affiche la bonne page
void refreshProviderHealth();    // 3. vérifie le serveur 3D tout de suite...
window.setInterval(() => void refreshProviderHealth(), 30_000);   // ...puis toutes les 30 s
```

```javascript
function publishHealth(status, message) {
  appState.providerHealth = { status, message };
  providerLabel.textContent = online ? "Serveur 3D : en ligne" : "Serveur 3D : hors ligne";
  window.dispatchEvent(new CustomEvent("forma3d:health", { detail: appState.providerHealth }));
}
```

`CustomEvent` = un **message diffusé** à toute la page. La page Créer l'écoute pour désactiver le bouton
d'envoi quand le serveur 3D est hors ligne. Les modules restent indépendants : ils ne s'appellent pas directement.

## Étape 9.4 — La navigation (`router.js`)

### Lire l'adresse

```javascript
function parseRoute(hash) {
  // "#/modeles?import=1"  →  chemin "/modeles", paramètre import=1
  // "#/modeles/3f9c...e1" →  page "detail" avec id = "3f9c...e1"
  if (parts.length === 1 && parts[0] === "creer") return { ...base, key: "create", path: "/creer" };
  if (parts.length === 2 && parts[0] === "modeles") return { ...base, key: "detail", id };
  ...
  return { ...base, key: "notFound" };
}
```

| Adresse | Page |
|---|---|
| `#/login` | Connexion (seule page publique) |
| `#/accueil` | Tableau de bord (par défaut) |
| `#/creer` | Créer un modèle |
| `#/modeles` | Mes modèles |
| `#/modeles/{id}` | Fiche d'un modèle |
| `#/exemples` | Exemples |
| `#/categories`, `#/cles-api`, `#/guide` | Administration |

### Protéger les pages

```javascript
if (!authenticated && !route.public) {
  rememberNextRoute(window.location.hash);          // retient la page demandée...
  window.location.replace("...#/login");            // ...et envoie vers la connexion
  return;
}
```

Après connexion, on revient sur la page demandée. **Attention** : ce garde n'est qu'un confort
d'affichage. La vraie protection est sur le serveur (`require_owner`, étape 7) : sans cookie valide,
toutes les données renvoient 401.

### Monter une page

```javascript
const page = pageModules[route.key];
container.innerHTML = typeof view.render === "function" ? view.render(route) : view.html;
app.append(container);
if (typeof view.mount === "function") activeCleanup = view.mount(route);
```

Chaque fichier de `pages/` respecte le **même contrat** :

| Export | Rôle |
|---|---|
| `title` (ou `titleFor(route)`) | Titre de l'onglet |
| `render(route)` | Renvoie le HTML de la page (texte) |
| `mount(route)` | Branche les boutons et charge les données ; peut renvoyer une fonction de nettoyage |

La page **Créer** est gardée en mémoire quand on la quitte : une génération en cours continue d'être suivie.
Après chaque changement, le titre de la page reçoit le **focus** (utile au clavier et aux lecteurs d'écran).

## Étape 9.5 — Le seul fichier qui parle au serveur (`api.js`)

**Règle du projet** : `fetch` n'apparaît **que** dans `api.js` (un test le vérifie). Les pages
appellent des fonctions claires comme `createGeneration(photo, category)`.

```javascript
export async function createGeneration(photo, category) {
  const body = new FormData();               // formulaire avec fichier
  body.append("file", photo);
  body.append("category", category);
  const response = await fetch("/models", { method: "POST", body, headers: { Accept: "application/json" } });
  return readResponse(response, "Le serveur a refusé cette photo.");
}
```

### Une seule façon de lire les réponses

```javascript
async function readResponse(response, fallbackMessage) {
  if (response.status === 401 && !url.pathname.startsWith("/auth/")) {
    window.dispatchEvent(new CustomEvent("forma3d:unauthorized"));   // session expirée
  }
  if (!response.ok) {
    const error = new Error(typeof data.detail === "string" ? data.detail : fallbackMessage);
    error.status = response.status;
    error.retryAfterSeconds = ...;                                     // lu dans Retry-After
    throw error;
  }
  return data;
}
```

- Une réponse en erreur devient une **exception JavaScript** avec le message du serveur.
- Un **401** prévient `auth.js` que la session a expiré.

`api.js` contient 24 fonctions : modèles, galerie, import, catégories, clés API, session et santé.

## Étape 9.6 — L'état de connexion (`auth.js`)

```javascript
let authenticated = false;

export async function refreshSession() {
  const session = await getSession();              // GET /auth/me
  setAuthenticated(session.authenticated === true);
}

window.addEventListener("forma3d:unauthorized", () => {
  setAuthenticated(false);
  rememberNextRoute(window.location.hash);
  window.sessionStorage.setItem(SESSION_EXPIRED_KEY, "1");   // la page de connexion dira « session expirée »
  window.location.hash = "#/login";
});
```

Le mot de passe n'est **jamais gardé** dans le navigateur. Le cookie est `HttpOnly` : JavaScript ne peut
même pas le lire. Ce module garde seulement un **indicateur** vrai/faux.

## Étape 9.7 — L'état partagé (`state.js`)

```javascript
export const appState = {
  selectedPhoto: null,
  isGenerating: false,
  generationStatus: "IDLE",       // IDLE, SENDING, PENDING, RUNNING, DONE, FAILED
  generationStartedAt: null,
  currentStatusUrl: null,
  pollingTimer: null,              // minuterie de suivi (1,5 s)
  clockTimer: null,                // minuterie du chronomètre (1 s)
  providerHealth: { status: "UNCONFIGURED", message: "..." },
};
```

Un petit objet partagé entre les modules, avec quelques fonctions pour le modifier
(`beginGeneration`, `updateGenerationStatus`, `stopGenerationTimers`).

## Étape 9.8 — Les formats d'affichage (`format.js`)

| Fonction | Exemple |
|---|---|
| `formatRelativeDate(date)` | « il y a 3 min » |
| `formatLongDate(date)` | « 17 novembre 2026 à 14:05 » |
| `formatMegabytes(octets)` | « 2,4 Mo » |
| `formatDuration(secondes)` | « 1 min 25 s » |
| `pluralize(2, "modèle")` | « modèles » |
| `isSavedModel(model)` | Vrai si c'est un modèle enregistré (UUID), faux pour un exemple |
| `exampleDescription(model)` | Description d'un exemple avec sa durée réellement mesurée |

## À retenir

> `main.js` démarre, `router.js` choisit l'écran, `api.js` est la **seule porte vers le serveur**,
> `auth.js` suit la connexion, `state.js` garde l'état. Chaque page suit le contrat `render` + `mount`.
