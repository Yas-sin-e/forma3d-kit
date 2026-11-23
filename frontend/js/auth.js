/*
 * Rôle : suit l'état de connexion de la propriétaire, vérifié par le serveur (étape 5f).
 * Exécution : main.js appelle refreshSession() avant de démarrer le routeur ; router.js lit
 * isAuthenticated() ; login.js appelle login() ; un 401 renvoyé par api.js ramène à #/login.
 *
 * Le mot de passe n'est jamais dans le navigateur : il est comparé côté serveur à
 * FORMA3D_OWNER_PASSWORD, et la session est un cookie HttpOnly signé (illisible en JavaScript).
 * Ce module ne garde qu'un indicateur en mémoire, rafraîchi par GET /auth/me.
 */
// Importe les appels HTTP de session.
import { getSession, loginOwner, logoutOwner } from "./api.js?v=20261117-r2";

// sessionStorage : petit stockage du navigateur, propre à l'onglet et effacé à sa fermeture.
// On y garde seulement la page demandée avant la connexion, jamais un mot de passe ni un jeton.
// Clé de stockage de la page demandée avant la connexion.
const NEXT_ROUTE_KEY = "forma3d:next-route";
// Clé de stockage de l'indicateur « session expirée ».
const SESSION_EXPIRED_KEY = "forma3d:session-expired";
// Indicateur de connexion en mémoire.
let authenticated = false;
// Vrai si le serveur a un mot de passe configuré.
let passwordConfigured = true;

// Met à jour l'indicateur de connexion, l'attribut data-auth du <body> (le CSS masque ou montre le menu)
// et prévient les autres modules par un événement personnalisé « forma3d:auth ».
function setAuthenticated(value) {
  // Mémorise la valeur.
  authenticated = value;
  // « member » ou « guest » sur le <body>.
  document.body.dataset.auth = value ? "member" : "guest";
  // Prévient les autres modules.
  window.dispatchEvent(new CustomEvent("forma3d:auth", { detail: { authenticated: value } }));
}

// Indique si la propriétaire est connectée, d'après la dernière réponse du serveur.
export function isAuthenticated() {
  // Renvoie l'indicateur.
  return authenticated;
}

/* Indique si le serveur a un mot de passe configuré (sinon la connexion est impossible). */
export function isPasswordConfigured() {
  // Renvoie l'indicateur.
  return passwordConfigured;
}

// Demande au serveur si la session est valide : GET /auth/me. Appelée au démarrage de la page.
// Le navigateur ne décide jamais seul : seul le serveur sait si le cookie est valide.
export async function refreshSession() {
  // Essaie...
  try {
    // ...demande la session au serveur...
    const session = await getSession();
    // ...configuré sauf si le serveur dit explicitement non...
    passwordConfigured = session.configured !== false;
    // ...connectée seulement si le serveur répond vrai.
    setAuthenticated(session.authenticated === true);
  // Erreur réseau...
  } catch {
    // ...considérée comme non connectée.
    setAuthenticated(false);
  }
  // Renvoie l'état final.
  return authenticated;
}

// Connexion : envoie le mot de passe (POST /auth/login) puis marque la session comme ouverte.
export async function login(password) {
  // Envoie le mot de passe (une erreur interrompt la fonction).
  await loginOwner(password);
  // Succès : connectée.
  setAuthenticated(true);
}

// Déconnexion : POST /auth/logout, puis retour à la page de connexion même si le serveur ne répond pas (finally).
export async function logout() {
  // Essaie...
  try {
    // ...de prévenir le serveur.
    await logoutOwner();
  // Dans tous les cas...
  } finally {
    // ...non connectée...
    setAuthenticated(false);
    // ...et retour à la page de connexion.
    window.location.hash = "#/login";
  }
}

/* Vrai une seule fois après une expiration de session : la page de connexion l'annonce. */
export function consumeSessionExpired() {
  // Lit l'indicateur.
  const expired = window.sessionStorage.getItem(SESSION_EXPIRED_KEY) === "1";
  // L'efface (lecture unique).
  window.sessionStorage.removeItem(SESSION_EXPIRED_KEY);
  // Renvoie vrai s'il était présent.
  return expired;
}

/* Mémorise la page demandée avant la connexion pour y revenir ensuite. */
export function rememberNextRoute(hash) {
  // Pas d'adresse ou page de connexion : rien à mémoriser.
  if (!hash || hash.startsWith("#/login")) return;
  // Mémorise l'adresse.
  window.sessionStorage.setItem(NEXT_ROUTE_KEY, hash);
}

// Renvoie la page mémorisée avant la connexion (une seule fois), sinon l'accueil.
// N'accepte qu'une adresse interne commençant par « #/ ».
export function consumeNextRoute() {
  // Lit l'adresse mémorisée.
  const next = window.sessionStorage.getItem(NEXT_ROUTE_KEY);
  // L'efface.
  window.sessionStorage.removeItem(NEXT_ROUTE_KEY);
  // Adresse interne valide, sinon l'accueil.
  return next && next.startsWith("#/") && !next.startsWith("#/login") ? next : "#/accueil";
}

// Une route du Studio a répondu 401 (session expirée ou serveur redémarré) : retour à la connexion.
// Écoute l'événement envoyé par api.js lors d'une réponse 401.
window.addEventListener("forma3d:unauthorized", () => {
  // Déjà déconnectée : rien à faire.
  if (!authenticated) return;
  // Marque la session comme fermée.
  setAuthenticated(false);
  // Mémorise la page en cours.
  rememberNextRoute(window.location.hash);
  // Note que la session a expiré.
  window.sessionStorage.setItem(SESSION_EXPIRED_KEY, "1");
  // Va à la page de connexion.
  window.location.hash = "#/login";
});
