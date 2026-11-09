/*
 * Rôle : gère le choix, le dépôt et la validation côté interface d'une photo.
 * Exécution : main.js initialise cette vue et reçoit le fichier quand le formulaire est soumis.
 */
import { appState } from "../state.js";

const acceptedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
const acceptedExtensions = new Set(["jpg", "jpeg", "png", "webp"]);
const maxUploadBytes = 10 * 1024 * 1024;

function validatePhoto(file) {
  const extension = file.name.split(".").pop().toLowerCase();
  if (!acceptedExtensions.has(extension) || (file.type && !acceptedTypes.has(file.type))) {
    return "Choisissez une photo JPG, PNG ou WebP.";
  }
  if (file.size === 0) return "Le fichier photo est vide.";
  if (file.size > maxUploadBytes) return "La limite de taille est de 10 Mo.";
  return null;
}

export function setupUploader(onSubmit) {
  const form = document.querySelector("#upload-form");
  const photoInput = document.querySelector("#photo-input");
  const categoryInput = document.querySelector("#product-category");
  const dropZone = document.querySelector("#drop-zone");
  const fileName = document.querySelector("#file-name");
  const submitButton = document.querySelector("#submit-button");
  const uploadFeedback = document.querySelector("#upload-feedback");
  const openLocalButton = document.querySelector("#open-local-glb");
  let selectedPhoto = null;
  let busy = false;
  let providerAvailable = false;
  let categoriesLoaded = false;

  function setFeedback(message = "") {
    uploadFeedback.textContent = message;
    uploadFeedback.hidden = message.length === 0;
  }

  function setSelectedPhoto(file) {
    selectedPhoto = file ?? null;
    appState.selectedPhoto = selectedPhoto;
    fileName.textContent = selectedPhoto?.name ?? "Aucun fichier sélectionné";
    setFeedback("");
    if (!selectedPhoto) {
      submitButton.disabled = true;
      return;
    }
    const error = validatePhoto(selectedPhoto);
    submitButton.disabled = busy || !providerAvailable || !categoriesLoaded || !categoryInput.value || Boolean(error);
    if (error) setFeedback(error);
  }

  function setBusy(isBusy) {
    busy = isBusy;
    photoInput.disabled = isBusy;
    categoryInput.disabled = isBusy;
    openLocalButton.disabled = isBusy;
    submitButton.disabled = isBusy || !providerAvailable || !categoriesLoaded || !selectedPhoto || !categoryInput.value || Boolean(validatePhoto(selectedPhoto));
    submitButton.setAttribute("aria-busy", isBusy ? "true" : "false");
    const label = submitButton.querySelector(".button-label");
    label.textContent = isBusy ? "Génération en cours" : "Créer le modèle 3D";
  }

  photoInput.addEventListener("change", () => setSelectedPhoto(photoInput.files[0]));
  categoryInput.addEventListener("change", () => {
    submitButton.disabled = busy || !providerAvailable || !categoriesLoaded || !selectedPhoto || !categoryInput.value || Boolean(validatePhoto(selectedPhoto));
    setFeedback("");
  });

  for (const eventName of ["dragenter", "dragover"]) {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      if (!busy) dropZone.classList.add("is-dragging");
    });
  }

  for (const eventName of ["dragleave", "drop"]) {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropZone.classList.remove("is-dragging");
    });
  }

  dropZone.addEventListener("drop", (event) => {
    if (busy) return;
    const files = event.dataTransfer?.files;
    if (!files?.length) return;
    try {
      photoInput.files = files;
      setSelectedPhoto(files[0]);
    } catch {
      setFeedback("Le navigateur n’a pas pu lire ce dépôt. Utilisez « Choisir une photo ».");
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !selectedPhoto) return;
    if (!categoryInput.value) {
      setFeedback("Choisissez une catégorie pour ce produit.");
      return;
    }
    const error = validatePhoto(selectedPhoto);
    if (error) {
      setFeedback(error);
      return;
    }
    setFeedback("");
    await onSubmit(selectedPhoto, categoryInput.value);
  });

  return {
    getSelectedPhoto: () => selectedPhoto,
    getSelectedCategory: () => categoryInput.value,
    setBusy,
    setError: setFeedback,
    setCategories(categories) {
      const previousValue = categoryInput.value;
      const activeCategories = categories.filter((category) => category.is_active);
      categoryInput.replaceChildren(new Option("Choisir une catégorie", ""));
      for (const category of activeCategories) {
        categoryInput.add(new Option(category.label, category.slug));
      }
      categoriesLoaded = true;
      categoryInput.value = activeCategories.some((category) => category.slug === previousValue)
        ? previousValue
        : "";
      submitButton.disabled = busy || !providerAvailable || !activeCategories.length || !selectedPhoto || !categoryInput.value || Boolean(validatePhoto(selectedPhoto));
      if (!activeCategories.length) setFeedback("Aucune catégorie active. Créez ou réactivez une catégorie pour continuer.");
    },
    setProviderAvailable(isAvailable) {
      providerAvailable = isAvailable;
      submitButton.disabled = busy || !providerAvailable || !categoriesLoaded || !selectedPhoto || !categoryInput.value || Boolean(validatePhoto(selectedPhoto));
    },
  };
}
