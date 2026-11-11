/*
 * Rôle : page d'accueil du Studio — présentation, chiffres clés, modèles récents, exemples et raccourcis.
 * Exécution : router.js monte cette page sur #/accueil (page par défaut après connexion).
 * Les chiffres viennent des routes existantes (galerie, clés API, catégories) ; rien n'est inventé.
 */
import { listApiKeys, listCategories, listGalleryModels } from "../api.js?v=20261112-c5";
import { appState } from "../state.js?v=20261112-c5";
import { exampleDescription, isSavedModel } from "../format.js?v=20261112-c5";
import { createModelCard } from "../views/gallery.js?v=20261112-c5";
import { emptyCubeIllustration } from "../views/illustrations.js?v=20261112-c5";
import { watchProductAppearance } from "../views/model-appearance.js?v=20261112-c5";

export const title = "Accueil";

const icons = {
  sparkle: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15Z"/>',
  upload: '<path d="M12 16V4m0 0-4 4m4-4 4 4"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="m10.8 12.2 8.7-8.7M16 7l3 3M18.5 4.5l2 2"/>',
  book: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20"/>',
  cube: '<path d="m12 2 9 5v10l-9 5-9-5V7l9-5Z"/><path d="m3.5 7.3 8.5 4.9 8.5-4.9M12 12.2V22"/>',
  tag: '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9-9-9Z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
};

function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
}

export function render() {
  return `
    <section class="page-shell dashboard-page" aria-labelledby="page-title">
      <header class="hero">
        <div class="hero-copy">
          <span class="hero-status provider-mirror" id="hero-status" data-status="checking"><span class="status-dot" aria-hidden="true"></span><span id="hero-status-label">Serveur 3D : vérification…</span></span>
          <h1 class="page-title hero-title" id="page-title" tabindex="-1">Transformez vos photos en <span class="text-accent">modèles 3D</span></h1>
          <p class="hero-lead">Créez, gérez et intégrez vos modèles 3D de produits pour l’e-commerce.</p>
          <div class="hero-actions">
            <a class="button button-primary button-large" href="#/creer">Créer un modèle 3D <span aria-hidden="true">→</span></a>
            <a class="button button-ghost button-large" href="#/exemples">Voir les exemples</a>
          </div>
        </div>
        <div class="hero-visual" aria-hidden="true">
          <model-viewer id="hero-viewer" class="hero-viewer" auto-rotate rotation-per-second="18deg" auto-rotate-delay="0" interaction-prompt="none" environment-image="neutral" tone-mapping="neutral" exposure="1.1" shadow-intensity="1" shadow-softness="1" camera-orbit="30deg 72deg 105%" disable-zoom disable-pan loading="eager"></model-viewer>
        </div>
      </header>

      <section class="stats-grid" aria-label="Chiffres clés">
        <article class="stat-card"><span class="stat-icon">${icon("cube")}</span><div><p class="stat-value" id="stat-models">—</p><p class="stat-label">Modèles enregistrés</p></div><a class="stat-link" href="#/modeles">Voir</a></article>
        <article class="stat-card"><span class="stat-icon">${icon("key")}</span><div><p class="stat-value" id="stat-keys">—</p><p class="stat-label">Clés API actives</p></div><a class="stat-link" href="#/cles-api">Gérer</a></article>
        <article class="stat-card"><span class="stat-icon">${icon("tag")}</span><div><p class="stat-value" id="stat-categories">—</p><p class="stat-label">Catégories disponibles</p></div><a class="stat-link" href="#/categories">Organiser</a></article>
      </section>

      <section class="dashboard-section" aria-labelledby="recent-title">
        <div class="section-header"><div><h2 id="recent-title">Vos modèles récents</h2><p>Les trois derniers modèles enregistrés dans votre bibliothèque.</p></div><a class="text-link" href="#/modeles">Tout voir →</a></div>
        <div class="card-grid card-grid-3" id="recent-grid" aria-live="polite"></div>
        <div class="empty-panel" id="recent-empty" hidden>
          ${emptyCubeIllustration()}
          <h3>Votre bibliothèque est vide</h3>
          <p>Créez votre premier modèle 3D à partir d’une photo, ou ajoutez un exemple du catalogue.</p>
          <a class="button button-primary" href="#/creer">Créer mon premier modèle</a>
        </div>
      </section>

      <section class="dashboard-section" aria-labelledby="examples-title">
        <div class="section-header"><div><h2 id="examples-title">Exemples du catalogue</h2><p>Modèles réellement générés à partir d’une seule photo pendant les essais.</p></div><a class="text-link" href="#/exemples">Explorer →</a></div>
        <div class="card-strip" id="examples-strip" aria-live="polite"></div>
      </section>

      <section class="dashboard-section" aria-labelledby="shortcuts-title">
        <div class="section-header"><div><h2 id="shortcuts-title">Raccourcis</h2><p>Les actions les plus fréquentes, en un clic.</p></div></div>
        <div class="shortcut-grid">
          <a class="shortcut-card" href="#/creer"><span class="shortcut-icon">${icon("sparkle")}</span><strong>Créer un modèle</strong><span>À partir d’une photo produit</span></a>
          <a class="shortcut-card" href="#/modeles?import=1"><span class="shortcut-icon">${icon("upload")}</span><strong>Importer un GLB</strong><span>Ajouter un fichier existant</span></a>
          <a class="shortcut-card" href="#/cles-api"><span class="shortcut-icon">${icon("key")}</span><strong>Gérer les clés API</strong><span>Créer ou révoquer un accès</span></a>
          <a class="shortcut-card" href="#/guide"><span class="shortcut-icon">${icon("book")}</span><strong>Guide d’intégration</strong><span>API, iframe et widget pas à pas</span></a>
        </div>
      </section>
      <p class="dashboard-error" id="dashboard-error" role="alert" hidden></p>
    </section>`;
}

