/*
 * Rôle : gère la création, le renommage, l'activation et la suppression des catégories.
 * Exécution : pages/categories.js monte la vue sur #/categories.
 * Refonte : chaque ligne affiche son statut en badge et le nombre de modèles enregistrés ;
 * désactivation et suppression passent par une fenêtre de confirmation (confirmDialog).
 */
import { createCategory, deleteCategory, listCategories, updateCategory } from "../api.js?v=20261112-c5";
import { confirmDialog } from "./confirm-dialog.js?v=20261112-c5";

export function setupCategoryManager(onCategoriesChanged, options = {}) {
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

  function makeCategoryRow(category, usage) {
    const row = document.createElement("article");
    row.className = category.is_active ? "category-admin-row" : "category-admin-row is-inactive";

    const main = document.createElement("div");
    main.className = "category-row-main";
    const status = document.createElement("span");
    status.className = category.is_active ? "status-badge" : "status-badge is-inactive";
    status.textContent = category.is_active ? "Active" : "Désactivée";
    const countBadge = document.createElement("span");
    countBadge.className = "category-count-badge";
    countBadge.textContent = usage === null ? "— modèle" : `${usage} modèle${usage > 1 ? "s" : ""}`;

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
    save.textContent = "Renommer";
    form.append(label, save);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await runAction(() => updateCategory(category.slug, { label: label.value }), "Nom de catégorie mis à jour.");
    });
    main.append(form, status, countBadge);

    const actions = document.createElement("div");
    actions.className = "category-admin-actions";
    const toggle = document.createElement("button");
    toggle.className = "button button-secondary";
    toggle.type = "button";
    toggle.textContent = category.is_active ? "Désactiver" : "Réactiver";
    toggle.addEventListener("click", async () => {
      if (category.is_active) {
        const confirmed = await confirmDialog({
          title: "Désactiver cette catégorie ?",
          message: `« ${category.label} » ne sera plus proposée pour les nouvelles créations. Les modèles existants la conservent ; vous pourrez la réactiver.`,
          confirmLabel: "Désactiver",
        });
        if (!confirmed) return;
      }
      await runAction(
        () => updateCategory(category.slug, { is_active: !category.is_active }),
        category.is_active ? "Catégorie désactivée. Les anciens modèles restent dans la galerie." : "Catégorie réactivée.",
      );
    });

    const remove = document.createElement("button");
    remove.className = "button button-danger";
    remove.type = "button";
    remove.textContent = "Supprimer";
    if (usage > 0) {
      // Le serveur refuse de supprimer une catégorie utilisée (HTTP 409) : on l'explique d'avance.
      remove.disabled = true;
      remove.title = "Catégorie utilisée par des modèles : désactivez-la plutôt.";
    }
    remove.addEventListener("click", async () => {
      const confirmed = await confirmDialog({
        title: "Supprimer cette catégorie ?",
        message: `La catégorie « ${category.label} » sera supprimée définitivement.`,
        confirmLabel: "Supprimer",
        danger: true,
      });
      if (!confirmed) return;
      await runAction(() => deleteCategory(category.slug), "Catégorie supprimée.");
    });
    actions.append(toggle, remove);
    row.append(main, actions);
    return row;
  }

  async function reload() {
    count.textContent = "Chargement des catégories…";
    try {
      const [response, counts] = await Promise.all([
        listCategories(true),
        typeof options.loadCounts === "function" ? options.loadCounts().catch(() => null) : Promise.resolve(null),
      ]);
      const categories = Array.isArray(response.items) ? response.items : [];
      count.textContent = categories.length + (categories.length === 1 ? " catégorie" : " catégories");
      list.replaceChildren(...categories.map((category) => makeCategoryRow(category, counts ? counts.get(category.slug) ?? 0 : null)));
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
