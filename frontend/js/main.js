/*
 * Rôle : démarre le routeur et partage l'état de disponibilité du serveur 3D.
 * Exécution : chargé une fois depuis index.html ; le contrôle de santé continue entre les pages.
 */
import { getProviderHealth } from "./api.js?v=20261110-11b-final";
import { appState } from "./state.js?v=20261110-11b-final";
import { startRouter } from "./router.js?v=20261110-11b-final";

const providerBadge = document.querySelector("#provider-badge");
const providerLabel = document.querySelector("#provider-label");
let providerCheckInFlight = false;

function publishHealth(status, message) {
  appState.providerHealth = { status, message };
  const online = status === "ONLINE";
  providerBadge.dataset.status = online ? "online" : status.toLowerCase();
  providerLabel.textContent = online ? "Serveur 3D : en ligne" : "Serveur 3D : hors ligne";
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

startRouter();
void refreshProviderHealth();
const providerHealthTimer = window.setInterval(() => void refreshProviderHealth(), 30_000);
window.addEventListener("pagehide", () => window.clearInterval(providerHealthTimer), { once: true });
