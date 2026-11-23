/*
 * Rôle : rassemble les modèles de démonstration fournis par l'API dans une galerie distincte.
 * Exécution : router.js monte cette page sur #/exemples ; un clic ouvre la fiche du modèle.
 * Refonte : une description courte sous chaque carte, avec la durée réellement mesurée
 * lors des essais de faisabilité (aucune durée n'est inventée).
 */
// Importe la copie d'un exemple et la liste des catégories.
import { copyExampleModel, listCategories } from "../api.js?v=20261117-r2";
// Importe la galerie.
import { setupGallery } from "../views/gallery.js?v=20261117-r2";
// Importe la description des exemples.
import { exampleDescription } from "../format.js?v=20261117-r2";

// Titre de l'onglet.
export const title = "Exemples de modèles";
// Expression régulière d'un UUID (modèle enregistré).
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Retourne le HTML de la page Exemples (catalogue et panneau d'ajout).
export function render() {
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - l'introduction de la page Exemples ;
  // - le panneau caché « Ajouter l'exemple à Mes modèles » : nom choisi, liste des catégories, boutons, message ;
  // - le panneau de la galerie : compteur, filtres par catégorie, grille des cartes, message d'état.
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
  // Panneau d'ajout.
  const panel = document.querySelector("#example-copy-panel");
  // Liste des catégories du panneau.
  const categorySelect = document.querySelector("#copy-example-category");
  // Message du panneau.
  const feedback = document.querySelector("#copy-example-feedback");
  // Exemple choisi.
  let selectedExample = null;
  // Branche la galerie...
  const gallery = setupGallery(
    // ...clic sur une carte : ouvre sa fiche...
    (model) => { window.location.hash = `#/modeles/${encodeURIComponent(model.id)}`; },
    // ...options :
    {
      // garde seulement les exemples (pas d'UUID)...
      filter: (model) => !generationIdPattern.test(model.id),
      // ...message si vide...
      emptyMessage: "Aucun exemple n’est disponible pour le moment.",
      // ...message si aucun résultat...
      noMatchMessage: "Aucun exemple dans cette catégorie.",
      // ...description sous chaque carte...
      description: exampleDescription,
      // ...texte du bouton d'action...
      actionLabel: "Ajouter à mes modèles",
      // ...au clic sur « Ajouter » :
      onAction(model) {
        // mémorise l'exemple...
        selectedExample = model;
        // ...affiche son nom...
        document.querySelector("#copy-example-name").textContent = `Modèle choisi : ${model.name}`;
        // ...efface l'ancien message...
        feedback.textContent = "";
        // ...montre le panneau...
        panel.hidden = false;
        // ...fait défiler jusqu'à lui...
        panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
        // ...présélectionne sa catégorie...
        categorySelect.value = model.category;
        // ...et place le focus sur la liste.
        categorySelect.focus({ preventScroll: true });
      },
    },
  );
  // Bouton Annuler : masque le panneau.
  document.querySelector("#cancel-copy-example").addEventListener("click", () => { panel.hidden = true; });
  // Charge les catégories, puis...
  void listCategories().then((response) => {
    // ...liste reçue...
    const categories = response.items ?? [];
    // ...transmise à la galerie (filtres)...
    gallery.setCategories(categories);
    // ...option vide en premier...
    categorySelect.replaceChildren(new Option("Choisir une catégorie", ""));
    // ...une option par catégorie.
    categories.forEach((category) => categorySelect.add(new Option(category.label, category.slug)));
  // Échec : option d'indisponibilité.
  }).catch(() => { categorySelect.replaceChildren(new Option("Catégories indisponibles", "")); });
  // À l'envoi du formulaire d'ajout...
  document.querySelector("#copy-example-form").addEventListener("submit", async (event) => {
    // ...empêche le rechargement...
    event.preventDefault();
    // ...aucun exemple choisi : arrêt...
    if (!selectedExample) return;
    // ...bouton d'envoi...
    const submit = event.currentTarget.querySelector("button[type=submit]");
    // ...désactivé...
    submit.disabled = true;
    // ...message d'attente...
    feedback.textContent = "Ajout de l’exemple…";
    // ...essaie...
    try {
      // ...de copier l'exemple...
      const result = await copyExampleModel(selectedExample.id, selectedExample.name, categorySelect.value);
      // ...message de succès...
      feedback.replaceChildren(document.createTextNode("Exemple ajouté à Mes modèles. "));
      // ...lien vers la fiche...
      const libraryLink = document.createElement("a");
      // ...adresse de la fiche...
      libraryLink.href = `#/modeles/${encodeURIComponent(result.id)}`;
      // ...texte du lien...
      libraryLink.textContent = "Ouvrir sa fiche";
      // ...ajouté au message...
      feedback.append(libraryLink);
      // ...puis recharge la galerie.
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
}
