/*
 * Rôle : expose la gestion des catégories sur sa propre page (menu Administration).
 * Exécution : router.js monte les actions CRUD sur #/categories.
 * Refonte : compteur de modèles enregistrés par catégorie, confirmations par fenêtre modale.
 */
// Importe le chargement de la galerie (pour compter les modèles).
import { listGalleryModels } from "../api.js?v=20261117-r2";
// Importe le test « modèle enregistré » (UUID).
import { isSavedModel } from "../format.js?v=20261117-r2";
// Importe la vue de gestion des catégories.
import { setupCategoryManager } from "../views/categories.js?v=20261117-r2";

// Titre de l'onglet (lu par router.js).
export const title = "Catégories";

// Retourne le HTML de la page Catégories.
export function render() {
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - l'introduction de la page (sur-titre, titre H1 focalisable, phrase d'accroche) ;
  // - le panneau « Vos catégories » avec son compteur (annoncé aux lecteurs d'écran) ;
  // - le formulaire d'ajout : champ du nom, champ caché du slug, bouton « Ajouter » ;
  // - la zone des messages et la liste des catégories, remplies par views/categories.js.
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
  // Charge la galerie.
  const response = await listGalleryModels();
  // Table « slug -> nombre de modèles ».
  const counts = new Map();
  // Pour chaque modèle reçu...
  for (const model of response.items ?? []) {
    // ...ignore les exemples...
    if (!isSavedModel(model)) continue;
    // ...ajoute 1 au compteur de sa catégorie.
    counts.set(model.category, (counts.get(model.category) ?? 0) + 1);
  }
  // Renvoie la table.
  return counts;
}

// Branche l'écran de gestion avec le nombre de modèles par catégorie.
export function mount() {
  // Branche la gestion ; aucune action en plus après un changement, compteurs fournis.
  setupCategoryManager(() => Promise.resolve(), { loadCounts: loadCategoryCounts });
}
