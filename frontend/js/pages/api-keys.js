/*
 * Rôle : permet à la propriétaire de créer, consulter et révoquer ses clés API, avec un guide d'utilisation.
 * Exécution : router.js monte cette page sur #/cles-api ; le secret reste en mémoire le temps de l’affichage.
 * Refonte : guide en 4 étapes, exemple curl réel (routes /api/v1 existantes), cartes avec badge
 * de statut et confirmation de révocation par fenêtre modale.
 * Une clé révoquée peut ensuite être supprimée définitivement (avec ses compteurs de quota).
 */
// Importe les appels HTTP des clés API.
import { createApiKey, deleteRevokedApiKey, listApiKeys, revokeApiKey } from "../api.js?v=20261117-r2";
// Importe la fenêtre de confirmation.
import { confirmDialog } from "../views/confirm-dialog.js?v=20261117-r2";
// Importe la mise en forme des dates et des pluriels.
import { formatLongDate, pluralize } from "../format.js?v=20261117-r2";

// Titre de l'onglet.
export const title = "Clés API";

// Fabrique l'exemple de commandes curl affiché sur la page, avec l'adresse réelle du serveur.
function curlExample(baseUrl) {
  // Renvoie un tableau de lignes...
  return [
    // ...commentaire de l'étape 1...
    "# 1. Envoyer une photo : la réponse contient l’identifiant du modèle",
    // ...envoi d'une photo à l'API...
    `curl -X POST ${baseUrl}/api/v1/models \\`,
    // ...en-tête de la clé...
    '  -H "X-API-Key: votre_clé_ici" \\',
    // ...fichier photo...
    '  -F "file=@photo.jpg" \\',
    // ...catégorie...
    '  -F "category=chair"',
    // ...ligne vide...
    "",
    // ...commentaire de l'étape 2...
    "# 2. Suivre l’état du modèle (PENDING, RUNNING, DONE ou FAILED)",
    // ...lecture de l'état du modèle...
    `curl ${baseUrl}/api/v1/models/IDENTIFIANT_DU_MODELE \\`,
    // ...en-tête de la clé.
    '  -H "X-API-Key: votre_clé_ici"',
  // Lignes jointes par des retours à la ligne.
  ].join("\n");
}

// Retourne le HTML de la page Clés API (mode d'emploi, création, liste).
export function render() {
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - l'introduction de la page Clés API ;
  // - le mode d'emploi en 4 étapes et un bloc de code curl avec son bouton Copier ;
  // - une note sur les quotas et l'usage côté serveur ;
  // - le formulaire de création et la zone qui affiche le secret une seule fois ;
  // - la liste des clés existantes avec son compteur.
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
  // Essaie...
  try {
    // ...de copier le texte...
    await navigator.clipboard.writeText(text);
    // ...marque l'état « copié »...
    button.dataset.copied = "true";
    // ...garde le texte du bouton...
    const previous = button.textContent;
    // ...affiche la confirmation...
    button.textContent = "Copié ✓";
    // ...et remet le texte après 1,8 seconde.
    window.setTimeout(() => { button.textContent = previous; button.dataset.copied = "false"; }, 1800);
    // Copie réussie.
    return true;
  // Refus du navigateur...
  } catch {
    // ...copie impossible.
    return false;
  }
}

