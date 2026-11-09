/*
 * Rôle : centralise tous les appels HTTP de l'interface vers l'API Forma3D.
 * Exécution : main.js et gallery.js utilisent ces fonctions pour envoyer une photo,
 * suivre son état et lire uniquement la galerie réelle du backend.
 */
async function readResponse(response, fallbackMessage) {
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : fallbackMessage;
    throw new Error(detail);
  }
  return data;
}

export async function createGeneration(photo, category) {
  const body = new FormData();
  body.append("file", photo);
  body.append("category", category);
  const response = await fetch("/models", {
    method: "POST",
    body,
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Le serveur a refusé cette photo.");
}

export async function getGenerationStatus(statusUrl) {
  const url = new URL(statusUrl, window.location.origin);
  if (url.origin !== window.location.origin) {
    throw new Error("Le serveur a renvoyé une adresse de suivi inattendue.");
  }
  const response = await fetch(url.pathname + url.search, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible de lire l'état de la génération.");
}

export async function listGalleryModels() {
  const response = await fetch("/models/gallery", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible de charger les modèles de démonstration.");
}

export async function getProviderHealth() {
  const response = await fetch("/health/provider", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Le contrôle du serveur 3D est indisponible.");
}

export async function listCategories(includeInactive = false) {
  const query = includeInactive ? "?include_inactive=true" : "";
  const response = await fetch("/categories" + query, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible de charger les catégories.");
}

export async function createCategory(payload) {
  const response = await fetch("/categories", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponse(response, "Impossible de créer la catégorie.");
}

export async function updateCategory(slug, payload) {
  const response = await fetch("/categories/" + encodeURIComponent(slug), {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponse(response, "Impossible de modifier la catégorie.");
}

export async function deleteCategory(slug) {
  const response = await fetch("/categories/" + encodeURIComponent(slug), {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (response.status === 204) return null;
  return readResponse(response, "Impossible de supprimer la catégorie.");
}
