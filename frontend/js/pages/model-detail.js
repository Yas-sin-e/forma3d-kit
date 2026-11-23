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
// Importe les appels HTTP utilisés par la fiche.
import { deleteModel, getGenerationStatus, listCategories, listGalleryModels, renameModel, changeModelCategory, setModelIntegrationEnabled } from "../api.js?v=20261117-r2";
// Importe la fenêtre de confirmation.
import { confirmDialog } from "../views/confirm-dialog.js?v=20261117-r2";
// Importe les données des exemples et la mise en forme.
import { exampleGenerationSeconds, exampleProviders, formatDuration, formatLongDate } from "../format.js?v=20261117-r2";
// Importe le recadrage et la correction d'apparence.
import { refitCamera, watchProductAppearance } from "../views/model-appearance.js?v=20261117-r2";

// Titre de base de l'onglet.
export const title = "Fiche du modèle";

// Retourne le HTML de la fiche d'un modèle (viewer, informations, intégration en 4 étapes).
export function render(route) {
  // Lien de retour : vers les exemples ou vers Mes modèles.
  const backHref = route.navKey === "examples" ? "#/exemples" : "#/modeles";
  // Texte de ce lien.
  const backLabel = route.navKey === "examples" ? "← Retour aux exemples" : "← Retour à Mes modèles";
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - le lien de retour et l'introduction (sous-titre mis à jour au chargement) ;
  // - le panneau « Aperçu 3D » : bascule Vue 3D / Photo / Comparer, scène avec squelette, <model-viewer>, photo et message ;
  // - le panneau « Informations » : nom, bouton Modifier, formulaire de renommage (nom et catégorie) ;
  // - la liste des faits (état, catégorie, origine, date, durée), le bouton Télécharger et le bouton Supprimer ;
  // - le guide d'intégration en 4 étapes : interrupteur, onglets IFrame / Widget, code à copier, aperçu réel dans un cadre ;
  // - la zone d'erreur.
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
  // « Modèle <identifiant> ».
  return `Modèle ${route.id}`;
}

