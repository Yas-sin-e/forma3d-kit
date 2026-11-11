/*
 * Rôle : affiche dans le Studio le guide d'intégration (version lisible de docs/INTEGRATION.md).
 * Exécution : router.js monte cette page sur #/guide ; les exemples utilisent l'adresse réelle du service.
 * Le dossier docs/ n'est pas servi par FastAPI : cette page rend le guide réellement accessible.
 * Toute modification du contrat doit être reportée dans les deux fichiers.
 */
export const title = "Guide d’intégration";

function codeBlock(label, code) {
  const escaped = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return `
    <div class="code-block">
      <div class="code-block-header"><span>${label}</span><button class="copy-button" type="button" data-copy-code>Copier</button></div>
      <pre><code>${escaped}</code></pre>
    </div>`;
}

export function render() {
  const base = window.location.origin;
  return `
    <section class="page-shell guide-page" aria-labelledby="page-title">
      <div class="page-intro"><p class="eyebrow">Documentation</p><h1 class="page-title" id="page-title" tabindex="-1">Guide d’intégration</h1><p class="page-lead">Connectez une boutique à Forma3D : envoi d’une photo par l’API, suivi, activation du modèle, puis affichage par iframe ou par la balise <code>&lt;forma3d-viewer&gt;</code>.</p></div>

      <nav class="panel guide-toc" aria-label="Sommaire du guide">
        <ol>
          <li><a href="#/guide#guide-key">Créer une clé</a></li>
          <li><a href="#/guide#guide-send">Envoyer une photo</a></li>
          <li><a href="#/guide#guide-status">Suivre le modèle</a></li>
          <li><a href="#/guide#guide-enable">Activer et intégrer</a></li>
          <li><a href="#/guide#guide-limits">Quotas et origines</a></li>
          <li><a href="#/guide#guide-security">Sécurité</a></li>
        </ol>
      </nav>

      <section class="panel guide-section" id="guide-key" aria-labelledby="guide-key-title">
        <h2 id="guide-key-title">1. Créer une clé API</h2>
        <p>Ouvrez <a class="text-link" href="#/cles-api">Clés API</a>, donnez un nom à la clé, puis copiez-la : elle n’est affichée qu’une seule fois et seule son empreinte est conservée. Rangez-la dans la configuration du <strong>serveur</strong> de la boutique, jamais dans du JavaScript public.</p>
      </section>

      <section class="panel guide-section" id="guide-send" aria-labelledby="guide-send-title">
        <h2 id="guide-send-title">2. Envoyer une photo</h2>
        <p>Photo JPG, PNG ou WebP de 10 Mo maximum, avec le slug d’une catégorie active (par exemple <code>chair</code>). La réponse est <code>202 Accepted</code> : la création continue en tâche de fond.</p>
        ${codeBlock("Terminal", `curl --fail-with-body -X POST "${base}/api/v1/models" \\\n  -H "X-API-Key: VOTRE_CLE" \\\n  -F "category=chair" \\\n  -F "file=@chaise.jpg;type=image/jpeg"`)}
        <p>La réponse contient <code>id</code>, <code>status</code>, <code>status_url</code>, <code>public_id</code> et <code>model_url</code> (absent tant que le modèle n’est pas terminé).</p>
      </section>

      <section class="panel guide-section" id="guide-status" aria-labelledby="guide-status-title">
        <h2 id="guide-status-title">3. Suivre le modèle et télécharger le GLB</h2>
        <p>L’état vaut <code>PENDING</code>, <code>RUNNING</code>, <code>DONE</code> ou <code>FAILED</code>. Interrogez la route toutes les 6 à 10 secondes : ces appels comptent dans la limite par minute.</p>
        ${codeBlock("Terminal", `curl --fail-with-body "${base}/api/v1/models/ID_DU_MODELE" \\\n  -H "X-API-Key: VOTRE_CLE"\n\ncurl --fail-with-body "${base}/api/v1/models/ID_DU_MODELE/glb" \\\n  -H "X-API-Key: VOTRE_CLE" -o chaise.glb`)}
      </section>

      <section class="panel guide-section" id="guide-enable" aria-labelledby="guide-enable-title">
        <h2 id="guide-enable-title">4. Activer puis intégrer le modèle</h2>
        <ol class="guide-list">
          <li>Dans <a class="text-link" href="#/modeles">Mes modèles</a>, ouvrez la fiche du modèle terminé et activez <strong>l’intégration publique</strong> (désactivée par défaut).</li>
          <li>Copiez le code depuis la fiche, ou demandez-le côté serveur : <code>GET /api/v1/models/{id}/integration-code</code> renvoie <code>iframe_html</code>, <code>widget_html</code> et <code>public_id</code>.</li>
          <li>Collez l’une des deux variantes dans la page produit. Remplacez <code>UUID_PUBLIC</code> par l’identifiant public réel de votre modèle.</li>
        </ol>
        ${codeBlock("HTML · IFrame", `<iframe src="${base}/embed/UUID_PUBLIC" title="Aperçu 3D du produit"\n  width="100%" height="480" loading="lazy" style="border:0"></iframe>`)}
        ${codeBlock("HTML · Widget Forma3D", `<script src="${base}/static/widget.js?v=20261111-ui" defer></script>\n<forma3d-viewer model="UUID_PUBLIC" height="480" auto-rotate></forma3d-viewer>`)}
        <p>Le widget ne reçoit jamais la clé API : il crée seulement une iframe vers la page publique <code>/embed/{public_id}</code>. Hauteur acceptée : 240 à 1200 px. Une page de test autonome est fournie dans <code>examples/integration.html</code>.</p>
      </section>

      <section class="panel guide-section" id="guide-limits" aria-labelledby="guide-limits-title">
        <h2 id="guide-limits-title">5. Quotas, erreurs et origines autorisées</h2>
        <ul class="guide-list">
          <li><strong>Quotas par clé</strong> : <code>API_DAILY_GENERATION_LIMIT</code> créations par jour UTC (20 par défaut) et <code>API_RATE_LIMIT_PER_MINUTE</code> requêtes par minute (10 par défaut). Au-delà : <code>429</code> avec <code>Retry-After</code>.</li>
          <li><strong>Erreurs</strong> : <code>401</code> clé absente ou révoquée, <code>403</code> catégorie inactive ou intégration non activée, <code>404</code> modèle inconnu, <code>409</code> modèle pas encore prêt, <code>413/415/422</code> photo refusée.</li>
          <li><strong>Iframe sur un autre domaine</strong> : ajoutez l’origine exacte du site à <code>EMBED_ALLOWED_ORIGINS</code> (règle CSP <code>frame-ancestors</code>), puis redémarrez le backend.</li>
          <li><strong>Appels JavaScript directs à l’API</strong> : l’origine doit aussi figurer dans <code>API_CORS_ORIGINS</code>. Les deux listes sont vides par défaut et refusent <code>*</code>.</li>
        </ul>
      </section>

      <section class="panel guide-section" id="guide-security" aria-labelledby="guide-security-title">
        <h2 id="guide-security-title">6. Sécurité et limites</h2>
        <ul class="guide-list">
          <li>La clé API est un secret serveur : ne la mettez ni dans le HTML, ni dans une application distribuée, ni dans Git.</li>
          <li>Après activation, quiconque connaît l’UUID public peut voir le modèle. Désactivez l’intégration sur la fiche pour couper l’accès public.</li>
          <li>Les exemples locaux utilisent HTTP. Un usage hors de votre machine demande un hébergement HTTPS et une protection d’accès au Studio.</li>
          <li>Forma3D est un prototype de démonstration, pas un service de production : le service gratuit de génération peut être indisponible et ne garantit ni délai ni qualité.</li>
        </ul>
      </section>
    </section>`;
}

export function mount() {
  document.querySelectorAll("[data-copy-code]").forEach((button) => {
    button.addEventListener("click", async () => {
      const code = button.closest(".code-block").querySelector("code").textContent;
      try {
        await navigator.clipboard.writeText(code);
        button.textContent = "Copié ✓";
        button.dataset.copied = "true";
        window.setTimeout(() => { button.textContent = "Copier"; button.dataset.copied = "false"; }, 1800);
      } catch {
        button.textContent = "Copie indisponible";
      }
    });
  });
}
