# 9. Étape 8 — Afficher un modèle sur un site partenaire

Fichiers : `backend/app/routers/api_v1.py`, `backend/app/routers/embed.py`, `frontend/widget.js`.

## Les trois façons d'intégrer

```
 Site partenaire                                    Forma3D
 ───────────────                                    ───────
 1. <iframe src=".../embed/{public_id}">  ────────► routers/embed.py  → page HTML + <model-viewer>
 2. <script src=".../static/widget.js">
    <forma3d-viewer model="{public_id}">  ────────► (crée une iframe vers /embed/{public_id})
 3. Son serveur : curl -H "X-API-Key: ..." ───────► routers/api_v1.py → créer, suivre, télécharger
```

Dans les trois cas, **rien n'est visible tant que la propriétaire n'a pas activé l'intégration** du modèle.

## Étape 8.1 — L'API externe versionnée (`routers/api_v1.py`)

**Versionnée** = toutes les adresses commencent par `/api/v1`. Si un jour le contrat change,
on crée `/api/v2` sans casser les sites qui utilisent `v1`.

### Les routes

| Méthode | Adresse | Rôle |
|---|---|---|
| POST | `/api/v1/models` | Envoie une photo → 202 |
| GET | `/api/v1/models/{id}` | État de la génération |
| GET | `/api/v1/models/{id}/glb` | Télécharge le GLB (409 si pas prêt) |
| GET | `/api/v1/models/{id}/integration-code` | Code `<iframe>` et code widget prêts à copier (403 si non activé) |

### Deux gardes enchaînés

```python
def require_api_v1_key(request, key = Depends(require_api_key), key_service = Depends(...)):
    reason = key_service.consume_rate_limit(key, request.app.state.api_rate_limit_per_minute)
    if reason == "revoked":
        raise HTTPException(status_code=401, ...)
    if reason == "rate_limit":
        raise HTTPException(status_code=429, detail="Limite de débit atteinte ; réessayez dans une minute.",
                            headers={"Retry-After": "60"})
    return key
```

1. `require_api_key` : la clé est-elle valide ? (sinon 401)
2. `require_api_v1_key` : a-t-elle dépassé **10 requêtes par minute** (réglable) ? (sinon 429)

### Créer un modèle : quota du jour en plus

```python
category_service.require_active(category)                         # catégorie active, sinon 403
reason = key_service.consume_daily_quota(_key, request.app.state.api_daily_generation_limit)
if reason == "daily_quota":
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    raise HTTPException(status_code=429, detail="Quota quotidien de créations atteint pour cette clé.",
                        headers={"Retry-After": str(wait_seconds)})    # secondes jusqu'à minuit UTC
record = service.create_generation(validated, content, category)
background_tasks.add_task(service.run, record.id)
```

| Limite | Valeur par défaut | Variable `.env` | Pourquoi |
|---|---|---|---|
| Requêtes par minute et par clé | 10 | `API_RATE_LIMIT_PER_MINUTE` | Éviter qu'un site sature le serveur |
| Créations par jour et par clé | 20 | `API_DAILY_GENERATION_LIMIT` | Le quota GPU gratuit est limité |

Ce sont **les mêmes** `UploadValidator` et `GenerationService` que le Studio : aucune règle n'est dupliquée.

### Les erreurs ont un format stable

Grâce au gestionnaire d'erreurs de `main.py`, un intégrateur reçoit toujours :

```json
{ "error": { "code": "rate_limited", "message": "Limite de débit atteinte ; réessayez dans une minute." } }
```

### Le code d'intégration est échappé

```python
source = escape(f"{base_url}/embed/{record.public_id}", quote=True)
title = escape(Path(record.filename).stem, quote=True)
iframe = f'<iframe src="{source}" title="Aperçu 3D : {title}" width="100%" height="480" loading="lazy" ...>'
```

`html.escape` transforme `<`, `>`, `"` en texte inoffensif. Un modèle nommé `"><script>...` ne peut pas
injecter de code dans la page du partenaire.

