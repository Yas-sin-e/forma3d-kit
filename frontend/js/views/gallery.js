/*
 * Rôle : affiche une bande de vignettes réelles et filtre les modèles par catégorie.
 * Exécution : main.js charge la galerie et cette vue ouvre le modèle choisi au clic ou au clavier.
 */
import { listGalleryModels } from "../api.js?v=20261111-5a";
import { appState } from "../state.js?v=20261111-5a";

function formatMegabytes(bytes) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(bytes / (1024 * 1024)) + " Mo";
}

export function setupGallery(onOpenModel, options = {}) {
  const filters = document.querySelector("#gallery-filters");
  const grid = document.querySelector("#gallery-grid");
  const count = document.querySelector("#gallery-count");
  const message = document.querySelector("#gallery-message");
  const emptyActions = document.querySelector("#library-empty-actions");
  let models = [];
  let categories = [];
  const includeModel = typeof options.filter === "function" ? options.filter : () => true;

  function createCard(model) {
    const article = document.createElement("article");
    article.className = "model-card";
    const openButton = document.createElement("button");
    openButton.className = "model-card-open";
    openButton.type = "button";
    openButton.setAttribute("aria-label", "Ouvrir « " + model.name + " » dans le viewer");

    const preview = document.createElement("div");
    preview.className = "model-card-preview";
    const miniViewer = document.createElement("model-viewer");
    miniViewer.setAttribute("src", model.model_url);
    miniViewer.setAttribute("alt", "Aperçu 3D : " + model.name);
    miniViewer.setAttribute("loading", "lazy");
    miniViewer.setAttribute("interaction-prompt", "none");
    miniViewer.setAttribute("environment-image", "neutral");
    miniViewer.setAttribute("tone-mapping", "neutral");
    miniViewer.setAttribute("exposure", "1.08");
    miniViewer.setAttribute("shadow-intensity", "0.45");
    miniViewer.setAttribute("shadow-softness", "0.8");
    miniViewer.setAttribute("camera-orbit", "0deg 75deg 100%");
    miniViewer.setAttribute("aria-hidden", "true");
    preview.append(miniViewer);

    const content = document.createElement("div");
    content.className = "model-card-content";

    const heading = document.createElement("h3");
    heading.textContent = model.name;

    const category = document.createElement("p");
    category.className = "model-card-category";
    category.textContent = categories.find((item) => item.slug === model.category)?.label ?? model.category;

    const source = document.createElement("span");
    source.className = "source-badge";
    const size = document.createElement("p");
    size.className = "model-card-size";
    size.textContent = "Modèle 3D · " + formatMegabytes(model.size_bytes);

    content.append(heading, category, source, size);
    const originLabels = {
      generated: "Généré par l’application",
      imported: "Importé",
      example: "Exemple",
    };
    source.textContent = options.sourceLabel?.(model) ?? originLabels[model.origin] ?? "Origine inconnue";
    const created = document.createElement("p");
    created.className = "model-card-date";
    created.textContent = model.created_at
      ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(model.created_at))
      : "Exemple du catalogue";
    content.append(created);
    openButton.append(preview, content);
    openButton.addEventListener("click", () => onOpenModel(model));
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

  function render() {
    const availableModels = models.filter(includeModel);
    const visibleModels = appState.selectedGalleryCategory === "all"
      ? availableModels
      : availableModels.filter((model) => model.category === appState.selectedGalleryCategory);
    grid.replaceChildren(...visibleModels.map(createCard));
    count.textContent = availableModels.length + (availableModels.length > 1 ? " modèles" : " modèle");
    message.hidden = visibleModels.length > 0;
    if (emptyActions) emptyActions.hidden = availableModels.length > 0;
    if (!availableModels.length) {
      message.textContent = options.emptyMessage ?? "Aucun modèle n’est disponible pour le moment.";
    } else if (!visibleModels.length) {
      message.textContent = options.noMatchMessage ?? "Aucun modèle dans cette catégorie.";
    }
  }

  function renderFilters() {
    const allButton = document.createElement("button");
    allButton.className = "filter-chip";
    allButton.type = "button";
    allButton.dataset.category = "all";
    allButton.setAttribute("aria-pressed", appState.selectedGalleryCategory === "all" ? "true" : "false");
    allButton.textContent = "Tous";
    const buttons = categories.map((category) => {
      const button = document.createElement("button");
      button.className = "filter-chip";
      button.type = "button";
      button.dataset.category = category.slug;
      button.setAttribute("aria-pressed", appState.selectedGalleryCategory === category.slug ? "true" : "false");
      button.textContent = category.label + (category.is_active ? "" : " · inactive");
      return button;
    });
    filters.replaceChildren(allButton, ...buttons);
    if (appState.selectedGalleryCategory !== "all" && !categories.some((item) => item.slug === appState.selectedGalleryCategory)) {
      appState.selectedGalleryCategory = "all";
      allButton.setAttribute("aria-pressed", "true");
    }
  }

  filters.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-category]");
    if (!button) return;
    appState.selectedGalleryCategory = button.dataset.category;
    filters.querySelectorAll("button[data-category]").forEach((filter) => {
      filter.setAttribute("aria-pressed", filter === button ? "true" : "false");
    });
    render();
  });

  async function load() {
    count.textContent = "Chargement des modèles…";
    message.hidden = true;
    try {
      const response = await listGalleryModels();
      models = Array.isArray(response.items) ? response.items : [];
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
      renderFilters();
      render();
    },
    selectCategory(category) {
      const button = filters.querySelector(`button[data-category="${category}"]`);
      if (!button) return;
      appState.selectedGalleryCategory = category;
      filters.querySelectorAll("button[data-category]").forEach((filter) => {
        filter.setAttribute("aria-pressed", filter === button ? "true" : "false");
      });
      render();
    },
    async openFirstModel() {
      if (!models.length) await load();
      const model = models[0];
      if (!model) return false;
      onOpenModel(model);
      return true;
    },
  };
}
