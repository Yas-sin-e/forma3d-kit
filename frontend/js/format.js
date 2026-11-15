/*
 * Rôle : regroupe les petites fonctions de mise en forme partagées (dates, tailles, durées).
 * Exécution : importé par les pages et les vues ; aucune requête réseau, aucun état.
 */
const generationIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/* Un identifiant UUID désigne un modèle enregistré ; les autres sont les exemples fixes du catalogue. */
export function isSavedModel(model) {
  return generationIdPattern.test(String(model?.id ?? ""));
}

/*
 * Fournisseur et durée réellement mesurés pour chaque exemple du catalogue.
 * TripoSR : essais de faisabilité (docs/etapes/etape-06.md).
 * TRELLIS : essais C2 avec détourage (docs/QUALITE-3D.md, section 3 bis) ; ces trois exemples
 * ont remplacé les versions TripoSR le 11 novembre 2026 (sauvegardées hors Git).
 * Aucune durée n'est inventée pour un modèle absent de cette liste.
 */
export const exampleProviders = {
  "stool-metal-01": "TRELLIS",
  "chair-bentwood": "TRELLIS",
  "chair-metal-01": "TripoSR",
  "chair-metal-02": "TripoSR",
  "side-table-metal": "TRELLIS",
};

export const exampleGenerationSeconds = {
  "stool-metal-01": 105.1,
  "chair-bentwood": 75.8,
  "chair-metal-01": 99.0,
  "chair-metal-02": 204.0,
  "side-table-metal": 91.2,
};

// Affiche une taille en mégaoctets (« 1,5 Mo »).
// Intl = API du navigateur pour formater nombres et dates selon la langue (ici le français).
export function formatMegabytes(bytes) {
  if (!Number.isFinite(bytes)) return "Taille inconnue";
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(bytes / (1024 * 1024)) + " Mo";
}

// Affiche une durée (« 1 min 33 s ») ; « Non communiquée » si la valeur est absente : aucune durée n'est inventée.
export function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "Non communiquée";
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return minutes ? `${minutes} min ${String(rest).padStart(2, "0")} s` : `${rest} s`;
}

/* Exemple : « il y a 2 jours ». Revient à une date courte si la valeur est invalide. */
export function formatRelativeDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const units = [
    ["year", 31_536_000],
    ["month", 2_592_000],
    ["week", 604_800],
    ["day", 86_400],
    ["hour", 3_600],
    ["minute", 60],
  ];
  const formatter = new Intl.RelativeTimeFormat("fr-FR", { numeric: "auto" });
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return formatter.format(Math.round(seconds / size), unit);
  }
  return "à l’instant";
}

// Affiche une date complète en français (« 15 novembre 2026 à 14:07 »).
export function formatLongDate(value) {
  if (!value) return "Date non disponible";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date non disponible"
    : new Intl.DateTimeFormat("fr-FR", { dateStyle: "long", timeStyle: "short" }).format(date);
}

// Accorde un mot avec un nombre : « 1 modèle », « 2 modèles ».
export function pluralize(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

/* Description courte d'un exemple : durée mesurée si elle est connue, sinon phrase sans chiffre. */
export function exampleDescription(model) {
  const seconds = exampleGenerationSeconds[model?.id];
  const provider = exampleProviders[model?.id];
  const by = provider ? ` avec ${provider}` : "";
  return Number.isFinite(seconds)
    ? `Généré${by} à partir d’une seule photo en ${formatDuration(seconds)}.`
    : `Généré${by} à partir d’une seule photo.`;
}
