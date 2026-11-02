/*
 * Rôle : relie les vues du studio à l'état commun et aux fonctions HTTP de api.js.
 * Exécution : chargé comme module par frontend/index.html à chaque ouverture de la page.
 */
import { createGeneration, getGenerationStatus, getProviderHealth } from "./api.js";
import { appState, beginGeneration, stopGenerationTimers, updateElapsedSeconds, updateGenerationStatus } from "./state.js";
import { setupUploader } from "./views/uploader.js";
import { createProgressView } from "./views/progress.js";
import { setupViewer } from "./views/viewer.js";
import { setupGallery } from "./views/gallery.js";

const uploader = setupUploader(startGeneration);
const progress = createProgressView();
const viewer = setupViewer();
const progressPanel = document.querySelector("#progress-panel");
const providerBadge = document.querySelector("#provider-badge");
const providerLabel = document.querySelector("#provider-label");
const providerNotice = document.querySelector("#provider-notice");
const providerMessage = document.querySelector("#provider-message");
const openDemoButton = document.querySelector("#open-demo-model");
let providerCheckInFlight = false;

const offlineMessage = "Le serveur 3D (Colab) est arrêté ou son lien a expiré (72 h). Relance le notebook, copie la nouvelle ligne dans backend/.env, redémarre le serveur.";

function updateProgress(status, options = {}) {
  const elapsedSeconds = appState.generationStartedAt === null
    ? undefined
    : updateElapsedSeconds();
  progress.render(status, { ...options, elapsedSeconds });
}

function stopTracking() {
  stopGenerationTimers();
  appState.currentStatusUrl = null;
}

function showFailure(message, title = "La génération a échoué") {
  const elapsedSeconds = appState.generationStartedAt === null
    ? undefined
    : updateElapsedSeconds();
  stopTracking();
  updateGenerationStatus("FAILED");
  uploader.setBusy(false);
  progress.render("FAILED", {
    summary: title,
    detail: message,
    elapsedSeconds,
  });
}

function sameOriginPath(value) {
  const url = new URL(value, window.location.origin);
  if (url.origin !== window.location.origin) {
    throw new Error("Le serveur a renvoyé une adresse de modèle inattendue.");
  }
  return url.pathname + url.search;
}

async function applyStatus(data) {
  if (data.status === "PENDING" || data.status === "RUNNING") {
    updateGenerationStatus(data.status);
    updateProgress(data.status);
    return false;
  }

  if (data.status === "FAILED") {
    showFailure(data.error_message || "Le fournisseur n’a pas renvoyé de modèle.");
    return true;
  }

  if (data.status !== "DONE" || !data.model_url) {
    showFailure("Le serveur n’a pas fourni de lien vers un GLB terminé.", "Réponse du serveur incomplète");
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
  await gallery.reload();
  gallery.selectCategory(data.category);
  progress.render("DONE", {
    summary: "Modèle terminé",
    detail: "Le serveur a validé le GLB 2.0 et l’a rendu disponible dans le viewer.",
    elapsedSeconds: updateElapsedSeconds(),
  });
  return true;
}

async function refreshStatus() {
  if (!appState.currentStatusUrl || appState.pollingInFlight) return false;
  appState.pollingInFlight = true;
  try {
    const data = await getGenerationStatus(appState.currentStatusUrl);
    return await applyStatus(data);
  } catch (error) {
    showFailure(error.message, "Suivi interrompu");
    return true;
  } finally {
    appState.pollingInFlight = false;
  }
}

async function startGeneration(photo, category) {
  if (appState.isGenerating || !photo) return;
  stopTracking();
  beginGeneration(photo);
  viewer.clear();
  uploader.setBusy(true);
  progress.render("SENDING", { elapsedSeconds: 0 });
  appState.clockTimer = window.setInterval(() => {
    updateProgress(appState.generationStatus);
  }, 1000);

  try {
    const data = await createGeneration(photo, category);
    if (typeof data.status_url !== "string") {
      throw new Error("La réponse du serveur ne contient pas d’adresse de suivi.");
    }
    appState.currentStatusUrl = sameOriginPath(data.status_url);
    const terminal = await applyStatus(data);
    if (!terminal && appState.currentStatusUrl) {
      appState.pollingTimer = window.setInterval(() => {
        void refreshStatus();
      }, 1500);
    }
  } catch (error) {
    showFailure(error.message, "Impossible de lancer la génération");
  }
}

progressPanel.addEventListener("forma3d:retry", () => {
  const photo = uploader.getSelectedPhoto();
  const category = uploader.getSelectedCategory();
  if (photo && category && !appState.isGenerating) void startGeneration(photo, category);
});

const gallery = setupGallery((model) => {
  if (appState.isGenerating) {
    viewer.announce("Une génération est en cours. Attendez son résultat avant de changer le modèle affiché.");
    return;
  }
  try {
    const modelUrl = sameOriginPath(model.model_url);
    viewer.showModel({
      url: modelUrl,
      downloadUrl: modelUrl,
      filename: model.filename,
      source: "gallery",
      category: model.category,
      sourcePhoto: model.source_image_url ? sameOriginPath(model.source_image_url) : null,
    });
    viewer.announce("Modèle de démonstration réel ouvert : " + model.name + ".");
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
    document.querySelector("#viewer-stage").scrollIntoView({ behavior, block: "center" });
  } catch (error) {
    viewer.announce(error.message);
  }
});

async function refreshProviderHealth() {
  if (providerCheckInFlight) return;
  providerCheckInFlight = true;
  try {
    const health = await getProviderHealth();
    const status = ["ONLINE", "OFFLINE", "UNCONFIGURED"].includes(health.status)
      ? health.status
      : "OFFLINE";
    const available = status === "ONLINE";
    providerBadge.dataset.status = available ? "online" : status.toLowerCase();
    providerLabel.textContent = available
      ? "Serveur 3D : en ligne"
      : "Serveur 3D : hors ligne";
    providerNotice.hidden = available;
    providerMessage.textContent = status === "UNCONFIGURED"
      ? health.message || "Le serveur 3D n’est pas configuré dans backend/.env."
      : health.message || offlineMessage;
    uploader.setProviderAvailable(available);
  } catch {
    providerBadge.dataset.status = "offline";
    providerLabel.textContent = "Serveur 3D : hors ligne";
    providerNotice.hidden = false;
    providerMessage.textContent = offlineMessage;
    uploader.setProviderAvailable(false);
  } finally {
    providerCheckInFlight = false;
  }
}

openDemoButton.addEventListener("click", async () => {
  if (!await gallery.openFirstModel()) {
    providerMessage.textContent = "Aucun modèle réel de démonstration n’est disponible sur ce poste.";
    return;
  }
  document.querySelector("#viewer-stage").scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    block: "center",
  });
});

void refreshProviderHealth();
const providerHealthTimer = window.setInterval(() => {
  void refreshProviderHealth();
}, 30_000);
window.addEventListener("pagehide", () => window.clearInterval(providerHealthTimer));
