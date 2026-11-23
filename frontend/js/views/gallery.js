/*
 * Rôle : construit les cartes de modèles et la grille filtrable par catégorie (avec compteurs).
 * Exécution : Mes modèles et Exemples appellent setupGallery() ; l'accueil réutilise createModelCard().
 * Refonte : badge d'origine sur l'aperçu, date relative, rotation animée au survol, compteur par filtre.
 */
// Importe le chargement de la galerie.
import { listGalleryModels } from "../api.js?v=20261117-r2";
// Importe l'état partagé (catégorie filtrée).
import { appState } from "../state.js?v=20261117-r2";
// Importe la mise en forme de la taille et de la date.
import { formatMegabytes, formatRelativeDate } from "../format.js?v=20261117-r2";
// Importe la correction d'apparence des GLB.
import { watchProductAppearance } from "./model-appearance.js?v=20261117-r2";

// Libellé du badge pour chaque provenance.
const originLabels = {
  // Généré depuis une photo.
  generated: "Généré",
  // Importé.
  imported: "Importé",
  // Exemple du catalogue.
  example: "Exemple",
};

/* Crée une carte autonome ; options : categories, onOpen, description, actionLabel, onAction. */
// Construit la carte d'un modèle avec document.createElement (création d'éléments un par un).
// Le texte est placé avec textContent : un nom de modèle ne peut pas injecter de HTML.
export function createModelCard(model, options = {}) {
  // Catégories connues (liste vide par défaut).
  const categories = options.categories ?? [];
  // Crée la carte.
  const article = document.createElement("article");
  // Sa classe CSS.
  article.className = "model-card";

  // Bouton qui ouvre la fiche (toute la carte est cliquable).
  const openButton = document.createElement("button");
  // Sa classe CSS.
  openButton.className = "model-card-open";
  // Type « button ».
  openButton.type = "button";
  // Nom accessible du bouton.
  openButton.setAttribute("aria-label", "Ouvrir la fiche de « " + model.name + " »");

  // Zone d'aperçu.
  const preview = document.createElement("div");
  // Sa classe CSS.
  preview.className = "model-card-preview";
  // Crée un mini viewer 3D.
  const miniViewer = document.createElement("model-viewer");
  // Branche la correction d'apparence.
  watchProductAppearance(miniViewer);
  // Adresse du GLB.
  miniViewer.setAttribute("src", model.model_url);
  // Texte alternatif.
  miniViewer.setAttribute("alt", "Aperçu 3D : " + model.name);
  // Chargement différé.
  miniViewer.setAttribute("loading", "lazy");
  // Pas d'animation d'invite.
  miniViewer.setAttribute("interaction-prompt", "none");
  // Éclairage neutre.
  miniViewer.setAttribute("environment-image", "neutral");
  // Rendu des couleurs neutre.
  miniViewer.setAttribute("tone-mapping", "neutral");
  // Exposition (luminosité).
  miniViewer.setAttribute("exposure", "1.1");
  // Intensité de l'ombre.
  miniViewer.setAttribute("shadow-intensity", "0.8");
  // Douceur de l'ombre.
  miniViewer.setAttribute("shadow-softness", "1");
  // Angle de caméra initial.
  miniViewer.setAttribute("camera-orbit", "25deg 75deg 105%");
  // Vitesse de rotation.
  miniViewer.setAttribute("rotation-per-second", "40deg");
  // Rotation immédiate quand elle est activée.
  miniViewer.setAttribute("auto-rotate-delay", "0");
  // Ignoré par les lecteurs d'écran (le bouton a déjà un nom).
  miniViewer.setAttribute("aria-hidden", "true");
  // Badge de provenance.
  const badge = document.createElement("span");
  // Sa classe CSS.
  badge.className = "source-badge";
  // data-origin : le CSS choisit la couleur.
  badge.dataset.origin = model.origin ?? "example";
  // Libellé personnalisé, sinon libellé de la table.
  badge.textContent = options.sourceLabel?.(model) ?? originLabels[model.origin] ?? "Origine inconnue";
  // Assemble l'aperçu.
  preview.append(miniViewer, badge);

  // Zone de texte.
  const content = document.createElement("div");
  // Sa classe CSS.
  content.className = "model-card-content";
  // Titre de la carte.
  const heading = document.createElement("h3");
  // Nom du modèle.
  heading.textContent = model.name;
  // Ligne d'informations.
  const meta = document.createElement("p");
  // Sa classe CSS.
  meta.className = "model-card-meta";
  // Libellé de la catégorie (ou son slug).
  const categoryLabel = categories.find((item) => item.slug === model.category)?.label ?? model.category;
  // Date relative, ou « Catalogue » pour un exemple.
  const dateLabel = model.created_at ? formatRelativeDate(model.created_at) : "Catalogue";
  // « Catégorie · date · taille ».
  meta.textContent = [categoryLabel, dateLabel, formatMegabytes(model.size_bytes)].filter(Boolean).join(" · ");
  // Assemble la zone de texte.
  content.append(heading, meta);
  // Si une description est demandée...
  if (options.description) {
    // ...crée un paragraphe...
    const description = document.createElement("p");
    // ...avec sa classe...
    description.className = "model-card-description";
    // ...texte fixe ou calculé par une fonction...
    description.textContent = typeof options.description === "function" ? options.description(model) : options.description;
    // ...et l'ajoute.
    content.append(description);
  }

  // Assemble le bouton.
  openButton.append(preview, content);
  // Clic : ouvre la fiche si une fonction est fournie.
  openButton.addEventListener("click", () => options.onOpen?.(model));
  // Aperçu animé : la miniature tourne seulement pendant le survol ou le focus clavier.
  // Démarre la rotation.
  const startRotation = () => miniViewer.setAttribute("auto-rotate", "");
  // Arrête la rotation.
  const stopRotation = () => miniViewer.removeAttribute("auto-rotate");
  // Souris qui entre : rotation.
  openButton.addEventListener("pointerenter", startRotation);
  // Souris qui sort : arrêt.
  openButton.addEventListener("pointerleave", stopRotation);
  // Focus clavier : rotation.
  openButton.addEventListener("focus", startRotation);
  // Perte du focus : arrêt.
  openButton.addEventListener("blur", stopRotation);
  // Ajoute le bouton à la carte.
  article.append(openButton);

  // Si une action est demandée...
  if (typeof options.onAction === "function") {
    // ...crée un bouton...
    const action = document.createElement("button");
    // ...de type « button »...
    action.type = "button";
    // ...avec son style...
    action.className = "button button-secondary model-card-action";
    // ...son texte...
    action.textContent = options.actionLabel ?? "Ajouter à mes modèles";
    // ...son action au clic...
    action.addEventListener("click", () => options.onAction(model));
    // ...et l'ajoute.
    article.append(action);
  }
  // Renvoie la carte.
  return article;
}

