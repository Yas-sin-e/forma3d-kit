/*
 * Rôle : présente les états connus de l'API sans afficher de pourcentage fictif.
 * Exécution : main.js l'actualise après l'envoi de la photo et à chaque réponse de suivi.
 */
const statusCopy = {
  IDLE: ["Aucune génération lancée.", "Le suivi affichera uniquement les états renvoyés par le serveur."],
  SENDING: ["Envoi de la photo…", "Le navigateur transmet la photo validée au serveur."],
  PENDING: ["Photo reçue · demande en file", "Le serveur a accepté la photo et la génération est en attente."],
  RUNNING: ["Création du modèle 3D en cours", "Votre modèle est en préparation à partir de la photo."],
  DONE: ["Modèle prêt", "Votre modèle est disponible dans l’aperçu."],
  FAILED: ["La création a échoué", "Aucun modèle n’a été créé. Vous pouvez réessayer avec la même photo."],
};

const stepForStatus = {
  SENDING: 0,
  PENDING: 1,
  RUNNING: 2,
  DONE: 4,
};

export function createProgressView() {
  const panel = document.querySelector("#progress-panel");
  const summary = document.querySelector("#progress-summary");
  const detail = document.querySelector("#progress-detail");
  const steps = [...document.querySelectorAll("#progress-steps .progress-step")];
  const elapsedTime = document.querySelector("#elapsed-time");
  const elapsedSeconds = document.querySelector("#elapsed-seconds");
  const retryButton = document.querySelector("#retry-button");

  function render(status, options = {}) {
    const [defaultSummary, defaultDetail] = statusCopy[status] ?? statusCopy.FAILED;
    const activeStep = status === "FAILED"
      ? Math.max(0, steps.findIndex((step) => step.dataset.state === "active"))
      : stepForStatus[status];

    panel.dataset.status = status;
    panel.setAttribute("aria-busy", ["SENDING", "PENDING", "RUNNING"].includes(status) ? "true" : "false");
    summary.textContent = options.summary ?? defaultSummary;
    detail.textContent = options.detail ?? defaultDetail;
    retryButton.hidden = status !== "FAILED";
    elapsedTime.hidden = options.elapsedSeconds === undefined;
    if (options.elapsedSeconds !== undefined) {
      elapsedSeconds.textContent = String(options.elapsedSeconds);
    }

    steps.forEach((step, index) => {
      let state = "todo";
      if (status === "DONE") state = "complete";
      else if (status === "FAILED" && index === activeStep) state = "error";
      else if (Number.isInteger(activeStep) && index < activeStep) state = "complete";
      else if (Number.isInteger(activeStep) && index === activeStep) state = "active";

      step.dataset.state = state;
      step.removeAttribute("aria-current");
      const marker = step.querySelector(".step-marker");
      if (index === 0) {
        step.querySelector("span:last-child").textContent = status === "SENDING"
          ? "Envoi de la photo"
          : "Photo envoyée";
      }
      if (state === "complete") marker.textContent = "✓";
      else if (state === "error") marker.textContent = "!";
      else marker.textContent = String(index + 1);
      if (state === "active" || state === "error") step.setAttribute("aria-current", "step");
    });
  }

  retryButton.addEventListener("click", () => {
    retryButton.dispatchEvent(new CustomEvent("forma3d:retry", { bubbles: true }));
  });

  render("IDLE");
  return { render };
}
