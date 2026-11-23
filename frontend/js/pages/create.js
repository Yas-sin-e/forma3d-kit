/*
 * Rôle : présente le parcours photo, la progression réelle et le viewer de création.
 * Exécution : router.js monte cette page sur #/creer et la conserve en mémoire de navigation.
 * Refonte : deux colonnes (40 % photo / 60 % viewer), suivi compact en dessous ;
 * le stepper en 3 étapes (redondant avec le suivi) et la note encadrée sont supprimés,
 * les conseils et détails techniques sont repliés en bas du formulaire.
 */
// Importe l'envoi d'une photo, le suivi et la liste des catégories.
import { createGeneration, getGenerationStatus, listCategories } from "../api.js?v=20261117-r2";
// Importe l'état partagé et ses fonctions de suivi.
import { appState, beginGeneration, stopGenerationTimers, updateElapsedSeconds, updateGenerationStatus } from "../state.js?v=20261117-r2";
// Importe le formulaire d'envoi.
import { setupUploader } from "../views/uploader.js?v=20261117-r2";
// Importe le panneau de suivi.
import { createProgressView } from "../views/progress.js?v=20261117-r2";
// Importe le viewer 3D.
import { setupViewer } from "../views/viewer.js?v=20261117-r2";
// Importe le balisage du viewer.
import { viewerMarkup } from "./viewer-markup.js?v=20261117-r2";

// Titre de l'onglet.
export const title = "Créer";