// Branche une galerie : charge les modèles, les filtre par catégorie et affiche les cartes.
// Entrées : onOpenModel (clic sur une carte), options (filtre, messages, action par carte).
export function setupGallery(onOpenModel, options = {}) {
  // Zone des filtres.
  const filters = document.querySelector("#gallery-filters");
  // Grille des cartes.
  const grid = document.querySelector("#gallery-grid");
  // Compteur.
  const count = document.querySelector("#gallery-count");
  // Message d'état.
  const message = document.querySelector("#gallery-message");
  // Actions affichées quand la bibliothèque est vide.
  const emptyActions = document.querySelector("#library-empty-actions");
  // Tous les modèles reçus.
  let models = [];
  // Catégories connues.
  let categories = [];
  // Vrai après la première réponse.
  let loaded = false;
  // Filtre fourni par la page, sinon tout est accepté.
  const includeModel = typeof options.filter === "function" ? options.filter : () => true;

  // Renvoie les modèles retenus par le filtre de la page (Mes modèles ou Exemples).
  function availableModels() {
    // Applique le filtre.
    return models.filter(includeModel);
  }

  // Réaffiche les cartes de la catégorie choisie, le compteur et les messages d'état vide.
  function render() {
    // Tant que l'API n'a pas répondu, on garde les cartes squelettes au lieu d'un faux état vide.
    if (!loaded) return;
    // Modèles retenus.
    const available = availableModels();
    // Catégorie « Tous »...
    const visibleModels = appState.selectedGalleryCategory === "all"
      // ...tous les modèles...
      ? available
      // ...sinon seulement ceux de la catégorie choisie.
      : available.filter((model) => model.category === appState.selectedGalleryCategory);
    // Remplace les cartes...
    grid.replaceChildren(...visibleModels.map((model) => createModelCard(model, {
      // ...catégories...
      categories,
      // ...ouverture de la fiche...
      onOpen: onOpenModel,
      // ...description...
      description: options.description,
      // ...libellé de provenance...
      sourceLabel: options.sourceLabel,
      // ...texte du bouton d'action...
      actionLabel: options.actionLabel,
      // ...action.
      onAction: options.onAction,
    })));
    // « 1 modèle » ou « N modèles ».
    count.textContent = available.length + (available.length > 1 ? " modèles" : " modèle");
    // Grille masquée si aucune carte.
    grid.hidden = visibleModels.length === 0;
    // Actions de bibliothèque vide visibles seulement si vide.
    if (emptyActions) emptyActions.hidden = available.length > 0;
    // Filtres masqués s'il n'y a aucun modèle.
    filters.hidden = available.length === 0;
    // Message masqué s'il y a des cartes ou si les actions de bibliothèque vide sont affichées.
    message.hidden = visibleModels.length > 0 || (Boolean(emptyActions) && available.length === 0);
    // Aucun modèle...
    if (!available.length) {
      // ...message « vide ».
      message.textContent = options.emptyMessage ?? "Aucun modèle n’est disponible pour le moment.";
    // Aucun dans cette catégorie...
    } else if (!visibleModels.length) {
      // ...message « aucun résultat ».
      message.textContent = options.noMatchMessage ?? "Aucun modèle dans cette catégorie.";
    }
    // Met à jour les filtres.
    renderFilters();
  }

  // Fabrique un bouton de filtre avec son compteur de modèles.
  function makeFilterButton(slug, label, total) {
    // Crée le bouton.
    const button = document.createElement("button");
    // Sa classe CSS.
    button.className = "filter-chip";
    // Type « button ».
    button.type = "button";
    // Slug de la catégorie.
    button.dataset.category = slug;
    // aria-pressed : indique le filtre choisi.
    button.setAttribute("aria-pressed", appState.selectedGalleryCategory === slug ? "true" : "false");
    // Texte du filtre.
    const text = document.createElement("span");
    // Libellé.
    text.textContent = label;
    // Compteur.
    const counter = document.createElement("span");
    // Sa classe CSS.
    counter.className = "filter-count";
    // Nombre de modèles.
    counter.textContent = String(total);
    // Texte lu par les lecteurs d'écran.
    counter.setAttribute("aria-label", `${total} modèle${total > 1 ? "s" : ""}`);
    // Assemble le bouton.
    button.append(text, counter);
    // Renvoie le bouton.
    return button;
  }

  // Reconstruit la ligne de filtres : « Tous » puis une entrée par catégorie.
  function renderFilters() {
    // Modèles retenus.
    const available = availableModels();
    // Catégorie choisie qui n'existe plus...
    if (appState.selectedGalleryCategory !== "all" && !categories.some((item) => item.slug === appState.selectedGalleryCategory)) {
      // ...retour à « Tous ».
      appState.selectedGalleryCategory = "all";
    }
    // Bouton « Tous ».
    const allButton = makeFilterButton("all", "Tous", available.length);
    // Un bouton par catégorie...
    const buttons = categories.map((category) => {
      // ...avec son nombre de modèles...
      const total = available.filter((model) => model.category === category.slug).length;
      // ...et la mention « inactive » si besoin.
      return makeFilterButton(category.slug, category.label + (category.is_active ? "" : " · inactive"), total);
    });
    // Remplace les filtres.
    filters.replaceChildren(allButton, ...buttons);
  }

  // Clic dans les filtres...
  filters.addEventListener("click", (event) => {
    // ...bouton visé...
    const button = event.target.closest("button[data-category]");
    // ...pas un filtre : rien à faire.
    if (!button) return;
    // Mémorise la catégorie choisie.
    appState.selectedGalleryCategory = button.dataset.category;
    // Réaffiche.
    render();
  });

  // Charge les modèles (GET /models/gallery) ; affiche des cartes « squelettes » pendant l'attente.
  async function load() {
    // Message d'attente.
    count.textContent = "Chargement…";
    // Masque le message d'état.
    message.hidden = true;
    // Affiche trois cartes vides animées...
    grid.replaceChildren(...Array.from({ length: 3 }, () => {
      // ...crée un bloc...
      const skeleton = document.createElement("div");
      // ...avec le style « squelette »...
      skeleton.className = "model-card skeleton-card";
      // ...ignoré par les lecteurs d'écran...
      skeleton.setAttribute("aria-hidden", "true");
      // ...et le renvoie.
      return skeleton;
    }));
    // Essaie...
    try {
      // ...de charger la galerie...
      const response = await listGalleryModels();
      // ...garde la liste...
      models = Array.isArray(response.items) ? response.items : [];
      // ...marque comme chargée...
      loaded = true;
      // ...et affiche.
      render();
    // Erreur...
    } catch (error) {
      // ...vide la grille...
      grid.replaceChildren();
      // ...compteur d'indisponibilité...
      count.textContent = "Galerie indisponible";
      // ...message d'erreur...
      message.textContent = error.message;
      // ...affiché.
      message.hidden = false;
    }
  }

  // Charge au démarrage.
  void load();
  // Renvoie les fonctions utilisables par la page...
  return {
    // ...recharger...
    reload: load,
    // ...définir les catégories :
    setCategories(nextCategories) {
      // garde la liste (vide si invalide)...
      categories = Array.isArray(nextCategories) ? nextCategories : [];
      // ...et réaffiche.
      render();
    },
    // Choisir une catégorie :
    selectCategory(category) {
      // la mémorise...
      appState.selectedGalleryCategory = category;
      // ...et réaffiche.
      render();
    },
  };
}
