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
    // Prévient auth.js par un événement personnalisé.
    window.dispatchEvent(new CustomEvent("forma3d:unauthorized"));
  }
  // Corps de la réponse (objet vide par défaut).
  let data = {};
  // Essaie...
  try {
    // ...de lire le corps comme du JSON.
    data = await response.json();
  // Corps vide ou pas du JSON...
  } catch {
    // ...on garde un objet vide.
    data = {};
  }
  // Statut d'erreur (4xx ou 5xx)...
  if (!response.ok) {
    // ...message du serveur s'il existe, sinon le message de secours.
    const detail = typeof data.detail === "string" ? data.detail : fallbackMessage;
    // Le message reste celui d'avant ; status, serverDetail et retryAfterSeconds permettent à une page
    // (par exemple Créer) d'expliquer la cause exacte et l'action à faire.
    // Crée l'erreur avec ce message.
    const error = new Error(detail);
    // Joint le code HTTP.
    error.status = response.status;
    // Joint le message exact du serveur.
    error.serverDetail = typeof data.detail === "string" ? data.detail : null;
    // Lit l'en-tête Retry-After (secondes à attendre), s'il existe.
    const retryAfter = Number.parseInt(response.headers.get("Retry-After") ?? "", 10);
    // Le garde seulement s'il est positif.
    error.retryAfterSeconds = Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null;
    // Interrompt la fonction appelante avec cette erreur.
    throw error;
  }
  // Succès : renvoie les données JSON.
  return data;
}