// Retourne le HTML de la page Créer (formulaire photo, viewer, suivi). Le routeur l'insère dans #app.
export function render() {
  // Le gabarit ci-dessous contient, dans l'ordre :
  // - l'introduction « Créez votre modèle 3D » ;
  // - la colonne de gauche : formulaire avec zone de dépôt de photo, aperçu, catégorie, message, bouton « Créer » ;
  // - une note de confidentialité, puis les conseils photo et les détails techniques repliables ;
  // - la colonne de droite : le viewer (viewerMarkup) ;
  // - en dessous, le suivi : 5 étapes, résumé de l'état, temps écoulé, avertissement photo, Réessayer, lien vers la fiche.
  return `
    <section class="page-shell create-page">
      <div class="page-intro">
        <p class="eyebrow">Atelier produit</p>
        <h1 class="page-title" id="create-page-title" tabindex="-1">Créez votre modèle 3D</h1>
        <p class="page-lead">Déposez une photo de votre produit, choisissez sa catégorie : l’aperçu 3D apparaît à droite.</p>
      </div>
      <section class="workspace" aria-label="Création et aperçu du produit">
          <form class="panel upload-panel" id="upload-form" aria-labelledby="photo-category-title">
            <div class="section-heading"><h2 id="photo-category-title">Photo et catégorie</h2><p>Une photo nette, un seul objet, un fond uni.</p></div>
            <input class="visually-hidden" id="photo-input" name="file" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp">
            <label class="drop-zone" id="drop-zone" for="photo-input" aria-describedby="format-note">
              <img class="drop-preview" id="drop-preview" alt="" hidden>
              <span class="drop-icon" aria-hidden="true">+</span>
              <span class="drop-title">Glissez une photo ici</span>
              <span class="drop-divider">ou</span>
              <span class="button button-secondary">Choisir une photo</span>
              <span class="file-name" id="file-name">Aucun fichier sélectionné</span>
            </label>
            <p class="format-note" id="format-note">JPG, PNG ou WebP · 10 Mo maximum.</p>
            <div class="category-field">
              <label for="product-category">Catégorie du produit</label>
              <select class="category-select" id="product-category" name="category" required>
                <option value="" selected disabled>Choisir une catégorie</option>
              </select>
            </div>
            <p class="upload-feedback" id="upload-feedback" role="alert" hidden></p>
            <div class="service-unavailable-note" id="service-unavailable-note" role="status" hidden>
              <span>Serveur 3D hors ligne : création momentanément indisponible</span><a href="#/exemples">Voir les exemples</a>
            </div>
            <button class="button button-primary submit-button" id="submit-button" type="submit" disabled>
              <span class="button-label">Créer le modèle 3D</span><span aria-hidden="true">→</span>
            </button>
            <p class="submit-reason" id="submit-reason" role="status" aria-live="polite" aria-atomic="true">Choisissez une photo pour activer la création.</p>
            <p class="privacy-note">N’envoyez pas de visages ni de données personnelles : la photo peut être traitée par un service externe.</p>
            <div class="create-help">
              <details class="photo-guidance" aria-labelledby="photo-guidance-title">
                <summary id="photo-guidance-title">Conseils photo</summary>
                <div class="photo-guidance-content"><ul>
                  <li>Photographiez un seul objet sur un fond uni.</li>
                  <li>Choisissez une lumière douce et une vue de trois quarts.</li>
                  <li>Faites occuper environ 70 % de l’image par l’objet.</li>
                  <li>Utilisez une vraie photo, jamais une capture d’écran.</li>
                </ul></div>
              </details>
              <details class="technical-details">
                <summary>Détails techniques</summary>
                <p id="technical-health-message">Le serveur 3D est indisponible.</p>
                <p>Le serveur temporaire Colab peut expirer. Pour le relancer, exécutez le notebook puis mettez à jour HF_SPACE_ID dans backend/.env.</p>
              </details>
            </div>
          </form>
          <div class="create-viewer-column">${viewerMarkup}</div>
      </section>
      <section class="panel progress-panel" id="progress-panel" aria-labelledby="progress-title" aria-busy="false">
        <div class="progress-content">
          <div class="progress-track-column">
            <div class="progress-title-row"><h2 id="progress-title">Suivi de création</h2></div>
            <div class="progress-scroll" tabindex="0" role="region" aria-label="Étapes de création, faites défiler horizontalement si nécessaire">
              <ol class="progress-steps" id="progress-steps" aria-label="Étapes renvoyées par le serveur">
                <li class="progress-step" data-step="0"><span class="step-marker" aria-hidden="true">1</span><span>Photo envoyée</span></li>
                <li class="progress-step" data-step="1"><span class="step-marker" aria-hidden="true">2</span><span>En file</span></li>
                <li class="progress-step" data-step="2"><span class="step-marker" aria-hidden="true">3</span><span>Création du modèle</span></li>
                <li class="progress-step" data-step="3"><span class="step-marker" aria-hidden="true">4</span><span>Validation du GLB</span></li>
                <li class="progress-step" data-step="4"><span class="step-marker" aria-hidden="true">5</span><span>Terminé</span></li>
              </ol>
            </div>
          </div>
          <div class="progress-output">
            <div class="progress-meta"><span class="activity-indicator" id="activity-indicator" aria-hidden="true"></span><div class="progress-live" role="status" aria-live="polite" aria-atomic="true"><p id="progress-summary">Aucune création en cours.</p><p id="progress-detail">Les états affichés viennent du serveur.</p></div></div>
            <p class="elapsed-time" id="elapsed-time" hidden>Temps écoulé : <span id="elapsed-seconds">0</span> s</p>
            <p class="image-preparation-warning" id="image-preparation-warning" role="status" aria-live="polite" hidden></p>
            <p class="timing-note">Le délai dépend de la disponibilité du service gratuit.</p>
            <button class="button button-secondary retry-button" id="retry-button" type="button" hidden>Réessayer avec cette photo</button>
            <a class="button button-primary detail-result-link" id="model-detail-link" href="#" hidden>Ouvrir la fiche du modèle →</a>
          </div>
        </div>
      </section>
    </section>
  `;
}

/* « 90 secondes » ou « 2 minutes » : délai lisible tiré de l'en-tête Retry-After. */
function formatWait(seconds) {
  // Moins d'une minute : en secondes (avec accord).
  if (seconds < 60) return `${seconds} seconde${seconds > 1 ? "s" : ""}`;
  // Sinon : minutes arrondies au-dessus.
  const minutes = Math.ceil(seconds / 60);
  // En minutes (avec accord).
  return `${minutes} minute${minutes > 1 ? "s" : ""}`;
}

/*
 * Traduit l'échec de l'envoi (POST /models) en titre + cause + action, sans jeton, chemin ni trace.
 * Codes réels du backend : 400 fichier vide ou nom invalide, 413 plus de 10 Mo, 415 format, type ou
 * contenu refusé (upload_validator.py), 422 catégorie inconnue ou désactivée, 401 session expirée.
 */
