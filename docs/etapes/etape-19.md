# Étape 19 — Sous-étape A : rendu fidèle des GLB dans le viewer

Date : 11 novembre 2026. Validée par l'étudiante (« OK pour A ») après l'audit du SaaS.

## But et livrable vérifiable

- But : afficher les GLB générés sans assombrissement artificiel, et garder le modèle entier dans le mode « Comparer ».
- Livrable : le même fichier GLB, affiché plus lisible ; aucun fichier n'est modifié côté serveur.
- **Ce n'est pas une amélioration de la géométrie.** Les pieds fins, le dossier simplifié et les faces cachées inventées restent des limites de TripoSR (photo unique).

## Diagnostic mesuré

Lecture en lecture seule des 5 GLB de faisabilité (`backend/data/feasibility-results/`) :

| Fichier | Sommets | Triangles | Attributs | Matériau | Normales | Texture |
|---|---:|---:|---|---|---|---|
| chair-bentwood.glb | 30 925 | 61 732 | POSITION, COLOR_0 | aucun | non | non |
| chair-met-01.glb | 21 644 | 43 211 | POSITION, COLOR_0 | aucun | non | non |
| chair-met-02.glb | 51 262 | 102 411 | POSITION, COLOR_0 | aucun | non | non |
| side-table-met.glb | 25 879 | 51 712 | POSITION, COLOR_0 | aucun | non | non |
| stool-met-01.glb | 65 520 | 130 868 | POSITION, COLOR_0 | aucun | non | non |

Sans matériau, la norme glTF impose un matériau par défaut **metallic = 1, roughness = 1**. Un métal parfait sans texture reflète l'environnement au lieu de montrer la couleur des sommets : le modèle paraît presque noir. Sans normales, le viewer calcule des faces plates (aspect facetté) ; ce point relève de la sous-étape B (post-traitement serveur).

Le modèle est bien orienté (axe Y vers le haut ; chaise : 0,64 × 1,08 × 0,74). Le cadrage coupé en mode « Comparer » venait du viewer : la scène passait à demi-largeur sans recalcul de la caméra.

## Fichiers

| Fichier | Rôle |
|---|---|
| `frontend/js/views/model-appearance.js` (nouveau) | `isDefaultGltfMaterial`, `applyProductAppearance` (metallic 0, roughness 0,8 uniquement pour le matériau par défaut), `refitCamera`, `watchProductAppearance` |
| `frontend/js/views/viewer.js` | Correction au chargement ; en mode Comparer : rotation en pause et recadrage |
| `frontend/js/pages/model-detail.js` | Même chose sur la fiche ; la rotation reprend en vue 3D seule |
| `frontend/js/views/gallery.js`, `frontend/js/pages/dashboard.js` | Correction sur les miniatures et le visuel de l'accueil |

Un matériau réellement créé (texture, ou valeurs différentes de 1/1) n'est pas touché : un GLB importé avec un vrai métal garde son rendu.

## Preuve

Capture headless Edge (SwiftShader) d'une page de test locale chargeant le vrai `chair-bentwood.glb` deux fois, avec model-viewer 4.4.0. Journal de la page :

```text
before: 1 matériau(x), metallic=1 roughness=1, corrigés=0
after:  1 matériau(x), metallic=1 roughness=1, corrigés=1, après: metallic=0 roughness=0.8
```

Visuellement, l'assise, le dossier et les pieds deviennent lisibles au lieu d'apparaître en noir réfléchissant. La capture n'est pas versionnée (elle montre un modèle issu d'une photo).

## Tests

- `backend/tests/test_frontend.py::test_viewers_fix_default_gltf_material_and_refit_in_compare_mode` et ajout du module à la liste « pas de fetch hors api.js ».
- Suite complète lancée une fois en fin d'étape.

## Non vérifié

- Le recadrage en mode « Comparer » dans le vrai Studio (pas de pilotage de navigateur) : à contrôler par l'étudiante sur une fiche avec photo source, au bureau et sur mobile.
- La couleur réelle reste celle des sommets générés : la chaise noire laquée apparaît gris foncé mat, ce qui est plus lisible mais pas « photoréaliste ».
