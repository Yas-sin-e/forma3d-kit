/*
 * Rôle : gère le choix, le dépôt et la validation côté interface d'une photo.
 * Exécution : create.js initialise cette vue et reçoit le fichier quand le formulaire est soumis.
 * Refonte : la photo choisie s'affiche en vignette dans la zone de dépôt (URL locale, rien n'est envoyé).
 */
// Importe l'état partagé.
import { appState } from "../state.js?v=20261117-r2";

// Types MIME acceptés.
const acceptedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
// Extensions acceptées.
const acceptedExtensions = new Set(["jpg", "jpeg", "png", "webp"]);
// Taille maximale : 10 Mo en octets.
const maxUploadBytes = 10 * 1024 * 1024;

// Contrôle la photo DANS le navigateur avant tout envoi : extension, type, fichier vide, 10 Mo maximum.
// Renvoie un message d'erreur ou null. Le serveur refait toujours ces contrôles (on ne fait jamais confiance au navigateur).
function validatePhoto(file) {
  // Extension du fichier en minuscules.
  const extension = file.name.split(".").pop().toLowerCase();
  // Extension refusée, ou type annoncé refusé...
  if (!acceptedExtensions.has(extension) || (file.type && !acceptedTypes.has(file.type))) {
    // ...message d'erreur.
    return "Choisissez une photo JPG, PNG ou WebP.";
  }
  // Fichier vide.
  if (file.size === 0) return "Le fichier photo est vide.";
  // Fichier trop gros.
  if (file.size > maxUploadBytes) return "La limite de taille est de 10 Mo.";
  // Aucun problème.
  return null;
}

