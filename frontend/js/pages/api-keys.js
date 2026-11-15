/*
 * Rôle : permet à la propriétaire de créer, consulter et révoquer ses clés API, avec un guide d'utilisation.
 * Exécution : router.js monte cette page sur #/cles-api ; le secret reste en mémoire le temps de l’affichage.
 * Refonte : guide en 4 étapes, exemple curl réel (routes /api/v1 existantes), cartes avec badge
 * de statut et confirmation de révocation par fenêtre modale.
 * Une clé révoquée peut ensuite être supprimée définitivement (avec ses compteurs de quota).
 */
import { createApiKey, deleteRevokedApiKey, listApiKeys, revokeApiKey } from "../api.js?v=20261115-e1";
import { confirmDialog } from "../views/confirm-dialog.js?v=20261115-e1";
import { formatLongDate, pluralize } from "../format.js?v=20261115-e1";

export const title = "Clés API";

// Fabrique l'exemple de commandes curl affiché sur la page, avec l'adresse réelle du serveur.
function curlExample(baseUrl) {
  return [
    "# 1. Envoyer une photo : la réponse contient l’identifiant du modèle",
    `curl -X POST ${baseUrl}/api/v1/models \\`,
    '  -H "X-API-Key: votre_clé_ici" \\',
    '  -F "file=@photo.jpg" \\',
    '  -F "category=chair"',
    "",
    "# 2. Suivre l’état du modèle (PENDING, RUNNING, DONE ou FAILED)",
    `curl ${baseUrl}/api/v1/models/IDENTIFIANT_DU_MODELE \\`,
    '  -H "X-API-Key: votre_clé_ici"',
  ].join("\n");
}

// Retourne le HTML de la page Clés API (mode d'emploi, création, liste).
export function render() {
  return `
    <section class="page-shell api-keys-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Intégration</p><h1 class="page-title" id="page-title" tabindex="-1">Clés API</h1><p class="page-lead">Une clé autorise un site ou un script à appeler l’API Forma3D en votre nom. Gardez-la privée et révoquez-la si elle est exposée.</p></div>

      <section class="panel" id="integration-guide" aria-labelledby="guide-title">
        <div class="section-header"><div><h2 id="guide-title">Comment utiliser l’API</h2><p>Quatre étapes, de la création de la clé au premier appel.</p></div><a class="text-link" href="#/guide">Guide complet →</a></div>
        <ol class="steps-guide">
          <li class="guide-card"><strong>Créez une clé</strong><span>Donnez-lui un nom pour la reconnaître, par exemple celui de la boutique.</span></li>
          <li class="guide-card"><strong>Copiez le secret</strong><span>Il n’est affiché qu’une fois : sauvegardez-le dans un gestionnaire de mots de passe.</span></li>
          <li class="guide-card"><strong>Ajoutez l’en-tête</strong><span>Envoyez <code>X-API-Key</code> dans chaque requête, depuis votre serveur.</span></li>
          <li class="guide-card"><strong>Testez l’API</strong><span>Lancez l’exemple <code>curl</code> ci-dessous avec votre clé.</span></li>
        </ol>
        <div class="code-block">
          <div class="code-block-header"><span>Exemple · terminal</span><button class="copy-button" id="copy-curl" type="button">Copier</button></div>
          <pre><code id="curl-example"></code></pre>
        </div>
        <p class="api-note">N’utilisez jamais la clé dans du JavaScript public : appelez l’API depuis un serveur. Quotas par clé : <code>API_DAILY_GENERATION_LIMIT</code> créations par jour et <code>API_RATE_LIMIT_PER_MINUTE</code> requêtes par minute (voir <code>.env.example</code>).</p>
      </section>

      <section class="panel api-key-panel" aria-labelledby="create-api-key-title">
        <h2 id="create-api-key-title">Créer une clé</h2>
        <form id="api-key-create-form" class="api-key-create-form"><label for="api-key-name">Nom pour la reconnaître</label><input id="api-key-name" name="name" maxlength="80" autocomplete="off" placeholder="Ex. Boutique de mobilier" required><button class="button button-primary" type="submit">Créer une clé API</button></form>
        <p id="api-key-feedback" class="api-key-feedback" role="status" aria-live="polite" hidden></p>
        <section id="api-key-reveal" class="api-key-reveal" aria-labelledby="api-key-reveal-title" hidden>
          <h3 id="api-key-reveal-title">Copiez votre clé maintenant</h3>
          <p>Elle ne sera affichée qu’une seule fois. Après avoir quitté cette page, créez-en une nouvelle si vous ne l’avez pas sauvegardée.</p>
          <div class="api-key-secret-row"><code id="api-key-secret" class="api-key-secret"></code><button class="button button-secondary" id="copy-api-key" type="button">Copier la clé</button></div>
        </section>
      </section>

      <section class="panel api-key-panel" aria-labelledby="api-key-list-title"><div class="gallery-heading"><div><h2 id="api-key-list-title">Clés existantes</h2><p class="gallery-copy">Seul le début de chaque clé est affiché ; le secret complet n’est jamais conservé.</p></div><span id="api-key-count" class="gallery-count" aria-live="polite">Chargement…</span></div><div id="api-key-list" class="api-key-list" aria-live="polite"></div></section>
    </section>`;
}

// Copie un texte dans le presse-papiers (navigator.clipboard) ; renvoie false si le navigateur refuse.
async function copyText(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    button.dataset.copied = "true";
    const previous = button.textContent;
    button.textContent = "Copié ✓";
    window.setTimeout(() => { button.textContent = previous; button.dataset.copied = "false"; }, 1800);
    return true;
  } catch {
    return false;
  }
}

