/*
 * Rôle : résout les URL hash, protège les pages par la connexion, charge une page à la fois
 * et maintient la navigation accessible (lien actif, titre, focus).
 * Exécution : main.js lance startRouter() au chargement de la coque HTML.
 * Refonte : routes #/login et #/accueil, redirection vers #/login sans session,
 * menu « Administration » (Catégories, Clés API, Guide), paramètres ?query et ancres #section.
 */
import { isAuthenticated, rememberNextRoute } from "./auth.js?v=20261112-c4";
import * as loginPage from "./pages/login.js?v=20261112-c4";
import * as dashboardPage from "./pages/dashboard.js?v=20261112-c4";
import * as createPage from "./pages/create.js?v=20261112-c4";
import * as modelsPage from "./pages/models.js?v=20261112-c4";
import * as modelDetailPage from "./pages/model-detail.js?v=20261112-c4";
import * as categoriesPage from "./pages/categories.js?v=20261112-c4";
import * as examplesPage from "./pages/examples.js?v=20261112-c4";
import * as apiKeysPage from "./pages/api-keys.js?v=20261112-c4";
import * as guidePage from "./pages/guide.js?v=20261112-c4";

const app = document.querySelector("#app");
const nav = document.querySelector("#main-nav");
const menuToggle = document.querySelector("#menu-toggle");
const adminGroup = document.querySelector("#admin-nav-group");
const pageModules = {
  login: loginPage,
  dashboard: dashboardPage,
  create: createPage,
  models: modelsPage,
  detail: modelDetailPage,
  categories: categoriesPage,
  examples: examplesPage,
  apiKeys: apiKeysPage,
  guide: guidePage,
};
const adminNavKeys = new Set(["categories", "api-keys", "guide"]);
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
let createContainer = null;
let activeContainer = null;
let activeCleanup = null;
let activePath = "";

