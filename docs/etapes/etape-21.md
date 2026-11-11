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

**Aucun fournisseur alternatif démontré à ce jour.** TripoSR reste le seul fournisseur prouvé. L'outil d'essai est prêt pour une relance après renouvellement du quota, ou avec un jeton gratuit défini dans le terminal de l'étudiante.

## Fichiers

| Fichier | Rôle |
|---|---|
| `docs/QUALITE-3D.md` | Grille, contrats, résultats, relance, licences |
| `tools/trials/trial_trellis.py` | Essai reproductible et mesures automatiques (`measure_glb`) |
| `backend/tests/test_trial_tools.py` | Tests de `measure_glb` sans réseau |

## Tests

`measure_glb` est testée sur un GLB minimal valide et sur un contenu invalide. Suite complète lancée une fois en fin d'étape. Le fournisseur 3D de l'application n'a pas été modifié.
