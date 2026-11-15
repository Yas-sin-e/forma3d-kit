/*
 * Rôle : suit l'état de connexion de la propriétaire, vérifié par le serveur (étape 5f).
 * Exécution : main.js appelle refreshSession() avant de démarrer le routeur ; router.js lit
 * isAuthenticated() ; login.js appelle login() ; un 401 renvoyé par api.js ramène à #/login.
 *
 * Le mot de passe n'est jamais dans le navigateur : il est comparé côté serveur à
 * FORMA3D_OWNER_PASSWORD, et la session est un cookie HttpOnly signé (illisible en JavaScript).
 * Ce module ne garde qu'un indicateur en mémoire, rafraîchi par GET /auth/me.
 */
import { getSession, loginOwner, logoutOwner } from "./api.js?v=20261115-e1";

// sessionStorage : petit stockage du navigateur, propre à l'onglet et effacé à sa fermeture.
// On y garde seulement la page demandée avant la connexion, jamais un mot de passe ni un jeton.
const NEXT_ROUTE_KEY = "forma3d:next-route";
const SESSION_EXPIRED_KEY = "forma3d:session-expired";
let authenticated = false;
let passwordConfigured = true;

// Met à jour l'indicateur de connexion, l'attribut data-auth du <body> (le CSS masque ou montre le menu)
// et prévient les autres modules par un événement personnalisé « forma3d:auth ».
function setAuthenticated(value) {
  authenticated = value;
  document.body.dataset.auth = value ? "member" : "guest";
  window.dispatchEvent(new CustomEvent("forma3d:auth", { detail: { authenticated: value } }));
}

// Indique si la propriétaire est connectée, d'après la dernière réponse du serveur.
export function isAuthenticated() {
  return authenticated;
}

/* Indique si le serveur a un mot de passe configuré (sinon la connexion est impossible). */
export function isPasswordConfigured() {
  return passwordConfigured;
}

// Demande au serveur si la session est valide : GET /auth/me. Appelée au démarrage de la page.
// Le navigateur ne décide jamais seul : seul le serveur sait si le cookie est valide.
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

// Connexion : envoie le mot de passe (POST /auth/login) puis marque la session comme ouverte.
export async function login(password) {
  await loginOwner(password);
  setAuthenticated(true);
}

// Déconnexion : POST /auth/logout, puis retour à la page de connexion même si le serveur ne répond pas (finally).
export async function logout() {
  try {
    await logoutOwner();
  } finally {
    setAuthenticated(false);
    window.location.hash = "#/login";
  }
}

/* Vrai une seule fois après une expiration de session : la page de connexion l'annonce. */
export function consumeSessionExpired() {
  const expired = window.sessionStorage.getItem(SESSION_EXPIRED_KEY) === "1";
  window.sessionStorage.removeItem(SESSION_EXPIRED_KEY);
  return expired;
}

/* Mémorise la page demandée avant la connexion pour y revenir ensuite. */
export function rememberNextRoute(hash) {
  if (!hash || hash.startsWith("#/login")) return;
  window.sessionStorage.setItem(NEXT_ROUTE_KEY, hash);
}

// Renvoie la page mémorisée avant la connexion (une seule fois), sinon l'accueil.
// N'accepte qu'une adresse interne commençant par « #/ ».
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
  window.sessionStorage.setItem(SESSION_EXPIRED_KEY, "1");
  window.location.hash = "#/login";
});
