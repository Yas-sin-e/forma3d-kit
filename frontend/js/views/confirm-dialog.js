/*
 * Rôle : remplace window.confirm() par une fenêtre modale accessible aux couleurs du Studio.
 * Exécution : les pages appellent confirmDialog({...}) avant une action sensible (révoquer, supprimer).
 * La promesse renvoie true si la propriétaire confirme, false si elle annule ou ferme.
 *
 * Les boutons concluent directement (finish) : on ne dépend pas seulement de l'événement « close »,
 * qui peut ne pas être déclenché par certains navigateurs. Cet événement reste écouté pour la touche
 * Échap ; finish() garantit qu'une seule réponse est donnée et que la fenêtre est retirée.
 */
// Fonction exportée ; les paramètres ont des valeurs par défaut.
export function confirmDialog({ title, message, confirmLabel = "Confirmer", cancelLabel = "Annuler", danger = false }) {
  // Renvoie une promesse : elle sera résolue quand la propriétaire répondra.
  return new Promise((resolve) => {
    // <dialog> : élément HTML natif de fenêtre modale. showModal() l'ouvre au premier plan et bloque le reste de la page.
    // Crée l'élément <dialog>.
    const dialog = document.createElement("dialog");
    // Classe CSS de la fenêtre.
    dialog.className = "confirm-dialog";
    // Le titre de la fenêtre sert de nom accessible.
    dialog.setAttribute("aria-labelledby", "confirm-dialog-title");
    // Le message sert de description accessible.
    dialog.setAttribute("aria-describedby", "confirm-dialog-message");

    // Crée le titre.
    const heading = document.createElement("h2");
    // Identifiant référencé par aria-labelledby.
    heading.id = "confirm-dialog-title";
    // Texte du titre (textContent : aucun HTML interprété).
    heading.textContent = title;
    // Crée le paragraphe du message.
    const text = document.createElement("p");
    // Identifiant référencé par aria-describedby.
    text.id = "confirm-dialog-message";
    // Texte du message.
    text.textContent = message;

    // Crée la zone des boutons.
    const actions = document.createElement("div");
    // Classe CSS de cette zone.
    actions.className = "confirm-dialog-actions";
    // Crée le bouton Annuler.
    const cancel = document.createElement("button");
    // Type « button » : ne soumet aucun formulaire.
    cancel.type = "button";
    // Style secondaire.
    cancel.className = "button button-secondary";
    // Texte du bouton.
    cancel.textContent = cancelLabel;
    // Crée le bouton Confirmer.
    const confirm = document.createElement("button");
    // Type « button ».
    confirm.type = "button";
    // Style rouge pour une action dangereuse, sinon style principal.
    confirm.className = danger ? "button button-danger-solid" : "button button-primary";
    // Texte du bouton.
    confirm.textContent = confirmLabel;
    // Place les deux boutons.
    actions.append(cancel, confirm);
    // Assemble la fenêtre.
    dialog.append(heading, text, actions);
    // Ajoute la fenêtre à la page.
    document.body.append(dialog);

    // Vrai dès qu'une réponse a été donnée.
    let settled = false;
    // Donne la réponse une seule fois (true = confirmé), ferme et retire la fenêtre.
    function finish(answer) {
      // Réponse déjà donnée : on ignore.
      if (settled) return;
      // Marque la réponse comme donnée.
      settled = true;
      // Ferme la fenêtre si elle est ouverte.
      if (dialog.open) dialog.close();
      // La retire de la page.
      dialog.remove();
      // Résout la promesse avec la réponse.
      resolve(answer);
    }

    // Annuler = faux.
    cancel.addEventListener("click", () => finish(false));
    // Confirmer = vrai.
    confirm.addEventListener("click", () => finish(true));
    // Clic dans la fenêtre...
    dialog.addEventListener("click", (event) => {
      // ...sur le fond (hors du contenu) : annulation.
      if (event.target === dialog) finish(false);
    });
    // Touche Échap : le navigateur ferme la fenêtre lui-même, ce qui vaut une annulation.
    // Échap : annulation.
    dialog.addEventListener("cancel", () => finish(false));
    // Toute autre fermeture : annulation.
    dialog.addEventListener("close", () => finish(false));

    // Ouvre la fenêtre au premier plan.
    dialog.showModal();
    // Place le focus sur Annuler (choix le plus prudent).
    cancel.focus();
  });
}
