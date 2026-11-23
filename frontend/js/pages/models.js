/*
 * Rôle : affiche la bibliothèque des modèles enregistrés (créés, importés ou copiés depuis les exemples).
 * Exécution : router.js monte la grille sur #/modeles ; #/modeles?import=1 ouvre directement l'import GLB.
 * Refonte : état vide illustré avec appel à l'action, cartes animées, filtres avec compteurs.
 */
// Importe l'import d'un GLB et la liste des catégories.
import { importGlbModel, listCategories } from "../api.js?v=20261117-r2";
// Importe la galerie.
import { setupGallery } from "../views/gallery.js?v=20261117-r2";
// Importe le dessin du cube (état vide).
import { emptyCubeIllustration } from "../views/illustrations.js?v=20261117-r2";

// Titre de l'onglet.
export const title = "Mes modèles";
// Expression régulière d'un UUID (modèle enregistré).
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Retourne le HTML de la page Mes modèles (bouton d'import, galerie).
export function render() {
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - l'introduction et le bouton « Importer un modèle (.glb) » ;
  // - le panneau caché d'import : fichier .glb, titre, catégorie, boutons et message ;
  // - l'en-tête de la galerie avec son compteur ;
  // - l'état vide illustré avec deux actions (créer à partir d'une photo, importer) ;
  // - les filtres, la grille des cartes et le message d'état.
  return `
    <section class="page-shell gallery-page" aria-labelledby="page-title">
      <div class="page-intro section-header">
        <div><p class="eyebrow">Votre catalogue</p><h1 class="page-title" id="page-title" tabindex="-1">Mes modèles</h1><p class="page-lead">Retrouvez ici les modèles créés, importés ou ajoutés depuis les exemples.</p></div>
        <button class="button button-primary" id="open-model-import" type="button">Importer un modèle (.glb)</button>
      </div>
      <section class="panel library-panel" aria-label="Vos modèles 3D">
        <section class="model-import-panel" id="model-import-panel" aria-labelledby="import-title" hidden>
          <h2 id="import-title">Importer un modèle GLB</h2>
          <p>Le fichier est vérifié puis enregistré dans Mes modèles. Un import n’est pas une génération à partir d’une photo : il sera marqué « Importé ».</p>
          <form id="model-import-form">
            <div class="import-grid">
              <div><label for="import-file">Fichier .glb</label><input id="import-file" name="file" type="file" accept=".glb,model/gltf-binary" required></div>
              <div><label for="import-title-field">Titre</label><input id="import-title-field" name="title" type="text" maxlength="100" placeholder="Ex. Fauteuil velours" required></div>
              <div><label for="import-category">Catégorie</label><select id="import-category" name="category" required><option value="">Chargement des catégories…</option></select></div>
            </div>
            <div class="form-actions"><button class="button button-primary" type="submit">Importer dans Mes modèles</button><button class="button button-secondary" id="cancel-model-import" type="button">Annuler</button></div>
            <p id="model-import-feedback" role="status" aria-live="polite"></p>
          </form>
        </section>
        <div class="gallery-heading"><div><h2>Modèles enregistrés</h2><p class="gallery-copy">Filtrez par catégorie, puis ouvrez une fiche pour télécharger ou intégrer le modèle.</p></div><span class="gallery-count" id="gallery-count" aria-live="polite">Chargement…</span></div>
        <div class="library-empty-actions" id="library-empty-actions" hidden>
          ${emptyCubeIllustration()}
          <h3>Votre bibliothèque est vide</h3>
          <p>Créez votre premier modèle 3D ! Partez d’une photo, importez un fichier GLB existant ou ajoutez un exemple du catalogue.</p>
          <div class="form-actions"><a class="button button-primary button-large" href="#/creer">Créer à partir d’une photo</a><button class="button button-secondary button-large" id="empty-import-button" type="button">Importer un modèle</button></div>
        </div>
        <div class="filter-list" id="gallery-filters" role="group" aria-label="Filtrer vos modèles par catégorie"></div>
        <div class="gallery-grid" id="gallery-grid" aria-live="polite"></div>
        <p class="gallery-message" id="gallery-message" role="status" hidden></p>
      </section>
    </section>`;
}

// Branche Mes modèles : galerie des modèles enregistrés et import d'un GLB (POST /models/import).
// #/modeles?import=1 ouvre directement le formulaire.
export function mount(route) {
  // Panneau d'import.
  const panel = document.querySelector("#model-import-panel");
  // Formulaire d'import.
  const form = document.querySelector("#model-import-form");
  // Champ du fichier.
  const fileInput = document.querySelector("#import-file");
  // Champ du titre.
  const titleInput = document.querySelector("#import-title-field");
  // Liste des catégories.
  const categorySelect = document.querySelector("#import-category");
  // Message du formulaire.
  const feedback = document.querySelector("#model-import-feedback");
  // Fonction qui ouvre le panneau d'import :
  const openImport = () => {
    // le rend visible...
    panel.hidden = false;
    // ...fait défiler jusqu'à lui...
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    // ...et place le focus sur le choix du fichier.
    fileInput.focus({ preventScroll: true });
  };
  // Bouton du haut : ouvre l'import.
  document.querySelector("#open-model-import").addEventListener("click", openImport);
  // Bouton de l'état vide : ouvre l'import.
  document.querySelector("#empty-import-button").addEventListener("click", openImport);
  // Bouton Annuler : masque le panneau.
  document.querySelector("#cancel-model-import").addEventListener("click", () => { panel.hidden = true; });
  // Quand un fichier est choisi...
  fileInput.addEventListener("change", () => {
    // ...premier fichier...
    const file = fileInput.files?.[0];
    // ...si le titre n'a pas été modifié à la main...
    if (file && !titleInput.dataset.edited) {
      // ...propose un titre tiré du nom du fichier.
      titleInput.value = file.name.replace(/\.glb$/i, "").replace(/[._-]+/g, " ").trim();
    }
  });
  // Dès que le titre est saisi, on ne le remplace plus.
  titleInput.addEventListener("input", () => { titleInput.dataset.edited = "true"; });
  // Branche la galerie...
  const gallery = setupGallery(
    // ...clic sur une carte : ouvre sa fiche...
    (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; },
    // ...options :
    {
      // garde seulement les modèles enregistrés (UUID)...
      filter: (model) => generationIdPattern.test(model.id),
      // ...message si vide...
      emptyMessage: "Vous n’avez pas encore de modèle enregistré.",
      // ...message si aucun résultat.
      noMatchMessage: "Aucun modèle dans cette catégorie.",
    },
  );
  // Charge les catégories, puis...
  void listCategories().then((response) => {
    // ...liste reçue...
    const categories = response.items ?? [];
    // ...transmise à la galerie...
    gallery.setCategories(categories);
    // ...option vide en premier...
    categorySelect.replaceChildren(new Option("Choisir une catégorie", ""));
    // ...une option par catégorie.
    categories.forEach((category) => categorySelect.add(new Option(category.label, category.slug)));
  // Échec : option d'indisponibilité.
  }).catch(() => { categorySelect.replaceChildren(new Option("Catégories indisponibles", "")); });
  // À l'envoi du formulaire...
  form.addEventListener("submit", async (event) => {
    // ...empêche le rechargement...
    event.preventDefault();
    // ...message d'attente...
    feedback.textContent = "Import du modèle…";
    // ...bouton d'envoi...
    const submit = form.querySelector("button[type=submit]");
    // ...désactivé...
    submit.disabled = true;
    // ...essaie...
    try {
      // ...d'importer le fichier...
      const result = await importGlbModel(fileInput.files[0], titleInput.value, categorySelect.value);
      // ...message de succès...
      feedback.replaceChildren(document.createTextNode("Modèle importé et enregistré dans Mes modèles. "));
      // ...lien vers la fiche...
      const detailLink = document.createElement("a");
      // ...adresse de la fiche...
      detailLink.href = `#/modeles/${encodeURIComponent(result.id)}`;
      // ...texte du lien...
      detailLink.textContent = "Ouvrir sa fiche";
      // ...ajouté au message...
      feedback.append(detailLink);
      // ...vide le formulaire...
      form.reset();
      // ...le titre redevient automatique...
      titleInput.dataset.edited = "";
      // ...et recharge la galerie.
      await gallery.reload();
    // Erreur...
    } catch (error) {
      // ...message affiché.
      feedback.textContent = error.message;
    // Dans tous les cas...
    } finally {
      // ...réactive le bouton.
      submit.disabled = false;
    }
  });
  // Raccourci de l'accueil : #/modeles?import=1 ouvre le formulaire d'import.
  if (route?.query?.get("import") === "1") openImport();
}
