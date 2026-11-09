/*
 * Rôle : gère la création, le renommage, l'activation et la suppression des catégories.
 * Exécution : main.js charge la vue et la connecte au formulaire et aux filtres de galerie.
 */
import { createCategory, deleteCategory, listCategories, updateCategory } from "../api.js";

export function setupCategoryManager(onCategoriesChanged) {
  const createForm = document.querySelector("#category-create-form");
  const slugInput = document.querySelector("#new-category-slug");
  const labelInput = document.querySelector("#new-category-label");
  const list = document.querySelector("#category-list");
  const count = document.querySelector("#category-count");
  const feedback = document.querySelector("#category-feedback");

  function showMessage(message = "", isError = false) {
    feedback.textContent = message;
    feedback.dataset.kind = isError ? "error" : "success";
    feedback.hidden = message.length === 0;
  }

  function makeCategoryRow(category) {
    const row = document.createElement("article");
    row.className = "category-admin-row";

    const status = document.createElement("p");
    status.className = "category-admin-status";
    status.textContent = category.is_active ? "Active" : "Désactivée";

    const form = document.createElement("form");
    form.className = "category-edit-form";
    const slug = document.createElement("input");
    slug.name = "slug";
    slug.value = category.slug;
    slug.maxLength = 64;
    slug.setAttribute("aria-label", "Identifiant de " + category.label);
    const label = document.createElement("input");
    label.name = "label";
    label.value = category.label;
    label.maxLength = 100;
    label.setAttribute("aria-label", "Nom affiché de " + category.label);
    const save = document.createElement("button");
    save.className = "button button-secondary";
    save.type = "submit";
    save.textContent = "Enregistrer";
    form.append(slug, label, save);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await runAction(() => updateCategory(category.slug, { slug: slug.value, label: label.value }), "Catégorie mise à jour.");
    });

    const actions = document.createElement("div");
    actions.className = "category-admin-actions";
    const toggle = document.createElement("button");
    toggle.className = "button button-secondary";
    toggle.type = "button";
    toggle.textContent = category.is_active ? "Désactiver" : "Réactiver";
    toggle.addEventListener("click", async () => {
      await runAction(
        () => updateCategory(category.slug, { is_active: !category.is_active }),
        category.is_active ? "Catégorie désactivée. Les anciens modèles restent dans la galerie." : "Catégorie réactivée.",
      );
    });

    const remove = document.createElement("button");
    remove.className = "button button-danger";
    remove.type = "button";
    remove.textContent = "Supprimer";
    remove.addEventListener("click", async () => {
      await runAction(() => deleteCategory(category.slug), "Catégorie supprimée.");
    });
    actions.append(toggle, remove);
    row.append(status, form, actions);
    return row;
  }

  async function reload() {
    count.textContent = "Chargement des catégories…";
    try {
      const response = await listCategories(true);
      const categories = Array.isArray(response.items) ? response.items : [];
      count.textContent = categories.length + (categories.length === 1 ? " catégorie" : " catégories");
      list.replaceChildren(...categories.map(makeCategoryRow));
      await onCategoriesChanged(categories);
      if (!categories.length) {
        const empty = document.createElement("p");
        empty.className = "category-empty";
        empty.textContent = "Aucune catégorie enregistrée.";
        list.append(empty);
      }
    } catch (error) {
      count.textContent = "Gestion indisponible";
      list.replaceChildren();
      showMessage(error.message, true);
    }
  }

  async function runAction(action, successMessage) {
    showMessage("");
    try {
      await action();
      showMessage(successMessage);
      await reload();
    } catch (error) {
      showMessage(error.message, true);
    }
  }

  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runAction(
      () => createCategory({ slug: slugInput.value, label: labelInput.value }),
      "Catégorie créée.",
    );
    if (!feedback.dataset.kind || feedback.dataset.kind !== "error") createForm.reset();
  });

  void reload();
  return { reload };
}
