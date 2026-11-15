/*
 * Rôle : centralise tous les appels HTTP de l'interface vers l'API Forma3D.
 * Exécution : main.js et gallery.js utilisent ces fonctions pour envoyer une photo,
 * suivre son état et lire uniquement la galerie réelle du backend.
 */
async function readResponse(response, fallbackMessage) {
  // Session expirée ou absente sur une route du Studio : auth.js renvoie vers l'écran de connexion.
  if (response.status === 401 && !new URL(response.url, window.location.origin).pathname.startsWith("/auth/")) {
    window.dispatchEvent(new CustomEvent("forma3d:unauthorized"));
  }
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

/*
 * Ajoute la taille du fichier à l'adresse du GLB : si le fichier est remplacé (ex. exemple passé
 * de TripoSR à TRELLIS), l'adresse change et le navigateur ne réutilise pas l'ancienne copie en cache.
 */
export function withFileVersion(url, sizeBytes) {
  if (typeof url !== "string" || !Number.isFinite(sizeBytes)) return url;
  return `${url}${url.includes("?") ? "&" : "?"}v=${sizeBytes}`;
}

export async function listGalleryModels() {
  const response = await fetch("/models/gallery", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  const data = await readResponse(response, "Impossible de charger les modèles de démonstration.");
  if (Array.isArray(data.items)) {
    data.items = data.items.map((item) => ({ ...item, model_url: withFileVersion(item.model_url, item.size_bytes) }));
  }
  return data;
}

export async function importGlbModel(file, title, category) {
  const body = new FormData();
  body.append("file", file);
  body.append("title", title);
  body.append("category", category);
  const response = await fetch("/models/import", {
    method: "POST",
    body,
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible d’importer ce modèle GLB.");
}

export async function copyExampleModel(exampleId, title, category) {
  const body = new FormData();
  body.append("title", title);
  body.append("category", category);
  const response = await fetch(`/models/examples/${encodeURIComponent(exampleId)}/copy`, {
    method: "POST",
    body,
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible d’ajouter cet exemple à vos modèles.");
}

export async function setModelIntegrationEnabled(modelId, enabled) {
  const response = await fetch(`/models/${encodeURIComponent(modelId)}/integration`, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  return readResponse(response, "Impossible de modifier l’intégration de ce modèle.");
}

/* Supprime définitivement un modèle du Studio : ligne, GLB et photo source (204 sans contenu). */
export async function deleteModel(modelId) {
  const response = await fetch(`/models/${encodeURIComponent(modelId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (response.status === 204) return null;
  return readResponse(response, "Impossible de supprimer ce modèle.");
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


export async function listApiKeys() {
  const response = await fetch("/api-keys", { cache: "no-store", headers: { Accept: "application/json" } });
  return readResponse(response, "Impossible de charger les clés API.");
}

export async function createApiKey(name) {
  const response = await fetch("/api-keys", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return readResponse(response, "Impossible de créer cette clé API.");
}

/* Supprime définitivement une clé déjà révoquée (204 sans contenu). */
export async function deleteRevokedApiKey(keyId) {
  const response = await fetch(`/api-keys/${encodeURIComponent(keyId)}/permanent`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (response.status === 204) return null;
  return readResponse(response, "Impossible de supprimer cette clé API.");
}

export async function revokeApiKey(keyId) {
  const response = await fetch(`/api-keys/${encodeURIComponent(keyId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible de révoquer cette clé API.");
}

/* Étape 5f : session de la propriétaire, vérifiée côté serveur (cookie HttpOnly signé). */
export async function getSession() {
  const response = await fetch("/auth/me", { cache: "no-store", headers: { Accept: "application/json" } });
  return readResponse(response, "Impossible de vérifier la session.");
}

export async function loginOwner(password) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  return readResponse(response, "Connexion refusée.");
}

export async function logoutOwner() {
  const response = await fetch("/auth/logout", { method: "POST", headers: { Accept: "application/json" } });
  return readResponse(response, "Déconnexion impossible.");
}