// Branche la page Clés API : création (secret affiché une fois), copie, révocation, suppression.
// Le secret n'est gardé qu'en mémoire et effacé en quittant la page.
export function mount() {
  // Formulaire de création.
  const form = document.querySelector("#api-key-create-form");
  // Champ du nom.
  const name = document.querySelector("#api-key-name");
  // Zone des messages.
  const feedback = document.querySelector("#api-key-feedback");
  // Zone qui affiche le secret.
  const reveal = document.querySelector("#api-key-reveal");
  // Élément qui contient le secret.
  const secretElement = document.querySelector("#api-key-secret");
  // Liste des clés.
  const list = document.querySelector("#api-key-list");
  // Compteur.
  const count = document.querySelector("#api-key-count");
  // Bloc de l'exemple curl.
  const curl = document.querySelector("#curl-example");
  // Secret affiché (en mémoire seulement).
  let revealedSecret = "";
  // Identifiant de la clé dont le secret est affiché.
  let revealedKeyId = null;

  /* Efface le secret affiché : une clé révoquée ou supprimée ne doit plus être visible. */
  function hideRevealFor(keyId) {
    // Autre clé que celle affichée : rien à faire.
    if (keyId !== revealedKeyId) return;
    // Masque la zone du secret.
    reveal.hidden = true;
    // Efface le secret de la page.
    secretElement.textContent = "";
    // Efface le secret de la mémoire.
    revealedSecret = "";
    // Oublie l'identifiant.
    revealedKeyId = null;
  }

  // Remplit l'exemple curl avec l'adresse réelle du serveur.
  curl.textContent = curlExample(window.location.origin);
  // Bouton Copier de l'exemple...
  document.querySelector("#copy-curl").addEventListener("click", async (event) => {
    // ...copie refusée...
    if (!(await copyText(curl.textContent, event.currentTarget))) {
      // ...message d'aide.
      showFeedback("La copie automatique est indisponible ; sélectionnez l’exemple à la main.");
    }
  });

  // Affiche un message sous le formulaire de création.
  function showFeedback(message) {
    // Texte du message.
    feedback.textContent = message;
    // Message visible.
    feedback.hidden = false;
  }

  // Construit la carte d'une clé avec le bouton « Révoquer » (clé active) ou « Supprimer définitivement » (clé révoquée).
  function makeKeyCard(key) {
    // Crée la carte.
    const card = document.createElement("article");
    // Classe différente pour une clé révoquée.
    card.className = key.revoked ? "api-key-card is-revoked" : "api-key-card";
    // Haut de la carte.
    const top = document.createElement("div");
    // Sa classe CSS.
    top.className = "api-key-card-top";
    // Titre : nom de la clé.
    const heading = document.createElement("h3");
    // Texte du titre.
    heading.textContent = key.name;
    // Badge de statut.
    const status = document.createElement("span");
    // Classe selon l'état.
    status.className = key.revoked ? "status-badge is-revoked" : "status-badge";
    // Texte du badge.
    status.textContent = key.revoked ? "Révoquée" : "Active";
    // Assemble le haut.
    top.append(heading, status);
    // Préfixe visible de la clé.
    const prefix = document.createElement("code");
    // Suivi de « … » (le reste n'est jamais connu).
    prefix.textContent = `${key.prefix}…`;
    // Date de création.
    const date = document.createElement("p");
    // Sa classe CSS.
    date.className = "api-key-meta";
    // Texte de la date.
    date.textContent = `Créée le ${formatLongDate(key.created_at)}`;
    // Assemble la carte.
    card.append(top, prefix, date);
    // Clé active...
    if (!key.revoked) {
      // ...bouton Révoquer...
      const revoke = document.createElement("button");
      // ...style « danger »...
      revoke.className = "button button-danger";
      // ...type « button »...
      revoke.type = "button";
      // ...texte...
      revoke.textContent = "Révoquer";
      // ...au clic...
      revoke.addEventListener("click", async () => {
        // ...demande une confirmation...
        const confirmed = await confirmDialog({
          // ...titre...
          title: "Révoquer cette clé ?",
          // ...explication...
          message: `La clé « ${key.name} » sera refusée immédiatement par l’API. Cette action est définitive.`,
          // ...texte du bouton...
          confirmLabel: "Révoquer la clé",
          // ...style rouge.
          danger: true,
        });
        // Annulé : arrêt.
        if (!confirmed) return;
        // Essaie...
        try {
          // ...de révoquer...
          await revokeApiKey(key.id);
          // ...masque le secret s'il concernait cette clé...
          hideRevealFor(key.id);
          // ...message de succès...
          showFeedback("Clé révoquée. Les appels avec cette clé seront refusés.");
          // ...et recharge la liste.
          await reload();
        // Erreur...
        } catch (error) {
          // ...message affiché.
          showFeedback(error.message);
        }
      });
      // Ajoute le bouton.
      card.append(revoke);
    // Clé révoquée...
    } else {
      // ...bouton Supprimer définitivement...
      const remove = document.createElement("button");
      // ...style « danger »...
      remove.className = "button button-danger";
      // ...type « button »...
      remove.type = "button";
      // ...texte...
      remove.textContent = "Supprimer définitivement";
      // ...au clic...
      remove.addEventListener("click", async () => {
        // ...demande une confirmation...
        const confirmed = await confirmDialog({
          // ...titre...
          title: "Supprimer définitivement cette clé ?",
          // ...explication...
          message: `La clé révoquée « ${key.name} » et ses compteurs de quota seront effacés. Cette action est irréversible.`,
          // ...texte du bouton...
          confirmLabel: "Supprimer définitivement",
          // ...style rouge.
          danger: true,
        });
        // Annulé : arrêt.
        if (!confirmed) return;
        // Essaie...
        try {
          // ...de supprimer...
          await deleteRevokedApiKey(key.id);
          // ...masque le secret s'il concernait cette clé...
          hideRevealFor(key.id);
          // ...message de succès...
          showFeedback("Clé supprimée définitivement.");
          // ...et recharge la liste.
          await reload();
        // Erreur...
        } catch (error) {
          // ...message affiché.
          showFeedback(error.message);
        }
      });
      // Ajoute le bouton.
      card.append(remove);
    }
    // Renvoie la carte.
    return card;
  }

  // Recharge la liste des clés (GET /api-keys) : actives d'abord, révoquées ensuite.
  async function reload() {
    // Message d'attente.
    count.textContent = "Chargement…";
    // Essaie...
    try {
      // ...de charger les clés...
      const response = await listApiKeys();
      // ...liste reçue...
      const keys = response.items ?? [];
      // ...nombre de clés actives...
      const active = keys.filter((key) => !key.revoked).length;
      // ...« 2 actives · 3 clés ».
      count.textContent = `${pluralize(active, "active")} · ${pluralize(keys.length, "clé")}`;
      // Aucune clé...
      if (!keys.length) {
        // ...crée un paragraphe...
        const empty = document.createElement("p");
        // ...avec sa classe...
        empty.className = "api-key-empty";
        // ...et son texte...
        empty.textContent = "Aucune clé API pour l’instant. Créez-en une ci-dessus pour préparer votre premier appel.";
        // ...l'affiche...
        list.replaceChildren(empty);
        // ...et s'arrête.
        return;
      }
      // Les clés actives d'abord, puis les révoquées.
      // Copie triée (faux = 0 avant vrai = 1).
      const sorted = [...keys].sort((a, b) => Number(a.revoked) - Number(b.revoked));
      // Affiche une carte par clé.
      list.replaceChildren(...sorted.map(makeKeyCard));
    // Erreur...
    } catch (error) {
      // ...compteur indisponible...
      count.textContent = "Indisponible";
      // ...message à la place de la liste.
      list.textContent = error.message;
    }
  }

  // À l'envoi du formulaire...
  form.addEventListener("submit", async (event) => {
    // ...empêche le rechargement...
    event.preventDefault();
    // ...masque l'ancien message...
    feedback.hidden = true;
    // ...masque l'ancien secret...
    reveal.hidden = true;
    // ...l'efface de la mémoire...
    revealedSecret = "";
    // ...bouton d'envoi...
    const submit = form.querySelector("button[type=submit]");
    // ...désactivé...
    submit.disabled = true;
    // ...essaie...
    try {
      // ...de créer la clé...
      const created = await createApiKey(name.value);
      // ...garde le secret...
      revealedSecret = created.key;
      // ...et l'identifiant...
      revealedKeyId = created.id;
      // ...affiche le secret...
      secretElement.textContent = revealedSecret;
      // ...rend la zone visible...
      reveal.hidden = false;
      // ...message d'avertissement...
      showFeedback("Clé créée. Copiez-la maintenant : le serveur ne pourra pas la réafficher.");
      // ...vide le formulaire...
      form.reset();
      // ...et recharge la liste.
      await reload();
    // Erreur...
    } catch (error) {
      // ...message affiché.
      showFeedback(error.message);
    // Dans tous les cas...
    } finally {
      // ...réactive le bouton.
      submit.disabled = false;
    }
  });

  // Bouton « Copier la clé »...
  document.querySelector("#copy-api-key").addEventListener("click", async (event) => {
    // ...copie le secret...
    const copied = await copyText(revealedSecret, event.currentTarget);
    // ...message selon le résultat.
    showFeedback(copied
      ? "Clé copiée. Rangez-la dans un endroit sûr."
      : "La copie automatique est indisponible ; sélectionnez la clé affichée.");
  });

  // Charge la liste au démarrage.
  void reload();
  // Le secret n'est gardé qu'en mémoire : on l'efface en quittant la page.
  // Fonction de nettoyage appelée par router.js en quittant la page.
  return () => { revealedSecret = ""; };
}