// Branche le formulaire d'envoi : choix ou glisser-déposer de la photo, catégorie, bouton de création.
// Entrées : onSubmit(photo, catégorie) appelé à l'envoi, onStateChange informé de chaque changement.
export function setupUploader(onSubmit, onStateChange = () => {}) {
  // Formulaire d'envoi.
  const form = document.querySelector("#upload-form");
  // Champ de choix du fichier.
  const photoInput = document.querySelector("#photo-input");
  // Liste déroulante des catégories.
  const categoryInput = document.querySelector("#product-category");
  // Zone de glisser-déposer.
  const dropZone = document.querySelector("#drop-zone");
  // Nom du fichier choisi.
  const fileName = document.querySelector("#file-name");
  // Bouton « Créer ».
  const submitButton = document.querySelector("#submit-button");
  // Texte qui explique l'état du bouton.
  const submitReason = document.querySelector("#submit-reason");
  // Zone d'erreur.
  const uploadFeedback = document.querySelector("#upload-feedback");
  // Bouton « Ouvrir un GLB local ».
  const openLocalButton = document.querySelector("#open-local-glb");
  // Image d'aperçu de la photo.
  const dropPreview = document.querySelector("#drop-preview");
  // Adresse temporaire de l'aperçu.
  let previewObjectUrl = null;
  // Photo choisie.
  let selectedPhoto = null;
  // Vrai pendant une génération.
  let busy = false;
  // Vrai si le serveur 3D est en ligne.
  let providerAvailable = false;
  // Vrai quand les catégories sont chargées.
  let categoriesLoaded = false;

  // Affiche ou efface le message d'erreur sous la zone de photo.
  function setFeedback(message = "") {
    // Texte de l'erreur.
    uploadFeedback.textContent = message;
    // Masquée si vide.
    uploadFeedback.hidden = message.length === 0;
  }

  // Active ou désactive le bouton « Créer » et explique pourquoi (photo, catégorie, serveur 3D, création en cours).
  function syncState() {
    // Erreur de la photo, s'il y en a une.
    const photoError = selectedPhoto ? validatePhoto(selectedPhoto) : "";
    // Vrai si une catégorie est choisie.
    const hasCategory = Boolean(categoryInput.value);
    // Bouton désactivé si une condition manque.
    submitButton.disabled = busy || !categoriesLoaded || !selectedPhoto || Boolean(photoError) || !hasCategory || !providerAvailable;
    // Le texte d'explication décrit le bouton (lecteurs d'écran).
    submitButton.setAttribute("aria-describedby", "submit-reason");
    // Raison : création en cours.
    if (busy) submitReason.textContent = "Création en cours.";
    // Raison : photo invalide.
    else if (photoError) submitReason.textContent = photoError;
    // Raison : pas de photo.
    else if (!selectedPhoto) submitReason.textContent = "Choisissez une photo pour activer la création.";
    // Raison : catégories en chargement.
    else if (!categoriesLoaded) submitReason.textContent = "Chargement des catégories…";
    // Raison : pas de catégorie.
    else if (!hasCategory) submitReason.textContent = "Choisissez une catégorie pour continuer.";
    // Raison : serveur 3D hors ligne.
    else if (!providerAvailable) submitReason.textContent = "Le serveur 3D est hors ligne. Consultez les exemples en attendant.";
    // Tout est prêt.
    else submitReason.textContent = "Tout est prêt pour créer le modèle.";
    // Prévient la page de l'état complet...
    onStateChange({
      // ...photo présente...
      hasPhoto: Boolean(selectedPhoto),
      // ...erreur éventuelle...
      photoError,
      // ...catégorie choisie...
      hasCategory,
      // ...serveur disponible...
      providerAvailable,
      // ...génération en cours.
      busy,
    });
  }

  // Affiche l'aperçu de la photo choisie.
  // URL.createObjectURL crée une adresse temporaire locale pour un fichier (rien n'est envoyé) ; revokeObjectURL la libère.
  function updatePreview(file, error) {
    // Ancien aperçu présent...
    if (previewObjectUrl !== null) {
      // ...on libère son adresse...
      URL.revokeObjectURL(previewObjectUrl);
      // ...et on l'oublie.
      previewObjectUrl = null;
    }
    // Pas d'image d'aperçu dans la page : rien à faire.
    if (!dropPreview) return;
    // Photo valide...
    if (file && !error) {
      // ...crée une adresse locale...
      previewObjectUrl = URL.createObjectURL(file);
      // ...l'affiche...
      dropPreview.src = previewObjectUrl;
      // ...rend l'image visible...
      dropPreview.hidden = false;
      // ...et change le style de la zone.
      dropZone.classList.add("has-photo");
    // Sinon...
    } else {
      // ...retire l'image...
      dropPreview.removeAttribute("src");
      // ...la masque...
      dropPreview.hidden = true;
      // ...et rétablit le style.
      dropZone.classList.remove("has-photo");
    }
  }

  // Mémorise la photo choisie, la valide, met à jour l'aperçu et l'état du bouton.
  function setSelectedPhoto(file) {
    // Photo choisie, ou null.
    selectedPhoto = file ?? null;
    // La recopie dans l'état partagé.
    appState.selectedPhoto = selectedPhoto;
    // Affiche son nom.
    fileName.textContent = selectedPhoto?.name ?? "Aucun fichier sélectionné";
    // Efface l'ancienne erreur.
    setFeedback("");
    // Valide la photo.
    const error = selectedPhoto ? validatePhoto(selectedPhoto) : "";
    // Affiche l'erreur éventuelle.
    if (error) setFeedback(error);
    // Met à jour l'aperçu.
    updatePreview(selectedPhoto, error);
    // Met à jour le bouton.
    syncState();
  }

  // Verrouille le formulaire pendant une génération et change le texte du bouton.
  function setBusy(isBusy) {
    // Mémorise l'état.
    busy = isBusy;
    // Verrouille le choix du fichier.
    photoInput.disabled = isBusy;
    // Verrouille la catégorie.
    categoryInput.disabled = isBusy;
    // Verrouille l'ouverture locale.
    openLocalButton.disabled = isBusy;
    // Signale le travail en cours aux lecteurs d'écran.
    submitButton.setAttribute("aria-busy", isBusy ? "true" : "false");
    // Texte du bouton.
    const label = submitButton.querySelector(".button-label");
    // Change ce texte.
    label.textContent = isBusy ? "Génération en cours" : "Créer le modèle 3D";
    // Met à jour le bouton.
    syncState();
  }

  // Nouveau fichier choisi : on le traite.
  photoInput.addEventListener("change", () => setSelectedPhoto(photoInput.files[0]));
  // Catégorie changée...
  categoryInput.addEventListener("change", () => {
    // ...efface l'erreur...
    setFeedback("");
    // ...met à jour le bouton.
    syncState();
  });

  // Pour l'entrée et le survol d'un fichier glissé...
  for (const eventName of ["dragenter", "dragover"]) {
    // ...on écoute l'événement...
    dropZone.addEventListener(eventName, (event) => {
      // ...empêche le navigateur d'ouvrir le fichier...
      event.preventDefault();
      // ...et montre la zone active.
      if (!busy) dropZone.classList.add("is-dragging");
    });
  }

  // Pour la sortie et le dépôt...
  for (const eventName of ["dragleave", "drop"]) {
    // ...on écoute l'événement...
    dropZone.addEventListener(eventName, (event) => {
      // ...empêche le comportement par défaut...
      event.preventDefault();
      // ...et retire le style actif.
      dropZone.classList.remove("is-dragging");
    });
  }

  // Au dépôt d'un fichier...
  dropZone.addEventListener("drop", (event) => {
    // ...génération en cours : ignoré.
    if (busy) return;
    // Fichiers déposés.
    const files = event.dataTransfer?.files;
    // Aucun fichier : rien à faire.
    if (!files?.length) return;
    // Essaie...
    try {
      // ...de les placer dans le champ de fichier...
      photoInput.files = files;
      // ...et traite le premier.
      setSelectedPhoto(files[0]);
    // Navigateur qui refuse...
    } catch {
      // ...message d'aide.
      setFeedback("Le navigateur n’a pas pu lire ce dépôt. Utilisez « Choisir une photo ».");
    }
  });

  // État initial du bouton.
  syncState();

  // À l'envoi du formulaire...
  form.addEventListener("submit", async (event) => {
    // ...empêche le rechargement de la page...
    event.preventDefault();
    // ...occupé ou pas de photo : on s'arrête.
    if (busy || !selectedPhoto) return;
    // Pas de catégorie...
    if (!categoryInput.value) {
      // ...message...
      setFeedback("Choisissez une catégorie pour ce produit.");
      // ...et arrêt.
      return;
    }
    // Revalide la photo.
    const error = validatePhoto(selectedPhoto);
    // Invalide...
    if (error) {
      // ...message...
      setFeedback(error);
      // ...et arrêt.
      return;
    }
    // Efface l'erreur.
    setFeedback("");
    // Transmet la photo et la catégorie à la page Créer.
    await onSubmit(selectedPhoto, categoryInput.value);
  });

  // Renvoie les fonctions utilisables par la page...
  return {
    // ...photo choisie...
    getSelectedPhoto: () => selectedPhoto,
    // ...catégorie choisie...
    getSelectedCategory: () => categoryInput.value,
    // ...verrouillage...
    setBusy,
    // ...affichage d'une erreur...
    setError: setFeedback,
    // ...remplissage de la liste des catégories :
    setCategories(categories) {
      // valeur choisie avant le rechargement...
      const previousValue = categoryInput.value;
      // ...catégories actives seulement...
      const activeCategories = categories.filter((category) => category.is_active);
      // ...option vide en premier...
      categoryInput.replaceChildren(new Option("Choisir une catégorie", ""));
      // ...pour chaque catégorie active...
      for (const category of activeCategories) {
        // ...ajoute une option (libellé affiché, slug envoyé).
        categoryInput.add(new Option(category.label, category.slug));
      }
      // Catégories chargées.
      categoriesLoaded = true;
      // Garde le choix précédent s'il existe encore...
      categoryInput.value = activeCategories.some((category) => category.slug === previousValue)
        // ...sinon...
        ? previousValue
        // ...aucun choix.
        : "";
      // Aucune catégorie active : message.
      if (!activeCategories.length) setFeedback("Aucune catégorie active. Créez ou réactivez une catégorie pour continuer.");
      // Met à jour le bouton.
      syncState();
    },
    // Indique si le serveur 3D est disponible :
    setProviderAvailable(isAvailable) {
      // mémorise la valeur...
      providerAvailable = isAvailable;
      // ...et met à jour le bouton.
      syncState();
    },
  };
}