/* Exemple : "#/modeles?import=1" → chemin "/modeles", query import=1 ; "#/cles-api#integration-guide" → ancre. */
function parseRoute(hash) {
  const withoutHash = hash.replace(/^#/, "");
  const [beforeAnchor, anchor = ""] = withoutHash.split("#");
  const [rawPath, rawQuery = ""] = beforeAnchor.split("?");
  const raw = rawPath || "/accueil";
  const query = new URLSearchParams(rawQuery);
  const parts = raw.split("/").filter(Boolean);
  const base = { query, anchor, fullPath: withoutHash || "/accueil" };
  const legacyRoute = { studio: "#/creer", gallery: "#/exemples", "category-management": "#/categories" };
  if (parts.length === 1 && legacyRoute[parts[0]]) return parseRoute(legacyRoute[parts[0]]);
  if (parts.length === 0 || (parts.length === 1 && parts[0] === "accueil")) return { ...base, key: "dashboard", navKey: "dashboard", path: "/accueil" };
  if (parts.length === 1 && parts[0] === "login") return { ...base, key: "login", navKey: null, path: "/login", public: true };
  if (parts.length === 1 && parts[0] === "creer") return { ...base, key: "create", navKey: "create", path: "/creer" };
  if (parts.length === 1 && parts[0] === "modeles") return { ...base, key: "models", navKey: "models", path: "/modeles" };
  if (parts.length === 2 && parts[0] === "modeles") {
    try {
      const id = decodeURIComponent(parts[1]);
      return { ...base, key: "detail", navKey: generationIdPattern.test(id) ? "models" : "examples", path: raw, id };
    } catch {
      return { ...base, key: "notFound", navKey: null, path: raw };
    }
  }
  if (parts.length === 1 && parts[0] === "categories") return { ...base, key: "categories", navKey: "categories", path: "/categories" };
  if (parts.length === 1 && parts[0] === "exemples") return { ...base, key: "examples", navKey: "examples", path: "/exemples" };
  if (parts.length === 1 && parts[0] === "guide") return { ...base, key: "guide", navKey: "guide", path: "/guide" };
  if (parts.length === 1 && parts[0] === "cles-api") return { ...base, key: "apiKeys", navKey: "api-keys", path: "/cles-api" };
  return { ...base, key: "notFound", navKey: null, path: raw };
}

function updateNavigation(navKey) {
  for (const link of nav.querySelectorAll("a[data-nav]")) {
    if (link.dataset.nav === navKey) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  adminGroup.dataset.active = adminNavKeys.has(navKey) ? "true" : "false";
  closeMenu();
}

function closeMenu() {
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "Ouvrir le menu");
  nav.classList.remove("is-open");
  adminGroup.open = false;
}

function removeActivePage() {
  if (!activeContainer) return;
  activeContainer.hidden = true;
  if (activePath !== "/creer") {
    if (typeof activeCleanup === "function") activeCleanup();
    activeContainer.remove();
  }
  activeContainer = null;
  activeCleanup = null;
}

function makeNotFoundPage() {
  return {
    title: "Page introuvable",
    html: `<section class="page-shell"><p class="eyebrow">Navigation</p><h1 class="page-title" tabindex="-1">Cette page n’existe pas</h1><p class="page-lead">Vérifiez l’adresse ou retournez à l’accueil du Studio.</p><p style="margin-top:24px"><a class="button button-primary" href="#/accueil">Retour à l’accueil</a></p></section>`,
  };
}

function renderRoute() {
  if (!window.location.hash || window.location.hash === "#/" || window.location.hash === "#") {
    window.location.replace(`${window.location.pathname}${window.location.search}#/accueil`);
    return;
  }
  const route = parseRoute(window.location.hash);
  const authenticated = isAuthenticated();
  document.body.dataset.auth = authenticated ? "member" : "guest";

  // Protection : sans session, toute page renvoie vers la connexion (la page demandée est mémorisée).
  if (!authenticated && !route.public) {
    rememberNextRoute(window.location.hash);
    window.location.replace(`${window.location.pathname}${window.location.search}#/login`);
    return;
  }
  if (authenticated && route.key === "login") {
    window.location.replace(`${window.location.pathname}${window.location.search}#/accueil`);
    return;
  }

  // La page Créer garde une identité fixe : elle reste en mémoire et removeActivePage() ne la détruit pas.
  const routeIdentity = route.key === "create" ? "/creer" : `${route.path}?${route.query.toString()}`;
  if (activePath === routeIdentity && activeContainer) {
    scrollToAnchor(route.anchor);
    return;
  }
  removeActivePage();
  updateNavigation(route.navKey);
  // Après une déconnexion, la page Créer mise en cache est détruite pour ne rien laisser en mémoire d'écran.
  if (route.key === "login" && createContainer) {
    createContainer.remove();
    createContainer = null;
  }

  if (route.key === "create" && createContainer) {
    createContainer.hidden = false;
    activeContainer = createContainer;
    activePath = routeIdentity;
    document.title = `${createPage.title} — Forma3D Studio`;
  } else {
    const page = pageModules[route.key];
    const view = route.key === "notFound" ? makeNotFoundPage() : page;
    const container = document.createElement("div");
    container.className = "route-page";
    container.dataset.route = route.path;
    container.innerHTML = typeof view.render === "function" ? view.render(route) : view.html;
    app.append(container);
    activeContainer = container;
    activePath = routeIdentity;
    const title = view.titleFor ? view.titleFor(route) : view.title;
    document.title = `${title} — Forma3D Studio`;
    if (route.key === "create") createContainer = container;
    if (typeof view.mount === "function") activeCleanup = view.mount(route);
  }

  window.scrollTo({ top: 0 });
  const heading = activeContainer.querySelector(".page-title");
  if (heading) heading.focus({ preventScroll: true });
  scrollToAnchor(route.anchor);
}

function scrollToAnchor(anchor) {
  if (!anchor) return;
  const target = document.getElementById(anchor);
  if (target) window.setTimeout(() => target.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
}

export function startRouter() {
  window.addEventListener("hashchange", renderRoute);
  nav.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  menuToggle.addEventListener("click", () => {
    const expanded = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", expanded ? "false" : "true");
    menuToggle.setAttribute("aria-label", expanded ? "Ouvrir le menu" : "Fermer le menu");
    nav.classList.toggle("is-open", !expanded);
  });
  // Ferme le menu Administration au clic extérieur ou avec Échap.
  document.addEventListener("click", (event) => {
    if (adminGroup.open && !adminGroup.contains(event.target)) adminGroup.open = false;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && adminGroup.open) {
      adminGroup.open = false;
      adminGroup.querySelector("summary").focus();
    }
  });
  renderRoute();
}
