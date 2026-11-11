/*
 * Rôle : expose la gestion des catégories sur sa propre page (menu Administration).
 * Exécution : router.js monte les actions CRUD sur #/categories.
 * Refonte : compteur de modèles enregistrés par catégorie, confirmations par fenêtre modale.
 */
import { listGalleryModels } from "../api.js?v=20261112-c4";
import { isSavedModel } from "../format.js?v=20261112-c4";
import { setupCategoryManager } from "../views/categories.js?v=20261112-c4";

export const title = "Catégories";

export function render() {
  return `
    <section class="page-shell" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Administration</p><h1 class="page-title" id="page-title" tabindex="-1">Catégories</h1><p class="page-lead">Organisez vos produits pour les retrouver et les filtrer plus facilement.</p></div>
      <section class="category-management panel" aria-labelledby="category-management-title">
        <div class="gallery-heading"><div><h2 id="category-management-title">Vos catégories</h2><p class="gallery-copy">Une catégorie utilisée ne peut pas être supprimée : désactivez-la, ses modèles restent consultables.</p></div><span class="gallery-count" id="category-count" aria-live="polite">Chargement…</span></div>
        <form class="category-create-form" id="category-create-form">
          <label><span>Nouvelle catégorie</span><input id="new-category-label" name="label" maxlength="100" placeholder="Ex. Lampes" required></label>
          <input id="new-category-slug" name="slug" type="hidden">
          <button class="button button-primary" type="submit">Ajouter la catégorie</button>
        </form>
        <p class="category-feedback" id="category-feedback" role="status" aria-live="polite" hidden></p>
        <div class="category-list" id="category-list" aria-live="polite"></div>
      </section>
    </section>`;
}

/* Compte les modèles enregistrés (UUID) par catégorie à partir de la galerie existante. */
async function loadCategoryCounts() {
  const response = await listGalleryModels();
  const counts = new Map();
  for (const model of response.items ?? []) {
    if (!isSavedModel(model)) continue;
    counts.set(model.category, (counts.get(model.category) ?? 0) + 1);
  }
  return counts;
}

export function mount() {
  setupCategoryManager(() => Promise.resolve(), { loadCounts: loadCategoryCounts });
}
