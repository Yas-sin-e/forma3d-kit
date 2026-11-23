/*
 * Rôle : gère la création, le renommage, l'activation et la suppression des catégories.
 * Exécution : pages/categories.js monte la vue sur #/categories.
 * Refonte : chaque ligne affiche son statut en badge et le nombre de modèles enregistrés ;
 * désactivation et suppression passent par une fenêtre de confirmation (confirmDialog).
 */
// Importe les appels HTTP des catégories.
import { createCategory, deleteCategory, listCategories, updateCategory } from "../api.js?v=20261117-r2";
// Importe la fenêtre de confirmation.
import { confirmDialog } from "./confirm-dialog.js?v=20261117-r2";

// Branche l'écran de gestion des catégories : création, renommage, activation, suppression.
export function setupCategoryManager(onCategoriesChanged, options = {}) {
  // Formulaire de création.
  const createForm = document.querySelector("#category-create-form");
  // Champ caché du slug.
  const slugInput = document.querySelector("#new-category-slug");
  // Champ du nom affiché.
  const labelInput = document.querySelector("#new-category-label");
  // Liste des catégories.
  const list = document.querySelector("#category-list");
  // Compteur affiché.
  const count = document.querySelector("#category-count");
  // Zone des messages.
  const feedback = document.querySelector("#category-feedback");

  // Affiche un message de succès ou d'erreur sous le formulaire.
  function showMessage(message = "", isError = false) {
    // Texte du message.
    feedback.textContent = message;
    // Type de message (le CSS choisit la couleur).
    feedback.dataset.kind = isError ? "error" : "success";
    // Masqué si le message est vide.
    feedback.hidden = message.length === 0;
  }

  // Construit la ligne d'une catégorie avec ses boutons (Renommer, Désactiver/Réactiver, Supprimer).
  function makeCategoryRow(category, usage) {
    // Crée la ligne.
    const row = document.createElement("article");
    // Classe différente pour une catégorie désactivée.
    row.className = category.is_active ? "category-admin-row" : "category-admin-row is-inactive";

    // Partie principale de la ligne.
    const main = document.createElement("div");
    // Sa classe CSS.
    main.className = "category-row-main";
    // Badge de statut.
    const status = document.createElement("span");
    // Classe du badge selon l'état.
    status.className = category.is_active ? "status-badge" : "status-badge is-inactive";
    // Texte du badge.
    status.textContent = category.is_active ? "Active" : "Désactivée";
    // Badge du nombre de modèles.
    const countBadge = document.createElement("span");
    // Sa classe CSS.
    countBadge.className = "category-count-badge";
    // « — modèle » si inconnu, sinon « 3 modèles ».
    countBadge.textContent = usage === null ? "— modèle" : `${usage} modèle${usage > 1 ? "s" : ""}`;

    // Formulaire de renommage.
    const form = document.createElement("form");
    // Sa classe CSS.
    form.className = "category-edit-form";
    // Champ du nom.
    const label = document.createElement("input");
    // Nom du champ.
    label.name = "label";
    // Valeur actuelle.
    label.value = category.label;
    // 100 caractères maximum.
    label.maxLength = 100;
    // Nom accessible du champ.
    label.setAttribute("aria-label", "Nom affiché de " + category.label);
    // Bouton « Renommer ».
    const save = document.createElement("button");
    // Style secondaire.
    save.className = "button button-secondary";
    // Type « submit » : il envoie le formulaire.
    save.type = "submit";
    // Texte du bouton.
    save.textContent = "Renommer";
    // Assemble le formulaire.
    form.append(label, save);
    // À l'envoi du formulaire...
    form.addEventListener("submit", async (event) => {
      // ...empêche le rechargement de la page...
      event.preventDefault();
      // ...renomme la catégorie et affiche le résultat.
      await runAction(() => updateCategory(category.slug, { label: label.value }), "Nom de catégorie mis à jour.");
    });
    // Assemble la partie principale.
    main.append(form, status, countBadge);

    // Zone des boutons d'action.
    const actions = document.createElement("div");
    // Sa classe CSS.
    actions.className = "category-admin-actions";
    // Bouton Désactiver / Réactiver.
    const toggle = document.createElement("button");
    // Style secondaire.
    toggle.className = "button button-secondary";
    // Type « button ».
    toggle.type = "button";
    // Texte selon l'état.
    toggle.textContent = category.is_active ? "Désactiver" : "Réactiver";
    // Au clic...
    toggle.addEventListener("click", async () => {
      // ...si la catégorie est active...
      if (category.is_active) {
        // ...demande une confirmation...
        const confirmed = await confirmDialog({
          // ...titre...
          title: "Désactiver cette catégorie ?",
          // ...explication...
          message: `« ${category.label} » ne sera plus proposée pour les nouvelles créations. Les modèles existants la conservent ; vous pourrez la réactiver.`,
          // ...texte du bouton de confirmation.
          confirmLabel: "Désactiver",
        });
        // Annulé : on s'arrête.
        if (!confirmed) return;
      }
      // Inverse l'état...
      await runAction(
        // ...requête de mise à jour...
        () => updateCategory(category.slug, { is_active: !category.is_active }),
        // ...message de succès selon le cas.
        category.is_active ? "Catégorie désactivée. Les anciens modèles restent dans la galerie." : "Catégorie réactivée.",
      );
    });

    // Bouton Supprimer.
    const remove = document.createElement("button");
    // Style « danger ».
    remove.className = "button button-danger";
    // Type « button ».
    remove.type = "button";
    // Texte du bouton.
    remove.textContent = "Supprimer";
    // Catégorie utilisée...
    if (usage > 0) {
      // Le serveur refuse de supprimer une catégorie utilisée (HTTP 409) : on l'explique d'avance.
      // ...bouton désactivé...
      remove.disabled = true;
      // ...avec une infobulle qui explique pourquoi.
      remove.title = "Catégorie utilisée par des modèles : désactivez-la plutôt.";
    }
    // Au clic...
    remove.addEventListener("click", async () => {
      // ...demande une confirmation...
      const confirmed = await confirmDialog({
        // ...titre...
        title: "Supprimer cette catégorie ?",
        // ...explication...
        message: `La catégorie « ${category.label} » sera supprimée définitivement.`,
        // ...texte du bouton...
        confirmLabel: "Supprimer",
        // ...style rouge.
        danger: true,
      });
      // Annulé : on s'arrête.
      if (!confirmed) return;
      // Supprime et affiche le résultat.
      await runAction(() => deleteCategory(category.slug), "Catégorie supprimée.");
    });
    // Place les deux boutons.
    actions.append(toggle, remove);
    // Assemble la ligne.
    row.append(main, actions);
    // Renvoie la ligne.
    return row;
  }

  // Recharge la liste (GET /categories?include_inactive=true) et le nombre de modèles par catégorie.
  async function reload() {
    // Message d'attente.
    count.textContent = "Chargement des catégories…";
    // Essaie...
    try {
      // ...de lancer deux demandes en parallèle...
      const [response, counts] = await Promise.all([
        // ...la liste complète des catégories...
        listCategories(true),
        // ...et le nombre de modèles (null en cas d'erreur ou d'absence de fonction).
        typeof options.loadCounts === "function" ? options.loadCounts().catch(() => null) : Promise.resolve(null),
      ]);
      // Liste des catégories (vide si la réponse est inattendue).
      const categories = Array.isArray(response.items) ? response.items : [];
      // « 1 catégorie » ou « N catégories ».
      count.textContent = categories.length + (categories.length === 1 ? " catégorie" : " catégories");
      // Remplace la liste par les nouvelles lignes.
      list.replaceChildren(...categories.map((category) => makeCategoryRow(category, counts ? counts.get(category.slug) ?? 0 : null)));
      // Prévient la page (pour mettre à jour d'autres éléments).
      await onCategoriesChanged(categories);
      // Liste vide...
      if (!categories.length) {
        // ...crée un paragraphe...
        const empty = document.createElement("p");
        // ...avec sa classe...
        empty.className = "category-empty";
        // ...et son texte...
        empty.textContent = "Aucune catégorie enregistrée.";
        // ...puis l'affiche.
        list.append(empty);
      }
    // Erreur...
    } catch (error) {
      // ...compteur d'indisponibilité...
      count.textContent = "Gestion indisponible";
      // ...liste vidée...
      list.replaceChildren();
      // ...message d'erreur.
      showMessage(error.message, true);
    }
  }

  // Exécute une action (créer, renommer…), affiche le résultat et recharge la liste ;
  // traduit les erreurs techniques du serveur en message simple.
  async function runAction(action, successMessage) {
    // Efface le message précédent.
    showMessage("");
    // Essaie...
    try {
      // ...l'action...
      await action();
      // ...affiche le succès...
      showMessage(successMessage);
      // ...et recharge la liste.
      await reload();
    // Erreur...
    } catch (error) {
      // ...message qui parle du slug...
      const detail = error.message.toLocaleLowerCase("fr-FR").includes("slug")
        // ...devient un message simple sur le nom...
        ? "Ce nom de catégorie est déjà utilisé ou ne peut pas être créé. Choisissez un autre nom."
        // ...message qui parle du libellé...
        : error.message.toLocaleLowerCase("fr-FR").includes("libellé")
          // ...devient un message sur la longueur...
          ? "Entrez un nom de catégorie de 100 caractères maximum."
          // ...sinon on garde le message du serveur.
          : error.message;
      // Affiche l'erreur.
      showMessage(detail, true);
    }
  }

  // À l'envoi du formulaire de création...
  createForm.addEventListener("submit", async (event) => {
    // ...empêche le rechargement de la page...
    event.preventDefault();
    // ...fabrique le slug à partir du nom :
    slugInput.value = labelInput.value
      // sépare lettres et accents...
      .normalize("NFD")
      // ...retire les accents...
      .replace(/[\u0300-\u036f]/g, "")
      // ...met en minuscules...
      .toLocaleLowerCase("fr-FR")
      // ...retire les espaces autour...
      .trim()
      // ...remplace tout autre caractère par un tiret...
      .replace(/[^a-z0-9]+/g, "-")
      // ...retire les tirets au début et à la fin...
      .replace(/^-|-$/g, "")
      // ...garde 64 caractères au maximum.
      .slice(0, 64);
    // Crée la catégorie...
    await runAction(
      // ...requête de création...
      () => createCategory({ slug: slugInput.value, label: labelInput.value }),
      // ...message de succès.
      "Catégorie créée.",
    );
    // Pas d'erreur : vide le formulaire.
    if (!feedback.dataset.kind || feedback.dataset.kind !== "error") createForm.reset();
  });

  // Charge la liste au démarrage.
  void reload();
  // Renvoie la fonction de rechargement.
  return { reload };
}
