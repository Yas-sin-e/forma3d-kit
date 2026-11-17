/*
 * Rôle : charge une fiche produit par identifiant et présente son état, sa photo, son GLB et son intégration.
 * Exécution : router.js monte cette page sur #/modeles/{id}, y compris pour signaler un identifiant inconnu.
 * Refonte : bascule Vue 3D / Photo source / Comparer, squelette de chargement, et intégration
 * guidée en 4 étapes (interrupteur, choix iframe/widget, code à copier, aperçu réel via /embed).
 * Sous-étape A : matériau mat pour les GLB sans matériau, recadrage et rotation en pause en mode Comparer.
 * Suppression : bouton « Supprimer ce modèle » avec confirmation, puis retour à Mes modèles.
 * Modification : bouton « Modifier » à côté du nom, formulaire en ligne pour le nom et la catégorie
 * (Entrée enregistre, Échap annule) ; seules les valeurs changées sont envoyées.
 */
import { deleteModel, getGenerationStatus, listCategories, listGalleryModels, renameModel, changeModelCategory, setModelIntegrationEnabled } from "../api.js?v=20261117-r2";
import { confirmDialog } from "../views/confirm-dialog.js?v=20261117-r2";
import { exampleGenerationSeconds, exampleProviders, formatDuration, formatLongDate } from "../format.js?v=20261117-r2";
import { refitCamera, watchProductAppearance } from "../views/model-appearance.js?v=20261117-r2";

export const title = "Fiche du modèle";

