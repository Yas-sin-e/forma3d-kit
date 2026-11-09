/*
 * Rôle : présente le parcours photo, la progression réelle et le viewer de création.
 * Exécution : router.js monte cette page sur #/creer et la conserve en mémoire de navigation.
 */
import { createGeneration, getGenerationStatus, listCategories } from "../api.js";
import { appState, beginGeneration, stopGenerationTimers, updateElapsedSeconds, updateGenerationStatus } from "../state.js";
import { setupUploader } from "../views/uploader.js";
import { createProgressView } from "../views/progress.js";
import { setupViewer } from "../views/viewer.js";
import { viewerMarkup } from "./viewer-markup.js";

export const title = "Créer";

export function render() {
  return `
    <section class="page-shell create-page">
      <div class="page-intro">
        <p class="eyebrow">Atelier produit</p>
        <h1 class="page-title" id="create-page-title" tabindex="-1">Créez votre modèle 3D</h1>
        <p class="page-lead">Ajoutez une photo de votre produit pour obtenir un aperçu 3D interactif.</p>
      </div>
      <section class="workspace" aria-label="Création et aperçu du produit">
        <aside class="control-column" aria-label="Photo et suivi">
          <form class="panel upload-panel" id="upload-form">
            <div class="section-heading">
              <span class="step-index" aria-hidden="true">01</span>
              <div><h2>Photo du produit</h2><p>Choisissez une image claire d’un seul objet.</p></div>
            </div>
            <input class="visually-hidden" id="photo-input" name="file" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp">
            <label class="drop-zone" id="drop-zone" for="photo-input" aria-describedby="format-note">
              <span class="drop-icon" aria-hidden="true">↑</span>
              <span class="drop-title">Glissez une photo ici</span>
              <span class="drop-divider">ou</span>
              <span class="button button-secondary">Choisir une photo</span>
              <span class="file-name" id="file-name">Aucun fichier sélectionné</span>
            </label>
            <p class="format-note" id="format-note">JPG, PNG ou WebP · 10 Mo maximum.</p>
            <div class="category-field">
              <label for="product-category">Catégorie du produit</label>
              <select class="category-select" id="product-category" name="category" required>
                <option value="" selected disabled>Choisir une catégorie</option>
              </select>
            </div>
            <p class="privacy-note">N’envoyez pas de visages ni de données personnelles. La photo peut être traitée par un service externe.</p>
            <p class="upload-feedback" id="upload-feedback" role="alert" hidden></p>
            <button class="button button-primary submit-button" id="submit-button" type="submit" disabled>
              <span class="button-label">Créer le modèle 3D</span><span aria-hidden="true">→</span>
            </button>
          </form>

          <aside class="service-unavailable-note" id="service-unavailable-note" hidden>
            <p>La création est momentanément indisponible. Vous pouvez parcourir les exemples.</p>
            <a class="button button-secondary" href="#/exemples">Voir les exemples</a>
            <details>
              <summary>Détails techniques</summary>
              <p id="technical-health-message">Le serveur 3D est indisponible.</p>
              <p>Le serveur temporaire Colab peut expirer. Pour le relancer, exécutez le notebook puis mettez à jour HF_SPACE_ID dans backend/.env.</p>
            </details>
          </aside>

          <details class="photo-guidance" aria-labelledby="photo-guidance-title">
            <summary id="photo-guidance-title">Conseils photo</summary>
            <div class="photo-guidance-content"><ul>
              <li>Photographiez un seul objet sur un fond uni.</li>
              <li>Choisissez une lumière douce et une vue de trois quarts.</li>
              <li>Faites occuper environ 70 % de l’image par l’objet.</li>
              <li>Utilisez une vraie photo, jamais une capture d’écran.</li>
            </ul></div>
          </details>

          <section class="panel progress-panel" id="progress-panel" aria-labelledby="progress-title" aria-busy="false">
            <div class="section-heading compact-heading">
              <span class="step-index" aria-hidden="true">02</span>
              <div><h2 id="progress-title">Suivi</h2><p id="progress-summary" role="status" aria-live="polite">Aucune création en cours.</p></div>
            </div>
            <ol class="progress-steps" id="progress-steps" aria-label="Étapes de création">
              <li class="progress-step" data-step="0"><span class="step-marker" aria-hidden="true">1</span><span>Photo envoyée</span></li>
              <li class="progress-step" data-step="1"><span class="step-marker" aria-hidden="true">2</span><span>En file</span></li>
              <li class="progress-step" data-step="2"><span class="step-marker" aria-hidden="true">3</span><span>Création du modèle</span></li>
              <li class="progress-step" data-step="3"><span class="step-marker" aria-hidden="true">4</span><span>Vérification du fichier</span></li>
              <li class="progress-step" data-step="4"><span class="step-marker" aria-hidden="true">5</span><span>Terminé</span></li>
            </ol>
            <div class="progress-meta"><span class="activity-indicator" id="activity-indicator" aria-hidden="true"></span><p id="progress-detail">Les états affichés viennent du serveur.</p></div>
            <p class="image-preparation-warning" id="image-preparation-warning" role="status" aria-live="polite" hidden></p>
            <p class="timing-note">La création peut prendre quelques minutes. Le délai dépend de la disponibilité du service.</p>
            <p class="elapsed-time" id="elapsed-time" hidden>Temps écoulé : <span id="elapsed-seconds">0</span> s</p>
            <button class="button button-secondary retry-button" id="retry-button" type="button" hidden>Réessayer avec cette photo</button>
            <a class="button button-secondary detail-result-link" id="model-detail-link" href="#" hidden>Ouvrir la fiche du modèle</a>
          </section>
        </aside>
        <div class="create-viewer-column">${viewerMarkup}</div>
      </section>
      <aside class="honesty-note"><span class="note-mark" aria-hidden="true">i</span><p>Modèle approximatif créé à partir d’une seule photo. Les dimensions et la géométrie ne sont pas garanties.</p></aside>
    </section>
  `;
}

