/*
 * Rôle : gère le verrou d'accès du Studio (connexion, session, déconnexion).
 * Exécution : router.js appelle isAuthenticated() avant chaque page ; login.js appelle login().
 *
 * IMPORTANT — solution TEMPORAIRE de démonstration :
 * le mot de passe est vérifié dans le navigateur. Toute personne qui lit ce fichier
 * peut le retrouver : ce n'est donc PAS une sécurité réelle, seulement un écran
 * d'accueil qui évite d'ouvrir le Studio par accident pendant une démonstration.
 * La version sûre prévue : POST /auth/login côté FastAPI (hash bcrypt du mot de passe
 * dans backend/.env, cookie HttpOnly). Cet appel sera alors ajouté dans api.js,
 * seul module autorisé à faire des requêtes HTTP, et login() ci-dessous l'utilisera.
 * Le Studio reste réservé à un usage local tant que ce backend n'existe pas.
 */

// Mot de passe par défaut, documenté dans docs/etapes/etape-16b.md. À remplacer par la vérification serveur.
const TEMPORARY_STUDIO_PASSWORD = "forma3d-demo";
const SESSION_KEY = "forma3d:session";
const NEXT_ROUTE_KEY = "forma3d:next-route";

function createSessionToken() {
  const bytes = new Uint8Array(16);
  window.crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function isAuthenticated() {
  try {
    return Boolean(window.sessionStorage.getItem(SESSION_KEY));
  } catch {
    return false;
  }
}

/* Simule la future route POST /auth/login ; renvoie une promesse pour garder la même signature. */
export async function login(password) {
  await new Promise((resolve) => window.setTimeout(resolve, 350));
  if (typeof password !== "string" || password !== TEMPORARY_STUDIO_PASSWORD) {
    throw new Error("Mot de passe incorrect. Vérifiez la saisie et réessayez.");
  }
  window.sessionStorage.setItem(SESSION_KEY, createSessionToken());
  document.body.dataset.auth = "member";
  window.dispatchEvent(new CustomEvent("forma3d:auth", { detail: { authenticated: true } }));
}

export function logout() {
  window.sessionStorage.removeItem(SESSION_KEY);
  document.body.dataset.auth = "guest";
  window.dispatchEvent(new CustomEvent("forma3d:auth", { detail: { authenticated: false } }));
  window.location.hash = "#/login";
}

/* Mémorise la page demandée avant la connexion pour y revenir ensuite. */
export function rememberNextRoute(hash) {
  if (!hash || hash.startsWith("#/login")) return;
  window.sessionStorage.setItem(NEXT_ROUTE_KEY, hash);
}

export function consumeNextRoute() {
  const next = window.sessionStorage.getItem(NEXT_ROUTE_KEY);
  window.sessionStorage.removeItem(NEXT_ROUTE_KEY);
  return next && next.startsWith("#/") && !next.startsWith("#/login") ? next : "#/accueil";
}
