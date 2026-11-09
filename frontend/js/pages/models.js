/*
 * Rôle : affiche uniquement les modèles que le vendeur a créés avec le Studio.
 * Exécution : router.js monte la grille sur #/modeles et la remplit depuis l'API existante.
 */
import { listCategories } from "../api.js";
import { setupGallery } from "../views/gallery.js";

export const title = "Mes modèles";
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function render() {
  return `
    <section class="page-shell gallery-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Votre catalogue</p><h1 class="page-title" id="page-title" tabindex="-1">Mes modèles</h1><p class="page-lead">Retrouvez ici les modèles créés à partir de vos photos.</p></div>
      <section class="panel library-panel" aria-label="Vos modèles 3D">
        <div class="gallery-heading"><div><h2>Modèles enregistrés</h2><p class="gallery-copy">Choisissez une catégorie pour filtrer votre collection.</p></div><span class="gallery-count" id="gallery-count" aria-live="polite">Chargement…</span></div>
        <div class="filter-list" id="gallery-filters" role="group" aria-label="Filtrer vos modèles par catégorie"></div>
        <div class="gallery-grid" id="gallery-grid" aria-live="polite"></div>
        <p class="gallery-message" id="gallery-message" role="status" hidden></p>
      </section>
    </section>`;
}

export function mount() {
  const gallery = setupGallery(
    (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; },
    {
      filter: (model) => generationIdPattern.test(model.id),
      emptyMessage: "Vous n’avez pas encore de modèle. Créez-en un à partir d’une photo.",
      noMatchMessage: "Aucun modèle dans cette catégorie.",
      sourceLabel: () => "Créé avec Forma3D",
    },
  );
  void listCategories(true).then((response) => gallery.setCategories(response.items ?? [])).catch(() => {});
}