// Retourne le HTML de la fiche d'un modèle (viewer, informations, intégration en 4 étapes).
export function render(route) {
  const backHref = route.navKey === "examples" ? "#/exemples" : "#/modeles";
  const backLabel = route.navKey === "examples" ? "← Retour aux exemples" : "← Retour à Mes modèles";
  return `
    <section class="page-shell detail-page" aria-labelledby="page-title">
      <a class="back-link" href="${backHref}">${backLabel}</a>
      <div class="page-intro"><p class="eyebrow">Détail du produit</p><h1 class="page-title" id="page-title" tabindex="-1">Fiche du modèle</h1><p class="page-lead" id="detail-subtitle">Chargement du modèle…</p></div>
      <div class="detail-layout">
        <section class="panel detail-viewer-panel" aria-labelledby="detail-viewer-title">
          <div class="detail-viewer-heading">
            <h2 id="detail-viewer-title">Aperçu 3D</h2>
            <div class="view-toggle" id="detail-view-toggle" role="group" aria-label="Mode d’affichage" hidden>
              <button type="button" data-view="model" aria-pressed="true">Vue 3D</button>
              <button type="button" data-view="photo" aria-pressed="false">Photo source</button>
              <button type="button" data-view="compare" aria-pressed="false">Comparer</button>
            </div>
          </div>
          <div class="detail-stage" id="detail-stage" data-view="model">
            <div class="stage-grid" aria-hidden="true"></div>
            <div class="viewer-skeleton" id="detail-skeleton" hidden>Chargement du modèle 3D…</div>
            <model-viewer id="detail-model-viewer" alt="Modèle 3D du produit" camera-controls touch-action="pan-y" interaction-prompt="none" environment-image="neutral" tone-mapping="neutral" shadow-intensity="1" shadow-softness="1" exposure="1.1" auto-rotate rotation-per-second="20deg" auto-rotate-delay="2500" camera-orbit="25deg 75deg 105%" loading="eager" hidden></model-viewer>
            <div class="stage-photo" id="detail-stage-photo" hidden><img id="detail-source-image" alt="Photo d’origine du produit"></div>
            <div class="detail-empty" id="detail-empty" role="status">Chargement des informations…</div>
          </div>
          <p class="stage-footnote"><span class="note-mark" aria-hidden="true">i</span>Aperçu 3D généré automatiquement — idéal pour la visualisation produit. La géométrie est une estimation.</p>
        </section>
        <aside class="panel detail-information" aria-labelledby="detail-name">
          <div class="detail-name-row">
            <h2 id="detail-name">Informations</h2>
            <button class="button button-ghost detail-rename" id="detail-rename" type="button" hidden aria-label="Modifier le nom ou la catégorie de ce modèle">✎ Modifier</button>
          </div>
          <form class="detail-rename-form" id="detail-rename-form" hidden>
            <label class="field-label" for="detail-rename-input">Nouveau nom</label>
            <input type="text" id="detail-rename-input" maxlength="80" required autocomplete="off">
            <label class="field-label" for="detail-category-select">Catégorie</label>
            <select id="detail-category-select"></select>
            <div class="detail-rename-actions">
              <button class="button button-primary" id="detail-rename-save" type="submit">Enregistrer</button>
              <button class="button button-secondary" id="detail-rename-cancel" type="button">Annuler</button>
            </div>
          </form>
          <p class="detail-rename-feedback" id="detail-rename-feedback" role="status" aria-live="polite"></p>
          <dl class="detail-facts">
            <div><dt>État</dt><dd id="detail-status">Chargement…</dd></div>
            <div><dt>Catégorie</dt><dd id="detail-category">—</dd></div>
            <div><dt>Origine</dt><dd id="detail-origin">—</dd></div>
            <div><dt>Date de création</dt><dd id="detail-date">—</dd></div>
            <div><dt>Durée de génération</dt><dd id="detail-duration">—</dd></div>
          </dl>
          <a class="button button-primary button-large detail-download" id="detail-download" href="#" download hidden>Télécharger le modèle (.glb)</a>
          <button class="button button-danger detail-delete" id="detail-delete" type="button" hidden>Supprimer ce modèle</button>
          <p class="detail-delete-feedback" id="detail-delete-feedback" role="status" aria-live="polite"></p>
        </aside>
      </div>

      <section class="panel integration-guide" id="detail-integration" aria-labelledby="detail-integration-title" hidden>
        <div class="section-header"><div><p class="eyebrow">Intégration</p><h2 id="detail-integration-title">Afficher ce modèle sur un site</h2><p>Suivez les étapes dans l’ordre : rien n’est visible publiquement tant que l’étape 1 n’est pas activée.</p></div></div>
        <ol class="guide-steps">
          <li class="guide-step" id="guide-step-enable">
            <span class="guide-step-number" aria-hidden="true">1</span>
            <div class="guide-step-body">
              <h3>Activez l’intégration</h3>
              <p id="detail-integration-status" role="status" aria-live="polite">Désactivée par défaut. Le modèle reste privé tant que vous ne l’activez pas.</p>
              <div class="switch-row">
                <button class="switch" id="detail-integration-toggle" type="button" role="switch" aria-checked="false" aria-labelledby="detail-switch-label"></button>
                <span class="switch-label" id="detail-switch-label">Intégration publique de ce modèle</span>
              </div>
            </div>
          </li>
          <li class="guide-step" data-locked="true" data-requires-enabled>
            <span class="guide-step-number" aria-hidden="true">2</span>
            <div class="guide-step-body">
              <h3>Choisissez votre méthode</h3>
              <p>L’iframe fonctionne partout ; le widget Forma3D est une balise HTML plus simple à personnaliser.</p>
              <div class="tabs" role="tablist" aria-label="Méthode d’intégration">
                <button class="tab" type="button" role="tab" id="tab-iframe" aria-selected="true" aria-controls="detail-integration-code" data-method="iframe">IFrame</button>
                <button class="tab" type="button" role="tab" id="tab-widget" aria-selected="false" aria-controls="detail-integration-code" data-method="widget" tabindex="-1">Widget Forma3D</button>
              </div>
            </div>
          </li>
          <li class="guide-step" data-locked="true" data-requires-enabled>
            <span class="guide-step-number" aria-hidden="true">3</span>
            <div class="guide-step-body">
              <h3>Copiez le code</h3>
              <p>Collez-le dans la page produit de votre site. Pour un autre domaine, il doit être ajouté aux sites autorisés (<code>EMBED_ALLOWED_ORIGINS</code>).</p>
              <div class="code-block" id="detail-integration-code" role="tabpanel" aria-labelledby="tab-iframe">
                <div class="code-block-header"><span id="detail-code-label">HTML · IFrame</span><button class="copy-button" id="detail-copy-code" type="button">Copier</button></div>
                <pre><code id="detail-embed-code">Activez l’intégration pour générer le code.</code></pre>
              </div>
              <p class="guide-feedback" id="detail-integration-copy-feedback" role="status" aria-live="polite"></p>
            </div>
          </li>
          <li class="guide-step" data-locked="true" data-requires-enabled>
            <span class="guide-step-number" aria-hidden="true">4</span>
            <div class="guide-step-body">
              <h3>Aperçu</h3>
              <p>Voici ce que verront les visiteurs : la vraie page d’intégration, affichée dans un cadre de navigateur.</p>
              <div class="browser-frame">
                <div class="browser-bar"><span></span><span></span><span></span><code id="detail-preview-url">votre-boutique.fr/produit</code></div>
                <iframe id="detail-preview-frame" title="Aperçu de l’intégration du modèle" loading="lazy"></iframe>
              </div>
            </div>
          </li>
        </ol>
      </section>
      <p class="detail-error" id="detail-error" role="alert" hidden></p>
    </section>`;
}

