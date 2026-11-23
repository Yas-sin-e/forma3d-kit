/*
 * Rôle : résout les URL hash, protège les pages par la connexion, charge une page à la fois
 * et maintient la navigation accessible (lien actif, titre, focus).
 * Exécution : main.js lance startRouter() au chargement de la coque HTML.
 * Refonte : routes #/login et #/accueil, redirection vers #/login sans session,
 * menu « Administration » (Catégories, Clés API, Guide), paramètres ?query et ancres #section.
 */
// Importe l'état de connexion et la mémorisation de la page demandée.
import { isAuthenticated, rememberNextRoute } from "./auth.js?v=20261117-r2";
// Importe chaque page comme un objet (render, mount, title...).
import * as loginPage from "./pages/login.js?v=20261117-r2";
// Page d'accueil.
import * as dashboardPage from "./pages/dashboard.js?v=20261117-r2";
// Page Créer.
import * as createPage from "./pages/create.js?v=20261117-r2";
// Page Mes modèles.
import * as modelsPage from "./pages/models.js?v=20261117-r2";
// Fiche d'un modèle.
import * as modelDetailPage from "./pages/model-detail.js?v=20261117-r2";
// Page Catégories.
import * as categoriesPage from "./pages/categories.js?v=20261117-r2";
// Page Exemples.
import * as examplesPage from "./pages/examples.js?v=20261117-r2";
// Page Clés API.
import * as apiKeysPage from "./pages/api-keys.js?v=20261117-r2";
// Page Guide.
import * as guidePage from "./pages/guide.js?v=20261117-r2";

// document.querySelector : trouve un élément de la page avec un sélecteur CSS (« #app » = id app).
// #app est le point de montage : le contenu de chaque page y est inséré.
const app = document.querySelector("#app");
// Menu principal.
const nav = document.querySelector("#main-nav");
// Bouton du menu mobile.
const menuToggle = document.querySelector("#menu-toggle");
// Menu déroulant Administration.
const adminGroup = document.querySelector("#admin-nav-group");
// Table « clé de route -> module de page ».
const pageModules = {
  // Connexion.
  login: loginPage,
  // Accueil.
  dashboard: dashboardPage,
  // Créer.
  create: createPage,
  // Mes modèles.
  models: modelsPage,
  // Fiche d'un modèle.
  detail: modelDetailPage,
  // Catégories.
  categories: categoriesPage,
  // Exemples.
  examples: examplesPage,
  // Clés API.
  apiKeys: apiKeysPage,
  // Guide.
  guide: guidePage,
};
// Entrées de menu rangées sous « Administration ».
const adminNavKeys = new Set(["categories", "api-keys", "guide"]);
// Expression régulière d'un UUID.
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
// Conteneur de la page Créer, gardé en mémoire.
let createContainer = null;
// Conteneur de la page affichée.
let activeContainer = null;
// Fonction de nettoyage de la page affichée.
let activeCleanup = null;
// Identité de la page affichée.
let activePath = "";

