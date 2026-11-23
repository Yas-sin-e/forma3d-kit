/*
 * Rôle : fournit les illustrations SVG inline réutilisées (cube 3D des états vides).
 * Exécution : importé par l'accueil, Mes modèles et le viewer ; renvoie du balisage statique.
 */
// Fonction exportée qui renvoie le dessin SVG d'un cube (état vide).
export function emptyCubeIllustration() {
  // Renvoie le balisage SVG écrit entre accents graves (gabarit de texte).
  return `
    <svg class="empty-illustration" viewBox="0 0 160 140" fill="none" aria-hidden="true">
      <ellipse cx="80" cy="122" rx="52" ry="9" fill="currentColor" opacity="0.08"/>
      <path d="M80 18 128 44v52l-48 26-48-26V44l48-26Z" stroke="currentColor" stroke-width="2" opacity="0.35" stroke-dasharray="5 6"/>
      <path d="M80 34 114 52v38L80 108 46 90V52l34-18Z" fill="rgb(45 212 191 / 0.08)" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>
      <path d="m46 52 34 19 34-19M80 71v37" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>
      <circle cx="122" cy="26" r="3" fill="var(--accent)"/><circle cx="36" cy="36" r="2" fill="var(--accent)" opacity="0.6"/>
      <path d="M134 70h10M139 65v10" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" opacity="0.7"/>
    </svg>`;
}
