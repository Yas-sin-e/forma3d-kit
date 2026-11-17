/*
 * Rôle : rassemble les modèles de démonstration fournis par l'API dans une galerie distincte.
 * Exécution : router.js monte cette page sur #/exemples ; un clic ouvre la fiche du modèle.
 * Refonte : une description courte sous chaque carte, avec la durée réellement mesurée
 * lors des essais de faisabilité (aucune durée n'est inventée).
 */
import { copyExampleModel, listCategories } from "../api.js?v=20261117-r2";
import { setupGallery } from "../views/gallery.js?v=20261117-r2";
import { exampleDescription } from "../format.js?v=20261117-r2";

export const title = "Exemples de modèles";
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Retourne le HTML de la page Exemples (catalogue et panneau d'ajout).
export function render() {
  return `
    <section class="page-shell gallery-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Galerie</p><h1 class="page-title" id="page-title" tabindex="-1">Exemples de modèles</h1><p class="page-lead">Ces modèles ont été réellement générés à partir d’une seule photo pendant les essais. Ouvrez une fiche pour les examiner, ou ajoutez-les à votre bibliothèque.</p></div>
      <section class="panel model-import-panel" id="example-copy-panel" aria-labelledby="copy-example-title" hidden>
        <h2 id="copy-example-title">Ajouter l’exemple à Mes modèles</h2>
        <p id="copy-example-name"></p>
        <form id="copy-example-form">
          <label for="copy-example-category">Catégorie</label><select id="copy-example-category" required></select>
          <div class="form-actions"><button class="button button-primary" type="submit">Ajouter à Mes modèles</button><button class="button button-secondary" id="cancel-copy-example" type="button">Annuler</button></div>
          <p id="copy-example-feedback" role="status" aria-live="polite"></p>
        </form>
      </section>
      <section class="panel library-panel" aria-label="Exemples de produits en 3D">
        <div class="gallery-heading"><div><h2>Exemples du Studio</h2><p class="gallery-copy">Découvrez le viewer et la qualité actuelle du service avant de créer vos propres modèles.</p></div><span class="gallery-count" id="gallery-count" aria-live="polite">Chargement…</span></div>
        <div class="filter-list" id="gallery-filters" role="group" aria-label="Filtrer les exemples par catégorie"></div>
        <div class="gallery-grid" id="gallery-grid" aria-live="polite"></div>
        <p class="gallery-message" id="gallery-message" role="status" hidden></p>
      </section>
    </section>`;
}

// Branche la page Exemples : galerie filtrée, ajout d'un exemple à « Mes modèles » (POST /models/examples/{id}/copy).
export function mount() {
  const panel = document.querySelector("#example-copy-panel");
  const categorySelect = document.querySelector("#copy-example-category");
  const feedback = document.querySelector("#copy-example-feedback");
  let selectedExample = null;
  const gallery = setupGallery(
    (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; },
    {
      filter: (model) => !generationIdPattern.test(model.id),
      emptyMessage: "Aucun exemple n’est disponible pour le moment.",
      noMatchMessage: "Aucun exemple dans cette catégorie.",
      description: exampleDescription,
      actionLabel: "Ajouter à mes modèles",
      onAction(model) {
        selectedExample = model;
        document.querySelector("#copy-example-name").textContent = `Modèle choisi : ${model.name}`;
        feedback.textContent = "";
        panel.hidden = false;
        panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
        categorySelect.value = model.category;
        categorySelect.focus({ preventScroll: true });
      },
    },
  );
  document.querySelector("#cancel-copy-example").addEventListener("click", () => { panel.hidden = true; });
  void listCategories().then((response) => {
    const categories = response.items ?? [];
    gallery.setCategories(categories);
    categorySelect.replaceChildren(new Option("Choisir une catégorie", ""));
    categories.forEach((category) => categorySelect.add(new Option(category.label, category.slug)));
  }).catch(() => { categorySelect.replaceChildren(new Option("Catégories indisponibles", "")); });
  document.querySelector("#copy-example-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selectedExample) return;
    const submit = event.currentTarget.querySelector("button[type=submit]");
    submit.disabled = true;
    feedback.textContent = "Ajout de l’exemple…";
    try {
      const result = await copyExampleModel(selectedExample.id, selectedExample.name, categorySelect.value);
      feedback.replaceChildren(document.createTextNode("Exemple ajouté à Mes modèles. "));
      const libraryLink = document.createElement("a");
      libraryLink.href = `#/modeles/${encodeURIComponent(result.id)}`;
      libraryLink.textContent = "Ouvrir sa fiche";
      feedback.append(libraryLink);
      await gallery.reload();
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      submit.disabled = false;
    }
  });
}
