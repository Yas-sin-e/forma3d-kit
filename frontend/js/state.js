/*
 * Rôle : conserve les données de session nécessaires entre les vues du studio.
 * Exécution : main.js met à jour ce petit état pendant l'envoi, le suivi et l'ouverture du viewer.
 */
export const appState = {
  selectedPhoto: null,
  isGenerating: false,
  generationStatus: "IDLE",
  generationStartedAt: null,
  elapsedSeconds: 0,
  selectedGalleryCategory: "all",
  currentStatusUrl: null,
  pollingTimer: null,
  clockTimer: null,
  pollingInFlight: false,
};

export function beginGeneration(photo) {
  appState.selectedPhoto = photo;
  appState.isGenerating = true;
  appState.generationStatus = "SENDING";
  appState.generationStartedAt = Date.now();
  appState.elapsedSeconds = 0;
  appState.currentStatusUrl = null;
}

export function updateGenerationStatus(status) {
  appState.generationStatus = status;
  appState.isGenerating = ["SENDING", "PENDING", "RUNNING"].includes(status);
}

export function updateElapsedSeconds() {
  if (appState.generationStartedAt === null) return 0;
  appState.elapsedSeconds = Math.max(0, Math.floor((Date.now() - appState.generationStartedAt) / 1000));
  return appState.elapsedSeconds;
}

export function stopGenerationTimers() {
  if (appState.pollingTimer !== null) {
    window.clearInterval(appState.pollingTimer);
    appState.pollingTimer = null;
  }
  if (appState.clockTimer !== null) {
    window.clearInterval(appState.clockTimer);
    appState.clockTimer = null;
  }
  appState.pollingInFlight = false;
}