/* Exemple : "#/modeles?import=1" → chemin "/modeles", query import=1 ; "#/cles-api#integration-guide" → ancre. */
// Analyse l'adresse après le « # » et renvoie la page à afficher (clé, entrée de menu, identifiant, paramètres).
// Équivalent de la table Routes d'Angular, écrite à la main.
function parseRoute(hash) {
  // Retire le « # » du début.
  const withoutHash = hash.replace(/^#/, "");
  // Sépare l'ancre éventuelle (deuxième « # »).
  const [beforeAnchor, anchor = ""] = withoutHash.split("#");
  // Sépare les paramètres après « ? ».
  const [rawPath, rawQuery = ""] = beforeAnchor.split("?");
  // Chemin, ou l'accueil par défaut.
  const raw = rawPath || "/accueil";
  // Paramètres sous forme d'objet lisible.
  const query = new URLSearchParams(rawQuery);
  // Morceaux du chemin, sans les vides.
  const parts = raw.split("/").filter(Boolean);
  // Informations communes à toutes les routes.
  const base = { query, anchor, fullPath: withoutHash || "/accueil" };
  // Anciennes adresses redirigées vers les nouvelles.
  const legacyRoute = { studio: "#/creer", gallery: "#/exemples", "category-management": "#/categories" };
  // Ancienne adresse : on analyse la nouvelle.
  if (parts.length === 1 && legacyRoute[parts[0]]) return parseRoute(legacyRoute[parts[0]]);
  // Accueil.
  if (parts.length === 0 || (parts.length === 1 && parts[0] === "accueil")) return { ...base, key: "dashboard", navKey: "dashboard", path: "/accueil" };
  // Connexion (seule page publique).
  if (parts.length === 1 && parts[0] === "login") return { ...base, key: "login", navKey: null, path: "/login", public: true };
  // Créer.
  if (parts.length === 1 && parts[0] === "creer") return { ...base, key: "create", navKey: "create", path: "/creer" };
  // Mes modèles.
  if (parts.length === 1 && parts[0] === "modeles") return { ...base, key: "models", navKey: "models", path: "/modeles" };
  // Fiche d'un modèle (#/modeles/<id>)...
  if (parts.length === 2 && parts[0] === "modeles") {
    // ...essaie...
    try {
      // ...de décoder l'identifiant...
      const id = decodeURIComponent(parts[1]);
      // ...UUID = modèle enregistré, sinon exemple (pour le lien actif du menu).
      return { ...base, key: "detail", navKey: generationIdPattern.test(id) ? "models" : "examples", path: raw, id };
    // Identifiant mal encodé...
    } catch {
      // ...page introuvable.
      return { ...base, key: "notFound", navKey: null, path: raw };
    }
  }
  // Catégories.
  if (parts.length === 1 && parts[0] === "categories") return { ...base, key: "categories", navKey: "categories", path: "/categories" };
  // Exemples.
  if (parts.length === 1 && parts[0] === "exemples") return { ...base, key: "examples", navKey: "examples", path: "/exemples" };
  // Guide.
  if (parts.length === 1 && parts[0] === "guide") return { ...base, key: "guide", navKey: "guide", path: "/guide" };
  // Clés API.
  if (parts.length === 1 && parts[0] === "cles-api") return { ...base, key: "apiKeys", navKey: "api-keys", path: "/cles-api" };
  // Toute autre adresse : page introuvable.
  return { ...base, key: "notFound", navKey: null, path: raw };
}

// Marque le lien actif du menu (aria-current) et referme le menu.
function updateNavigation(navKey) {
  // Pour chaque lien du menu...
  for (const link of nav.querySelectorAll("a[data-nav]")) {
    // ...lien de la page actuelle : marqué « page en cours »...
    if (link.dataset.nav === navKey) link.setAttribute("aria-current", "page");
    // ...sinon marque retirée.
    else link.removeAttribute("aria-current");
  }
  // Met en évidence « Administration » si la page en fait partie.
  adminGroup.dataset.active = adminNavKeys.has(navKey) ? "true" : "false";
  // Referme le menu.
  closeMenu();
}

// Referme le menu mobile et le sous-menu Administration.
function closeMenu() {
  // Bouton marqué comme replié.
  menuToggle.setAttribute("aria-expanded", "false");
  // Texte lu par les lecteurs d'écran.
  menuToggle.setAttribute("aria-label", "Ouvrir le menu");
  // Retire la classe qui ouvre le menu mobile.
  nav.classList.remove("is-open");
  // Referme le sous-menu Administration.
  adminGroup.open = false;
}

// Retire la page affichée et appelle sa fonction de nettoyage (arrêt des minuteurs).
// Exception : la page Créer est seulement cachée, pour ne pas perdre une génération en cours.
function removeActivePage() {
  // Aucune page affichée : rien à faire.
  if (!activeContainer) return;
  // Cache la page.
  activeContainer.hidden = true;
  // Si ce n'est pas la page Créer...
  if (activePath !== "/creer") {
    // ...appelle sa fonction de nettoyage...
    if (typeof activeCleanup === "function") activeCleanup();
    // ...et la retire du document.
    activeContainer.remove();
  }
  // Plus de page active.
  activeContainer = null;
  // Plus de nettoyage en attente.
  activeCleanup = null;
}

// Fabrique la page « Cette page n'existe pas » pour une adresse inconnue.
function makeNotFoundPage() {
  // Renvoie un objet page simple...
  return {
    // ...titre de l'onglet...
    title: "Page introuvable",
    // ...contenu HTML.
    html: `<section class="page-shell"><p class="eyebrow">Navigation</p><h1 class="page-title" tabindex="-1">Cette page n’existe pas</h1><p class="page-lead">Vérifiez l’adresse ou retournez à l’accueil du Studio.</p><p style="margin-top:24px"><a class="button button-primary" href="#/accueil">Retour à l’accueil</a></p></section>`,
  };
}

// Cœur du routeur : choisit la page selon l'adresse, protège par la connexion, insère le HTML (render)
// puis branche les écouteurs (mount). Équivalent du RouterOutlet + garde CanActivate d'Angular.
function renderRoute() {
  // Pas d'adresse après « # »...
  if (!window.location.hash || window.location.hash === "#/" || window.location.hash === "#") {
    // ...on remplace l'adresse par l'accueil (sans ajouter d'entrée à l'historique)...
    window.location.replace(`${window.location.pathname}${window.location.search}#/accueil`);
    // ...et on s'arrête : le changement d'adresse relancera le routeur.
    return;
  }
  // Analyse l'adresse.
  const route = parseRoute(window.location.hash);
  // État de connexion.
  const authenticated = isAuthenticated();
  // Met à jour l'attribut data-auth du <body>.
  document.body.dataset.auth = authenticated ? "member" : "guest";

  // Protection : sans session, toute page renvoie vers la connexion (la page demandée est mémorisée).
  // Non connectée et page privée...
  if (!authenticated && !route.public) {
    // ...mémorise la page...
    rememberNextRoute(window.location.hash);
    // ...va à la connexion...
    window.location.replace(`${window.location.pathname}${window.location.search}#/login`);
    // ...et s'arrête.
    return;
  }
  // Déjà connectée et page de connexion demandée...
  if (authenticated && route.key === "login") {
    // ...va à l'accueil...
    window.location.replace(`${window.location.pathname}${window.location.search}#/accueil`);
    // ...et s'arrête.
    return;
  }

  // La page Créer garde une identité fixe : elle reste en mémoire et removeActivePage() ne la détruit pas.
  // Identité de la page (fixe pour Créer).
  const routeIdentity = route.key === "create" ? "/creer" : `${route.path}?${route.query.toString()}`;
  // Même page déjà affichée...
  if (activePath === routeIdentity && activeContainer) {
    // ...on défile seulement jusqu'à l'ancre...
    scrollToAnchor(route.anchor);
    // ...et on s'arrête.
    return;
  }
  // Retire la page précédente.
  removeActivePage();
  // Met à jour le menu.
  updateNavigation(route.navKey);
  // Après une déconnexion, la page Créer mise en cache est détruite pour ne rien laisser en mémoire d'écran.
  // Page de connexion et page Créer en mémoire...
  if (route.key === "login" && createContainer) {
    // ...on supprime la page Créer...
    createContainer.remove();
    // ...et on l'oublie.
    createContainer = null;
  }

  // Page Créer déjà en mémoire...
  if (route.key === "create" && createContainer) {
    // ...on la réaffiche...
    createContainer.hidden = false;
    // ...elle devient la page active...
    activeContainer = createContainer;
    // ...on mémorise son identité...
    activePath = routeIdentity;
    // ...et on change le titre de l'onglet.
    document.title = `${createPage.title} — Forma3D Studio`;
  // Sinon on construit la page...
  } else {
    // ...module de la page...
    const page = pageModules[route.key];
    // ...ou la page introuvable...
    const view = route.key === "notFound" ? makeNotFoundPage() : page;
    // ...nouveau conteneur <div>...
    const container = document.createElement("div");
    // ...classe CSS commune...
    container.className = "route-page";
    // ...chemin de la route (pour le CSS et les tests)...
    container.dataset.route = route.path;
    // innerHTML : insère le HTML produit par render(). Ce HTML est écrit dans le code (pas de saisie utilisateur) ;
    // les données venant du serveur sont ensuite placées avec textContent.
    // ...insère le HTML de la page...
    container.innerHTML = typeof view.render === "function" ? view.render(route) : view.html;
    // ...ajoute le conteneur dans #app...
    app.append(container);
    // ...il devient la page active...
    activeContainer = container;
    // ...on mémorise son identité...
    activePath = routeIdentity;
    // ...titre calculé ou fixe...
    const title = view.titleFor ? view.titleFor(route) : view.title;
    // ...titre de l'onglet...
    document.title = `${title} — Forma3D Studio`;
    // ...garde la page Créer en mémoire...
    if (route.key === "create") createContainer = container;
    // ...branche ses écouteurs et garde sa fonction de nettoyage.
    if (typeof view.mount === "function") activeCleanup = view.mount(route);
  }

  // Remonte en haut de la page.
  window.scrollTo({ top: 0 });
  // Titre principal de la page.
  const heading = activeContainer.querySelector(".page-title");
  // Place le focus dessus (lecteurs d'écran), sans faire défiler.
  if (heading) heading.focus({ preventScroll: true });
  // Défile jusqu'à l'ancre éventuelle.
  scrollToAnchor(route.anchor);
}

// Fait défiler jusqu'à une section de la page si l'adresse contient une ancre.
function scrollToAnchor(anchor) {
  // Pas d'ancre : rien à faire.
  if (!anchor) return;
  // Élément visé par l'ancre.
  const target = document.getElementById(anchor);
  // Défile en douceur jusqu'à lui, après un court délai (le temps d'afficher la page).
  if (target) window.setTimeout(() => target.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
}

// Démarre le routage : écoute « hashchange » (changement d'adresse après le #) et les clics du menu.
// Le serveur ne sert qu'une page ; c'est ce code qui change le contenu, sans rechargement.
export function startRouter() {
  // Change de page à chaque changement d'adresse.
  window.addEventListener("hashchange", renderRoute);
  // Clic dans le menu...
  nav.addEventListener("click", (event) => {
    // ...sur un lien : on referme le menu.
    if (event.target.closest("a")) closeMenu();
  });
  // Clic sur le bouton du menu mobile...
  menuToggle.addEventListener("click", () => {
    // ...état actuel...
    const expanded = menuToggle.getAttribute("aria-expanded") === "true";
    // ...inverse l'état...
    menuToggle.setAttribute("aria-expanded", expanded ? "false" : "true");
    // ...met à jour le texte lu par les lecteurs d'écran...
    menuToggle.setAttribute("aria-label", expanded ? "Ouvrir le menu" : "Fermer le menu");
    // ...ouvre ou ferme le menu.
    nav.classList.toggle("is-open", !expanded);
  });
  // Ferme le menu Administration au clic extérieur ou avec Échap.
  // Clic n'importe où...
  document.addEventListener("click", (event) => {
    // ...hors du menu Administration ouvert : on le ferme.
    if (adminGroup.open && !adminGroup.contains(event.target)) adminGroup.open = false;
  });
  // Touche du clavier...
  document.addEventListener("keydown", (event) => {
    // ...Échap avec le menu ouvert...
    if (event.key === "Escape" && adminGroup.open) {
      // ...on le ferme...
      adminGroup.open = false;
      // ...et on remet le focus sur son titre.
      adminGroup.querySelector("summary").focus();
    }
  });
  // Affiche la page de l'adresse actuelle.
  renderRoute();
}
