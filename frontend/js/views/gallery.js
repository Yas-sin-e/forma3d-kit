/*
 * Rôle : construit les cartes de modèles et la grille filtrable par catégorie (avec compteurs).
 * Exécution : Mes modèles et Exemples appellent setupGallery() ; l'accueil réutilise createModelCard().
 * Refonte : badge d'origine sur l'aperçu, date relative, rotation animée au survol, compteur par filtre.
 */
import { listGalleryModels } from "../api.js?v=20261112-c3";
import { appState } from "../state.js?v=20261112-c3";
import { formatMegabytes, formatRelativeDate } from "../format.js?v=20261112-c3";
import { watchProductAppearance } from "./model-appearance.js?v=20261112-c3";

const originLabels = {
  generated: "Généré",
  imported: "Importé",
  example: "Exemple",
};

/* Crée une carte autonome ; options : categories, onOpen, description, actionLabel, onAction. */
export function createModelCard(model, options = {}) {
  const categories = options.categories ?? [];
  const article = document.createElement("article");
  article.className = "model-card";

  const openButton = document.createElement("button");
  openButton.className = "model-card-open";
  openButton.type = "button";
  openButton.setAttribute("aria-label", "Ouvrir la fiche de « " + model.name + " »");

  const preview = document.createElement("div");
  preview.className = "model-card-preview";
  const miniViewer = document.createElement("model-viewer");
  watchProductAppearance(miniViewer);
  miniViewer.setAttribute("src", model.model_url);
  miniViewer.setAttribute("alt", "Aperçu 3D : " + model.name);
  miniViewer.setAttribute("loading", "lazy");
  miniViewer.setAttribute("interaction-prompt", "none");
  miniViewer.setAttribute("environment-image", "neutral");
  miniViewer.setAttribute("tone-mapping", "neutral");
  miniViewer.setAttribute("exposure", "1.1");
  miniViewer.setAttribute("shadow-intensity", "0.8");
  miniViewer.setAttribute("shadow-softness", "1");
  miniViewer.setAttribute("camera-orbit", "25deg 75deg 105%");
  miniViewer.setAttribute("rotation-per-second", "40deg");
  miniViewer.setAttribute("auto-rotate-delay", "0");
  miniViewer.setAttribute("aria-hidden", "true");
  const badge = document.createElement("span");
  badge.className = "source-badge";
  badge.dataset.origin = model.origin ?? "example";
  badge.textContent = options.sourceLabel?.(model) ?? originLabels[model.origin] ?? "Origine inconnue";
  preview.append(miniViewer, badge);

  const content = document.createElement("div");
  content.className = "model-card-content";
  const heading = document.createElement("h3");
  heading.textContent = model.name;
  const meta = document.createElement("p");
  meta.className = "model-card-meta";
  const categoryLabel = categories.find((item) => item.slug === model.category)?.label ?? model.category;
  const dateLabel = model.created_at ? formatRelativeDate(model.created_at) : "Catalogue";
  meta.textContent = [categoryLabel, dateLabel, formatMegabytes(model.size_bytes)].filter(Boolean).join(" · ");
  content.append(heading, meta);
  if (options.description) {
    const description = document.createElement("p");
    description.className = "model-card-description";
    description.textContent = typeof options.description === "function" ? options.description(model) : options.description;
    content.append(description);
  }

  openButton.append(preview, content);
  openButton.addEventListener("click", () => options.onOpen?.(model));
  // Aperçu animé : la miniature tourne seulement pendant le survol ou le focus clavier.
  const startRotation = () => miniViewer.setAttribute("auto-rotate", "");
  const stopRotation = () => miniViewer.removeAttribute("auto-rotate");
  openButton.addEventListener("pointerenter", startRotation);
  openButton.addEventListener("pointerleave", stopRotation);
  openButton.addEventListener("focus", startRotation);
  openButton.addEventListener("blur", stopRotation);
  article.append(openButton);

  if (typeof options.onAction === "function") {
    const action = document.createElement("button");
    action.type = "button";
    action.className = "button button-secondary model-card-action";
    action.textContent = options.actionLabel ?? "Ajouter à mes modèles";
    action.addEventListener("click", () => options.onAction(model));
    article.append(action);
  }
  return article;
}