function sameOriginPath(value) {
  const url = new URL(value, window.location.origin);
  if (url.origin !== window.location.origin) throw new Error("Le serveur a renvoyé une adresse inattendue.");
  return url.pathname + url.search;
}

export function mount() {
  const uploader = setupUploader(startGeneration);
  const progress = createProgressView();
  const viewer = setupViewer();
  const progressPanel = document.querySelector("#progress-panel");
  const warning = document.querySelector("#image-preparation-warning");
  const unavailable = document.querySelector("#service-unavailable-note");
  const technicalMessage = document.querySelector("#technical-health-message");
  const resultLink = document.querySelector("#model-detail-link");

  function updateProgress(status, options = {}) {
    const elapsedSeconds = appState.generationStartedAt === null ? undefined : updateElapsedSeconds();
    progress.render(status, { ...options, elapsedSeconds });
  }

  function stopTracking() {
    stopGenerationTimers();
    appState.currentStatusUrl = null;
  }

  function showFailure(message, titleText = "La création a échoué") {
    const elapsedSeconds = appState.generationStartedAt === null ? undefined : updateElapsedSeconds();
    stopTracking();
    updateGenerationStatus("FAILED");
    uploader.setBusy(false);
    progress.render("FAILED", { summary: titleText, detail: message, elapsedSeconds });
  }

  async function applyStatus(data) {
    warning.hidden = !data.image_warning;
    warning.textContent = data.image_warning
      ? `${data.image_warning} Conseil : choisissez une photo nette, bien éclairée et centrée sur un seul objet.`
      : "";
    if (data.status === "PENDING" || data.status === "RUNNING") {
      updateGenerationStatus(data.status);
      updateProgress(data.status);
      return false;
    }
    if (data.status === "FAILED") {
      showFailure("Nous n’avons pas pu créer ce modèle. Vérifiez la photo et réessayez.");
      return true;
    }
    if (data.status !== "DONE" || !data.model_url) {
      showFailure("Le serveur n’a pas fourni de fichier terminé.", "Réponse incomplète");
      return true;
    }

    const modelUrl = sameOriginPath(data.model_url);
    stopTracking();
    updateGenerationStatus("DONE");
    uploader.setBusy(false);
    viewer.showModel({
      url: modelUrl,
      downloadUrl: modelUrl,
      filename: data.filename,
      source: "generated",
      category: data.category,
      sourcePhoto: appState.selectedPhoto,
    });
    resultLink.href = `#/modeles/${encodeURIComponent(data.id)}`;
    resultLink.hidden = false;
    progress.render("DONE", { summary: "Votre modèle est prêt", detail: "Le fichier a été vérifié et peut être téléchargé.", elapsedSeconds: updateElapsedSeconds() });
    return true;
  }

  async function refreshStatus() {
    if (!appState.currentStatusUrl || appState.pollingInFlight) return false;
    appState.pollingInFlight = true;
    try {
      return await applyStatus(await getGenerationStatus(appState.currentStatusUrl));
    } catch (error) {
      showFailure("La mise à jour s’est interrompue. Vérifiez votre connexion puis réessayez.", "Suivi indisponible");
      return true;
    } finally {
      appState.pollingInFlight = false;
    }
  }

  async function startGeneration(photo, category) {
    if (appState.isGenerating || !photo) return;
    stopTracking();
    beginGeneration(photo);
    warning.hidden = true;
    warning.textContent = "";
    resultLink.hidden = true;
    viewer.clear();
    uploader.setBusy(true);
    progress.render("SENDING", { elapsedSeconds: 0 });
    appState.clockTimer = window.setInterval(() => updateProgress(appState.generationStatus), 1000);
    try {
      const data = await createGeneration(photo, category);
      if (typeof data.status_url !== "string") throw new Error("La réponse ne contient pas le suivi de la création.");
      appState.currentStatusUrl = sameOriginPath(data.status_url);
      const terminal = await applyStatus(data);
      if (!terminal && appState.currentStatusUrl) appState.pollingTimer = window.setInterval(() => void refreshStatus(), 1500);
    } catch (error) {
      showFailure("Impossible de lancer la création. Vérifiez la photo et réessayez.", "Création indisponible");
    }
  }

  function updateProviderHealth(event) {
    const health = event?.detail ?? appState.providerHealth;
    const online = health?.status === "ONLINE";
    unavailable.hidden = online;
    technicalMessage.textContent = health?.message || "Relancez le serveur 3D puis actualisez la page.";
    uploader.setProviderAvailable(online);
  }

  progressPanel.addEventListener("forma3d:retry", () => {
    const photo = uploader.getSelectedPhoto();
    const category = uploader.getSelectedCategory();
    if (photo && category && !appState.isGenerating) void startGeneration(photo, category);
  });
  window.addEventListener("forma3d:health", updateProviderHealth);
  updateProviderHealth();
  void listCategories(true).then((response) => uploader.setCategories(response.items ?? [])).catch((error) => uploader.setError(error.message));
}