export function describeUploadError(error) {
  // Erreur réseau (le navigateur n'a pas joint le serveur)...
  if (error instanceof TypeError) {
    // ...titre et message.
    return ["Studio injoignable", "Le Studio ne répond pas. Vérifiez que le serveur est lancé (scripts/dev.ps1) et votre connexion, puis réessayez."];
  }
  // Message exact du serveur, s'il existe.
  const detail = typeof error?.serverDetail === "string" ? error.serverDetail.trim() : "";
  // Choix selon le code HTTP...
  switch (error?.status) {
    // 400 : fichier vide ou nom invalide.
    case 400:
      // Titre et message.
      return ["Photo refusée", `${detail || "Le fichier envoyé n'est pas utilisable."} Choisissez une autre photo puis réessayez.`];
    // 413 : trop lourd.
    case 413:
      // Titre et message.
      return ["Photo trop lourde", "Votre photo dépasse 10 Mo. Réduisez-la ou choisissez une image plus légère."];
    // 415 : format refusé.
    case 415:
      // Titre et message.
      return ["Format non accepté", `${detail || "Ce format de fichier n'est pas accepté."} Enregistrez la photo en JPG, PNG ou WebP avec un logiciel d'image (renommer le fichier ne suffit pas), puis réessayez.`];
    // 422 : catégorie refusée.
    case 422:
      // Titre et message.
      return ["Catégorie indisponible", `${detail || "La catégorie choisie n'est pas valide."} Choisissez une autre catégorie, ou réactivez-la dans Administration → Catégories.`];
    // 401 : session expirée.
    case 401:
      // Titre et message.
      return ["Session expirée", "Votre session a expiré. Reconnectez-vous : la page de connexion va s'ouvrir."];
    // 429 : trop de demandes...
    case 429:
      // ...délai connu...
      return ["Trop de demandes", error.retryAfterSeconds
        // ...message avec le délai...
        ? `Trop de demandes en peu de temps. Réessayez dans ${formatWait(error.retryAfterSeconds)}.`
        // ...sinon message sans délai.
        : "Trop de demandes en peu de temps. Patientez un moment, puis réessayez."];
    // Erreurs du serveur (500, 502, 503, 504)...
    case 500:
    case 502:
    case 503:
    case 504:
      // ...titre et message.
      return ["Erreur du serveur", "Le serveur a rencontré un problème. Réessayez dans un instant ; si cela continue, redémarrez le serveur."];
    // Tout autre cas...
    default:
      // ...titre et message générique.
      return ["Création indisponible", "Impossible de lancer la création pour une raison inattendue. Réessayez ; si cela continue, redémarrez le serveur."];
  }
}

// Garde seulement le chemin d'une adresse renvoyée par le serveur, et refuse une adresse d'un autre site.
function sameOriginPath(value) {
  // Transforme la valeur en adresse complète.
  const url = new URL(value, window.location.origin);
  // Autre site : refus.
  if (url.origin !== window.location.origin) throw new Error("Le serveur a renvoyé une adresse inattendue.");
  // Renvoie seulement le chemin et les paramètres.
  return url.pathname + url.search;
}

