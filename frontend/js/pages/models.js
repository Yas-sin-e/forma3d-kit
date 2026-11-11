/*
 * Rôle : affiche uniquement les modèles que le vendeur a créés avec le Studio.
 * Exécution : router.js monte la grille sur #/modeles et la remplit depuis l'API existante.
 */
import { importGlbModel, listCategories } from "../api.js?v=20261111-5b";
import { setupGallery } from "../views/gallery.js?v=20261111-5b";

export const title = "Mes modèles";
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function render() {
  return `
    <section class="page-shell gallery-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Votre catalogue</p><h1 class="page-title" id="page-title" tabindex="-1">Mes modèles</h1><p class="page-lead">Retrouvez ici les modèles créés, importés ou ajoutés depuis les exemples.</p></div>
      <section class="panel library-panel" aria-label="Vos modèles 3D">
        <div class="gallery-heading"><div><h2>Modèles enregistrés</h2><p class="gallery-copy">Cette liste rassemble les modèles terminés associés à votre compte local.</p></div><button class="button button-primary" id="open-model-import" type="button">Importer un modèle (.glb)</button><span class="gallery-count" id="gallery-count" aria-live="polite">Chargement…</span></div>
        <section class="model-import-panel panel" id="model-import-panel" aria-labelledby="import-title" hidden>
          <h2 id="import-title">Importer un modèle GLB</h2>
          <p>Le fichier est vérifié puis enregistré dans Mes modèles. L’import n’est pas une génération à partir d’une photo.</p>
          <form id="model-import-form">
            <label for="import-file">Fichier .glb</label><input id="import-file" name="file" type="file" accept=".glb,model/gltf-binary" required>
            <label for="import-title-field">Titre</label><input id="import-title-field" name="title" type="text" maxlength="100" required>
            <label for="import-category">Catégorie</label><select id="import-category" name="category" required><option value="">Chargement des catégories…</option></select>
            <div class="form-actions"><button class="button button-primary" type="submit">Importer dans Mes modèles</button><button class="button button-secondary" id="cancel-model-import" type="button">Annuler</button></div>
            <p id="model-import-feedback" role="status" aria-live="polite"></p>
          </form>
        </section>
        <div class="library-empty-actions" id="library-empty-actions" hidden><p>Votre liste contient les créations, les imports GLB et les exemples que vous choisissez d’ajouter.</p><div><a class="button button-primary" href="#/creer">Créer à partir d’une photo</a><button class="button button-secondary" id="empty-import-button" type="button">Importer un modèle</button></div></div>
        <div class="filter-list" id="gallery-filters" role="group" aria-label="Filtrer vos modèles par catégorie"></div>
        <div class="gallery-grid" id="gallery-grid" aria-live="polite"></div>
        <p class="gallery-message" id="gallery-message" role="status" hidden></p>
      </section>
    </section>`;
}

export function mount() {
  const panel = document.querySelector("#model-import-panel");
  const form = document.querySelector("#model-import-form");
  const fileInput = document.querySelector("#import-file");
  const titleInput = document.querySelector("#import-title-field");
  const categorySelect = document.querySelector("#import-category");
  const feedback = document.querySelector("#model-import-feedback");
  const openImport = () => { panel.hidden = false; fileInput.focus(); };
  document.querySelector("#open-model-import").addEventListener("click", openImport);
  document.querySelector("#empty-import-button").addEventListener("click", openImport);
  document.querySelector("#cancel-model-import").addEventListener("click", () => { panel.hidden = true; });
  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (file && !titleInput.dataset.edited) {
      titleInput.value = file.name.replace(/\.glb$/i, "").replace(/[._-]+/g, " ").trim();
    }
  });
  titleInput.addEventListener("input", () => { titleInput.dataset.edited = "true"; });
  const gallery = setupGallery(
    (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; },
    {
      filter: (model) => generationIdPattern.test(model.id),
      emptyMessage: "Vous n’avez pas encore de modèle enregistré.",
      noMatchMessage: "Aucun modèle dans cette catégorie.",
    },
  );
  void listCategories().then((response) => {
    const categories = response.items ?? [];
    gallery.setCategories(categories);
    categorySelect.replaceChildren(new Option("Choisir une catégorie", ""));
    categories.forEach((category) => categorySelect.add(new Option(category.label, category.slug)));
  }).catch(() => { categorySelect.replaceChildren(new Option("Catégories indisponibles", "")); });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    feedback.textContent = "Import du modèle…";
    const submit = form.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      const result = await importGlbModel(fileInput.files[0], titleInput.value, categorySelect.value);
      feedback.replaceChildren(document.createTextNode("Modèle importé et enregistré dans Mes modèles. "));
      const detailLink = document.createElement("a");
      detailLink.href = `#/modeles/${encodeURIComponent(result.id)}`;
      detailLink.textContent = "Ouvrir sa fiche";
      feedback.append(detailLink);
      form.reset();
      titleInput.dataset.edited = "";
      await gallery.reload();
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      submit.disabled = false;
    }
  });
}
