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
export const PRODUCT_METALLIC = 0;
export const PRODUCT_ROUGHNESS = 0.8;

/* Vrai si le matériau ressemble au défaut glTF (aucune texture, metallic et roughness à 1). */
export function isDefaultGltfMaterial(material) {
  const pbr = material?.pbrMetallicRoughness;
  if (!pbr) return false;
  const hasBaseTexture = Boolean(pbr.baseColorTexture?.texture);
  const hasMetalTexture = Boolean(pbr.metallicRoughnessTexture?.texture);
  return !hasBaseTexture && !hasMetalTexture && pbr.metallicFactor === 1 && pbr.roughnessFactor === 1;
}

/*
 * Rend mats les matériaux par défaut ; un matériau réellement créé par un artiste (texture,
 * ou valeurs différentes de 1/1) est laissé intact. Renvoie le nombre de matériaux corrigés.
 */
export function applyProductAppearance(viewer) {
  const materials = viewer?.model?.materials ?? [];
  let corrected = 0;
  for (const material of materials) {
    if (!isDefaultGltfMaterial(material)) continue;
    material.pbrMetallicRoughness.setMetallicFactor(PRODUCT_METALLIC);
    material.pbrMetallicRoughness.setRoughnessFactor(PRODUCT_ROUGHNESS);
    corrected += 1;
  }
  return corrected;
}

export const BASE_RADIUS_PERCENT = 105;

/*
 * Distance de caméra (en % du cadrage idéal) pour une scène de rapport largeur/hauteur donné.
 * Le cadrage automatique se règle sur la hauteur : dans une scène plus haute que large
 * (mode « Comparer » à demi-largeur), on recule la caméra d'autant pour garder le modèle entier.
 */
export function radiusForAspect(aspect) {
  if (!Number.isFinite(aspect) || aspect <= 0) return BASE_RADIUS_PERCENT;
  return Math.round(BASE_RADIUS_PERCENT * Math.max(1, 1 / aspect));
}

/* Recalcule le cadrage après un changement de taille de la scène (ex. passage en mode « Comparer »). */
export function refitCamera(viewer) {
  if (!viewer || typeof viewer.updateFraming !== "function") return;
  // Deux images d'attente : la nouvelle mise en page CSS doit être appliquée avant de mesurer.
  window.requestAnimationFrame(() => window.requestAnimationFrame(() => {
    const { width, height } = viewer.getBoundingClientRect();
    const theta = viewer.getCameraOrbit?.().theta ?? 0;
    viewer.cameraTarget = "auto auto auto";
    viewer.cameraOrbit = `${theta}rad 75deg ${radiusForAspect(width / height)}%`;
    void viewer.updateFraming();
  }));
}

/* Branche la correction sur un viewer : à chaque nouveau modèle chargé. */
export function watchProductAppearance(viewer) {
  viewer?.addEventListener("load", () => applyProductAppearance(viewer));
}
