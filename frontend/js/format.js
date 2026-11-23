/*
 * Rôle : regroupe les petites fonctions de mise en forme partagées (dates, tailles, durées).
 * Exécution : importé par les pages et les vues ; aucune requête réseau, aucun état.
 */
// Expression régulière d'un UUID (identifiant d'un modèle enregistré).
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/* Un identifiant UUID désigne un modèle enregistré ; les autres sont les exemples fixes du catalogue. */
// Fonction exportée : vrai si le modèle est enregistré.
export function isSavedModel(model) {
  // Teste l'identifiant (chaîne vide s'il manque).
  return generationIdPattern.test(String(model?.id ?? ""));
}

/*
 * Fournisseur et durée réellement mesurés pour chaque exemple du catalogue.
 * TripoSR : essais de faisabilité (docs/etapes/etape-06.md).
 * TRELLIS : essais C2 avec détourage (docs/QUALITE-3D.md, section 3 bis) ; ces trois exemples
 * ont remplacé les versions TripoSR le 11 novembre 2026 (sauvegardées hors Git).
 * Aucune durée n'est inventée pour un modèle absent de cette liste.
 */
// Fournisseur utilisé pour chaque exemple.
export const exampleProviders = {
  // Tabouret : TRELLIS.
  "stool-metal-01": "TRELLIS",
  // Chaise en bois : TRELLIS.
  "chair-bentwood": "TRELLIS",
  // Chaise métal 01 : TripoSR.
  "chair-metal-01": "TripoSR",
  // Chaise métal 02 : TripoSR.
  "chair-metal-02": "TripoSR",
  // Table d'appoint : TRELLIS.
  "side-table-metal": "TRELLIS",
};

// Durée réelle mesurée pour chaque exemple, en secondes.
export const exampleGenerationSeconds = {
  // Tabouret.
  "stool-metal-01": 105.1,
  // Chaise en bois.
  "chair-bentwood": 75.8,
  // Chaise métal 01.
  "chair-metal-01": 99.0,
  // Chaise métal 02.
  "chair-metal-02": 204.0,
  // Table d'appoint.
  "side-table-metal": 91.2,
};

// Affiche une taille en mégaoctets (« 1,5 Mo »).
// Intl = API du navigateur pour formater nombres et dates selon la langue (ici le français).
export function formatMegabytes(bytes) {
  // Valeur qui n'est pas un nombre : texte de repli.
  if (!Number.isFinite(bytes)) return "Taille inconnue";
  // Convertit en Mo avec une décimale au maximum.
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(bytes / (1024 * 1024)) + " Mo";
}

// Affiche une durée (« 1 min 33 s ») ; « Non communiquée » si la valeur est absente : aucune durée n'est inventée.
export function formatDuration(seconds) {
  // Valeur absente ou négative : aucune durée inventée.
  if (!Number.isFinite(seconds) || seconds < 0) return "Non communiquée";
  // Arrondit à la seconde.
  const total = Math.round(seconds);
  // Nombre de minutes entières.
  const minutes = Math.floor(total / 60);
  // Secondes restantes.
  const rest = total % 60;
  // « 1 min 05 s » ou « 45 s ».
  return minutes ? `${minutes} min ${String(rest).padStart(2, "0")} s` : `${rest} s`;
}

/* Exemple : « il y a 2 jours ». Revient à une date courte si la valeur est invalide. */
export function formatRelativeDate(value) {
  // Pas de valeur : texte vide.
  if (!value) return "";
  // Convertit en date.
  const date = new Date(value);
  // Date invalide : texte vide.
  if (Number.isNaN(date.getTime())) return "";
  // Écart avec maintenant, en secondes (négatif = passé).
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  // Unités du plus grand au plus petit, avec leur durée en secondes...
  const units = [
    // ...année...
    ["year", 31_536_000],
    // ...mois...
    ["month", 2_592_000],
    // ...semaine...
    ["week", 604_800],
    // ...jour...
    ["day", 86_400],
    // ...heure...
    ["hour", 3_600],
    // ...minute.
    ["minute", 60],
  ];
  // Outil du navigateur qui écrit « il y a 2 jours », « hier »...
  const formatter = new Intl.RelativeTimeFormat("fr-FR", { numeric: "auto" });
  // Pour chaque unité...
  for (const [unit, size] of units) {
    // ...la première assez grande donne le texte.
    if (Math.abs(seconds) >= size) return formatter.format(Math.round(seconds / size), unit);
  }
  // Moins d'une minute.
  return "à l’instant";
}

// Affiche une date complète en français (« 15 novembre 2026 à 14:07 »).
export function formatLongDate(value) {
  // Pas de valeur : texte de repli.
  if (!value) return "Date non disponible";
  // Convertit en date.
  const date = new Date(value);
  // Date invalide...
  return Number.isNaN(date.getTime())
    // ...texte de repli...
    ? "Date non disponible"
    // ...sinon date longue et heure en français.
    : new Intl.DateTimeFormat("fr-FR", { dateStyle: "long", timeStyle: "short" }).format(date);
}

// Accorde un mot avec un nombre : « 1 modèle », « 2 modèles ».
// « singular » est accordé au pluriel en ajoutant un « s » par défaut.
export function pluralize(count, singular, plural = `${singular}s`) {
  // Choisit la forme selon le nombre.
  return `${count} ${count === 1 ? singular : plural}`;
}

/* Description courte d'un exemple : durée mesurée si elle est connue, sinon phrase sans chiffre. */
export function exampleDescription(model) {
  // Durée connue pour cet exemple.
  const seconds = exampleGenerationSeconds[model?.id];
  // Fournisseur connu pour cet exemple.
  const provider = exampleProviders[model?.id];
  // « avec TRELLIS », ou rien.
  const by = provider ? ` avec ${provider}` : "";
  // Durée connue...
  return Number.isFinite(seconds)
    // ...phrase avec la durée...
    ? `Généré${by} à partir d’une seule photo en ${formatDuration(seconds)}.`
    // ...sinon phrase sans chiffre.
    : `Généré${by} à partir d’une seule photo.`;
}
