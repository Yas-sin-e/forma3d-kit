/*
 * Rôle : remplace window.confirm() par une fenêtre modale accessible aux couleurs du Studio.
 * Exécution : les pages appellent confirmDialog({...}) avant une action sensible (révoquer, supprimer).
 * La promesse renvoie true si la propriétaire confirme, false si elle annule ou ferme.
 */
export function confirmDialog({ title, message, confirmLabel = "Confirmer", cancelLabel = "Annuler", danger = false }) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "confirm-dialog";
    dialog.setAttribute("aria-labelledby", "confirm-dialog-title");
    dialog.setAttribute("aria-describedby", "confirm-dialog-message");

    const heading = document.createElement("h2");
    heading.id = "confirm-dialog-title";
    heading.textContent = title;
    const text = document.createElement("p");
    text.id = "confirm-dialog-message";
    text.textContent = message;

    const actions = document.createElement("div");
    actions.className = "confirm-dialog-actions";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "button button-secondary";
    cancel.textContent = cancelLabel;
    const confirm = document.createElement("button");
    confirm.type = "button";
    confirm.className = danger ? "button button-danger-solid" : "button button-primary";
    confirm.textContent = confirmLabel;
    actions.append(cancel, confirm);
    dialog.append(heading, text, actions);
    document.body.append(dialog);

    let answer = false;
    cancel.addEventListener("click", () => dialog.close());
    confirm.addEventListener("click", () => { answer = true; dialog.close(); });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      dialog.remove();
      resolve(answer);
    }, { once: true });

    dialog.showModal();
    cancel.focus();
  });
}
