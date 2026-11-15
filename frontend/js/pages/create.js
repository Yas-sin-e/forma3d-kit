/*
 * Rôle : présente le parcours photo, la progression réelle et le viewer de création.
 * Exécution : router.js monte cette page sur #/creer et la conserve en mémoire de navigation.
 * Refonte : deux colonnes (40 % photo / 60 % viewer), suivi compact en dessous ;
 * le stepper en 3 étapes (redondant avec le suivi) et la note encadrée sont supprimés,
 * les conseils et détails techniques sont repliés en bas du formulaire.
 */
import { createGeneration, getGenerationStatus, listCategories } from "../api.js?v=20261115-e1";
import { appState, beginGeneration, stopGenerationTimers, updateElapsedSeconds, updateGenerationStatus } from "../state.js?v=20261115-e1";
import { setupUploader } from "../views/uploader.js?v=20261115-e1";
import { createProgressView } from "../views/progress.js?v=20261115-e1";
import { setupViewer } from "../views/viewer.js?v=20261115-e1";
import { viewerMarkup } from "./viewer-markup.js?v=20261115-e1";

export const title = "Créer";

export function render() {
  return `
    <section class="page-shell create-page">
      <div class="page-intro">
        <p class="eyebrow">Atelier produit</p>
        <h1 class="page-title" id="create-page-title" tabindex="-1">Créez votre modèle 3D</h1>
        <p class="page-lead">Déposez une photo de votre produit, choisissez sa catégorie : l’aperçu 3D apparaît à droite.</p>
      </div>
      <section class="workspace" aria-label="Création et aperçu du produit">
          <form class="panel upload-panel" id="upload-form" aria-labelledby="photo-category-title">
            <div class="section-heading"><h2 id="photo-category-title">Photo et catégorie</h2><p>Une photo nette, un seul objet, un fond uni.</p></div>
            <input class="visually-hidden" id="photo-input" name="file" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp">
            <label class="drop-zone" id="drop-zone" for="photo-input" aria-describedby="format-note">
              <img class="drop-preview" id="drop-preview" alt="" hidden>
              <span class="drop-icon" aria-hidden="true">+</span>
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
            <p class="upload-feedback" id="upload-feedback" role="alert" hidden></p>
            <div class="service-unavailable-note" id="service-unavailable-note" role="status" hidden>
              <span>Serveur 3D hors ligne : création momentanément indisponible</span><a href="#/exemples">Voir les exemples</a>
            </div>
            <button class="button button-primary submit-button" id="submit-button" type="submit" disabled>
              <span class="button-label">Créer le modèle 3D</span><span aria-hidden="true">→</span>
            </button>
            <p class="submit-reason" id="submit-reason" role="status" aria-live="polite" aria-atomic="true">Choisissez une photo pour activer la création.</p>
            <p class="privacy-note">N’envoyez pas de visages ni de données personnelles : la photo peut être traitée par un service externe.</p>
            <div class="create-help">
              <details class="photo-guidance" aria-labelledby="photo-guidance-title">
                <summary id="photo-guidance-title">Conseils photo</summary>
                <div class="photo-guidance-content"><ul>
                  <li>Photographiez un seul objet sur un fond uni.</li>
                  <li>Choisissez une lumière douce et une vue de trois quarts.</li>
                  <li>Faites occuper environ 70 % de l’image par l’objet.</li>
                  <li>Utilisez une vraie photo, jamais une capture d’écran.</li>
                </ul></div>
              </details>
              <details class="technical-details">
                <summary>Détails techniques</summary>
                <p id="technical-health-message">Le serveur 3D est indisponible.</p>
                <p>Le serveur temporaire Colab peut expirer. Pour le relancer, exécutez le notebook puis mettez à jour HF_SPACE_ID dans backend/.env.</p>
              </details>
            </div>
          </form>
          <div class="create-viewer-column">${viewerMarkup}</div>
      </section>
      <section class="panel progress-panel" id="progress-panel" aria-labelledby="progress-title" aria-busy="false">
        <div class="progress-content">
          <div class="progress-track-column">
            <div class="progress-title-row"><h2 id="progress-title">Suivi de création</h2></div>
            <div class="progress-scroll" tabindex="0" role="region" aria-label="Étapes de création, faites défiler horizontalement si nécessaire">
              <ol class="progress-steps" id="progress-steps" aria-label="Étapes renvoyées par le serveur">
                <li class="progress-step" data-step="0"><span class="step-marker" aria-hidden="true">1</span><span>Photo envoyée</span></li>
                <li class="progress-step" data-step="1"><span class="step-marker" aria-hidden="true">2</span><span>En file</span></li>
                <li class="progress-step" data-step="2"><span class="step-marker" aria-hidden="true">3</span><span>Création du modèle</span></li>
                <li class="progress-step" data-step="3"><span class="step-marker" aria-hidden="true">4</span><span>Validation du GLB</span></li>
                <li class="progress-step" data-step="4"><span class="step-marker" aria-hidden="true">5</span><span>Terminé</span></li>
              </ol>
            </div>
          </div>
          <div class="progress-output">
            <div class="progress-meta"><span class="activity-indicator" id="activity-indicator" aria-hidden="true"></span><div class="progress-live" role="status" aria-live="polite" aria-atomic="true"><p id="progress-summary">Aucune création en cours.</p><p id="progress-detail">Les états affichés viennent du serveur.</p></div></div>
            <p class="elapsed-time" id="elapsed-time" hidden>Temps écoulé : <span id="elapsed-seconds">0</span> s</p>
            <p class="image-preparation-warning" id="image-preparation-warning" role="status" aria-live="polite" hidden></p>
            <p class="timing-note">Le délai dépend de la disponibilité du service gratuit.</p>
            <button class="button button-secondary retry-button" id="retry-button" type="button" hidden>Réessayer avec cette photo</button>
            <a class="button button-primary detail-result-link" id="model-detail-link" href="#" hidden>Ouvrir la fiche du modèle →</a>
          </div>
        </div>
      </section>
    </section>
  `;
}

