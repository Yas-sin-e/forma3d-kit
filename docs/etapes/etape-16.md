# Étape 16 — Intégrer un modèle à une boutique (Sprint 5d)

## But

Donner à un vendeur un extrait à copier pour afficher dans sa boutique un modèle 3D qu'il a explicitement activé dans sa fiche Forma3D. Cette étape ajoute une page de visionneuse isolée et un petit widget web sans framework.

## Parcours d'une intégration

1. La propriétaire active « Intégration sur un site » depuis `#/modeles/{id}`. Un modèle inachevé ne peut pas être activé.
2. Le Studio affiche deux extraits : une iframe directe et `<forma3d-viewer>`. Ils sont visibles uniquement après l'activation.
3. L'iframe charge `/embed/{public_id}`. La page cherche le modèle terminé et activé, puis charge son GLB par la route de modèle public existante.
4. Le navigateur du site marchand vérifie la politique CSP `frame-ancestors` renvoyée avec la page. Le même site est accepté ; les autres origines doivent être ajoutées dans `EMBED_ALLOWED_ORIGINS`.

```text
Fiche Studio → activation explicite → code iframe ou widget
                                      ↓
Site marchand → /embed/{UUID public} → model-viewer → GLB public activé
```

## Fichiers à comprendre

| Fichier | Rôle et raison |
|---|---|
| `backend/app/routers/embed.py` | Construit la page viewer sans navigation Studio, vérifie l'activation par le service existant et applique `frame-ancestors`. |
| `backend/app/config.py` | Analyse `EMBED_ALLOWED_ORIGINS` comme liste d'origines HTTP(S) exactes ; refuse `*`, les identifiants et les chemins. |
| `backend/app/main.py` | Enregistre la route et transmet la configuration CSP à l'application. |
| `backend/app/routers/api_v1.py` et `backend/app/schemas.py` | Fournissent au client le code d'iframe et la balise de widget dans le contrat d'intégration. |
| `frontend/js/pages/model-detail.js` | Affiche les extraits après activation, permet la copie et explique le réglage des domaines autorisés. |
| `frontend/widget.js` | Définit `<forma3d-viewer>`, valide l'UUID public et crée l'iframe ; il ne fait pas de requête API et ne charge pas le modèle lui-même. |
| `.env.example` | Documente `EMBED_ALLOWED_ORIGINS`. La liste vide interdit le cadrage depuis un autre domaine. |
| `backend/tests/test_embed.py` | Vérifie la page activée/inactive, les 404, le GLB, la CSP et les en-têtes avec SQLite temporaire et sans réseau externe. |

## Politique et limites

- `EMBED_ALLOWED_ORIGINS` attend par exemple `https://boutique.example,https://admin.example`, sans chemin ni barre finale requise. Valeur vide : seul le même site peut intégrer le viewer. Le joker `*` est rejeté.
- `API_CORS_ORIGINS` et `EMBED_ALLOWED_ORIGINS` ont des rôles différents : CORS protège les appels API faits depuis JavaScript ; `frame-ancestors` contrôle quels sites peuvent afficher la page dans une iframe.
- Le widget est une commodité qui crée une iframe ; l'isolation de rendu et la politique de cadrage restent celles de `/embed/{public_id}`.
- Une page inconnue, un modèle désactivé, supprimé ou sans GLB renvoie 404. La route ne révèle pas de chemin local ni la photo source.
- Le modèle public est accessible à toute personne connaissant son UUID après activation. Le Studio n'a toujours pas d'authentification et reste local ou de démonstration ; ne pas exposer son interface d'administration publiquement.
- La page charge la bibliothèque `<model-viewer>` 4.4.0 depuis le CDN Google, comme le Studio. Un navigateur sans accès à ce CDN ne pourra pas afficher le viewer.

## Vérification et limites de la session

La suite complète pytest contient 99 tests et passe ; les tests d'intégration utilisent un GLB synthétique et des chemins temporaires. La vérification ciblée compte 15 tests. `HF_SPACE_ID` a été vidé dans le processus et dotenv désactivé ; aucun appel fournisseur n'a eu lieu. Le code JavaScript a été vérifié par `node --check` et les diffs par `git diff --check`.

Aucun navigateur n'a été piloté dans cette étape : la mise en page de la fiche, le bouton de copie, l'intégration sur une boutique réelle et les restrictions CSP dans un navigateur ne sont pas visuellement vérifiés. La génération d'un vrai modèle 3D n'a pas été retestée.
