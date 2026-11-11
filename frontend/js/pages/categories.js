/*
 * Rôle : expose la gestion des catégories sur sa propre page de navigation.
 * Exécution : router.js monte les actions CRUD sur #/categories.
 */
import { setupCategoryManager } from "../views/categories.js?v=20261111-5a";

export const title = "Catégories";

export function render() {
  return `
    <section class="page-shell" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Organisation</p><h1 class="page-title" id="page-title" tabindex="-1">Catégories</h1><p class="page-lead">Organisez les produits pour les retrouver plus facilement.</p></div>
      <section class="category-management panel" aria-labelledby="category-management-title">
        <div class="gallery-heading"><div><h2 id="category-management-title">Vos catégories</h2><p class="gallery-copy">Les catégories désactivées restent associées aux modèles existants.</p></div><span class="gallery-count" id="category-count" aria-live="polite">Chargement…</span></div>
        <form class="category-create-form" id="category-create-form">
          <label><span>Nom de la catégorie</span><input id="new-category-label" name="label" maxlength="100" placeholder="Ex. Lampes" required></label>
          <input id="new-category-slug" name="slug" type="hidden">
          <button class="button button-primary" type="submit">Ajouter une catégorie</button>
        </form>
        <p class="category-feedback" id="category-feedback" role="status" aria-live="polite" hidden></p>
        <div class="category-list" id="category-list" aria-live="polite"></div>
      </section>
    </section>`;
}

export function mount() {
  setupCategoryManager(() => Promise.resolve());
}
