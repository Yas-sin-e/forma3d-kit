# Étape 17 — Documentation et preuve intégrateur (Sprint 5e)

## But et livrable

Le but est de permettre à une personne qui développe une boutique de comprendre le contrat d'intégration sans lire tout le backend. Le livrable est `docs/INTEGRATION.md` plus `examples/integration.html`, une petite page HTML qui utilise le vrai widget avec une origine de service et un UUID public saisis.

## Comment lire l'exemple

La page demande l'adresse de Forma3D et l'identifiant public du modèle. Elle vérifie le format de l'origine et l'UUID, charge ensuite `/static/widget.js` depuis le service, puis crée `<forma3d-viewer>`. Elle n'a pas de modèle embarqué et ne déclenche pas de génération. L'intégration ne fonctionne que si le modèle existe, est terminé et a été explicitement activé ; le domaine de la page doit aussi être admis par `EMBED_ALLOWED_ORIGINS`.

## Parcours API expliqué dans le guide

1. La propriétaire crée une clé dans le Studio local et la copie une seule fois.
2. Un serveur de boutique conserve la clé et envoie une photo par `POST /api/v1/models`.
3. Le serveur marchand consulte `GET /api/v1/models/{id}` jusqu'à un état terminal, puis télécharge le GLB si l'état est `DONE`.
4. La propriétaire active le modèle dans le Studio ; le serveur marchand peut ensuite demander `GET /api/v1/models/{id}/integration-code`.
5. La page boutique utilise l'iframe ou le widget, sans transmettre la clé au navigateur du client.

```text
Serveur marchand --X-API-Key--> API v1 --> GenerationService --> SQLite + stockage GLB
       |                                             |
       +-- code widget / iframe <-- activation Studio + modèle public
                                         |
Boutique --<forma3d-viewer>--> /embed/{UUID public} --> viewer 3D
```

## Fichiers et raisons

| Fichier | Rôle |
|---|---|
| `docs/INTEGRATION.md` | Contrat concret : commandes curl, états, intégration, erreurs, quota et sécurité. |
| `examples/integration.html` | Démonstration autonome qui ne préremplit aucun modèle et n'expose aucune clé. |
| `frontend/widget.js` | Custom element déjà créé en 5d, il isole le viewer dans une iframe. |
| `backend/app/routers/api_v1.py` | Sert la génération authentifiée, le suivi, le GLB et les extraits d'intégration. |
| `backend/app/routers/embed.py` | Sert la vue publique minimale sous CSP. |
| `docs/STOCKAGE.md` | Explique le lien entre base SQLite, clés, compteurs et modèle public. |

## Vérification honnête

Deux tests statiques ciblés passent : ils vérifient la page exemple et le guide sans contacter l'API. La syntaxe de tous les fichiers JavaScript du frontend et du script inline de l'exemple a été contrôlée ; `git diff --check` doit être relancé après cette mise à jour documentaire.

La suite complète n'a pas été vérifiée pour cette étape. Sous le sandbox, le premier test `TestClient` se bloque sur son appel HTTP local. La commande nécessitant l'autorisation réseau locale a été refusée par le contrôle automatique après l'atteinte de la limite d'usage ; aucune tentative de contournement n'a été faite. La suite comptait 99 tests verts avant les modifications de 5e.

Le démarrage du serveur local n'a pas été confirmé : le processus lancé s'est arrêté et l'accès socket local a été refusé. Microsoft Edge n'a pas pu être activé après une nouvelle sélection (`failed to activate captured window`). Le rendu visuel, la vraie intégration sur un site tiers, le fournisseur distant et la CI ne sont pas vérifiés. Ne pas annoncer le Sprint 5 terminé avant pytest complet et vérification manuelle.
