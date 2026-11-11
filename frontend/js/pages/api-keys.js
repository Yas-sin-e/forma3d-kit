/*
 * Rôle : permet à la propriétaire de créer, consulter et révoquer ses clés API.
 * Exécution : router.js monte cette page uniquement sur #/cles-api ; le secret reste en mémoire le temps de l’affichage.
 */
import { createApiKey, listApiKeys, revokeApiKey } from "../api.js?v=20261111-5b";

export const title = "Clés API";

export function render() {
  return `
    <section class="page-shell api-keys-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Intégration</p><h1 class="page-title" id="page-title" tabindex="-1">Clés API</h1><p class="page-lead">Créez une clé pour autoriser vos futurs appels à l’API Forma3D. Gardez-la privée et révoquez-la si elle est exposée.</p></div>
      <section class="panel api-key-panel" aria-labelledby="create-api-key-title">
        <h2 id="create-api-key-title">Créer une clé</h2>
        <form id="api-key-create-form" class="api-key-create-form"><label for="api-key-name">Nom pour la reconnaître</label><input id="api-key-name" name="name" maxlength="80" autocomplete="off" placeholder="Ex. Boutique de mobilier" required><button class="button button-primary" type="submit">Créer une clé API</button></form>
        <p id="api-key-feedback" class="api-key-feedback" role="status" aria-live="polite" hidden></p>
        <section id="api-key-reveal" class="api-key-reveal" aria-labelledby="api-key-reveal-title" hidden><h3 id="api-key-reveal-title">Copiez votre clé maintenant</h3><p>Elle ne sera affichée qu’une seule fois. Après avoir quitté cette page, créez-en une nouvelle si vous ne l’avez pas sauvegardée.</p><code id="api-key-secret" class="api-key-secret"></code><button class="button button-secondary" id="copy-api-key" type="button">Copier la clé</button></section>
      </section>
      <section class="panel api-key-panel" aria-labelledby="api-key-list-title"><div class="gallery-heading"><div><h2 id="api-key-list-title">Clés existantes</h2><p class="gallery-copy">La liste n’affiche jamais les clés complètes.</p></div><span id="api-key-count" class="gallery-count" aria-live="polite">Chargement…</span></div><div id="api-key-list" class="api-key-list" aria-live="polite"></div></section>
    </section>`;
}

export function mount() {
  const form = document.querySelector("#api-key-create-form");
  const name = document.querySelector("#api-key-name");
  const feedback = document.querySelector("#api-key-feedback");
  const reveal = document.querySelector("#api-key-reveal");
  const secretElement = document.querySelector("#api-key-secret");
  const list = document.querySelector("#api-key-list");
  const count = document.querySelector("#api-key-count");
  let revealedSecret = "";

  async function reload() {
    count.textContent = "Chargement…";
    try {
      const response = await listApiKeys();
      const keys = response.items ?? [];
      count.textContent = `${keys.length} ${keys.length === 1 ? "clé" : "clés"}`;
      if (!keys.length) {
        const empty = document.createElement("p");
        empty.className = "api-key-empty";
        empty.textContent = "Aucune clé API. Créez-en une pour préparer l’accès à l’API.";
        list.replaceChildren(empty);
        return;
      }
      list.replaceChildren(...keys.map((key) => {
        const row = document.createElement("article");
        row.className = "api-key-row";
        const identity = document.createElement("div");
        const title = document.createElement("h3");
        title.textContent = key.name;
        const prefix = document.createElement("code");
        prefix.textContent = `${key.prefix}…`;
        const date = document.createElement("p");
        date.textContent = new Date(key.created_at).toLocaleString("fr-FR");
        identity.append(title, prefix, date);
        const status = document.createElement("span");
        status.className = key.revoked ? "api-key-status is-revoked" : "api-key-status";
        status.textContent = key.revoked ? "Révoquée" : "Active";
        row.append(identity, status);
        if (!key.revoked) {
          const revoke = document.createElement("button");
          revoke.className = "button button-danger";
          revoke.type = "button";
          revoke.textContent = "Révoquer";
          revoke.addEventListener("click", async () => {
            if (!window.confirm(`Révoquer la clé « ${key.name} » ? Les appels qui l’utilisent seront refusés.`)) return;
            try {
              await revokeApiKey(key.id);
              feedback.textContent = "Clé révoquée. Les appels avec cette clé seront refusés.";
              feedback.hidden = false;
              await reload();
            } catch (error) {
              feedback.textContent = error.message;
              feedback.hidden = false;
            }
          });
          row.append(revoke);
        }
        return row;
      }));
    } catch (error) {
      count.textContent = "Indisponible";
      list.textContent = error.message;
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    feedback.hidden = true;
    reveal.hidden = true;
    revealedSecret = "";
    const submit = form.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      const created = await createApiKey(name.value);
      revealedSecret = created.key;
      secretElement.textContent = revealedSecret;
      reveal.hidden = false;
      feedback.textContent = "Clé créée. Copiez-la maintenant : le serveur ne pourra pas la réafficher.";
      feedback.hidden = false;
      form.reset();
      await reload();
    } catch (error) {
      feedback.textContent = error.message;
      feedback.hidden = false;
    } finally {
      submit.disabled = false;
    }
  });

  document.querySelector("#copy-api-key").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(revealedSecret);
      feedback.textContent = "Clé copiée. Rangez-la dans un endroit sûr.";
    } catch {
      feedback.textContent = "La copie automatique est indisponible ; sélectionnez la clé affichée.";
    }
    feedback.hidden = false;
  });

  void reload();
}