// Envoie une photo et sa catégorie pour lancer une génération : POST /models.
// fetch = fonction du navigateur qui envoie une requête HTTP et renvoie une promesse (équivalent de
// HttpClient d'Angular). FormData = formulaire avec fichier (multipart), comme un <form> envoyé à la main.
export async function createGeneration(photo, category) {
  // Formulaire multipart vide.
  const body = new FormData();
  // Ajoute le fichier photo.
  body.append("file", photo);
  // Ajoute la catégorie.
  body.append("category", category);
  // Envoie la requête et attend la réponse...
  const response = await fetch("/models", {
    // ...méthode POST...
    method: "POST",
    // ...corps : le formulaire...
    body,
    // ...on demande une réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse (ou lève une erreur).
  return readResponse(response, "Le serveur a refusé cette photo.");
}

// Lit l'état d'une génération (PENDING, RUNNING, DONE, FAILED) : GET sur l'adresse de suivi reçue.
// Sécurité : refuse une adresse qui ne pointe pas vers ce serveur ; cache désactivé pour lire l'état réel.
export async function getGenerationStatus(statusUrl) {
  // Transforme l'adresse en objet URL complet.
  const url = new URL(statusUrl, window.location.origin);
  // Adresse vers un autre site...
  if (url.origin !== window.location.origin) {
    // ...refusée.
    throw new Error("Le serveur a renvoyé une adresse de suivi inattendue.");
  }
  // Requête GET sur le chemin de suivi...
  const response = await fetch(url.pathname + url.search, {
    // ...sans cache...
    cache: "no-store",
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de lire l'état de la génération.");
}

/*
 * Ajoute la taille du fichier à l'adresse du GLB : si le fichier est remplacé (ex. exemple passé
 * de TripoSR à TRELLIS), l'adresse change et le navigateur ne réutilise pas l'ancienne copie en cache.
 */
export function withFileVersion(url, sizeBytes) {
  // Pas d'adresse ou taille inconnue : adresse inchangée.
  if (typeof url !== "string" || !Number.isFinite(sizeBytes)) return url;
  // Ajoute « ?v=taille » (ou « &v=taille » s'il y a déjà des paramètres).
  return `${url}${url.includes("?") ? "&" : "?"}v=${sizeBytes}`;
}

// Liste les exemples et les modèles enregistrés : GET /models/gallery.
// Chaque adresse de GLB reçoit sa taille en paramètre pour contourner le cache si le fichier change.
export async function listGalleryModels() {
  // GET /models/gallery...
  const response = await fetch("/models/gallery", {
    // ...sans cache...
    cache: "no-store",
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  const data = await readResponse(response, "Impossible de charger les modèles de démonstration.");
  // Si la liste existe...
  if (Array.isArray(data.items)) {
    // ...ajoute la version à l'adresse de chaque GLB.
    data.items = data.items.map((item) => ({ ...item, model_url: withFileVersion(item.model_url, item.size_bytes) }));
  }
  // Renvoie les données.
  return data;
}

// Importe un fichier .glb dans « Mes modèles » : POST /models/import (fichier, titre, catégorie).
export async function importGlbModel(file, title, category) {
  // Formulaire multipart.
  const body = new FormData();
  // Fichier GLB.
  body.append("file", file);
  // Titre.
  body.append("title", title);
  // Catégorie.
  body.append("category", category);
  // POST /models/import...
  const response = await fetch("/models/import", {
    // ...méthode...
    method: "POST",
    // ...corps...
    body,
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  return readResponse(response, "Impossible d’importer ce modèle GLB.");
}

// Copie un exemple du catalogue dans « Mes modèles » : POST /models/examples/{id}/copy.
// encodeURIComponent protège l'identifiant placé dans l'adresse.
export async function copyExampleModel(exampleId, title, category) {
  // Formulaire multipart.
  const body = new FormData();
  // Titre.
  body.append("title", title);
  // Catégorie.
  body.append("category", category);
  // POST vers l'adresse de copie de l'exemple...
  const response = await fetch(`/models/examples/${encodeURIComponent(exampleId)}/copy`, {
    // ...méthode...
    method: "POST",
    // ...corps...
    body,
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  return readResponse(response, "Impossible d’ajouter cet exemple à vos modèles.");
}

// Active ou désactive l'affichage public d'un modèle : PATCH /models/{id}/integration.
// JSON.stringify transforme l'objet JavaScript en texte JSON pour le corps de la requête.
export async function setModelIntegrationEnabled(modelId, enabled) {
  // PATCH sur l'intégration du modèle...
  const response = await fetch(`/models/${encodeURIComponent(modelId)}/integration`, {
    // ...méthode...
    method: "PATCH",
    // ...on envoie et attend du JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : {"enabled": true/false}.
    body: JSON.stringify({ enabled }),
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de modifier l’intégration de ce modèle.");
}

// Renomme un modèle enregistré : PATCH /models/{id}/name avec {"name": "..."}.
export async function renameModel(modelId, name) {
  // PATCH sur le nom du modèle...
  const response = await fetch(`/models/${encodeURIComponent(modelId)}/name`, {
    // ...méthode...
    method: "PATCH",
    // ...en-têtes JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : {"name": "..."}.
    body: JSON.stringify({ name }),
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de renommer ce modèle.");
}

// Change la catégorie d'un modèle enregistré : PATCH /models/{id}/category avec {"category": "slug"}.
export async function changeModelCategory(modelId, category) {
  // PATCH sur la catégorie du modèle...
  const response = await fetch(`/models/${encodeURIComponent(modelId)}/category`, {
    // ...méthode...
    method: "PATCH",
    // ...en-têtes JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : {"category": "..."}.
    body: JSON.stringify({ category }),
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de changer la catégorie de ce modèle.");
}

/* Supprime définitivement un modèle du Studio : ligne, GLB et photo source (204 sans contenu). */
export async function deleteModel(modelId) {
  // DELETE sur le modèle...
  const response = await fetch(`/models/${encodeURIComponent(modelId)}`, {
    // ...méthode...
    method: "DELETE",
    // ...réponse JSON en cas d'erreur.
    headers: { Accept: "application/json" },
  });
  // 204 = supprimé, pas de contenu à lire.
  if (response.status === 204) return null;
  // Sinon lit l'erreur.
  return readResponse(response, "Impossible de supprimer ce modèle.");
}

// Demande l'état du serveur 3D (ONLINE, OFFLINE, UNCONFIGURED) : GET /health/provider.
export async function getProviderHealth() {
  // GET /health/provider...
  const response = await fetch("/health/provider", {
    // ...sans cache...
    cache: "no-store",
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  return readResponse(response, "Le contrôle du serveur 3D est indisponible.");
}

// Liste les catégories : GET /categories (avec ?include_inactive=true pour l'écran de gestion).
export async function listCategories(includeInactive = false) {
  // Paramètre d'URL pour inclure les catégories désactivées.
  const query = includeInactive ? "?include_inactive=true" : "";
  // GET /categories (avec le paramètre éventuel)...
  const response = await fetch("/categories" + query, {
    // ...sans cache...
    cache: "no-store",
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de charger les catégories.");
}

// Crée une catégorie : POST /categories avec {slug, label}.
export async function createCategory(payload) {
  // POST /categories...
  const response = await fetch("/categories", {
    // ...méthode...
    method: "POST",
    // ...en-têtes JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : {slug, label}.
    body: JSON.stringify(payload),
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de créer la catégorie.");
}

// Renomme, active ou désactive une catégorie : PATCH /categories/{slug}.
export async function updateCategory(slug, payload) {
  // PATCH sur la catégorie...
  const response = await fetch("/categories/" + encodeURIComponent(slug), {
    // ...méthode...
    method: "PATCH",
    // ...en-têtes JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : champs à modifier.
    body: JSON.stringify(payload),
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de modifier la catégorie.");
}

// Supprime une catégorie inutilisée : DELETE /categories/{slug} (réponse 204 sans contenu).
export async function deleteCategory(slug) {
  // DELETE sur la catégorie...
  const response = await fetch("/categories/" + encodeURIComponent(slug), {
    // ...méthode...
    method: "DELETE",
    // ...réponse JSON en cas d'erreur.
    headers: { Accept: "application/json" },
  });
  // 204 = supprimée.
  if (response.status === 204) return null;
  // Sinon lit l'erreur.
  return readResponse(response, "Impossible de supprimer la catégorie.");
}


// Liste les clés API (nom, préfixe, état), jamais leur secret : GET /api-keys.
export async function listApiKeys() {
  // GET /api-keys sans cache.
  const response = await fetch("/api-keys", { cache: "no-store", headers: { Accept: "application/json" } });
  // Lit la réponse.
  return readResponse(response, "Impossible de charger les clés API.");
}

// Crée une clé API : POST /api-keys. La réponse contient le secret, affiché une seule fois.
export async function createApiKey(name) {
  // POST /api-keys...
  const response = await fetch("/api-keys", {
    // ...méthode...
    method: "POST",
    // ...en-têtes JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : {"name": "..."}.
    body: JSON.stringify({ name }),
  });
  // Lit la réponse (elle contient le secret).
  return readResponse(response, "Impossible de créer cette clé API.");
}

/* Supprime définitivement une clé déjà révoquée (204 sans contenu). */
export async function deleteRevokedApiKey(keyId) {
  // DELETE sur l'adresse « permanent » de la clé...
  const response = await fetch(`/api-keys/${encodeURIComponent(keyId)}/permanent`, {
    // ...méthode...
    method: "DELETE",
    // ...réponse JSON en cas d'erreur.
    headers: { Accept: "application/json" },
  });
  // 204 = supprimée.
  if (response.status === 204) return null;
  // Sinon lit l'erreur.
  return readResponse(response, "Impossible de supprimer cette clé API.");
}

// Révoque une clé (elle est refusée aussitôt, sa trace reste) : DELETE /api-keys/{id}.
export async function revokeApiKey(keyId) {
  // DELETE sur la clé...
  const response = await fetch(`/api-keys/${encodeURIComponent(keyId)}`, {
    // ...méthode...
    method: "DELETE",
    // ...réponse JSON.
    headers: { Accept: "application/json" },
  });
  // Lit la réponse.
  return readResponse(response, "Impossible de révoquer cette clé API.");
}

/* Étape 5f : session de la propriétaire, vérifiée côté serveur (cookie HttpOnly signé). */
export async function getSession() {
  // GET /auth/me sans cache.
  const response = await fetch("/auth/me", { cache: "no-store", headers: { Accept: "application/json" } });
  // Lit la réponse.
  return readResponse(response, "Impossible de vérifier la session.");
}

// Envoie le mot de passe : POST /auth/login. En cas de succès, le serveur pose le cookie de session ;
// le navigateur le renverra tout seul à chaque requête (JavaScript ne peut pas le lire).
export async function loginOwner(password) {
  // POST /auth/login...
  const response = await fetch("/auth/login", {
    // ...méthode...
    method: "POST",
    // ...en-têtes JSON...
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    // ...corps : {"password": "..."}.
    body: JSON.stringify({ password }),
  });
  // Lit la réponse.
  return readResponse(response, "Connexion refusée.");
}

// Ferme la session : POST /auth/logout (le serveur efface le cookie).
export async function logoutOwner() {
  // POST /auth/logout.
  const response = await fetch("/auth/logout", { method: "POST", headers: { Accept: "application/json" } });
  // Lit la réponse.
  return readResponse(response, "Déconnexion impossible.");
}