// Titre de l'onglet du navigateur pour cette fiche.
export function titleFor(route) {
  return `Modèle ${route.id}`;
}

// Branche la fiche : chargement des données, vues 3D/photo/comparer, intégration, suppression.
// Renvoie une fonction de nettoyage (arrêt du minuteur), appelée en quittant la page.
export function mount(route) {
  const $ = (selector) => document.querySelector(selector);
  const modelViewer = $("#detail-model-viewer");
  const stage = $("#detail-stage");
  const skeleton = $("#detail-skeleton");
  const empty = $("#detail-empty");
  const error = $("#detail-error");
  const subtitle = $("#detail-subtitle");
  const name = $("#detail-name");
  const state = $("#detail-status");
  const category = $("#detail-category");
  const origin = $("#detail-origin");
  const date = $("#detail-date");
  const duration = $("#detail-duration");
  const download = $("#detail-download");
  const viewToggle = $("#detail-view-toggle");
  const stagePhoto = $("#detail-stage-photo");
  const sourceImage = $("#detail-source-image");
  const integration = $("#detail-integration");
  const integrationStatus = $("#detail-integration-status");
  const integrationToggle = $("#detail-integration-toggle");
  const embedCode = $("#detail-embed-code");
  const codeLabel = $("#detail-code-label");
  const codePanel = $("#detail-integration-code");
  const copyFeedback = $("#detail-integration-copy-feedback");
  const previewFrame = $("#detail-preview-frame");
  const previewUrl = $("#detail-preview-url");
  const enableStep = $("#guide-step-enable");
  const deleteButton = $("#detail-delete");
  const deleteFeedback = $("#detail-delete-feedback");
  const renameButton = $("#detail-rename");
  const renameForm = $("#detail-rename-form");
  const renameInput = $("#detail-rename-input");
  const renameSave = $("#detail-rename-save");
  const renameFeedback = $("#detail-rename-feedback");
  const categorySelect = $("#detail-category-select");
  const tabs = [...document.querySelectorAll(".tab[data-method]")];
  let pollTimer = null;
  // Vrai seulement si la fiche vient de l'historique en base (pas d'un exemple de démonstration).
  let storedInHistory = false;
  let generation = null;
  let model = null;
  let labels = [];
  let method = "iframe";
  let currentModelUrl = null;

  // Change l'affichage : « model » (3D), « photo » (photo source) ou « compare » (côte à côte).
  function setView(mode) {
    const previous = stage.dataset.view;
    stage.dataset.view = mode;
    stagePhoto.hidden = mode === "model";
    viewToggle.querySelectorAll("button[data-view]").forEach((button) => {
      button.setAttribute("aria-pressed", button.dataset.view === mode ? "true" : "false");
    });
    // Comparaison : modèle immobile face à la photo ; la rotation reprend en vue 3D seule.
    if (mode === "compare") modelViewer.removeAttribute("auto-rotate");
    else if (mode === "model") modelViewer.setAttribute("auto-rotate", "");
    if (previous !== mode && !modelViewer.hidden) refitCamera(modelViewer);
  }

  // Affiche un message d'erreur à la place du modèle.
  function showError(message) {
    empty.hidden = true;
    skeleton.hidden = true;
    modelViewer.hidden = true;
    error.textContent = message;
    error.hidden = false;
    subtitle.textContent = "Impossible d’afficher cette fiche.";
    name.textContent = "Modèle introuvable";
  }

  // Fabrique le code à coller sur un site : iframe vers /embed/{public_id}, ou balise du widget.
  function integrationSnippet() {
    const baseUrl = window.location.origin;
    const publicId = model.public_id;
    if (method === "widget") {
      return `<script src="${baseUrl}/static/widget.js?v=20261117-r2" defer></script>\n<forma3d-viewer model="${publicId}" height="480" auto-rotate></forma3d-viewer>`;
    }
    return `<iframe src="${baseUrl}/embed/${encodeURIComponent(publicId)}" title="Aperçu 3D du produit" width="100%" height="480" loading="lazy" style="border:0"></iframe>`;
  }

  // Met à jour les 4 étapes de l'intégration (interrupteur, méthode, code, aperçu) selon l'activation.
  function renderIntegration() {
    integration.hidden = !model?.public_id;
    if (!model?.public_id) return;
    const enabled = Boolean(model.embed_enabled);
    integrationToggle.setAttribute("aria-checked", String(enabled));
    integrationStatus.textContent = enabled
      ? "Activée : ce modèle peut être affiché sur les sites autorisés."
      : "Désactivée par défaut. Le modèle reste privé tant que vous ne l’activez pas.";
    enableStep.dataset.done = String(enabled);
    document.querySelectorAll("[data-requires-enabled]").forEach((step) => {
      step.dataset.locked = String(!enabled);
      step.setAttribute("aria-disabled", String(!enabled));
    });
    tabs.forEach((tab) => {
      const selected = tab.dataset.method === method;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      tab.disabled = !enabled;
    });
    codePanel.setAttribute("aria-labelledby", method === "widget" ? "tab-widget" : "tab-iframe");
    codeLabel.textContent = method === "widget" ? "HTML · Widget Forma3D" : "HTML · IFrame";
    $("#detail-copy-code").disabled = !enabled;
    if (enabled) {
      embedCode.textContent = integrationSnippet();
      const embedPath = `/embed/${encodeURIComponent(model.public_id)}`;
      if (previewFrame.getAttribute("src") !== embedPath) previewFrame.setAttribute("src", embedPath);
      previewUrl.textContent = `${window.location.host}${embedPath}`;
    } else {
      embedCode.textContent = "Activez l’intégration (étape 1) pour générer le code.";
      previewFrame.removeAttribute("src");
      previewUrl.textContent = "votre-boutique.fr/produit";
    }
  }

  // Remplit la fiche avec l'enregistrement reçu (état, catégorie, origine, dates) et affiche le modèle.
  function showGeneration(record, nextModel = null) {
    const displayName = nextModel?.name || record.filename || "Modèle";
    name.textContent = displayName;
    subtitle.textContent = nextModel
      ? "Examinez le modèle, comparez-le à la photo d’origine, puis téléchargez-le ou intégrez-le."
      : record.status === "FAILED"
        ? "La création n’a pas abouti. Aucun fichier n’est disponible."
        : "Le modèle est encore en cours de création.";
    state.textContent = record.status === "DONE" ? "Prêt" : record.status === "RUNNING" ? "Création en cours" : record.status === "PENDING" ? "En attente" : record.status === "FAILED" ? "Échec" : "Exemple disponible";
    category.textContent = labels.find((item) => item.slug === (nextModel?.category || record.category))?.label || nextModel?.category || record.category || "Non classée";
    const originLabels = { generated: "Généré par l’application", imported: "Importé", example: "Exemple du catalogue" };
    const exampleProvider = exampleProviders[route.id];
    origin.textContent = (originLabels[nextModel?.origin || record.origin] || "Origine inconnue")
      + (exampleProvider ? ` · ${exampleProvider}` : "");
    date.textContent = record.created_at ? formatLongDate(record.created_at) : "Non disponible pour cet exemple";
    // Pour les exemples, la durée affichée est celle mesurée lors des essais (étape 6), jamais estimée.
    const measured = Number.isFinite(record.duration_seconds) ? record.duration_seconds : exampleGenerationSeconds[route.id];
    duration.textContent = formatDuration(measured);
    error.hidden = true;
    renderIntegration();
    deleteButton.hidden = !storedInHistory || ["PENDING", "RUNNING"].includes(record.status);
    // Seuls les modèles enregistrés en base se renomment ; les exemples de démonstration sont fixes.
    renameButton.hidden = !storedInHistory || !renameForm.hidden;

    const modelUrl = nextModel?.model_url || record.model_url;
    if (modelUrl) {
      if (currentModelUrl !== modelUrl) {
        currentModelUrl = modelUrl;
        skeleton.hidden = false;
        modelViewer.src = modelUrl;
      }
      modelViewer.alt = `Modèle 3D : ${displayName}`;
      modelViewer.hidden = false;
      empty.hidden = true;
      download.href = modelUrl;
      download.download = nextModel?.filename || (record.filename ? record.filename.replace(/\.[^.]+$/, "") + ".glb" : "forma3d-modele.glb");
      download.hidden = false;
    } else {
      modelViewer.removeAttribute("src");
      modelViewer.hidden = true;
      skeleton.hidden = true;
      empty.textContent = record.status === "FAILED" ? "Aucun fichier 3D n’a été créé." : "Le modèle apparaîtra ici une fois prêt.";
      empty.hidden = false;
      download.hidden = true;
    }
    const photoUrl = nextModel
      ? nextModel.source_image_url
      : record.status === "DONE"
        ? `/models/${encodeURIComponent(record.id)}/source-image`
        : null;
    if (photoUrl) {
      if (sourceImage.getAttribute("src") !== photoUrl) sourceImage.src = photoUrl;
      viewToggle.hidden = false;
    } else {
      sourceImage.removeAttribute("src");
      viewToggle.hidden = true;
      setView("model");
    }
  }

  watchProductAppearance(modelViewer);
  modelViewer.addEventListener("load", () => { skeleton.hidden = true; });
  modelViewer.addEventListener("error", () => {
    skeleton.hidden = true;
    empty.textContent = "Le modèle n’a pas pu être affiché. Le téléchargement reste disponible.";
    empty.hidden = false;
  });

  viewToggle.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-view]");
    if (button) setView(button.dataset.view);
  });

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      method = tab.dataset.method;
      copyFeedback.textContent = "";
      renderIntegration();
    });
    tab.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
      const next = tabs[(tabs.indexOf(tab) + 1) % tabs.length];
      next.focus();
      next.click();
    });
  });

  $("#detail-copy-code").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    try {
      // navigator.clipboard : API du navigateur pour écrire dans le presse-papiers (bouton « Copier »).
      await navigator.clipboard.writeText(embedCode.textContent);
      button.dataset.copied = "true";
      button.textContent = "Copié ✓";
      copyFeedback.textContent = "Code copié. Collez-le dans la page produit de votre site.";
      window.setTimeout(() => { button.textContent = "Copier"; button.dataset.copied = "false"; }, 1800);
    } catch {
      const range = document.createRange();
      range.selectNodeContents(embedCode);
      window.getSelection()?.removeAllRanges();
      window.getSelection()?.addRange(range);
      copyFeedback.textContent = "La copie automatique est indisponible ; le code est sélectionné.";
    }
  });

  integrationToggle.addEventListener("click", async () => {
    if (!model?.public_id || integrationToggle.disabled) return;
    const enabled = !model.embed_enabled;
    integrationToggle.disabled = true;
    integrationStatus.textContent = "Mise à jour de l’autorisation…";
    try {
      const updated = await setModelIntegrationEnabled(model.id, enabled);
      model = { ...model, public_id: updated.public_id, embed_enabled: updated.embed_enabled };
      showGeneration(generation, model);
    } catch (toggleError) {
      integrationStatus.textContent = toggleError.message || "Impossible de modifier l’intégration.";
    } finally {
      integrationToggle.disabled = false;
    }
  });

  deleteButton.addEventListener("click", async () => {
    const displayName = name.textContent || "ce modèle";
    const embedWarning = model?.embed_enabled
      ? " L’intégration est activée : l’iframe ou le widget affiché sur vos sites cessera de fonctionner."
      : "";
    const confirmed = await confirmDialog({
      title: "Supprimer définitivement ce modèle ?",
      message: `« ${displayName} » : le modèle 3D et sa photo source seront effacés. Cette action est irréversible.${embedWarning}`,
      confirmLabel: "Supprimer définitivement",
      danger: true,
    });
    if (!confirmed) return;
    deleteButton.disabled = true;
    deleteFeedback.textContent = "Suppression en cours…";
    try {
      await deleteModel(route.id);
      if (pollTimer !== null) window.clearInterval(pollTimer);
      window.location.hash = "#/modeles";
    } catch (deleteError) {
      deleteFeedback.textContent = deleteError.message || "Impossible de supprimer ce modèle.";
      deleteButton.disabled = false;
    }
  });

  // Ouvre ou ferme le formulaire de renommage placé sous le nom.
  function setRenaming(open) {
    renameForm.hidden = !open;
    name.hidden = open;
    renameButton.hidden = open || !storedInHistory;
    if (open) {
      renameInput.value = name.textContent;
      fillCategorySelect();
      renameFeedback.textContent = "";
      renameInput.focus();
      renameInput.select();
    } else {
      renameButton.focus();
    }
  }

  // Remplit la liste des catégories actives et présélectionne celle du modèle.
  // Une catégorie désactivée encore portée par le modèle reste affichée pour ne pas la perdre.
  function fillCategorySelect() {
    const current = model?.category || generation?.category || "";
    const choices = labels.filter((item) => item.is_active || item.slug === current);
    categorySelect.replaceChildren(...choices.map((item) => {
      const option = document.createElement("option");
      option.value = item.slug;
      option.textContent = item.is_active ? item.label : `${item.label} (désactivée)`;
      option.selected = item.slug === current;
      return option;
    }));
  }

  renameButton.addEventListener("click", () => setRenaming(true));
  $("#detail-rename-cancel").addEventListener("click", () => setRenaming(false));
  renameForm.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setRenaming(false);
  });
  renameForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newName = renameInput.value.trim();
    if (!newName) {
      renameFeedback.textContent = "Le nom ne peut pas être vide.";
      return;
    }
    const newCategory = categorySelect.value;
    const nameChanged = newName !== name.textContent;
    const categoryChanged = Boolean(newCategory) && newCategory !== (model?.category || generation?.category);
    if (!nameChanged && !categoryChanged) {
      setRenaming(false);
      return;
    }
    renameSave.disabled = true;
    renameFeedback.textContent = "Enregistrement…";
    try {
      // Deux routes distinctes : on n'appelle que celle(s) dont la valeur a changé.
      if (nameChanged) generation = await renameModel(route.id, newName);
      if (categoryChanged) generation = await changeModelCategory(route.id, newCategory);
      // La galerie affiche le nom sans extension : on recalcule la même valeur pour la fiche.
      const displayName = generation.filename.replace(/\.[^.]+$/, "");
      if (model) model = { ...model, name: displayName, category: generation.category };
      setRenaming(false);
      showGeneration(generation, model);
      document.title = `${name.textContent} — Forma3D Studio`;
      renameFeedback.textContent = "Modifications enregistrées.";
    } catch (renameError) {
      renameFeedback.textContent = renameError.message || "Impossible d’enregistrer les modifications.";
    } finally {
      renameSave.disabled = false;
    }
  });

  // Charge la galerie, les catégories et l'état du modèle (GET /models/gallery, /categories, /models/{id}).
  async function load() {
    try {
      const [galleryResponse, categoryResponse] = await Promise.all([
        listGalleryModels(),
        listCategories(true).catch(() => ({ items: [] })),
      ]);
      model = (galleryResponse.items ?? []).find((item) => item.id === route.id) || null;
      labels = categoryResponse.items ?? [];
      try {
        generation = await getGenerationStatus(`/models/${encodeURIComponent(route.id)}`);
        storedInHistory = true;
      } catch (statusError) {
        if (!model) {
          showError(statusError.message.includes("Génération introuvable")
            ? "Ce modèle est introuvable. Il a peut-être été supprimé."
            : "Les informations de ce modèle ne sont pas disponibles.");
          return;
        }
        generation = { id: model.id, status: "DONE", filename: model.filename, category: model.category };
      }
      showGeneration(generation, model);
      document.title = `${name.textContent} — Forma3D Studio`;
      if (generation.status === "PENDING" || generation.status === "RUNNING") {
        pollTimer = window.setInterval(async () => {
          try {
            generation = await getGenerationStatus(`/models/${encodeURIComponent(route.id)}`);
            model = (await listGalleryModels()).items?.find((item) => item.id === route.id) || model;
            showGeneration(generation, model);
            if (!["PENDING", "RUNNING"].includes(generation.status)) window.clearInterval(pollTimer);
          } catch {
            window.clearInterval(pollTimer);
          }
        }, 2000);
      }
    } catch {
      showError("Impossible de charger les modèles pour le moment. Réessayez plus tard.");
    }
  }

  void load();
  return () => { if (pollTimer !== null) window.clearInterval(pollTimer); };
}
