/*
 * Rôle : résout les URL hash, charge une page à la fois et maintient la navigation accessible.
 * Exécution : main.js lance startRouter() au chargement de la coque HTML.
 */
import * as createPage from "./pages/create.js?v=20261111-5b";
import * as modelsPage from "./pages/models.js?v=20261111-5b";
import * as modelDetailPage from "./pages/model-detail.js?v=20261111-5b";
import * as categoriesPage from "./pages/categories.js?v=20261111-5b";
import * as examplesPage from "./pages/examples.js?v=20261111-5b";
import * as apiKeysPage from "./pages/api-keys.js?v=20261111-5b";

const app = document.querySelector("#app");
const nav = document.querySelector("#main-nav");
const menuToggle = document.querySelector("#menu-toggle");
const pageModules = { create: createPage, models: modelsPage, detail: modelDetailPage, categories: categoriesPage, examples: examplesPage, apiKeys: apiKeysPage };
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
let createContainer = null;
let activeContainer = null;
let activeCleanup = null;
let activePath = "";

function parseRoute(hash) {
  const raw = hash.replace(/^#/, "") || "/creer";
  const parts = raw.split("/").filter(Boolean);
  const legacyRoute = { studio: "#/creer", gallery: "#/exemples", "category-management": "#/categories" };
  if (parts.length === 1 && legacyRoute[parts[0]]) return parseRoute(legacyRoute[parts[0]]);
  if (parts.length === 1 && parts[0] === "creer") return { key: "create", navKey: "create", path: "/creer" };
  if (parts.length === 1 && parts[0] === "modeles") return { key: "models", navKey: "models", path: "/modeles" };
  if (parts.length === 2 && parts[0] === "modeles") {
    try {
      const id = decodeURIComponent(parts[1]);
      return { key: "detail", navKey: generationIdPattern.test(id) ? "models" : "examples", path: raw, id };
    } catch {
      return { key: "notFound", navKey: null, path: raw };
    }
  }
  if (parts.length === 1 && parts[0] === "categories") return { key: "categories", navKey: "categories", path: "/categories" };
  if (parts.length === 1 && parts[0] === "exemples") return { key: "examples", navKey: "examples", path: "/exemples" };
  if (parts.length === 1 && parts[0] === "cles-api") return { key: "apiKeys", navKey: "api-keys", path: "/cles-api" };
  return { key: "notFound", navKey: null, path: raw };
}

function updateNavigation(navKey) {
  for (const link of nav.querySelectorAll("a[data-nav]")) {
    if (link.dataset.nav === navKey) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  closeMenu();
}

function closeMenu() {
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "Ouvrir le menu");
  nav.classList.remove("is-open");
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
    html: `<section class="page-shell"><p class="eyebrow">Navigation</p><h1 class="page-title" tabindex="-1">Cette page n’existe pas</h1><p class="page-lead">Vérifiez l’adresse ou retournez à la création de modèle.</p><a class="button button-primary" href="#/creer">Aller à Créer</a></section>`,
  };
}

function renderRoute() {
  const route = parseRoute(window.location.hash);
  if (!window.location.hash) {
    window.location.replace(`${window.location.pathname}${window.location.search}#/creer`);
    return;
  }
  if (activePath === route.path && activeContainer) return;
  removeActivePage();
  updateNavigation(route.navKey);

  if (route.key === "create" && createContainer) {
    createContainer.hidden = false;
    activeContainer = createContainer;
    activePath = route.path;
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
    activePath = route.path;
    const title = view.titleFor ? view.titleFor(route) : view.title;
    document.title = `${title} — Forma3D Studio`;
    if (route.key === "create") createContainer = container;
    if (typeof view.mount === "function") activeCleanup = view.mount(route);
  }

  const heading = activeContainer.querySelector(".page-title");
  if (heading) heading.focus({ preventScroll: true });
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
  renderRoute();
}
