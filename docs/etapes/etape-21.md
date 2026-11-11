# Étape 21 — Sous-étape C : grille de qualité et essais de fournisseurs

Date : 11 novembre 2026. Validée par l'étudiante (« OK pour C »). Début du travail du Sprint 6 sur la qualité 3D.

## But et livrable

- But : juger un fournisseur 3D sur des critères mesurables, puis essayer une alternative gratuite à TripoSR sur les mêmes photos.
- Livrable : `docs/QUALITE-3D.md` (grille écrite avant les essais, contrats observés, résultats, licences) et l'outil `tools/trials/trial_trellis.py`.

## Ce qui a été fait

1. Grille de 10 critères : validité GLB, taille, durée, contenu (sommets, matériau, normales, texture), proportions, puis silhouette, structure, faces cachées et couleur notées par l'étudiante.
2. Lecture des contrats réels avec `view_api()` : `trellis-community/TRELLIS` (une fonction GLB, plusieurs vues possibles) et `microsoft/TRELLIS.2` (enchaînement en session) sont en ligne ; `JeffreyXiang/TRELLIS` est en `CONFIG_ERROR`.
3. Essais sur `chair-bentwood.jpg` : un échec `FileNotFoundError` (session non ouverte), puis l'arrêt sur le quota ZeroGPU anonyme. Aucun contournement ; TRELLIS.2 n'a pas été essayé pour la même raison.

## Résultat

Premier passage bloqué par le quota anonyme. Relance le soir même avec le jeton gratuit de l'étudiante, saisi de façon masquée dans son terminal (jamais affiché, écrit ni envoyé ailleurs qu'à Hugging Face, effacé à la fin) : **3 GLB TRELLIS valides sur 3**, en 38,6 à 85,6 s, avec une texture PNG. Mesures complètes dans `docs/QUALITE-3D.md`.

TRELLIS est techniquement faisable mais **pas encore démontré dans Forma3D** (aucun adaptateur). Notes visuelles à remplir par l'étudiante. Correction de l'outil : `gradio_client` 2.7 attend le paramètre `token` (et non `hf_token`).

## Sous-étape C2

Après la comparaison visuelle de l'étudiante (TripoSR : bonne forme, couleurs fausses ; TRELLIS : bonnes couleurs mais sol reconstruit et demi-lune devenue ovale), nouvel essai avec `tools/trials/trial_models.py` :

- TRELLIS **avec détourage** (`/preprocess_image`) : 3 GLB sur 3, sol supprimé, proportions cohérentes.
- Stable Fast 3D : 3 échecs (délai réseau, puis détourage renvoyant une image vide).
- InstantMesh : 1 GLB sans texture, puis arrêt sur le quota gratuit (offre payante refusée).

Détails dans `docs/QUALITE-3D.md`, section 3 bis.

## Fichiers

| Fichier | Rôle |
|---|---|
| `docs/QUALITE-3D.md` | Grille, contrats, résultats, relance, licences |
| `tools/trials/trial_trellis.py` | Essai reproductible et mesures automatiques (`measure_glb`) |
| `tools/trials/trial_models.py` | Essais multi-modèles (C2) |
| `backend/tests/test_trial_tools.py` | Tests des outils d'essai sans réseau |

## Tests

`measure_glb` est testée sur un GLB minimal valide et sur un contenu invalide. Suite complète lancée une fois en fin d'étape. Le fournisseur 3D de l'application n'a pas été modifié.