// Branche la page Clés API : création (secret affiché une fois), copie, révocation, suppression.
// Le secret n'est gardé qu'en mémoire et effacé en quittant la page.
export function mount() {
  const form = document.querySelector("#api-key-create-form");
  const name = document.querySelector("#api-key-name");
  const feedback = document.querySelector("#api-key-feedback");
  const reveal = document.querySelector("#api-key-reveal");
  const secretElement = document.querySelector("#api-key-secret");
  const list = document.querySelector("#api-key-list");
  const count = document.querySelector("#api-key-count");
  const curl = document.querySelector("#curl-example");
  let revealedSecret = "";
  let revealedKeyId = null;

  /* Efface le secret affiché : une clé révoquée ou supprimée ne doit plus être visible. */
  function hideRevealFor(keyId) {
    if (keyId !== revealedKeyId) return;
    reveal.hidden = true;
    secretElement.textContent = "";
    revealedSecret = "";
    revealedKeyId = null;
  }

  curl.textContent = curlExample(window.location.origin);
  document.querySelector("#copy-curl").addEventListener("click", async (event) => {
    if (!(await copyText(curl.textContent, event.currentTarget))) {
      showFeedback("La copie automatique est indisponible ; sélectionnez l’exemple à la main.");
    }
  });

  // Affiche un message sous le formulaire de création.
  function showFeedback(message) {
    feedback.textContent = message;
    feedback.hidden = false;
  }

  // Construit la carte d'une clé avec le bouton « Révoquer » (clé active) ou « Supprimer définitivement » (clé révoquée).
  function makeKeyCard(key) {
    const card = document.createElement("article");
    card.className = key.revoked ? "api-key-card is-revoked" : "api-key-card";
    const top = document.createElement("div");
    top.className = "api-key-card-top";
    const heading = document.createElement("h3");
    heading.textContent = key.name;
    const status = document.createElement("span");
    status.className = key.revoked ? "status-badge is-revoked" : "status-badge";
    status.textContent = key.revoked ? "Révoquée" : "Active";
    top.append(heading, status);
    const prefix = document.createElement("code");
    prefix.textContent = `${key.prefix}…`;
    const date = document.createElement("p");
    date.className = "api-key-meta";
    date.textContent = `Créée le ${formatLongDate(key.created_at)}`;
    card.append(top, prefix, date);
    if (!key.revoked) {
      const revoke = document.createElement("button");
      revoke.className = "button button-danger";
      revoke.type = "button";
      revoke.textContent = "Révoquer";
      revoke.addEventListener("click", async () => {
        const confirmed = await confirmDialog({
          title: "Révoquer cette clé ?",
          message: `La clé « ${key.name} » sera refusée immédiatement par l’API. Cette action est définitive.`,
          confirmLabel: "Révoquer la clé",
          danger: true,
        });
        if (!confirmed) return;
        try {
          await revokeApiKey(key.id);
          hideRevealFor(key.id);
          showFeedback("Clé révoquée. Les appels avec cette clé seront refusés.");
          await reload();
        } catch (error) {
          showFeedback(error.message);
        }
      });
      card.append(revoke);
    } else {
      const remove = document.createElement("button");
      remove.className = "button button-danger";
      remove.type = "button";
      remove.textContent = "Supprimer définitivement";
      remove.addEventListener("click", async () => {
        const confirmed = await confirmDialog({
          title: "Supprimer définitivement cette clé ?",
          message: `La clé révoquée « ${key.name} » et ses compteurs de quota seront effacés. Cette action est irréversible.`,
          confirmLabel: "Supprimer définitivement",
          danger: true,
        });
        if (!confirmed) return;
        try {
          await deleteRevokedApiKey(key.id);
          hideRevealFor(key.id);
          showFeedback("Clé supprimée définitivement.");
          await reload();
        } catch (error) {
          showFeedback(error.message);
        }
      });
      card.append(remove);
    }
    return card;
  }

  // Recharge la liste des clés (GET /api-keys) : actives d'abord, révoquées ensuite.
  async function reload() {
    count.textContent = "Chargement…";
    try {
      const response = await listApiKeys();
      const keys = response.items ?? [];
      const active = keys.filter((key) => !key.revoked).length;
      count.textContent = `${pluralize(active, "active")} · ${pluralize(keys.length, "clé")}`;
      if (!keys.length) {
        const empty = document.createElement("p");
        empty.className = "api-key-empty";
        empty.textContent = "Aucune clé API pour l’instant. Créez-en une ci-dessus pour préparer votre premier appel.";
        list.replaceChildren(empty);
        return;
      }
      // Les clés actives d'abord, puis les révoquées.
      const sorted = [...keys].sort((a, b) => Number(a.revoked) - Number(b.revoked));
      list.replaceChildren(...sorted.map(makeKeyCard));
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
      revealedKeyId = created.id;
      secretElement.textContent = revealedSecret;
      reveal.hidden = false;
      showFeedback("Clé créée. Copiez-la maintenant : le serveur ne pourra pas la réafficher.");
      form.reset();
      await reload();
    } catch (error) {
      showFeedback(error.message);
    } finally {
      submit.disabled = false;
    }
  });

  document.querySelector("#copy-api-key").addEventListener("click", async (event) => {
    const copied = await copyText(revealedSecret, event.currentTarget);
    showFeedback(copied
      ? "Clé copiée. Rangez-la dans un endroit sûr."
      : "La copie automatique est indisponible ; sélectionnez la clé affichée.");
  });

  void reload();
  // Le secret n'est gardé qu'en mémoire : on l'efface en quittant la page.
  return () => { revealedSecret = ""; };
}
