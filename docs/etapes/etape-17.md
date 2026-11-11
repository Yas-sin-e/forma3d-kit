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

## Guide accessible dans le Studio

`docs/` n'est pas servi par FastAPI : un lien vers `docs/INTEGRATION.md` ne s'ouvrirait pas dans le navigateur. La page `frontend/js/pages/guide.js` (route `#/guide`) reprend donc le même contrat en HTML, avec l'adresse réelle du service insérée dans les commandes `curl` et les extraits iframe/widget, et un bouton Copier par bloc. Elle est reliée depuis le raccourci « Guide d'intégration » de l'accueil, le menu Administration, le pied de page et la page Clés API. Les identifiants restent des marqueurs (`ID_DU_MODELE`, `UUID_PUBLIC`) : aucun modèle n'est inventé.

## Vérification honnête

- Tests statiques : le guide et l'exemple (tests de Codex) et la page `#/guide` (route, liens, contrat).
- Suite pytest complète lancée une fois en fin d'étape (résultat dans le compte rendu de commit).
- `node --check` sur les modules JavaScript.
- Non vérifié : rendu de la page `#/guide` dans un navigateur (pas de pilotage demandé), intégration depuis un vrai site tiers, génération réelle avec le service 3D et CI GitHub.
