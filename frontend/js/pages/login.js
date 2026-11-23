/*
 * Rôle : affiche l'écran de connexion plein écran du Studio (mot de passe unique).
 * Exécution : router.js monte cette page sur #/login et y redirige toute visite non connectée.
 * Étape 5f : le mot de passe est envoyé à POST /auth/login et vérifié par le serveur.
 */
// Importe les fonctions de connexion et de session.
import { consumeNextRoute, consumeSessionExpired, isPasswordConfigured, login } from "../auth.js?v=20261117-r2";

// Titre de l'onglet.
export const title = "Connexion";

// Retourne le HTML de l'écran de connexion.
export function render() {
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - la carte de connexion avec le logo (cube SVG) et le titre « Forma3D Studio » ;
  // - le formulaire : champ mot de passe (autocomplete current-password) et bouton Afficher/Masquer ;
  // - la zone d'erreur annoncée aux lecteurs d'écran (role="alert"), masquée au départ ;
  // - le bouton « Accéder au Studio » et une note sur l'usage local sans HTTPS.
  return `
    <section class="login-screen" aria-labelledby="page-title">
      <div class="login-card">
        <span class="login-logo" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="m16 3 11 6.2v13.6L16 29 5 22.8V9.2L16 3Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="m5.5 9.5 10.5 6 10.5-6M16 15.5V28" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
          </svg>
        </span>
        <p class="eyebrow">Console privée</p>
        <h1 class="page-title" id="page-title" tabindex="-1">Forma3D Studio</h1>
        <p class="login-lead">Saisissez le mot de passe de la propriétaire pour accéder au Studio.</p>
        <form class="login-form" id="login-form" novalidate>
          <label for="login-password">Mot de passe</label>
          <div class="password-field">
            <input id="login-password" name="password" type="password" autocomplete="current-password" required>
            <button class="password-toggle" id="password-toggle" type="button" aria-pressed="false" aria-controls="login-password">Afficher</button>
          </div>
          <p class="login-error" id="login-error" role="alert" hidden></p>
          <button class="button button-primary login-submit" id="login-submit" type="submit">
            <span class="button-label">Accéder au Studio</span><span aria-hidden="true">→</span>
          </button>
        </form>
        <p class="login-note">Session protégée par le serveur · usage local tant que le Studio n’est pas déployé en HTTPS.</p>
      </div>
    </section>`;
}

// Branche la connexion : afficher/masquer, envoi (POST /auth/login), messages d'erreur,
// annonce d'une session expirée, puis retour à la page demandée.
export function mount() {
  // Formulaire de connexion.
  const form = document.querySelector("#login-form");
  // Champ du mot de passe.
  const password = document.querySelector("#login-password");
  // Zone d'erreur.
  const error = document.querySelector("#login-error");
  // Bouton d'envoi.
  const submit = document.querySelector("#login-submit");
  // Bouton Afficher / Masquer.
  const toggle = document.querySelector("#password-toggle");

  // Clic sur Afficher / Masquer...
  toggle.addEventListener("click", () => {
    // ...vrai si le mot de passe est visible...
    const visible = password.type === "text";
    // ...inverse le type du champ (texte ou masqué)...
    password.type = visible ? "password" : "text";
    // ...change le texte du bouton...
    toggle.textContent = visible ? "Afficher" : "Masquer";
    // ...et son état enfoncé.
    toggle.setAttribute("aria-pressed", String(!visible));
  });

  // À l'envoi du formulaire...
  form.addEventListener("submit", async (event) => {
    // ...empêche le rechargement de la page...
    event.preventDefault();
    // ...masque l'ancienne erreur...
    error.hidden = true;
    // ...champ vide...
    if (!password.value) {
      // ...message...
      error.textContent = "Saisissez le mot de passe.";
      // ...affiché...
      error.hidden = false;
      // ...focus sur le champ...
      password.focus();
      // ...et arrêt.
      return;
    }
    // Désactive le bouton pendant la vérification.
    submit.disabled = true;
    // Texte d'attente.
    submit.querySelector(".button-label").textContent = "Vérification…";
    // Essaie...
    try {
      // ...de se connecter...
      await login(password.value);
      // ...puis va à la page demandée avant la connexion.
      window.location.hash = consumeNextRoute();
    // Refus...
    } catch (loginError) {
      // ...affiche le message du serveur...
      error.textContent = loginError.message;
      // ...rend l'erreur visible...
      error.hidden = false;
      // ...et sélectionne le mot de passe pour le retaper.
      password.select();
    // Dans tous les cas...
    } finally {
      // ...réactive le bouton...
      submit.disabled = false;
      // ...et remet son texte.
      submit.querySelector(".button-label").textContent = "Accéder au Studio";
    }
  });

  // Session expirée...
  if (consumeSessionExpired()) {
    // ...message...
    error.textContent = "Votre session a expiré. Reconnectez-vous pour continuer.";
    // ...affiché.
    error.hidden = false;
  }
  // Aucun mot de passe configuré sur le serveur...
  if (!isPasswordConfigured()) {
    // ...message d'aide...
    error.textContent = "Connexion impossible : définissez FORMA3D_OWNER_PASSWORD dans backend/.env, puis redémarrez le serveur.";
    // ...affiché.
    error.hidden = false;
  }
  // Place le focus sur le champ après un court délai.
  window.setTimeout(() => password.focus(), 50);
}
