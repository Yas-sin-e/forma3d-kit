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

/*
 * Recalcule le cadrage après un changement de taille de la scène (ex. mode « Comparer »
 * qui passe le viewer à demi-largeur) : sans cela, le modèle reste cadré pour l'ancienne largeur.
 */
export function refitCamera(viewer) {
  if (!viewer || typeof viewer.updateFraming !== "function") return;
  window.requestAnimationFrame(() => {
    viewer.cameraTarget = "auto auto auto";
    viewer.cameraOrbit = `${viewer.getCameraOrbit?.().theta ?? 0}rad 75deg auto`;
    void viewer.updateFraming();
  });
}

/* Branche la correction sur un viewer : à chaque nouveau modèle chargé. */
export function watchProductAppearance(viewer) {
  viewer?.addEventListener("load", () => applyProductAppearance(viewer));
}
