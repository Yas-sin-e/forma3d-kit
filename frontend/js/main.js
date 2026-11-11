/*
 * Rôle : démarre le Studio — état de connexion, routeur, bouton de déconnexion
 * et contrôle de disponibilité du serveur 3D partagé entre les pages.
 * Exécution : chargé une fois depuis index.html ; le contrôle de santé continue entre les pages.
 * Étape 5f : la session est demandée au serveur (GET /auth/me) avant le premier affichage.
 */
import { getProviderHealth } from "./api.js?v=20261112-c4";
import { logout, refreshSession } from "./auth.js?v=20261112-c4";
import { appState } from "./state.js?v=20261112-c4";
import { startRouter } from "./router.js?v=20261112-c4";

const providerBadge = document.querySelector("#provider-badge");
const providerLabel = document.querySelector("#provider-label");
const logoutButton = document.querySelector("#logout-button");
let providerCheckInFlight = false;

function publishHealth(status, message) {
  appState.providerHealth = { status, message };
  const online = status === "ONLINE";
  providerBadge.dataset.status = online ? "online" : status.toLowerCase();
  providerLabel.textContent = online ? "Serveur 3D : en ligne" : "Serveur 3D : hors ligne";
  providerBadge.title = online ? "La création de modèles est disponible." : message;
  window.dispatchEvent(new CustomEvent("forma3d:health", { detail: appState.providerHealth }));
}

async function refreshProviderHealth() {
  if (providerCheckInFlight) return;
  providerCheckInFlight = true;
  try {
    const health = await getProviderHealth();
    const status = ["ONLINE", "OFFLINE", "UNCONFIGURED"].includes(health.status) ? health.status : "OFFLINE";
    publishHealth(status, health.message || "Le serveur 3D est indisponible.");
  } catch {
    publishHealth("OFFLINE", "Le serveur 3D est arrêté ou son adresse temporaire a expiré.");
  } finally {
    providerCheckInFlight = false;
  }
}

logoutButton.addEventListener("click", () => void logout());

// Le routeur démarre après la réponse du serveur, pour éviter d'afficher une page puis de rediriger.
await refreshSession();
startRouter();
void refreshProviderHealth();
const providerHealthTimer = window.setInterval(() => void refreshProviderHealth(), 30_000);
window.addEventListener("pagehide", () => window.clearInterval(providerHealthTimer), { once: true });