/* « 90 secondes » ou « 2 minutes » : délai lisible tiré de l'en-tête Retry-After. */
function formatWait(seconds) {
  if (seconds < 60) return `${seconds} seconde${seconds > 1 ? "s" : ""}`;
  const minutes = Math.ceil(seconds / 60);
  return `${minutes} minute${minutes > 1 ? "s" : ""}`;
}

/*
 * Traduit l'échec de l'envoi (POST /models) en titre + cause + action, sans jeton, chemin ni trace.
 * Codes réels du backend : 400 fichier vide ou nom invalide, 413 plus de 10 Mo, 415 format, type ou
 * contenu refusé (upload_validator.py), 422 catégorie inconnue ou désactivée, 401 session expirée.
 */
export function describeUploadError(error) {
  if (error instanceof TypeError) {
    return ["Studio injoignable", "Le Studio ne répond pas. Vérifiez que le serveur est lancé (scripts/dev.ps1) et votre connexion, puis réessayez."];
  }
  const detail = typeof error?.serverDetail === "string" ? error.serverDetail.trim() : "";
  switch (error?.status) {
    case 400:
      return ["Photo refusée", `${detail || "Le fichier envoyé n'est pas utilisable."} Choisissez une autre photo puis réessayez.`];
    case 413:
      return ["Photo trop lourde", "Votre photo dépasse 10 Mo. Réduisez-la ou choisissez une image plus légère."];
    case 415:
      return ["Format non accepté", `${detail || "Ce format de fichier n'est pas accepté."} Enregistrez la photo en JPG, PNG ou WebP avec un logiciel d'image (renommer le fichier ne suffit pas), puis réessayez.`];
    case 422:
      return ["Catégorie indisponible", `${detail || "La catégorie choisie n'est pas valide."} Choisissez une autre catégorie, ou réactivez-la dans Administration → Catégories.`];
    case 401:
      return ["Session expirée", "Votre session a expiré. Reconnectez-vous : la page de connexion va s'ouvrir."];
    case 429:
      return ["Trop de demandes", error.retryAfterSeconds
        ? `Trop de demandes en peu de temps. Réessayez dans ${formatWait(error.retryAfterSeconds)}.`
        : "Trop de demandes en peu de temps. Patientez un moment, puis réessayez."];
    case 500:
    case 502:
    case 503:
    case 504:
      return ["Erreur du serveur", "Le serveur a rencontré un problème. Réessayez dans un instant ; si cela continue, redémarrez le serveur."];
    default:
      return ["Création indisponible", "Impossible de lancer la création pour une raison inattendue. Réessayez ; si cela continue, redémarrez le serveur."];
  }
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
      // Le serveur fournit la vraie cause (quota, Space indisponible…), déjà nettoyée de tout secret.
      showFailure(data.error_message || "Nous n’avons pas pu créer ce modèle. Vérifiez la photo et réessayez.");
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
      // Cause exacte et action à faire ; pour 401, api.js renvoie en plus vers la page de connexion.
      const [titleText, message] = describeUploadError(error);
      showFailure(message, titleText);
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
