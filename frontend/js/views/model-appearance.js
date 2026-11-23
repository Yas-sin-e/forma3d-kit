/*
 * Rôle : corrige l'apparence des GLB sans matériau et recadre la caméra quand la scène change de taille.
 * Exécution : appelé à l'événement « load » de chaque <model-viewer> du Studio (Créer, fiche, cartes, accueil).
 *
 * Pourquoi : les GLB produits par TripoSR n'ont ni matériau ni normales, seulement une couleur par sommet.
 * La norme glTF impose alors un matériau par défaut 100 % métallique et rugueux (metallic = 1,
 * roughness = 1) : avec l'éclairage du viewer, la couleur paraît presque noire.
 * On remplace ce défaut par un matériau mat (metallic = 0, roughness = 0,8).
 * C'est une correction d'AFFICHAGE : le fichier GLB téléchargé et sa géométrie ne changent pas.
 */
// Facteur métallique du matériau produit : 0 = pas métallique.
export const PRODUCT_METALLIC = 0;
// Rugosité du matériau produit : 0,8 = plutôt mat.
export const PRODUCT_ROUGHNESS = 0.8;

/* Vrai si le matériau ressemble au défaut glTF (aucune texture, metallic et roughness à 1). */
export function isDefaultGltfMaterial(material) {
  // Partie PBR du matériau (couleur, métal, rugosité).
  const pbr = material?.pbrMetallicRoughness;
  // Pas de partie PBR : ce n'est pas le matériau par défaut.
  if (!pbr) return false;
  // Vrai si une texture de couleur existe.
  const hasBaseTexture = Boolean(pbr.baseColorTexture?.texture);
  // Vrai si une texture métal/rugosité existe.
  const hasMetalTexture = Boolean(pbr.metallicRoughnessTexture?.texture);
  // Défaut glTF = aucune texture et facteurs à 1.
  return !hasBaseTexture && !hasMetalTexture && pbr.metallicFactor === 1 && pbr.roughnessFactor === 1;
}

/*
 * Rend mats les matériaux par défaut ; un matériau réellement créé par un artiste (texture,
 * ou valeurs différentes de 1/1) est laissé intact. Renvoie le nombre de matériaux corrigés.
 */
// Matériaux du modèle chargé (liste vide si absent).
export function applyProductAppearance(viewer) {
  // Compteur de corrections.
  const materials = viewer?.model?.materials ?? [];
  // Pour chaque matériau...
  let corrected = 0;
  // ...pas le défaut : on passe au suivant.
  for (const material of materials) {
    // Met le facteur métallique à 0.
    if (!isDefaultGltfMaterial(material)) continue;
    // Met la rugosité à 0,8.
    material.pbrMetallicRoughness.setMetallicFactor(PRODUCT_METALLIC);
    // Compte la correction.
    material.pbrMetallicRoughness.setRoughnessFactor(PRODUCT_ROUGHNESS);
    corrected += 1;
  // Renvoie le nombre de corrections.
  }
  return corrected;
}
// Distance de caméra de base : 105 % du cadrage idéal.

export const BASE_RADIUS_PERCENT = 105;

/*
 * Distance de caméra (en % du cadrage idéal) pour une scène de rapport largeur/hauteur donné.
 * Le cadrage automatique se règle sur la hauteur : dans une scène plus haute que large
 * (mode « Comparer » à demi-largeur), on recule la caméra d'autant pour garder le modèle entier.
 */
// Rapport invalide : distance de base.
export function radiusForAspect(aspect) {
  // Plus la scène est étroite, plus on recule.
  if (!Number.isFinite(aspect) || aspect <= 0) return BASE_RADIUS_PERCENT;
  return Math.round(BASE_RADIUS_PERCENT * Math.max(1, 1 / aspect));
}

/* Recalcule le cadrage après un changement de taille de la scène (ex. passage en mode « Comparer »). */
// Pas de viewer ou fonction absente : rien à faire.
export function refitCamera(viewer) {
  if (!viewer || typeof viewer.updateFraming !== "function") return;
  // Attend deux images avant de mesurer.
  // Deux images d'attente : la nouvelle mise en page CSS doit être appliquée avant de mesurer.
  window.requestAnimationFrame(() => window.requestAnimationFrame(async () => {
    // model-viewer ne redimensionne sa zone de rendu qu'à un événement « resize » (constaté dans le navigateur).
    // Déclenche un « resize » pour que model-viewer remesure sa zone.
    window.dispatchEvent(new Event("resize"));
    // Largeur et hauteur réelles du viewer.
    const { width, height } = viewer.getBoundingClientRect();
    // Angle horizontal actuel de la caméra (0 par défaut).
    const theta = viewer.getCameraOrbit?.().theta ?? 0;
    // Vise le centre automatique du modèle.
    viewer.cameraTarget = "auto auto auto";
    // Garde l'angle, inclinaison 75°, distance adaptée au rapport.
    viewer.cameraOrbit = `${theta}rad 75deg ${radiusForAspect(width / height)}%`;
    // Attend le nouveau cadrage.
    await viewer.updateFraming();
    // Place la caméra immédiatement, sans animation.
    viewer.jumpCameraToGoal?.();
  }));
}

/* Branche la correction sur un viewer : à chaque nouveau modèle chargé. */
export function watchProductAppearance(viewer) {
  // À chaque chargement de modèle, applique la correction.
  viewer?.addEventListener("load", () => applyProductAppearance(viewer));
}