## Étape 8.2 — La page d'intégration (`routers/embed.py`)

`GET /embed/{public_id}` renvoie une petite page HTML complète qui contient seulement `<model-viewer>`.

```python
def _viewer_page(record, auto_rotate):
    model_url = escape(f"/public/models/{record.public_id}/glb", quote=True)
    return ('<!doctype html>...'
            '<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.4.0/model-viewer.min.js"></script>'
            f'<model-viewer src="{model_url}" alt="Aperçu 3D : {title}" camera-controls ...{rotate}></model-viewer>')
```

- `?auto-rotate=1` dans l'adresse fait tourner le modèle tout seul.
- Si le modèle n'est pas activé : une page d'erreur neutre (« Ce modèle 3D n'est pas disponible »), code 404.

### Les en-têtes de sécurité

```python
headers = {
    "Content-Security-Policy": _frame_ancestors(request),   # qui peut m'afficher dans une iframe
    "Cache-Control": "no-store",                            # désactivé = disparaît tout de suite
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

def _frame_ancestors(request) -> str:
    allowed_origins = tuple(request.app.state.embed_allowed_origins)
    return "frame-ancestors 'self'" + (" " + " ".join(allowed_origins) if allowed_origins else "")
```

- **CSP `frame-ancestors`** : le **navigateur** refuse d'afficher la page dans une iframe d'un site
  qui n'est pas dans la liste. Par défaut : seulement Forma3D lui-même (`'self'`).
- La liste se règle avec `EMBED_ALLOWED_ORIGINS=https://ma-boutique.com` dans `.env`.
- `no-store` : quand la propriétaire désactive un modèle, aucune copie ne reste en cache.

## Étape 8.3 — Le widget (`frontend/widget.js`)

Le partenaire colle deux lignes :

```html
<script src="https://forma3d.example/static/widget.js" defer></script>
<forma3d-viewer model="9b1c...e7" height="480" auto-rotate></forma3d-viewer>
```

### Une balise HTML inventée : le Web Component

```javascript
(() => {
  const widgetOrigin = new URL(document.currentScript.src, document.baseURI).origin;
  const publicIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  class Forma3DViewer extends HTMLElement {
    connectedCallback() {
      const root = this.shadowRoot || this.attachShadow({ mode: "open" });
      const publicId = (this.getAttribute("model") || "").trim();
      if (!publicIdPattern.test(publicId)) { /* message « modèle indisponible » */ return; }
      const height = Math.min(1200, Math.max(240, parsedHeight));
      const source = new URL(`/embed/${encodeURIComponent(publicId)}`, widgetOrigin);
      if (this.hasAttribute("auto-rotate")) source.searchParams.set("auto-rotate", "1");
      const iframe = document.createElement("iframe");
      iframe.src = source.toString();
      iframe.loading = "lazy";
      root.append(iframe);
    }
  }
  if (!customElements.get("forma3d-viewer")) customElements.define("forma3d-viewer", Forma3DViewer);
})();
```

- **`(() => { ... })()`** : fonction exécutée tout de suite ; ses variables ne polluent pas la page du partenaire.
- **`customElements.define`** : apprend au navigateur une nouvelle balise, `<forma3d-viewer>`.
- **`connectedCallback`** : appelée quand la balise apparaît dans la page.
- **Shadow DOM** (`attachShadow`) : le style du widget est isolé ; le CSS de la boutique ne le casse pas, et inversement.
- **`widgetOrigin`** : l'iframe pointe vers le serveur **d'où vient le script**, pas vers la boutique.
- Le `public_id` est vérifié (forme d'UUID) et la hauteur est bornée entre 240 et 1200 px.
- Finalement, le widget **crée une iframe vers `/embed`** : il hérite donc de toutes les protections de l'étape 8.2.

## À retenir

> L'intégration est **fermée par défaut** à trois niveaux : le modèle (désactivé), les sites autorisés
> (CORS et `frame-ancestors` vides), et l'API (clé + limite par minute + quota du jour).
