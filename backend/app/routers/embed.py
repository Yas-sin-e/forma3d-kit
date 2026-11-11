# Rôle : sert une page isolée contenant seulement le viewer d’un modèle activé.
# Exécution : une iframe ou le widget Forma3D ouvre /embed/{public_id}.
"""Page d’intégration 3D minimale avec politique CSP de cadrage explicite."""

from html import escape
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.models import GenerationRecord
from app.routers.models import _get_enabled_public_model, get_generation_service
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/embed", tags=["embed"])


def _frame_ancestors(request: Request) -> str:
    """Construit une directive CSP limitée au même site et aux origines configurées."""
    allowed_origins = tuple(request.app.state.embed_allowed_origins)
    return "frame-ancestors 'self'" + (" " + " ".join(allowed_origins) if allowed_origins else "")


def _error_page() -> str:
    """Retourne un message simple lorsque le modèle ne peut pas être intégré."""
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Modèle 3D indisponible</title><style>'
        'body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0E1218;'
        'color:#F1F5F9;font:16px system-ui,sans-serif;padding:24px;box-sizing:border-box}'
        'p{max-width:34rem;line-height:1.55}</style></head><body>'
        '<p role="alert">Ce modèle 3D n’est pas disponible. Il a peut-être été désactivé ou supprimé.</p>'
        '</body></html>'
    )


def _viewer_page(record: GenerationRecord, auto_rotate: bool) -> str:
    """Construit le document d’iframe sans navigation Studio ni donnée privée."""
    title = escape(Path(record.filename).stem, quote=True)
    rotate = " auto-rotate" if auto_rotate else ""
    model_url = escape(f"/public/models/{record.public_id}/glb", quote=True)
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{title} — aperçu 3D</title>'
        '<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.4.0/model-viewer.min.js"></script>'
        '<style>html,body{width:100%;height:100%;margin:0;background:#0E1218;overflow:hidden}'
        'model-viewer{display:block;width:100%;height:100%;min-height:320px;background:#0E1218}'
        '</style></head><body>'
        f'<model-viewer src="{model_url}" alt="Aperçu 3D : {title}" camera-controls touch-action="pan-y"'
        f' interaction-prompt="none" environment-image="neutral" exposure="1.08" shadow-intensity="0.72"{rotate}></model-viewer>'
        '</body></html>'
    )


@router.get("/{public_id}", response_class=HTMLResponse, include_in_schema=False)
def show_embedded_model(
    public_id: str,
    request: Request,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> HTMLResponse:
    """Affiche uniquement le viewer d’un modèle DONE avec intégration activée."""
    headers = {
        "Content-Security-Policy": _frame_ancestors(request),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    try:
        record, _model_path = _get_enabled_public_model(public_id, service)
    except HTTPException:
        return HTMLResponse(content=_error_page(), status_code=404, headers=headers)
    return HTMLResponse(
        content=_viewer_page(record, request.query_params.get("auto-rotate") == "1"),
        status_code=200,
        headers=headers,
    )
