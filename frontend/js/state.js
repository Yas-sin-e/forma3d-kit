/*
 * Rôle : conserve les données de session nécessaires entre les vues du studio.
 * Exécution : main.js met à jour ce petit état pendant l'envoi, le suivi et l'ouverture du viewer.
 */
// Objet unique partagé par tous les modules (export = utilisable ailleurs).
export const appState = {
  // Photo choisie pour la génération en cours.
  selectedPhoto: null,
  // Vrai pendant une génération.
  isGenerating: false,
  // État de la génération (IDLE = aucune).
  generationStatus: "IDLE",
  // Heure de départ en millisecondes.
  generationStartedAt: null,
  // Secondes écoulées affichées par le chronomètre.
  elapsedSeconds: 0,
  // Catégorie choisie dans le filtre de la galerie.
  selectedGalleryCategory: "all",
  // URL de suivi de la génération en cours.
  currentStatusUrl: null,
  // Minuteur d'interrogation du serveur.
  pollingTimer: null,
  // Minuteur du chronomètre.
  clockTimer: null,
  // Vrai pendant une interrogation en cours.
  pollingInFlight: false,
  // Dernier état connu du serveur 3D.
  providerHealth: { status: "UNCONFIGURED", message: "Le serveur 3D n'est pas configuré." },
};

// Démarre le suivi d'une génération : mémorise la photo, l'heure de départ et l'état « SENDING ».
export function beginGeneration(photo) {
  // Mémorise la photo.
  appState.selectedPhoto = photo;
  // Une génération commence.
  appState.isGenerating = true;
  // État : envoi en cours.
  appState.generationStatus = "SENDING";
  // Heure de départ.
  appState.generationStartedAt = Date.now();
  // Remet le chronomètre à zéro.
  appState.elapsedSeconds = 0;
  // Pas encore d'URL de suivi.
  appState.currentStatusUrl = null;
}

// Enregistre le nouvel état et calcule si une génération est encore en cours.
export function updateGenerationStatus(status) {
  // Mémorise l'état.
  appState.generationStatus = status;
  // En cours si l'état est l'un de ces trois.
  appState.isGenerating = ["SENDING", "PENDING", "RUNNING"].includes(status);
}

// Calcule le temps écoulé depuis le départ, en secondes entières (pour le chronomètre).
export function updateElapsedSeconds() {
  // Pas de départ : 0 seconde.
  if (appState.generationStartedAt === null) return 0;
  // Calcule les secondes écoulées (jamais négatives).
  appState.elapsedSeconds = Math.max(0, Math.floor((Date.now() - appState.generationStartedAt) / 1000));
  // Renvoie la valeur.
  return appState.elapsedSeconds;
}

// Arrête les deux minuteurs (interrogation du serveur et chronomètre).
// setInterval/clearInterval : fonctions du navigateur pour répéter une action à intervalle régulier.
export function stopGenerationTimers() {
  // Si le minuteur d'interrogation existe...
  if (appState.pollingTimer !== null) {
    // ...on l'arrête...
    window.clearInterval(appState.pollingTimer);
    // ...et on l'oublie.
    appState.pollingTimer = null;
  }
  // Si le chronomètre existe...
  if (appState.clockTimer !== null) {
    // ...on l'arrête...
    window.clearInterval(appState.clockTimer);
    // ...et on l'oublie.
    appState.clockTimer = null;
  }
  // Plus aucune interrogation en cours.
  appState.pollingInFlight = false;
}
