/*
 * Rôle : suit l'état de connexion de la propriétaire, vérifié par le serveur (étape 5f).
 * Exécution : main.js appelle refreshSession() avant de démarrer le routeur ; router.js lit
 * isAuthenticated() ; login.js appelle login() ; un 401 renvoyé par api.js ramène à #/login.
 *
 * Le mot de passe n'est jamais dans le navigateur : il est comparé côté serveur à
 * FORMA3D_OWNER_PASSWORD, et la session est un cookie HttpOnly signé (illisible en JavaScript).
 * Ce module ne garde qu'un indicateur en mémoire, rafraîchi par GET /auth/me.
 */
import { getSession, loginOwner, logoutOwner } from "./api.js?v=20261112-c4";

const NEXT_ROUTE_KEY = "forma3d:next-route";
let authenticated = false;
let passwordConfigured = true;

function setAuthenticated(value) {
  authenticated = value;
  document.body.dataset.auth = value ? "member" : "guest";
  window.dispatchEvent(new CustomEvent("forma3d:auth", { detail: { authenticated: value } }));
}

export function isAuthenticated() {
  return authenticated;
}

/* Indique si le serveur a un mot de passe configuré (sinon la connexion est impossible). */
export function isPasswordConfigured() {
  return passwordConfigured;
}

export async function refreshSession() {
  try {
    const session = await getSession();
    passwordConfigured = session.configured !== false;
    setAuthenticated(session.authenticated === true);
  } catch {
    setAuthenticated(false);
  }
  return authenticated;
}

export async function login(password) {
  await loginOwner(password);
  setAuthenticated(true);
}

export async function logout() {
  try {
    await logoutOwner();
  } finally {
    setAuthenticated(false);
    window.location.hash = "#/login";
  }
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

// Une route du Studio a répondu 401 (session expirée ou serveur redémarré) : retour à la connexion.
window.addEventListener("forma3d:unauthorized", () => {
  if (!authenticated) return;
  setAuthenticated(false);
  rememberNextRoute(window.location.hash);
  window.location.hash = "#/login";
});
