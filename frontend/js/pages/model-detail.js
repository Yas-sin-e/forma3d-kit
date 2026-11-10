/*
 * Rôle : charge une fiche produit par identifiant et présente son état, sa photo et son GLB.
 * Exécution : router.js monte cette page sur #/modeles/{id}, y compris pour signaler un identifiant inconnu.
 */
import { getGenerationStatus, listCategories, listGalleryModels } from "../api.js?v=20261110-11b-final";

export const title = "Fiche du modèle";

export function render(route) {
  const backHref = route.navKey === "examples" ? "#/exemples" : "#/modeles";
  const backLabel = route.navKey === "examples" ? "← Retour aux exemples" : "← Retour à Mes modèles";
  return `
    <section class="page-shell detail-page" aria-labelledby="page-title">
      <a class="back-link" href="${backHref}">${backLabel}</a>
      <div class="page-intro"><p class="eyebrow">Détail du produit</p><h1 class="page-title" id="page-title" tabindex="-1">Fiche du modèle</h1><p class="page-lead" id="detail-subtitle">Chargement du modèle…</p></div>
      <div class="detail-layout">
        <section class="panel detail-viewer-panel" aria-label="Aperçu 3D">
          <model-viewer id="detail-model-viewer" alt="Modèle 3D du produit" camera-controls touch-action="pan-y" interaction-prompt="none" environment-image="neutral" tone-mapping="neutral" shadow-intensity="0.72" shadow-softness="0.8" exposure="1.08" loading="eager" hidden></model-viewer>
          <div class="detail-empty" id="detail-empty" role="status">Chargement des informations…</div>
        </section>
        <aside class="panel detail-information" aria-labelledby="detail-name">
          <h2 id="detail-name">Informations</h2>
          <dl class="detail-facts">
            <div><dt>État</dt><dd id="detail-status">Chargement…</dd></div>
            <div><dt>Catégorie</dt><dd id="detail-category">—</dd></div>
            <div><dt>Origine</dt><dd id="detail-origin">—</dd></div>
            <div><dt>Date de création</dt><dd id="detail-date">—</dd></div>
            <div><dt>Durée</dt><dd id="detail-duration">—</dd></div>
          </dl>
          <a class="button button-primary detail-download" id="detail-download" href="#" download hidden>Télécharger le modèle</a>
          <figure class="detail-source-photo" id="detail-source-figure" hidden><figcaption>Photo d’origine</figcaption><img id="detail-source-image" alt="Photo d’origine du produit"></figure>
        </aside>
      </div>
      <p class="detail-error" id="detail-error" role="alert" hidden></p>
    </section>`;
}

export function titleFor(route) {
  return `Modèle ${route.id}`;
}

function formatDate(value) {
  if (!value) return "Date non disponible";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Date non disponible" : new Intl.DateTimeFormat("fr-FR", { dateStyle: "long", timeStyle: "short" }).format(date);
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "Non communiquée";
  const totalSeconds = Math.round(seconds);
  const minutes = Math.floor(totalSeconds / 60);
  const remainder = totalSeconds % 60;
  return minutes ? `${minutes} min ${remainder} s` : `${remainder} s`;
}

export function mount(route) {
  const modelViewer = document.querySelector("#detail-model-viewer");
  const empty = document.querySelector("#detail-empty");
  const error = document.querySelector("#detail-error");
  const subtitle = document.querySelector("#detail-subtitle");
  const name = document.querySelector("#detail-name");
  const state = document.querySelector("#detail-status");
  const category = document.querySelector("#detail-category");
  const origin = document.querySelector("#detail-origin");
  const date = document.querySelector("#detail-date");
  const duration = document.querySelector("#detail-duration");
  const download = document.querySelector("#detail-download");
  const sourceFigure = document.querySelector("#detail-source-figure");
  const sourceImage = document.querySelector("#detail-source-image");
  let pollTimer = null;
  let generation = null;

  function showError(message) {
    empty.hidden = true;
    modelViewer.hidden = true;
    error.textContent = message;
    error.hidden = false;
    subtitle.textContent = "Impossible d’afficher cette fiche.";
    name.textContent = "Modèle introuvable";
  }

  function showGeneration(record, model = null, labels = []) {
    const displayName = model?.name || record.filename || "Modèle";
    name.textContent = displayName;
    subtitle.textContent = model
      ? "Consultez le modèle et les informations de votre produit."
      : record.status === "FAILED"
        ? "La création n’a pas abouti. Aucun fichier n’est disponible."
        : "Le modèle est encore en cours de création.";
    state.textContent = record.status === "DONE" ? "Prêt" : record.status === "RUNNING" ? "Création en cours" : record.status === "PENDING" ? "En attente" : record.status === "FAILED" ? "Échec" : "Exemple disponible";
    category.textContent = labels.find((item) => item.slug === (model?.category || record.category))?.label || model?.category || record.category || "Non classée";
    const originLabels = { generated: "Généré par l’application", imported: "Importé", example: "Exemple" };
    origin.textContent = originLabels[model?.origin || record.origin] || "Origine inconnue";
    date.textContent = record.created_at ? formatDate(record.created_at) : "Date non disponible pour cet exemple";
    duration.textContent = formatDuration(record.duration_seconds);
    error.hidden = true;

    const modelUrl = model?.model_url || record.model_url;
    if (modelUrl) {
      modelViewer.src = modelUrl;
      modelViewer.alt = `Modèle 3D : ${displayName}`;
      modelViewer.hidden = false;
      empty.hidden = true;
      download.href = modelUrl;
      download.download = model?.filename || (record.filename ? record.filename.replace(/\.[^.]+$/, "") + ".glb" : "forma3d-modele.glb");
      download.hidden = false;
    } else {
      modelViewer.removeAttribute("src");
      modelViewer.hidden = true;
      empty.textContent = record.status === "FAILED" ? "Aucun fichier 3D n’a été créé." : "Le modèle apparaîtra ici une fois prêt.";
      empty.hidden = false;
      download.hidden = true;
    }
    const photoUrl = model
      ? model.source_image_url
      : record.status === "DONE"
        ? `/models/${encodeURIComponent(record.id)}/source-image`
        : null;
    if (photoUrl) {
      sourceImage.src = photoUrl;
      sourceFigure.hidden = false;
    } else {
      sourceImage.removeAttribute("src");
      sourceFigure.hidden = true;
    }
  }

  async function load() {
    try {
      const [galleryResponse, categoryResponse] = await Promise.all([
        listGalleryModels(),
        listCategories(true).catch(() => ({ items: [] })),
      ]);
      const model = (galleryResponse.items ?? []).find((item) => item.id === route.id) || null;
      const labels = categoryResponse.items ?? [];
      try {
        generation = await getGenerationStatus(`/models/${encodeURIComponent(route.id)}`);
      } catch (statusError) {
        if (!model) {
          showError(statusError.message.includes("Génération introuvable")
            ? "Ce modèle est introuvable. Il a peut-être été supprimé."
            : "Les informations de ce modèle ne sont pas disponibles.");
          return;
        }
        generation = { id: model.id, status: "DONE", filename: model.filename, category: model.category };
      }
      showGeneration(generation, model, labels);
      document.title = `${name.textContent} — Forma3D Studio`;
      if (generation.status === "PENDING" || generation.status === "RUNNING") {
        pollTimer = window.setInterval(async () => {
          try {
            generation = await getGenerationStatus(`/models/${encodeURIComponent(route.id)}`);
            const refreshed = (await listGalleryModels()).items?.find((item) => item.id === route.id) || model;
            showGeneration(generation, refreshed, labels);
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
