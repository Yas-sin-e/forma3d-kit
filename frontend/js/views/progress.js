/*
 * Rôle : présente les états connus de l'API sans afficher de pourcentage fictif.
 * Exécution : main.js l'actualise après l'envoi de la photo et à chaque réponse de suivi.
 */
// Textes (titre, détail) affichés pour chaque état.
const statusCopy = {
  // Aucun travail.
  IDLE: ["Aucune génération lancée.", "Le suivi affichera uniquement les états renvoyés par le serveur."],
  // Envoi en cours.
  SENDING: ["Envoi de la photo…", "Le navigateur transmet la photo validée au serveur."],
  // En attente côté serveur.
  PENDING: ["Photo reçue · demande en file", "Le serveur a accepté la photo et la génération est en attente."],
  // Génération en cours.
  RUNNING: ["Création du modèle 3D en cours", "Votre modèle est en préparation à partir de la photo."],
  // Terminé.
  DONE: ["Modèle prêt", "Votre modèle est disponible dans l’aperçu."],
  // Échec.
  FAILED: ["La création a échoué", "Aucun modèle n’a été créé. Vous pouvez réessayer avec la même photo."],
};

// Étape à mettre en évidence pour chaque état (de 0 à 4).
const stepForStatus = {
  // Envoi : étape 1.
  SENDING: 0,
  // En attente : étape 2.
  PENDING: 1,
  // En cours : étape 3.
  RUNNING: 2,
  // Terminé : au-delà de la dernière étape (tout est fait).
  DONE: 4,
};

// Prépare le panneau « Suivi de création » et renvoie la fonction render qui l'actualise.
export function createProgressView() {
  // Panneau de suivi.
  const panel = document.querySelector("#progress-panel");
  // Titre de l'état.
  const summary = document.querySelector("#progress-summary");
  // Détail de l'état.
  const detail = document.querySelector("#progress-detail");
  // Les étapes, converties en tableau.
  const steps = [...document.querySelectorAll("#progress-steps .progress-step")];
  // Zone du temps écoulé.
  const elapsedTime = document.querySelector("#elapsed-time");
  // Nombre de secondes affiché.
  const elapsedSeconds = document.querySelector("#elapsed-seconds");
  // Bouton « Réessayer ».
  const retryButton = document.querySelector("#retry-button");

  // Affiche l'état reçu : titre, détail, temps écoulé, et colore les 5 étapes (faite, active, erreur, à venir).
  function render(status, options = {}) {
    // Textes de l'état (ceux de l'échec si l'état est inconnu).
    const [defaultSummary, defaultDetail] = statusCopy[status] ?? statusCopy.FAILED;
    // Étape active : en cas d'échec, celle qui était en cours...
    const activeStep = status === "FAILED"
      ? Math.max(0, steps.findIndex((step) => step.dataset.state === "active"))
      // ...sinon celle associée à l'état.
      : stepForStatus[status];

    // data-status : le CSS colore le panneau.
    panel.dataset.status = status;
    // aria-busy : signale aux lecteurs d'écran un travail en cours.
    panel.setAttribute("aria-busy", ["SENDING", "PENDING", "RUNNING"].includes(status) ? "true" : "false");
    // Titre (personnalisé ou par défaut).
    summary.textContent = options.summary ?? defaultSummary;
    // Détail (personnalisé ou par défaut).
    detail.textContent = options.detail ?? defaultDetail;
    // Bouton Réessayer visible seulement en cas d'échec.
    retryButton.hidden = status !== "FAILED";
    // Temps masqué s'il n'est pas fourni.
    elapsedTime.hidden = options.elapsedSeconds === undefined;
    // Temps fourni...
    if (options.elapsedSeconds !== undefined) {
      // ...on l'affiche.
      elapsedSeconds.textContent = String(options.elapsedSeconds);
    }

    // Pour chaque étape...
    steps.forEach((step, index) => {
      // ...« à venir » par défaut...
      let state = "todo";
      // ...tout est fait si terminé...
      if (status === "DONE") state = "complete";
      // ...erreur sur l'étape qui a échoué...
      else if (status === "FAILED" && index === activeStep) state = "error";
      // ...faite si elle précède l'étape active...
      else if (Number.isInteger(activeStep) && index < activeStep) state = "complete";
      // ...active si c'est l'étape en cours.
      else if (Number.isInteger(activeStep) && index === activeStep) state = "active";

      // data-state : le CSS colore l'étape.
      step.dataset.state = state;
      // Retire l'indication d'étape courante.
      step.removeAttribute("aria-current");
      // Pastille de l'étape (numéro ou symbole).
      const marker = step.querySelector(".step-marker");
      // Première étape : son libellé change selon l'état...
      if (index === 0) {
        // ...« Envoi de la photo » pendant l'envoi...
        step.querySelector("span:last-child").textContent = status === "SENDING"
          ? "Envoi de la photo"
          // ...sinon « Photo envoyée ».
          : "Photo envoyée";
      }
      // Faite : coche.
      if (state === "complete") marker.textContent = "✓";
      // Erreur : point d'exclamation.
      else if (state === "error") marker.textContent = "!";
      // Sinon : numéro de l'étape.
      else marker.textContent = String(index + 1);
      // Étape active ou en erreur : signalée aux lecteurs d'écran.
      if (state === "active" || state === "error") step.setAttribute("aria-current", "step");
    });
  }

  // Clic sur Réessayer...
  retryButton.addEventListener("click", () => {
    // ...envoie un événement qui remonte jusqu'à la page Créer.
    retryButton.dispatchEvent(new CustomEvent("forma3d:retry", { bubbles: true }));
  });

  // Affiche l'état initial.
  render("IDLE");
  // Renvoie la fonction d'actualisation.
  return { render };
}
