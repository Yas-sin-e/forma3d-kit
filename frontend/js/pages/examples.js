/*
 * Rôle : rassemble les modèles de démonstration fournis par l'API dans une galerie distincte.
 * Exécution : router.js monte cette page sur #/exemples ; un clic ouvre la fiche du modèle.
 */
import { listCategories } from "../api.js";
import { setupGallery } from "../views/gallery.js";

export const title = "Exemples de modèles";
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function render() {
  return `
    <section class="page-shell gallery-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Galerie</p><h1 class="page-title" id="page-title" tabindex="-1">Exemples de modèles</h1><p class="page-lead">Explorez les exemples disponibles et ouvrez leur fiche pour les examiner.</p></div>
      <section class="panel library-panel" aria-label="Exemples de produits en 3D">
        <div class="gallery-heading"><div><h2>Exemples du Studio</h2><p class="gallery-copy">Ces modèles servent à découvrir le viewer et les possibilités du service.</p></div><span class="gallery-count" id="gallery-count" aria-live="polite">Chargement…</span></div>
        <div class="filter-list" id="gallery-filters" role="group" aria-label="Filtrer les exemples par catégorie"></div>
        <div class="gallery-grid" id="gallery-grid" aria-live="polite"></div>
        <p class="gallery-message" id="gallery-message" role="status" hidden></p>
      </section>
    </section>`;
}

export function mount() {
  const gallery = setupGallery(
    (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; },
    {
      filter: (model) => !generationIdPattern.test(model.id),
      emptyMessage: "Aucun exemple n’est disponible pour le moment.",
      noMatchMessage: "Aucun exemple dans cette catégorie.",
      sourceLabel: () => "Exemple du Studio",
    },
  );
  void listCategories(true).then((response) => gallery.setCategories(response.items ?? [])).catch(() => {});
}
