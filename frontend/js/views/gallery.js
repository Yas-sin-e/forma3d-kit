/*
 * Rôle : affiche et filtre les cinq GLB de démonstration réellement disponibles.
 * Exécution : main.js charge les entrées du backend et cette vue ouvre le modèle choisi.
 */
import { listGalleryModels } from "../api.js";
import { appState } from "../state.js";

const categoryLabels = {
  chair: "Chaise",
  stool: "Tabouret",
  "side-table": "Table d’appoint",
};

function formatMegabytes(bytes) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(bytes / (1024 * 1024)) + " Mo";
}

export function setupGallery(onOpenModel) {
  const filters = document.querySelector("#gallery-filters");
  const grid = document.querySelector("#gallery-grid");
  const count = document.querySelector("#gallery-count");
  const message = document.querySelector("#gallery-message");
  let models = [];

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
    miniViewer.setAttribute("shadow-intensity", "0.65");
    miniViewer.setAttribute("camera-orbit", "0deg 75deg 100%");
    preview.append(miniViewer);

    const content = document.createElement("div");
    content.className = "model-card-content";

    const heading = document.createElement("h3");
    heading.textContent = model.name;

    const category = document.createElement("p");
    category.className = "model-card-category";
    category.textContent = categoryLabels[model.category] ?? "Mobilier";

    const source = document.createElement("span");
    source.className = "source-badge";
    source.textContent = model.source === "generated_by_app"
      ? "Généré par l’application"
      : "Importé manuellement";

    const size = document.createElement("p");
    size.className = "model-card-size";
    size.textContent = "GLB · " + formatMegabytes(model.size_bytes);

    const openButton = document.createElement("button");
    openButton.className = "button button-secondary model-card-open";
    openButton.type = "button";
    openButton.textContent = "Ouvrir dans le viewer";
    openButton.addEventListener("click", () => onOpenModel(model));

    content.append(heading, category, source, size, openButton);
    article.append(preview, content);
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
