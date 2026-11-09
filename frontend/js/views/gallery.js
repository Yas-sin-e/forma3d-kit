/*
 * Rôle : affiche une bande de vignettes réelles et filtre les modèles par catégorie.
 * Exécution : main.js charge la galerie et cette vue ouvre le modèle choisi au clic ou au clavier.
 */
import { listGalleryModels } from "../api.js";
import { appState } from "../state.js";

function formatMegabytes(bytes) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(bytes / (1024 * 1024)) + " Mo";
}

export function setupGallery(onOpenModel) {
  const filters = document.querySelector("#gallery-filters");
  const grid = document.querySelector("#gallery-grid");
  const count = document.querySelector("#gallery-count");
  const message = document.querySelector("#gallery-message");
  let models = [];
  let categories = [];

  function createCard(model) {
    const article = document.createElement("article");
    article.className = "model-card";

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
    source.textContent = model.source === "generated_by_app"
      ? "Généré par l’application"
      : "Importé manuellement";

    const size = document.createElement("p");
    size.className = "model-card-size";
    size.textContent = "GLB · " + formatMegabytes(model.size_bytes);

    content.append(heading, category, source, size);
    article.append(preview, content);
    article.setAttribute("role", "button");
    article.tabIndex = 0;
    article.setAttribute("aria-label", "Ouvrir « " + model.name + " » dans le viewer");
    article.addEventListener("click", () => onOpenModel(model));
    article.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      onOpenModel(model);
    });
    return article;
  }

  function render() {
    const visibleModels = appState.selectedGalleryCategory === "all"
      ? models
      : models.filter((model) => model.category === appState.selectedGalleryCategory);
    grid.replaceChildren(...visibleModels.map(createCard));
    count.textContent = models.length + (models.length > 1 ? " modèles réels" : " modèle réel");
    message.hidden = visibleModels.length > 0;
    if (!models.length) {
      message.textContent = "Aucun GLB de faisabilité réel n’est disponible sur ce poste. Aucun modèle fictif n’est affiché.";
    } else if (!visibleModels.length) {
      message.textContent = "Aucun modèle réel dans cette catégorie.";
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
