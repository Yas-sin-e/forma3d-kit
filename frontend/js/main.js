/*
 * Rôle : démarre le Studio — état de connexion, routeur, bouton de déconnexion
 * et contrôle de disponibilité du serveur 3D partagé entre les pages.
 * Exécution : chargé une fois depuis index.html ; le contrôle de santé continue entre les pages.
 * Étape 5f : la session est demandée au serveur (GET /auth/me) avant le premier affichage.
 */
// Importe la fonction qui interroge l'état du serveur 3D.
import { getProviderHealth } from "./api.js?v=20261117-r2";
// Importe la déconnexion et la vérification de session.
import { logout, refreshSession } from "./auth.js?v=20261117-r2";
// Importe l'état partagé entre les pages.
import { appState } from "./state.js?v=20261117-r2";
// Importe le démarrage du routeur.
import { startRouter } from "./router.js?v=20261117-r2";

// Élément HTML du badge « Serveur 3D ».
const providerBadge = document.querySelector("#provider-badge");
// Élément du texte du badge.
const providerLabel = document.querySelector("#provider-label");
// Bouton de déconnexion.
const logoutButton = document.querySelector("#logout-button");
// Vrai pendant une vérification en cours.
let providerCheckInFlight = false;

// Met à jour le badge « Serveur 3D » et diffuse l'état aux pages par l'événement « forma3d:health ».
// CustomEvent = événement personnalisé : les modules communiquent sans s'importer entre eux.
function publishHealth(status, message) {
  // Mémorise l'état dans l'état partagé.
  appState.providerHealth = { status, message };
  // Vrai si le serveur est en ligne.
  const online = status === "ONLINE";
  // Change l'attribut data-status (le CSS choisit la couleur).
  providerBadge.dataset.status = online ? "online" : status.toLowerCase();
  // Change le texte du badge.
  providerLabel.textContent = online ? "Serveur 3D : en ligne" : "Serveur 3D : hors ligne";
  // Infobulle : message de disponibilité ou explication de la panne.
  providerBadge.title = online ? "La création de modèles est disponible." : message;
  // Prévient toutes les pages du nouvel état.
  window.dispatchEvent(new CustomEvent("forma3d:health", { detail: appState.providerHealth }));
}

// Interroge l'état du serveur 3D (GET /health/provider) ; toute erreur est affichée comme « hors ligne ».
// providerCheckInFlight évite deux vérifications en même temps.
async function refreshProviderHealth() {
  // Une vérification est déjà en cours : on ne fait rien.
  if (providerCheckInFlight) return;
  // Marque la vérification comme en cours.
  providerCheckInFlight = true;
  // Essaie...
  try {
    // ...attend la réponse du serveur...
    const health = await getProviderHealth();
    // ...garde l'état s'il est connu, sinon « OFFLINE »...
    const status = ["ONLINE", "OFFLINE", "UNCONFIGURED"].includes(health.status) ? health.status : "OFFLINE";
    // ...et le publie avec son message.
    publishHealth(status, health.message || "Le serveur 3D est indisponible.");
  // Erreur réseau...
  } catch {
    // ...publiée comme « hors ligne ».
    publishHealth("OFFLINE", "Le serveur 3D est arrêté ou son adresse temporaire a expiré.");
  // Dans tous les cas...
  } finally {
    // ...la vérification est terminée.
    providerCheckInFlight = false;
  }
}

// Un clic sur « Déconnexion » lance la déconnexion (void = on n'attend pas le résultat).
logoutButton.addEventListener("click", () => void logout());

// Le routeur démarre après la réponse du serveur, pour éviter d'afficher une page puis de rediriger.
// « await » au niveau du module : la suite attend la réponse du serveur sur la session.
// Attend la réponse du serveur sur la session.
await refreshSession();
// Démarre le routeur (affiche la page demandée).
startRouter();
// Première vérification du serveur 3D.
void refreshProviderHealth();
// Revérifie toutes les 30 secondes.
const providerHealthTimer = window.setInterval(() => void refreshProviderHealth(), 30_000);
// Arrête la vérification quand on quitte la page.
window.addEventListener("pagehide", () => window.clearInterval(providerHealthTimer), { once: true });