export function setupGallery(onOpenModel, options = {}) {
  const filters = document.querySelector("#gallery-filters");
  const grid = document.querySelector("#gallery-grid");
  const count = document.querySelector("#gallery-count");
  const message = document.querySelector("#gallery-message");
  const emptyActions = document.querySelector("#library-empty-actions");
  let models = [];
  let categories = [];
  let loaded = false;
  const includeModel = typeof options.filter === "function" ? options.filter : () => true;

  function availableModels() {
    return models.filter(includeModel);
  }

  function render() {
    // Tant que l'API n'a pas répondu, on garde les cartes squelettes au lieu d'un faux état vide.
    if (!loaded) return;
    const available = availableModels();
    const visibleModels = appState.selectedGalleryCategory === "all"
      ? available
      : available.filter((model) => model.category === appState.selectedGalleryCategory);
    grid.replaceChildren(...visibleModels.map((model) => createModelCard(model, {
      categories,
      onOpen: onOpenModel,
      description: options.description,
      sourceLabel: options.sourceLabel,
      actionLabel: options.actionLabel,
      onAction: options.onAction,
    })));
    count.textContent = available.length + (available.length > 1 ? " modèles" : " modèle");
    grid.hidden = visibleModels.length === 0;
    if (emptyActions) emptyActions.hidden = available.length > 0;
    filters.hidden = available.length === 0;
    message.hidden = visibleModels.length > 0 || (Boolean(emptyActions) && available.length === 0);
    if (!available.length) {
      message.textContent = options.emptyMessage ?? "Aucun modèle n’est disponible pour le moment.";
    } else if (!visibleModels.length) {
      message.textContent = options.noMatchMessage ?? "Aucun modèle dans cette catégorie.";
    }
    renderFilters();
  }

  function makeFilterButton(slug, label, total) {
    const button = document.createElement("button");
    button.className = "filter-chip";
    button.type = "button";
    button.dataset.category = slug;
    button.setAttribute("aria-pressed", appState.selectedGalleryCategory === slug ? "true" : "false");
    const text = document.createElement("span");
    text.textContent = label;
    const counter = document.createElement("span");
    counter.className = "filter-count";
    counter.textContent = String(total);
    counter.setAttribute("aria-label", `${total} modèle${total > 1 ? "s" : ""}`);
    button.append(text, counter);
    return button;
  }

  function renderFilters() {
    const available = availableModels();
    if (appState.selectedGalleryCategory !== "all" && !categories.some((item) => item.slug === appState.selectedGalleryCategory)) {
      appState.selectedGalleryCategory = "all";
    }
    const allButton = makeFilterButton("all", "Tous", available.length);
    const buttons = categories.map((category) => {
      const total = available.filter((model) => model.category === category.slug).length;
      return makeFilterButton(category.slug, category.label + (category.is_active ? "" : " · inactive"), total);
    });
    filters.replaceChildren(allButton, ...buttons);
  }

  filters.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-category]");
    if (!button) return;
    appState.selectedGalleryCategory = button.dataset.category;
    render();
  });

  async function load() {
    count.textContent = "Chargement…";
    message.hidden = true;
    grid.replaceChildren(...Array.from({ length: 3 }, () => {
      const skeleton = document.createElement("div");
      skeleton.className = "model-card skeleton-card";
      skeleton.setAttribute("aria-hidden", "true");
      return skeleton;
    }));
    try {
      const response = await listGalleryModels();
      models = Array.isArray(response.items) ? response.items : [];
      loaded = true;
      render();
    } catch (error) {
      grid.replaceChildren();
      count.textContent = "Galerie indisponible";
      message.textContent = error.message;
      message.hidden = false;
    }
  }

  void load();
  return {
    reload: load,
    setCategories(nextCategories) {
      categories = Array.isArray(nextCategories) ? nextCategories : [];
      render();
    },
    selectCategory(category) {
      appState.selectedGalleryCategory = category;
      render();
    },
  };
}
