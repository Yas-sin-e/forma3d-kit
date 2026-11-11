# Étape 22 — Sous-étape C3 : TRELLIS branché dans Forma3D

Date : 11 novembre 2026. Validée par l'étudiante (« Oui, branche TRELLIS ») après la comparaison visuelle C2.

## But et livrable vérifiable

- But : qu'une génération lancée depuis Forma3D puisse utiliser TRELLIS (couleurs texturées, sol détouré), TripoSR restant le défaut.
- Livrable vérifiable : avec `IMAGE3D_PROVIDER=trellis`, une photo envoyée dans le Studio donne un GLB réel, validé, affiché et téléchargeable. C'est la seule preuve de réussite selon `docs/QUALITE-3D.md`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `backend/app/providers/trellis.py` (nouveau) | `TrellisSpaceProvider` : `view_api()`, `/start_session`, `/preprocess_image` (détourage), `/generate_and_extract_glb`, contrôle GLB 2.0, délai global, erreurs claires (quota), jeton masqué |
| `backend/app/config.py` | `IMAGE3D_PROVIDER` (`triposr` par défaut ou `trellis`) et `TRELLIS_SPACE_ID` (identifiant « propriétaire/nom » obligatoire, jamais une URL) |
| `backend/app/main.py` | Choisit le fournisseur au démarrage ; message de santé propre à TRELLIS |
| `backend/app/services/glb_finisher.py` | Met `metallicFactor = 0` quand un matériau texturé l'omet (cas TRELLIS, sinon métal par défaut) |
| `.env.example` | Documente les deux nouvelles variables |
| `backend/tests/test_trellis_provider.py` (nouveau) | 9 tests avec un faux client Gradio |

## Sécurité et limites

- Le jeton `HF_TOKEN` n'est envoyé qu'à un identifiant de Space Hugging Face ; il est masqué dans les messages d'erreur.
- Quota GPU gratuit limité par jour (épuisé deux fois pendant les essais) : la création peut échouer avec un message explicite ; aucun abonnement, aucun contournement.
- Licence : TRELLIS est sous MIT ; l'usage commercial des modèles générés reste à confirmer. Photos de produits uniquement, sans personne.
- La table en demi-lune risque encore d'être trop profonde (face cachée devinée) ; le parcours multi-vues n'est pas branché.

## Activation (par l'étudiante, dans `backend/.env`, jamais commité)

```text
IMAGE3D_PROVIDER=trellis
HF_TOKEN=votre_jeton_gratuit
```

Puis redémarrer le serveur. Revenir à TripoSR : `IMAGE3D_PROVIDER=triposr`.

## Tests

```bash
cd backend
.venv/Scripts/python.exe -m pytest -q tests/test_trellis_provider.py tests/test_glb_finisher.py
```

## Vérification réelle

Première tentative (11/11, soir) : le Studio a appelé TRELLIS, refus du Space pour quota GPU gratuit épuisé (« 120s requested vs. 0s left »). La chaîne Forma3D → Space fonctionne jusqu'au quota ; le résultat GLB n'est pas encore obtenu. La page Créer affichait un message générique accusant la photo : elle montre maintenant la vraie cause renvoyée par le serveur.

Tant qu'une génération n'a pas abouti, TRELLIS n'est **pas** déclaré démontré dans Forma3D.

## Exemples du catalogue remplacés (11 novembre 2026)

À la demande de l'étudiante, les exemples chaise cintrée, tabouret et table d'appoint utilisent désormais les GLB TRELLIS détourés des essais C2 (75,8 s, 105,1 s et 91,2 s), passés par la finition (normales ajoutées, `metallicFactor` mis à 0). Les deux chaises métal restent TripoSR.

- Originaux TripoSR sauvegardés dans `backend/data/feasibility-results-triposr/` (hors Git) : pour revenir en arrière, les recopier dans `backend/data/feasibility-results/`.
- Honnêteté : `frontend/js/format.js` associe à chaque exemple son fournisseur et sa durée mesurée ; la fiche affiche « Exemple du catalogue · TRELLIS » ou « · TripoSR ».
- Ces exemples sont des résultats d'essai par script : ils ne remplacent pas la preuve d'une génération lancée depuis le Studio.
