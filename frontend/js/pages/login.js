/*
 * Rôle : affiche l'écran de connexion plein écran du Studio (mot de passe unique).
 * Exécution : router.js monte cette page sur #/login et y redirige toute visite non connectée.
 */
import { consumeNextRoute, login } from "../auth.js?v=20261111-ui";

export const title = "Connexion";

export function render() {
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
        <p class="login-note">Verrou de démonstration : à utiliser en local uniquement.</p>
      </div>
    </section>`;
}

export function mount() {
  const form = document.querySelector("#login-form");
  const password = document.querySelector("#login-password");
  const error = document.querySelector("#login-error");
  const submit = document.querySelector("#login-submit");
  const toggle = document.querySelector("#password-toggle");

  toggle.addEventListener("click", () => {
    const visible = password.type === "text";
    password.type = visible ? "password" : "text";
    toggle.textContent = visible ? "Afficher" : "Masquer";
    toggle.setAttribute("aria-pressed", String(!visible));
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;
    if (!password.value) {
      error.textContent = "Saisissez le mot de passe.";
      error.hidden = false;
      password.focus();
      return;
    }
    submit.disabled = true;
    submit.querySelector(".button-label").textContent = "Vérification…";
    try {
      await login(password.value);
      window.location.hash = consumeNextRoute();
    } catch (loginError) {
      error.textContent = loginError.message;
      error.hidden = false;
      password.select();
    } finally {
      submit.disabled = false;
      submit.querySelector(".button-label").textContent = "Accéder au Studio";
    }
  });

  window.setTimeout(() => password.focus(), 50);
}
