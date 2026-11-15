/*
 * Rôle : centralise tous les appels HTTP de l'interface vers l'API Forma3D.
 * Exécution : main.js et gallery.js utilisent ces fonctions pour envoyer une photo,
 * suivre son état et lire uniquement la galerie réelle du backend.
 */
// Lit la réponse du serveur pour toutes les fonctions de ce fichier.
// Entrées : response (réponse HTTP), fallbackMessage (message de secours).
// Effet : renvoie le JSON si tout va bien ; sinon lève une erreur avec le message du serveur.
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
    // Le message reste celui d'avant ; status, serverDetail et retryAfterSeconds permettent à une page
    // (par exemple Créer) d'expliquer la cause exacte et l'action à faire.
    const error = new Error(detail);
    error.status = response.status;
    error.serverDetail = typeof data.detail === "string" ? data.detail : null;
    const retryAfter = Number.parseInt(response.headers.get("Retry-After") ?? "", 10);
    error.retryAfterSeconds = Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null;
    throw error;
  }
  return data;
}

// Envoie une photo et sa catégorie pour lancer une génération : POST /models.
// fetch = fonction du navigateur qui envoie une requête HTTP et renvoie une promesse (équivalent de
// HttpClient d'Angular). FormData = formulaire avec fichier (multipart), comme un <form> envoyé à la main.
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

// Lit l'état d'une génération (PENDING, RUNNING, DONE, FAILED) : GET sur l'adresse de suivi reçue.
// Sécurité : refuse une adresse qui ne pointe pas vers ce serveur ; cache désactivé pour lire l'état réel.
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

// Liste les exemples et les modèles enregistrés : GET /models/gallery.
// Chaque adresse de GLB reçoit sa taille en paramètre pour contourner le cache si le fichier change.
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

// Importe un fichier .glb dans « Mes modèles » : POST /models/import (fichier, titre, catégorie).
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

// Copie un exemple du catalogue dans « Mes modèles » : POST /models/examples/{id}/copy.
// encodeURIComponent protège l'identifiant placé dans l'adresse.
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

// Active ou désactive l'affichage public d'un modèle : PATCH /models/{id}/integration.
// JSON.stringify transforme l'objet JavaScript en texte JSON pour le corps de la requête.
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

// Demande l'état du serveur 3D (ONLINE, OFFLINE, UNCONFIGURED) : GET /health/provider.
export async function getProviderHealth() {
  const response = await fetch("/health/provider", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Le contrôle du serveur 3D est indisponible.");
}

// Liste les catégories : GET /categories (avec ?include_inactive=true pour l'écran de gestion).
export async function listCategories(includeInactive = false) {
  const query = includeInactive ? "?include_inactive=true" : "";
  const response = await fetch("/categories" + query, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return readResponse(response, "Impossible de charger les catégories.");
}

// Crée une catégorie : POST /categories avec {slug, label}.
export async function createCategory(payload) {
  const response = await fetch("/categories", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponse(response, "Impossible de créer la catégorie.");
}

// Renomme, active ou désactive une catégorie : PATCH /categories/{slug}.
export async function updateCategory(slug, payload) {
  const response = await fetch("/categories/" + encodeURIComponent(slug), {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponse(response, "Impossible de modifier la catégorie.");
}

// Supprime une catégorie inutilisée : DELETE /categories/{slug} (réponse 204 sans contenu).
export async function deleteCategory(slug) {
  const response = await fetch("/categories/" + encodeURIComponent(slug), {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (response.status === 204) return null;
  return readResponse(response, "Impossible de supprimer la catégorie.");
}


// Liste les clés API (nom, préfixe, état), jamais leur secret : GET /api-keys.
export async function listApiKeys() {
  const response = await fetch("/api-keys", { cache: "no-store", headers: { Accept: "application/json" } });
  return readResponse(response, "Impossible de charger les clés API.");
}

// Crée une clé API : POST /api-keys. La réponse contient le secret, affiché une seule fois.
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

// Révoque une clé (elle est refusée aussitôt, sa trace reste) : DELETE /api-keys/{id}.
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

// Envoie le mot de passe : POST /auth/login. En cas de succès, le serveur pose le cookie de session ;
// le navigateur le renverra tout seul à chaque requête (JavaScript ne peut pas le lire).
export async function loginOwner(password) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  return readResponse(response, "Connexion refusée.");
}

// Ferme la session : POST /auth/logout (le serveur efface le cookie).
export async function logoutOwner() {
  const response = await fetch("/auth/logout", { method: "POST", headers: { Accept: "application/json" } });
  return readResponse(response, "Déconnexion impossible.");
}