export function mount() {
  const heroStatus = document.querySelector("#hero-status");
  const heroLabel = document.querySelector("#hero-status-label");
  const heroViewer = document.querySelector("#hero-viewer");
  const recentGrid = document.querySelector("#recent-grid");
  const recentEmpty = document.querySelector("#recent-empty");
  const strip = document.querySelector("#examples-strip");
  const errorBox = document.querySelector("#dashboard-error");
  const openModel = (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; };

  function updateHealth(event) {
    const health = event?.detail ?? appState.providerHealth;
    const online = health?.status === "ONLINE";
    heroStatus.dataset.status = online ? "online" : "offline";
    heroLabel.textContent = online ? "Serveur 3D en ligne · création disponible" : "Serveur 3D hors ligne · exemples disponibles";
  }

  function skeletons(target, total) {
    target.replaceChildren(...Array.from({ length: total }, () => {
      const card = document.createElement("div");
      card.className = "model-card skeleton-card";
      card.setAttribute("aria-hidden", "true");
      return card;
    }));
  }

  async function load() {
    skeletons(recentGrid, 3);
    skeletons(strip, 5);
    const [galleryResult, keysResult, categoriesResult] = await Promise.allSettled([
      listGalleryModels(),
      listApiKeys(),
      listCategories(),
    ]);
    const categories = categoriesResult.status === "fulfilled" ? categoriesResult.value.items ?? [] : [];
    document.querySelector("#stat-categories").textContent = categoriesResult.status === "fulfilled" ? String(categories.length) : "—";
    document.querySelector("#stat-keys").textContent = keysResult.status === "fulfilled"
      ? String((keysResult.value.items ?? []).filter((key) => !key.revoked).length)
      : "—";

    if (galleryResult.status !== "fulfilled") {
      recentGrid.replaceChildren();
      strip.replaceChildren();
      document.querySelector("#stat-models").textContent = "—";
      errorBox.textContent = "Impossible de charger les modèles pour le moment. Vérifiez que le serveur Forma3D est lancé.";
      errorBox.hidden = false;
      return;
    }
    const items = galleryResult.value.items ?? [];
    const saved = items.filter(isSavedModel)
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
    const examples = items.filter((model) => !isSavedModel(model));
    document.querySelector("#stat-models").textContent = String(saved.length);

    recentEmpty.hidden = saved.length > 0;
    recentGrid.hidden = saved.length === 0;
    recentGrid.replaceChildren(...saved.slice(0, 3).map((model) => createModelCard(model, { categories, onOpen: openModel })));

    strip.replaceChildren(...examples.map((model) => createModelCard(model, {
      categories,
      onOpen: openModel,
      description: exampleDescription,
    })));

    // Le visuel du héros montre un vrai modèle du catalogue (le premier exemple disponible).
    const heroModel = examples[0] ?? saved[0];
    watchProductAppearance(heroViewer);
    if (heroModel) heroViewer.src = heroModel.model_url;
  }

  window.addEventListener("forma3d:health", updateHealth);
  updateHealth();
  void load();
  return () => window.removeEventListener("forma3d:health", updateHealth);
}