// Branche la fiche : chargement des données, vues 3D/photo/comparer, intégration, suppression.
// Renvoie une fonction de nettoyage (arrêt du minuteur), appelée en quittant la page.
export function mount(route) {
  // Raccourci : $("#id") = document.querySelector("#id").
  const $ = (selector) => document.querySelector(selector);
  // Viewer 3D de la fiche.
  const modelViewer = $("#detail-model-viewer");
  // Scène (data-view).
  const stage = $("#detail-stage");
  // Squelette de chargement.
  const skeleton = $("#detail-skeleton");
  // Message de la scène.
  const empty = $("#detail-empty");
  // Zone d'erreur.
  const error = $("#detail-error");
  // Sous-titre.
  const subtitle = $("#detail-subtitle");
  // Nom du modèle.
  const name = $("#detail-name");
  // État.
  const state = $("#detail-status");
  // Catégorie.
  const category = $("#detail-category");
  // Origine.
  const origin = $("#detail-origin");
  // Date de création.
  const date = $("#detail-date");
  // Durée de génération.
  const duration = $("#detail-duration");
  // Lien de téléchargement.
  const download = $("#detail-download");
  // Bascule Vue 3D / Photo / Comparer.
  const viewToggle = $("#detail-view-toggle");
  // Zone de la photo dans la scène.
  const stagePhoto = $("#detail-stage-photo");
  // Image de la photo source.
  const sourceImage = $("#detail-source-image");
  // Panneau d'intégration.
  const integration = $("#detail-integration");
  // Texte d'état de l'intégration.
  const integrationStatus = $("#detail-integration-status");
  // Interrupteur d'intégration.
  const integrationToggle = $("#detail-integration-toggle");
  // Code à copier.
  const embedCode = $("#detail-embed-code");
  // Libellé du bloc de code.
  const codeLabel = $("#detail-code-label");
  // Bloc de code (panneau des onglets).
  const codePanel = $("#detail-integration-code");
  // Message après copie.
  const copyFeedback = $("#detail-integration-copy-feedback");
  // Iframe d'aperçu.
  const previewFrame = $("#detail-preview-frame");
  // Adresse affichée dans le faux navigateur.
  const previewUrl = $("#detail-preview-url");
  // Étape 1 du guide.
  const enableStep = $("#guide-step-enable");
  // Bouton Supprimer.
  const deleteButton = $("#detail-delete");
  // Message de suppression.
  const deleteFeedback = $("#detail-delete-feedback");
  // Bouton Modifier.
  const renameButton = $("#detail-rename");
  // Formulaire de modification.
  const renameForm = $("#detail-rename-form");
  // Champ du nouveau nom.
  const renameInput = $("#detail-rename-input");
  // Bouton Enregistrer.
  const renameSave = $("#detail-rename-save");
  // Message de modification.
  const renameFeedback = $("#detail-rename-feedback");
  // Liste des catégories du formulaire.
  const categorySelect = $("#detail-category-select");
  // Onglets IFrame et Widget.
  const tabs = [...document.querySelectorAll(".tab[data-method]")];
  // Minuteur d'actualisation (pour une génération en cours).
  let pollTimer = null;
  // Vrai seulement si la fiche vient de l'historique en base (pas d'un exemple de démonstration).
  let storedInHistory = false;
  // Données de génération reçues du serveur.
  let generation = null;
  // Données de galerie du modèle.
  let model = null;
  // Catégories connues.
  let labels = [];
  // Méthode d'intégration choisie.
  let method = "iframe";
  // Adresse du GLB affichée.
  let currentModelUrl = null;

  // Change l'affichage : « model » (3D), « photo » (photo source) ou « compare » (côte à côte).
  function setView(mode) {
    // Mode précédent.
    const previous = stage.dataset.view;
    // data-view : le CSS dispose la scène.
    stage.dataset.view = mode;
    // Photo masquée en mode 3D seule.
    stagePhoto.hidden = mode === "model";
    // Pour chaque bouton de la bascule...
    viewToggle.querySelectorAll("button[data-view]").forEach((button) => {
      // ...marque celui du mode choisi.
      button.setAttribute("aria-pressed", button.dataset.view === mode ? "true" : "false");
    });
    // Comparaison : modèle immobile face à la photo ; la rotation reprend en vue 3D seule.
    // Comparer : arrête la rotation.
    if (mode === "compare") modelViewer.removeAttribute("auto-rotate");
    // Vue 3D : relance la rotation.
    else if (mode === "model") modelViewer.setAttribute("auto-rotate", "");
    // Le mode a changé et le viewer est visible : recadre.
    if (previous !== mode && !modelViewer.hidden) refitCamera(modelViewer);
  }

  // Affiche un message d'erreur à la place du modèle.
  // Masque le message de la scène.
  function showError(message) {
    // Masque le squelette.
    empty.hidden = true;
    // Masque le viewer.
    skeleton.hidden = true;
    // Texte de l'erreur.
    modelViewer.hidden = true;
    // Erreur visible.
    error.textContent = message;
    // Sous-titre d'échec.
    error.hidden = false;
    // Nom de repli.
    subtitle.textContent = "Impossible d’afficher cette fiche.";
    name.textContent = "Modèle introuvable";
  }

  // Fabrique le code à coller sur un site : iframe vers /embed/{public_id}, ou balise du widget.
  // Adresse réelle du serveur.
  function integrationSnippet() {
    // UUID public du modèle.
    const baseUrl = window.location.origin;
    // Méthode « widget »...
    const publicId = model.public_id;
    // ...balise du script et balise <forma3d-viewer>.
    if (method === "widget") {
      return `<script src="${baseUrl}/static/widget.js?v=20261117-r2" defer></script>\n<forma3d-viewer model="${publicId}" height="480" auto-rotate></forma3d-viewer>`;
    // Sinon : balise <iframe> vers /embed.
    }
    return `<iframe src="${baseUrl}/embed/${encodeURIComponent(publicId)}" title="Aperçu 3D du produit" width="100%" height="480" loading="lazy" style="border:0"></iframe>`;
  }

  // Met à jour les 4 étapes de l'intégration (interrupteur, méthode, code, aperçu) selon l'activation.
  // Panneau masqué si le modèle n'a pas d'UUID public.
  function renderIntegration() {
    // Pas d'UUID : arrêt.
    integration.hidden = !model?.public_id;
    // Vrai si l'intégration est activée.
    if (!model?.public_id) return;
    // État de l'interrupteur (lecteurs d'écran).
    const enabled = Boolean(model.embed_enabled);
    // Texte d'état...
    integrationToggle.setAttribute("aria-checked", String(enabled));
    // ...activée...
    integrationStatus.textContent = enabled
      // ...ou désactivée.
      ? "Activée : ce modèle peut être affiché sur les sites autorisés."
      // Étape 1 marquée comme faite ou non.
      : "Désactivée par défaut. Le modèle reste privé tant que vous ne l’activez pas.";
    // Pour chaque étape suivante...
    enableStep.dataset.done = String(enabled);
    // ...verrouillée si l'intégration est désactivée...
    document.querySelectorAll("[data-requires-enabled]").forEach((step) => {
      // ...et signalée comme indisponible.
      step.dataset.locked = String(!enabled);
      step.setAttribute("aria-disabled", String(!enabled));
    // Pour chaque onglet...
    });
    // ...vrai si c'est la méthode choisie...
    tabs.forEach((tab) => {
      // ...onglet sélectionné ou non...
      const selected = tab.dataset.method === method;
      // ...seul l'onglet sélectionné reçoit le focus au clavier...
      tab.setAttribute("aria-selected", String(selected));
      // ...désactivé si l'intégration est coupée.
      tab.tabIndex = selected ? 0 : -1;
      tab.disabled = !enabled;
    // Le bloc de code est relié à l'onglet choisi.
    });
    // Libellé du bloc de code.
    codePanel.setAttribute("aria-labelledby", method === "widget" ? "tab-widget" : "tab-iframe");
    // Bouton Copier désactivé si l'intégration est coupée.
    codeLabel.textContent = method === "widget" ? "HTML · Widget Forma3D" : "HTML · IFrame";
    // Intégration activée...
    $("#detail-copy-code").disabled = !enabled;
    // ...affiche le code...
    if (enabled) {
      // ...chemin de la page /embed...
      embedCode.textContent = integrationSnippet();
      // ...charge l'aperçu s'il a changé...
      const embedPath = `/embed/${encodeURIComponent(model.public_id)}`;
      // ...adresse affichée dans le faux navigateur.
      if (previewFrame.getAttribute("src") !== embedPath) previewFrame.setAttribute("src", embedPath);
      // Intégration désactivée...
      previewUrl.textContent = `${window.location.host}${embedPath}`;
    // ...texte d'invitation...
    } else {
      // ...vide l'aperçu...
      embedCode.textContent = "Activez l’intégration (étape 1) pour générer le code.";
      // ...adresse fictive.
      previewFrame.removeAttribute("src");
      previewUrl.textContent = "votre-boutique.fr/produit";
    }
  }

  // Remplit la fiche avec l'enregistrement reçu (état, catégorie, origine, dates) et affiche le modèle.
  // Nom affiché : celui de la galerie, sinon le nom de fichier.
  function showGeneration(record, nextModel = null) {
    // Affiche le nom.
    const displayName = nextModel?.name || record.filename || "Modèle";
    // Sous-titre selon la situation...
    name.textContent = displayName;
    // ...modèle disponible...
    subtitle.textContent = nextModel
      // ...échec...
      ? "Examinez le modèle, comparez-le à la photo d’origine, puis téléchargez-le ou intégrez-le."
      : record.status === "FAILED"
        // ...ou en cours.
        ? "La création n’a pas abouti. Aucun fichier n’est disponible."
        // Texte de l'état en français.
        : "Le modèle est encore en cours de création.";
    // Libellé de la catégorie (ou slug, ou « Non classée »).
    state.textContent = record.status === "DONE" ? "Prêt" : record.status === "RUNNING" ? "Création en cours" : record.status === "PENDING" ? "En attente" : record.status === "FAILED" ? "Échec" : "Exemple disponible";
    // Libellés des provenances.
    category.textContent = labels.find((item) => item.slug === (nextModel?.category || record.category))?.label || nextModel?.category || record.category || "Non classée";
    // Fournisseur connu pour un exemple.
    const originLabels = { generated: "Généré par l’application", imported: "Importé", example: "Exemple du catalogue" };
    // Origine affichée...
    const exampleProvider = exampleProviders[route.id];
    // ...avec le fournisseur s'il est connu.
    origin.textContent = (originLabels[nextModel?.origin || record.origin] || "Origine inconnue")
      // Date longue, ou texte de repli.
      + (exampleProvider ? ` · ${exampleProvider}` : "");
    date.textContent = record.created_at ? formatLongDate(record.created_at) : "Non disponible pour cet exemple";
    // Durée réelle, sinon durée mesurée pour un exemple.
    // Pour les exemples, la durée affichée est celle mesurée lors des essais (étape 6), jamais estimée.
    // Durée affichée.
    const measured = Number.isFinite(record.duration_seconds) ? record.duration_seconds : exampleGenerationSeconds[route.id];
    // Masque l'erreur.
    duration.textContent = formatDuration(measured);
    // Met à jour l'intégration.
    error.hidden = true;
    // Supprimer visible seulement pour un modèle en base et terminé.
    renderIntegration();
    deleteButton.hidden = !storedInHistory || ["PENDING", "RUNNING"].includes(record.status);
    // Modifier visible seulement pour un modèle en base, formulaire fermé.
    // Seuls les modèles enregistrés en base se renomment ; les exemples de démonstration sont fixes.
    renameButton.hidden = !storedInHistory || !renameForm.hidden;
    // Adresse du GLB.

    // Si elle existe...
    const modelUrl = nextModel?.model_url || record.model_url;
    // ...et a changé...
    if (modelUrl) {
      // ...on la mémorise...
      if (currentModelUrl !== modelUrl) {
        // ...on montre le squelette...
        currentModelUrl = modelUrl;
        // ...et on charge le modèle.
        skeleton.hidden = false;
        modelViewer.src = modelUrl;
      // Texte alternatif.
      }
      // Viewer visible.
      modelViewer.alt = `Modèle 3D : ${displayName}`;
      // Message masqué.
      modelViewer.hidden = false;
      // Lien de téléchargement.
      empty.hidden = true;
      // Nom proposé, toujours en .glb.
      download.href = modelUrl;
      // Lien visible.
      download.download = nextModel?.filename || (record.filename ? record.filename.replace(/\.[^.]+$/, "") + ".glb" : "forma3d-modele.glb");
      // Pas de GLB...
      download.hidden = false;
    // ...retire le modèle...
    } else {
      // ...masque le viewer...
      modelViewer.removeAttribute("src");
      // ...masque le squelette...
      modelViewer.hidden = true;
      // ...message selon l'état...
      skeleton.hidden = true;
      // ...affiché...
      empty.textContent = record.status === "FAILED" ? "Aucun fichier 3D n’a été créé." : "Le modèle apparaîtra ici une fois prêt.";
      // ...téléchargement masqué.
      empty.hidden = false;
      download.hidden = true;
    // Adresse de la photo source...
    }
    // ...celle de la galerie...
    const photoUrl = nextModel
      // ...sinon, si terminé...
      ? nextModel.source_image_url
      // ...celle de la génération...
      : record.status === "DONE"
        // ...sinon aucune.
        ? `/models/${encodeURIComponent(record.id)}/source-image`
        // Photo disponible...
        : null;
    // ...charge-la si elle a changé...
    if (photoUrl) {
      // ...bascule visible.
      if (sourceImage.getAttribute("src") !== photoUrl) sourceImage.src = photoUrl;
      // Sinon...
      viewToggle.hidden = false;
    // ...retire la photo...
    } else {
      // ...masque la bascule...
      sourceImage.removeAttribute("src");
      // ...revient à la vue 3D.
      viewToggle.hidden = true;
      setView("model");
    }
  }
  // Branche la correction d'apparence.

  // Modèle chargé : masque le squelette.
  watchProductAppearance(modelViewer);
  // Erreur d'affichage...
  modelViewer.addEventListener("load", () => { skeleton.hidden = true; });
  // ...masque le squelette...
  modelViewer.addEventListener("error", () => {
    // ...message...
    skeleton.hidden = true;
    // ...affiché.
    empty.textContent = "Le modèle n’a pas pu être affiché. Le téléchargement reste disponible.";
    empty.hidden = false;
  });
  // Clic dans la bascule...

  // ...bouton visé...
  viewToggle.addEventListener("click", (event) => {
    // ...change le mode.
    const button = event.target.closest("button[data-view]");
    if (button) setView(button.dataset.view);
  });
  // Pour chaque onglet...

  // ...au clic...
  tabs.forEach((tab) => {
    // ...mémorise la méthode...
    tab.addEventListener("click", () => {
      // ...efface le message de copie...
      method = tab.dataset.method;
      // ...et met à jour l'intégration.
      copyFeedback.textContent = "";
      renderIntegration();
    // Au clavier...
    });
    // ...seules les flèches gauche et droite comptent...
    tab.addEventListener("keydown", (event) => {
      // ...onglet suivant (en boucle)...
      if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
      // ...focus dessus...
      const next = tabs[(tabs.indexOf(tab) + 1) % tabs.length];
      // ...et sélection.
      next.focus();
      next.click();
    });
  });
  // Bouton Copier le code...

  // ...le bouton cliqué...
  $("#detail-copy-code").addEventListener("click", async (event) => {
    // ...essaie...
    const button = event.currentTarget;
    try {
      // ...de copier le code...
      // navigator.clipboard : API du navigateur pour écrire dans le presse-papiers (bouton « Copier »).
      // ...marque l'état « copié »...
      await navigator.clipboard.writeText(embedCode.textContent);
      // ...confirme sur le bouton...
      button.dataset.copied = "true";
      // ...message d'aide...
      button.textContent = "Copié ✓";
      // ...remet le texte après 1,8 seconde.
      copyFeedback.textContent = "Code copié. Collez-le dans la page produit de votre site.";
      // Copie refusée...
      window.setTimeout(() => { button.textContent = "Copier"; button.dataset.copied = "false"; }, 1800);
    // ...crée une sélection...
    } catch {
      // ...qui contient le code...
      const range = document.createRange();
      // ...efface l'ancienne sélection...
      range.selectNodeContents(embedCode);
      // ...sélectionne le code...
      window.getSelection()?.removeAllRanges();
      // ...et explique quoi faire.
      window.getSelection()?.addRange(range);
      copyFeedback.textContent = "La copie automatique est indisponible ; le code est sélectionné.";
    }
  });
  // Clic sur l'interrupteur...

  // ...pas d'UUID ou déjà en cours : arrêt...
  integrationToggle.addEventListener("click", async () => {
    // ...nouvel état demandé...
    if (!model?.public_id || integrationToggle.disabled) return;
    // ...désactive l'interrupteur...
    const enabled = !model.embed_enabled;
    // ...message d'attente...
    integrationToggle.disabled = true;
    // ...essaie...
    integrationStatus.textContent = "Mise à jour de l’autorisation…";
    // ...d'enregistrer l'activation...
    try {
      // ...met à jour les données locales...
      const updated = await setModelIntegrationEnabled(model.id, enabled);
      // ...et réaffiche la fiche.
      model = { ...model, public_id: updated.public_id, embed_enabled: updated.embed_enabled };
      // Erreur...
      showGeneration(generation, model);
    // ...message affiché.
    } catch (toggleError) {
      // Dans tous les cas...
      integrationStatus.textContent = toggleError.message || "Impossible de modifier l’intégration.";
    // ...réactive l'interrupteur.
    } finally {
      integrationToggle.disabled = false;
    }
  });
  // Clic sur Supprimer...

  // ...nom affiché...
  deleteButton.addEventListener("click", async () => {
    // ...avertissement si l'intégration est activée...
    const displayName = name.textContent || "ce modèle";
    const embedWarning = model?.embed_enabled
      ? " L’intégration est activée : l’iframe ou le widget affiché sur vos sites cessera de fonctionner."
      // ...demande une confirmation...
      : "";
    // ...titre...
    const confirmed = await confirmDialog({
      // ...explication...
      title: "Supprimer définitivement ce modèle ?",
      // ...texte du bouton...
      message: `« ${displayName} » : le modèle 3D et sa photo source seront effacés. Cette action est irréversible.${embedWarning}`,
      // ...style rouge.
      confirmLabel: "Supprimer définitivement",
      danger: true,
    // Annulé : arrêt.
    });
    // Désactive le bouton.
    if (!confirmed) return;
    // Message d'attente.
    deleteButton.disabled = true;
    // Essaie...
    deleteFeedback.textContent = "Suppression en cours…";
    // ...de supprimer...
    try {
      // ...arrête l'actualisation...
      await deleteModel(route.id);
      // ...et retourne à Mes modèles.
      if (pollTimer !== null) window.clearInterval(pollTimer);
      // Erreur...
      window.location.hash = "#/modeles";
    // ...message affiché...
    } catch (deleteError) {
      // ...bouton réactivé.
      deleteFeedback.textContent = deleteError.message || "Impossible de supprimer ce modèle.";
      deleteButton.disabled = false;
    }
  });

  // Ouvre ou ferme le formulaire de renommage placé sous le nom.
  // Formulaire visible ou non.
  function setRenaming(open) {
    // Nom masqué pendant la modification.
    renameForm.hidden = !open;
    // Bouton Modifier masqué pendant la modification.
    name.hidden = open;
    // Ouverture...
    renameButton.hidden = open || !storedInHistory;
    // ...préremplit le nom...
    if (open) {
      // ...remplit la liste des catégories...
      renameInput.value = name.textContent;
      // ...efface l'ancien message...
      fillCategorySelect();
      // ...focus sur le champ...
      renameFeedback.textContent = "";
      // ...et sélectionne le texte.
      renameInput.focus();
      // Fermeture...
      renameInput.select();
    // ...focus sur le bouton Modifier.
    } else {
      renameButton.focus();
    }
  }

  // Remplit la liste des catégories actives et présélectionne celle du modèle.
  // Une catégorie désactivée encore portée par le modèle reste affichée pour ne pas la perdre.
  // Catégorie actuelle du modèle.
  function fillCategorySelect() {
    // Catégories actives, plus la catégorie actuelle même si elle est désactivée.
    const current = model?.category || generation?.category || "";
    // Remplace les options...
    const choices = labels.filter((item) => item.is_active || item.slug === current);
    // ...crée une option...
    categorySelect.replaceChildren(...choices.map((item) => {
      // ...valeur : le slug...
      const option = document.createElement("option");
      // ...texte : le libellé (avec « désactivée » si besoin)...
      option.value = item.slug;
      // ...sélectionnée si c'est la catégorie actuelle...
      option.textContent = item.is_active ? item.label : `${item.label} (désactivée)`;
      // ...et la renvoie.
      option.selected = item.slug === current;
      return option;
    }));
  }
  // Bouton Modifier : ouvre le formulaire.

  // Bouton Annuler : le ferme.
  renameButton.addEventListener("click", () => setRenaming(true));
  // Au clavier dans le formulaire...
  $("#detail-rename-cancel").addEventListener("click", () => setRenaming(false));
  // ...Échap le ferme.
  renameForm.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setRenaming(false);
  // À l'envoi du formulaire...
  });
  // ...empêche le rechargement...
  renameForm.addEventListener("submit", async (event) => {
    // ...nouveau nom sans espaces autour...
    event.preventDefault();
    // ...vide...
    const newName = renameInput.value.trim();
    // ...message...
    if (!newName) {
      // ...et arrêt.
      renameFeedback.textContent = "Le nom ne peut pas être vide.";
      return;
    // Nouvelle catégorie.
    }
    // Vrai si le nom a changé.
    const newCategory = categorySelect.value;
    // Vrai si la catégorie a changé.
    const nameChanged = newName !== name.textContent;
    // Rien n'a changé...
    const categoryChanged = Boolean(newCategory) && newCategory !== (model?.category || generation?.category);
    // ...ferme le formulaire...
    if (!nameChanged && !categoryChanged) {
      // ...et arrêt.
      setRenaming(false);
      return;
    // Désactive Enregistrer.
    }
    // Message d'attente.
    renameSave.disabled = true;
    // Essaie...
    renameFeedback.textContent = "Enregistrement…";
    try {
      // ...de renommer si besoin...
      // Deux routes distinctes : on n'appelle que celle(s) dont la valeur a changé.
      // ...et de changer la catégorie si besoin.
      if (nameChanged) generation = await renameModel(route.id, newName);
      if (categoryChanged) generation = await changeModelCategory(route.id, newCategory);
      // Nom sans extension.
      // La galerie affiche le nom sans extension : on recalcule la même valeur pour la fiche.
      // Met à jour les données de galerie locales.
      const displayName = generation.filename.replace(/\.[^.]+$/, "");
      // Ferme le formulaire.
      if (model) model = { ...model, name: displayName, category: generation.category };
      // Réaffiche la fiche.
      setRenaming(false);
      // Met à jour le titre de l'onglet.
      showGeneration(generation, model);
      // Message de succès.
      document.title = `${name.textContent} — Forma3D Studio`;
      // Erreur...
      renameFeedback.textContent = "Modifications enregistrées.";
    // ...message affiché.
    } catch (renameError) {
      // Dans tous les cas...
      renameFeedback.textContent = renameError.message || "Impossible d’enregistrer les modifications.";
    // ...réactive Enregistrer.
    } finally {
      renameSave.disabled = false;
    }
  });

  // Charge la galerie, les catégories et l'état du modèle (GET /models/gallery, /categories, /models/{id}).
  // Essaie...
  async function load() {
    // ...de charger en parallèle...
    try {
      // ...la galerie...
      const [galleryResponse, categoryResponse] = await Promise.all([
        // ...et toutes les catégories (liste vide en cas d'échec).
        listGalleryModels(),
        listCategories(true).catch(() => ({ items: [] })),
      // Cherche le modèle dans la galerie.
      ]);
      // Garde les catégories.
      model = (galleryResponse.items ?? []).find((item) => item.id === route.id) || null;
      // Essaie...
      labels = categoryResponse.items ?? [];
      // ...de lire la génération en base...
      try {
        // ...elle existe : modèle enregistré.
        generation = await getGenerationStatus(`/models/${encodeURIComponent(route.id)}`);
        // Pas en base...
        storedInHistory = true;
      // ...et pas dans la galerie...
      } catch (statusError) {
        // ...message adapté...
        if (!model) {
          showError(statusError.message.includes("Génération introuvable")
            ? "Ce modèle est introuvable. Il a peut-être été supprimé."
            // ...et arrêt.
            : "Les informations de ce modèle ne sont pas disponibles.");
          return;
        // Exemple du catalogue : données construites à partir de la galerie.
        }
        generation = { id: model.id, status: "DONE", filename: model.filename, category: model.category };
      // Affiche la fiche.
      }
      // Met à jour le titre de l'onglet.
      showGeneration(generation, model);
      // Génération en cours...
      document.title = `${name.textContent} — Forma3D Studio`;
      // ...actualise toutes les 2 secondes...
      if (generation.status === "PENDING" || generation.status === "RUNNING") {
        // ...essaie...
        pollTimer = window.setInterval(async () => {
          // ...de relire la génération...
          try {
            // ...et la galerie...
            generation = await getGenerationStatus(`/models/${encodeURIComponent(route.id)}`);
            // ...réaffiche...
            model = (await listGalleryModels()).items?.find((item) => item.id === route.id) || model;
            // ...et arrête quand le travail est fini.
            showGeneration(generation, model);
            // Erreur...
            if (!["PENDING", "RUNNING"].includes(generation.status)) window.clearInterval(pollTimer);
          // ...arrête l'actualisation.
          } catch {
            window.clearInterval(pollTimer);
          }
        }, 2000);
      // Erreur de chargement...
      }
    // ...message affiché.
    } catch {
      showError("Impossible de charger les modèles pour le moment. Réessayez plus tard.");
    }
  }
  // Lance le chargement.

  // Fonction de nettoyage : arrête l'actualisation en quittant la page.
  void load();
  return () => { if (pollTimer !== null) window.clearInterval(pollTimer); };
}
