# Rôle : sert une page isolée contenant seulement le viewer d’un modèle activé.
# Exécution : une iframe ou le widget Forma3D ouvre /embed/{public_id}.
"""Page d’intégration 3D minimale avec politique CSP de cadrage explicite."""

# html.escape (standard) : remplace < > & " par des entités HTML.
# Un nom de fichier ne peut donc pas injecter de script dans la page (protection XSS).
from html import escape
# Path : pour retirer l'extension du nom de fichier.
from pathlib import Path
# Annotated : associe un type et une dépendance FastAPI.
from typing import Annotated

# Outils FastAPI : routeur, injection, erreur HTTP, requête.
from fastapi import APIRouter, Depends, HTTPException, Request
# HTMLResponse : réponse dont le corps est une page HTML (et non du JSON).
from fastapi.responses import HTMLResponse

# Objet métier d'une génération.
from app.models import GenerationRecord
# Réutilise la lecture d'un modèle activé et la fourniture du service.
from app.routers.models import _get_enabled_public_model, get_generation_service
# Service de génération.
from app.services.generation_service import GenerationService

# Groupe de routes préfixées par /embed.
router = APIRouter(prefix="/embed", tags=["embed"])


# Construit l'en-tête CSP frame-ancestors.
def _frame_ancestors(request: Request) -> str:
    """Construit une directive CSP limitée au même site et aux origines configurées.

    frame-ancestors dit au NAVIGATEUR quels sites ont le droit d'afficher cette page dans une iframe.
    Par défaut : seulement 'self' (Forma3D lui-même) ; EMBED_ALLOWED_ORIGINS ajoute des sites précis.
    """
    # Origines autorisées configurées.
    allowed_origins = tuple(request.app.state.embed_allowed_origins)
    # « frame-ancestors 'self' » suivi des origines autorisées, s'il y en a.
    return "frame-ancestors 'self'" + (" " + " ".join(allowed_origins) if allowed_origins else "")


# Page HTML d'erreur.
def _error_page() -> str:
    """Retourne un message simple lorsque le modèle ne peut pas être intégré."""
    # Renvoie une page complète...
    return (
        # ...début du document en français, encodage UTF-8...
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        # ...adaptation aux écrans mobiles...
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        # ...titre de l'onglet et début du style...
        '<title>Modèle 3D indisponible</title><style>'
        # ...fond sombre, contenu centré...
        'body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0E1218;'
        # ...texte clair...
        'color:#F1F5F9;font:16px system-ui,sans-serif;padding:24px;box-sizing:border-box}'
        # ...largeur de lecture limitée...
        'p{max-width:34rem;line-height:1.55}</style></head><body>'
        # ...message d'erreur annoncé aux lecteurs d'écran...
        '<p role="alert">Ce modèle 3D n’est pas disponible. Il a peut-être été désactivé ou supprimé.</p>'
        # ...fin du document.
        '</body></html>'
    )


# Page HTML du viewer.
def _viewer_page(record: GenerationRecord, auto_rotate: bool) -> str:
    """Construit le document d’iframe sans navigation Studio ni donnée privée."""
    # Nom du modèle sans extension, échappé (pas d'injection de HTML).
    title = escape(Path(record.filename).stem, quote=True)
    # Attribut de rotation automatique, seulement si demandé.
    rotate = " auto-rotate" if auto_rotate else ""
    # URL publique du GLB, échappée.
    model_url = escape(f"/public/models/{record.public_id}/glb", quote=True)
    # Renvoie une page complète...
    return (
        # ...début du document...
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        # ...adaptation aux mobiles...
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        # ...titre de l'onglet...
        f'<title>{title} — aperçu 3D</title>'
        # ...charge le composant <model-viewer> depuis le CDN de Google...
        '<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.4.0/model-viewer.min.js"></script>'
        # ...la page occupe tout le cadre, sans défilement...
        '<style>html,body{width:100%;height:100%;margin:0;background:#0E1218;overflow:hidden}'
        # ...le viewer occupe toute la page...
        'model-viewer{display:block;width:100%;height:100%;min-height:320px;background:#0E1218}'
        # ...fin de l'en-tête...
        '</style></head><body>'
        # ...le viewer : fichier, texte alternatif, rotation et zoom à la souris...
        f'<model-viewer src="{model_url}" alt="Aperçu 3D : {title}" camera-controls touch-action="pan-y"'
        # ...pas d'animation d'invite, éclairage neutre, exposition, ombre, rotation facultative...
        f' interaction-prompt="none" environment-image="neutral" exposure="1.08" shadow-intensity="0.72"{rotate}></model-viewer>'
        # ...fin du document.
        '</body></html>'
    )


# Route GET /embed/{public_id}, renvoie du HTML, masquée de /docs.
@router.get("/{public_id}", response_class=HTMLResponse, include_in_schema=False)
# Affiche le viewer d'un modèle...
def show_embedded_model(
    # ...UUID public lu dans l'URL...
    public_id: str,
    # ...requête...
    request: Request,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> HTMLResponse:
    """Affiche uniquement le viewer d’un modèle DONE avec intégration activée."""
    # En-têtes de sécurité : CSP (qui peut encadrer la page), no-store (pas de cache),
    # nosniff (ne pas deviner un autre type de contenu), Referrer-Policy (adresse transmise limitée).
    # En-têtes de la réponse...
    headers = {
        # ...qui peut encadrer cette page...
        "Content-Security-Policy": _frame_ancestors(request),
        # ...pas de cache...
        "Cache-Control": "no-store",
        # ...pas de devinette de type...
        "X-Content-Type-Options": "nosniff",
        # ...adresse d'origine limitée.
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    # Essaie de lire un modèle terminé et activé...
    try:
        # ...sinon une erreur HTTP est levée.
        record, _model_path = _get_enabled_public_model(public_id, service)
    # Modèle absent ou désactivé...
    except HTTPException:
        # ...page d'erreur 404.
        return HTMLResponse(content=_error_page(), status_code=404, headers=headers)
    # Renvoie la page du viewer...
    return HTMLResponse(
        # ...rotation automatique si ?auto-rotate=1...
        content=_viewer_page(record, request.query_params.get("auto-rotate") == "1"),
        # ...statut 200...
        status_code=200,
        # ...avec les en-têtes de sécurité.
        headers=headers,
    )