// Branche la page Créer : formulaire, viewer, suivi, état du serveur 3D.
// Appelée par le routeur juste après render() (équivalent de ngOnInit d'Angular).
export function mount() {
  // Branche le formulaire ; startGeneration est appelée à l'envoi.
  const uploader = setupUploader(startGeneration);
  // Branche le panneau de suivi.
  const progress = createProgressView();
  // Branche le viewer.
  const viewer = setupViewer();
  // Panneau de suivi.
  const progressPanel = document.querySelector("#progress-panel");
  // Avertissement de préparation photo.
  const warning = document.querySelector("#image-preparation-warning");
  // Note « serveur 3D hors ligne ».
  const unavailable = document.querySelector("#service-unavailable-note");
  // Message technique du serveur 3D.
  const technicalMessage = document.querySelector("#technical-health-message");
  // Lien vers la fiche du modèle créé.
  const resultLink = document.querySelector("#model-detail-link");

  // Rafraîchit le panneau de suivi avec le temps écoulé.
  function updateProgress(status, options = {}) {
    // Temps écoulé, ou rien si aucune génération.
    const elapsedSeconds = appState.generationStartedAt === null ? undefined : updateElapsedSeconds();
    // Actualise le panneau avec ce temps.
    progress.render(status, { ...options, elapsedSeconds });
  }

  // Arrête l'interrogation du serveur et oublie l'adresse de suivi.
  function stopTracking() {
    // Arrête les minuteurs.
    stopGenerationTimers();
    // Oublie l'adresse de suivi.
    appState.currentStatusUrl = null;
  }

  // Affiche un échec (titre + message) et rend le formulaire de nouveau utilisable.
  function showFailure(message, titleText = "La création a échoué") {
    // Temps écoulé.
    const elapsedSeconds = appState.generationStartedAt === null ? undefined : updateElapsedSeconds();
    // Arrête le suivi.
    stopTracking();
    // État : échec.
    updateGenerationStatus("FAILED");
    // Déverrouille le formulaire.
    uploader.setBusy(false);
    // Affiche l'échec.
    progress.render("FAILED", { summary: titleText, detail: message, elapsedSeconds });
  }

  // Applique l'état renvoyé par le serveur : suivi si PENDING/RUNNING, message réel si FAILED,
  // affichage du modèle et lien vers sa fiche si DONE. Renvoie true quand le suivi est terminé.
  async function applyStatus(data) {
    // Avertissement visible seulement s'il existe.
    warning.hidden = !data.image_warning;
    // Texte de l'avertissement...
    warning.textContent = data.image_warning
      // ...suivi d'un conseil...
      ? `${data.image_warning} Conseil : choisissez une photo nette, bien éclairée et centrée sur un seul objet.`
      // ...sinon vide.
      : "";
    // En attente ou en cours...
    if (data.status === "PENDING" || data.status === "RUNNING") {
      // ...mémorise l'état...
      updateGenerationStatus(data.status);
      // ...actualise le panneau...
      updateProgress(data.status);
      // ...le suivi continue.
      return false;
    }
    // Échec...
    if (data.status === "FAILED") {
      // Le serveur fournit la vraie cause (quota, Space indisponible…), déjà nettoyée de tout secret.
      // ...affiche le message du serveur (ou un message de repli)...
      showFailure(data.error_message || "Nous n’avons pas pu créer ce modèle. Vérifiez la photo et réessayez.");
      // ...le suivi est terminé.
      return true;
    }
    // État inattendu ou pas d'adresse de GLB...
    if (data.status !== "DONE" || !data.model_url) {
      // ...échec « réponse incomplète »...
      showFailure("Le serveur n’a pas fourni de fichier terminé.", "Réponse incomplète");
      // ...suivi terminé.
      return true;
    }

    // Chemin du GLB (même site seulement).
    const modelUrl = sameOriginPath(data.model_url);
    // Arrête le suivi.
    stopTracking();
    // État : terminé.
    updateGenerationStatus("DONE");
    // Déverrouille le formulaire.
    uploader.setBusy(false);
    // Affiche le modèle dans le viewer...
    viewer.showModel({
      // ...adresse du GLB...
      url: modelUrl,
      // ...adresse de téléchargement...
      downloadUrl: modelUrl,
      // ...nom de fichier...
      filename: data.filename,
      // ...source : généré...
      source: "generated",
      // ...catégorie...
      category: data.category,
      // ...photo source (fichier local).
      sourcePhoto: appState.selectedPhoto,
    });
    // Adresse de la fiche du modèle.
    resultLink.href = `#/modeles/${encodeURIComponent(data.id)}`;
    // Lien visible.
    resultLink.hidden = false;
    // Panneau : modèle prêt.
    progress.render("DONE", { summary: "Votre modèle est prêt", detail: "Le fichier a été vérifié et peut être téléchargé.", elapsedSeconds: updateElapsedSeconds() });
    // Suivi terminé.
    return true;
  }

  // Interroge l'adresse de suivi (GET /models/{id}) ; pollingInFlight évite deux requêtes en même temps.
  async function refreshStatus() {
    // Pas d'adresse ou interrogation déjà en cours : arrêt.
    if (!appState.currentStatusUrl || appState.pollingInFlight) return false;
    // Marque l'interrogation en cours.
    appState.pollingInFlight = true;
    // Essaie...
    try {
      // ...de lire l'état et de l'appliquer.
      return await applyStatus(await getGenerationStatus(appState.currentStatusUrl));
    // Erreur...
    } catch (error) {
      // ...échec « suivi indisponible »...
      showFailure("La mise à jour s’est interrompue. Vérifiez votre connexion puis réessayez.", "Suivi indisponible");
      // ...suivi terminé.
      return true;
    // Dans tous les cas...
    } finally {
      // ...l'interrogation est finie.
      appState.pollingInFlight = false;
    }
  }

  // Lance une génération : POST /models, puis interrogation toutes les 1,5 s jusqu'à DONE ou FAILED.
  // Si l'envoi échoue, describeUploadError explique la cause et l'action à faire.
  async function startGeneration(photo, category) {
    // Génération déjà en cours ou pas de photo : arrêt.
    if (appState.isGenerating || !photo) return;
    // Arrête un ancien suivi.
    stopTracking();
    // Démarre l'état de génération.
    beginGeneration(photo);
    // Masque l'avertissement.
    warning.hidden = true;
    // Efface son texte.
    warning.textContent = "";
    // Masque le lien vers la fiche.
    resultLink.hidden = true;
    // Vide le viewer.
    viewer.clear();
    // Verrouille le formulaire.
    uploader.setBusy(true);
    // Panneau : envoi en cours.
    progress.render("SENDING", { elapsedSeconds: 0 });
    // Chronomètre : actualise le panneau chaque seconde.
    appState.clockTimer = window.setInterval(() => updateProgress(appState.generationStatus), 1000);
    // Essaie...
    try {
      // ...d'envoyer la photo...
      const data = await createGeneration(photo, category);
      // ...pas d'adresse de suivi : erreur...
      if (typeof data.status_url !== "string") throw new Error("La réponse ne contient pas le suivi de la création.");
      // ...mémorise l'adresse de suivi...
      appState.currentStatusUrl = sameOriginPath(data.status_url);
      // ...applique le premier état reçu...
      const terminal = await applyStatus(data);
      // ...et interroge toutes les 1,5 seconde si le travail n'est pas fini.
      if (!terminal && appState.currentStatusUrl) appState.pollingTimer = window.setInterval(() => void refreshStatus(), 1500);
    // Erreur d'envoi...
    } catch (error) {
      // Cause exacte et action à faire ; pour 401, api.js renvoie en plus vers la page de connexion.
      // ...titre et message adaptés...
      const [titleText, message] = describeUploadError(error);
      // ...affichés.
      showFailure(message, titleText);
    }
  }

  // Réagit à l'état du serveur 3D (événement forma3d:health) : active ou bloque la création.
  function updateProviderHealth(event) {
    // État reçu par l'événement, sinon celui de l'état partagé.
    const health = event?.detail ?? appState.providerHealth;
    // Vrai si le serveur est en ligne.
    const online = health?.status === "ONLINE";
    // Note « hors ligne » masquée si en ligne.
    unavailable.hidden = online;
    // Message technique.
    technicalMessage.textContent = health?.message || "Relancez le serveur 3D puis actualisez la page.";
    // Active ou bloque le bouton « Créer ».
    uploader.setProviderAvailable(online);
  }

  // Bouton Réessayer (événement venu du panneau)...
  progressPanel.addEventListener("forma3d:retry", () => {
    // ...photo choisie...
    const photo = uploader.getSelectedPhoto();
    // ...catégorie choisie...
    const category = uploader.getSelectedCategory();
    // ...relance si tout est prêt.
    if (photo && category && !appState.isGenerating) void startGeneration(photo, category);
  });
  // Écoute les changements d'état du serveur 3D.
  window.addEventListener("forma3d:health", updateProviderHealth);
  // Applique l'état actuel.
  updateProviderHealth();
  // Charge toutes les catégories pour le formulaire ; en cas d'échec, affiche l'erreur.
  void listCategories(true).then((response) => uploader.setCategories(response.items ?? [])).catch((error) => uploader.setError(error.message));
}
