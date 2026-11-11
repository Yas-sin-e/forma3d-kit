/*
 * Rôle : gère la création, le renommage, l'activation et la suppression des catégories.
 * Exécution : main.js charge la vue et la connecte au formulaire et aux filtres de galerie.
 */
import { createCategory, deleteCategory, listCategories, updateCategory } from "../api.js?v=20261111-5a";

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
    const label = document.createElement("input");
    label.name = "label";
    label.value = category.label;
    label.maxLength = 100;
    label.setAttribute("aria-label", "Nom affiché de " + category.label);
    const save = document.createElement("button");
    save.className = "button button-secondary";
    save.type = "submit";
    save.textContent = "Enregistrer";
    form.append(label, save);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await runAction(() => updateCategory(category.slug, { label: label.value }), "Nom de catégorie mis à jour.");
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
      if (!window.confirm(`Supprimer la catégorie « ${category.label} » ? Cette action est définitive.`)) return;
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
      const detail = error.message.toLocaleLowerCase("fr-FR").includes("slug")
        ? "Ce nom de catégorie est déjà utilisé ou ne peut pas être créé. Choisissez un autre nom."
        : error.message.toLocaleLowerCase("fr-FR").includes("libellé")
          ? "Entrez un nom de catégorie de 100 caractères maximum."
          : error.message;
      showMessage(detail, true);
    }
  }

  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    slugInput.value = labelInput.value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("fr-FR")
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 64);
    await runAction(
      () => createCategory({ slug: slugInput.value, label: labelInput.value }),
      "Catégorie créée.",
    );
    if (!feedback.dataset.kind || feedback.dataset.kind !== "error") createForm.reset();
  });

  void reload();
  return { reload };
}
