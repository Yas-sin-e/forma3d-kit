# Étape 20 — Sous-étape B : finition du GLB côté serveur

Date : 11 novembre 2026. Validée par l'étudiante (« OK pour B »).

## But et livrable vérifiable

- But : que le fichier GLB enregistré après une génération soit correct dans **n'importe quel** viewer (téléchargement, page `/embed`, plateforme e-commerce), pas seulement dans le Studio.
- Livrable : chaque nouveau GLB généré reçoit un matériau mat et des normales par sommet ; positions, indices et couleurs restent identiques.
- Ce n'est **pas** une amélioration de la géométrie : la forme produite par TripoSR est inchangée.

## Pourquoi c'est utile en plus de la sous-étape A

La sous-étape A corrige l'affichage dans les viewers du Studio. Mais la page publique `/embed/{public_id}`, un fichier téléchargé ou un autre logiciel lisaient toujours le matériau glTF par défaut (100 % métallique). La sous-étape B corrige le fichier lui-même.

## Fichiers

| Fichier | Rôle |
|---|---|
| `backend/app/services/glb_finisher.py` (nouveau) | `finish_glb()` : lit le GLB, ajoute le matériau `forma3d-product` (metallic 0, roughness 0,8) aux primitives sans matériau et un attribut `NORMAL` calculé (moyenne pondérée par l'aire des triangles), puis réécrit le conteneur aligné sur 4 octets |
| `backend/app/services/generation_service.py` | `_finish_generated_model()` appelé avant `save_model()` ; l'original est gardé si le résultat n'est pas un GLB 2.0 valide |
| `backend/tests/test_glb_finisher.py` (nouveau) | 6 tests : finition d'un GLB brut, GLB complet inchangé, matériau d'auteur conservé, fichiers invalides inchangés, calcul des normales, branchement dans le service |

**Aucune dépendance ajoutée** : le calcul utilise `struct` et `math` de Python (numpy n'était pas nécessaire).

## Règles de sécurité

- La finition ne lève jamais d'exception : structure inattendue (buffer externe, accesseur creux, primitive non triangulaire, indice hors limites) → fichier d'origine renvoyé.
- Un matériau existant n'est jamais remplacé ; un GLB qui a déjà ses normales n'en reçoit pas d'autres.
- Seuls les nouveaux GLB **générés** sont finis. Les imports GLB (fichiers de la propriétaire), les exemples du catalogue et les modèles déjà enregistrés ne sont pas modifiés.

## Preuve sur les 5 GLB réels (copies dans un dossier temporaire)

| Fichier | Durée | GLB 2.0 valide | Taille avant → après |
|---|---:|---|---|
| chair-bentwood | 0,14 s | oui | 1 236 604 → 1 608 008 octets |
| chair-met-01 | 0,09 s | oui | 865 856 → 1 125 884 octets |
| chair-met-02 | 0,21 s | oui | 2 050 148 → 2 665 596 octets |
| side-table-met | 0,09 s | oui | 1 035 632 → 1 346 484 octets |
| stool-met-01 | 0,29 s | oui | 2 619 760 → 3 406 304 octets |

Capture headless Edge (model-viewer 4.4.0, sans la correction A) : le fichier complété apparaît mat et lisible, le fichier brut sombre et réfléchissant. **L'effet des normales est à peine visible** sur ces maillages denses (20 000 à 65 000 sommets) : le gain visible vient surtout du matériau. Les fichiers grossissent d'environ 30 % (12 octets de normale par sommet). La capture n'est pas versionnée.

## Tests

```bash
cd backend
.venv/Scripts/python.exe -m pytest -q tests/test_glb_finisher.py
```

## Non vérifié et suite possible

- Pas de génération réelle : le serveur 3D était hors ligne. Le branchement est prouvé par un fournisseur de test qui renvoie un GLB brut.
- Les modèles déjà enregistrés ne sont pas repris. Un script de reprise réécrirait des fichiers existants : à proposer séparément, avec sauvegarde et accord explicite.
