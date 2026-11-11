# Rôle : essaie plusieurs modèles image-vers-3D (Stable Fast 3D, TRELLIS détouré, InstantMesh) sur les mêmes photos.
# Exécution : à la main depuis la racine du dépôt (commande en bas) ; hors application, GLB rangés dans backend/data/trials/.
"""Essais comparatifs de la sous-étape C2 (voir docs/QUALITE-3D.md).

Pour chaque modèle, le script :
1. lit le contrat réel du Space (view_api) et s'arrête si une fonction attendue manque ;
2. reproduit l'enchaînement de l'interface web (détourage du fond, puis génération) ;
3. copie le GLB obtenu et imprime les mesures automatiques de la grille.

Le jeton Hugging Face facultatif est lu dans la variable HF_TOKEN du terminal et n'est envoyé
qu'à huggingface.co. Au premier message de quota, l'essai s'arrête : aucun contournement.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("trial_trellis", Path(__file__).with_name("trial_trellis.py"))
_trial_trellis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_trial_trellis)
measure_glb = _trial_trellis.measure_glb

SPACES = {
    "sf3d": "stabilityai/stable-fast-3d",
    "trellis": "trellis-community/TRELLIS",
    "instantmesh": "TencentARC/InstantMesh",
}
REQUIRED_FUNCTIONS = {
    "sf3d": {"/requires_bg_remove", "/run_button"},
    "trellis": {"/start_session", "/preprocess_image", "/generate_and_extract_glb"},
    "instantmesh": {"/preprocess", "/generate_mvs", "/make3d"},
}


def file_path_from_output(value) -> str | None:
    """Extrait un chemin de fichier d'une sortie Gradio (chaîne, dict path/value, ou None)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    if isinstance(value, dict):
        for key in ("path", "value", "name"):
            if isinstance(value.get(key), str) and value[key]:
                return value[key]
    return None


def missing_functions(model: str, endpoints: set[str]) -> set[str]:
    """Fonctions attendues absentes du contrat lu : l'essai doit alors s'arrêter."""
    return REQUIRED_FUNCTIONS[model] - endpoints


def _run_sf3d(client, handle_file, photo: Path) -> str:
    preview, model_file = client.predict(image=handle_file(str(photo)), fr=0.85, api_name="/requires_bg_remove")
    glb = file_path_from_output(model_file)
    if glb:
        return glb
    preview_path = file_path_from_output(preview)
    if not preview_path:
        raise RuntimeError("Le détourage n'a renvoyé aucune image.")
    _, model_file = client.predict(
        input_image=handle_file(preview_path), foreground_ratio=0.85, remesh_option="None",
        vertex_count=-1, texture_size=1024, api_name="/run_button",
    )
    glb = file_path_from_output(model_file)
    if not glb:
        raise RuntimeError("Stable Fast 3D n'a renvoyé aucun modèle.")
    return glb


def _run_trellis(client, handle_file, photo: Path) -> str:
    client.predict(api_name="/start_session")
    prepared = file_path_from_output(client.predict(image=handle_file(str(photo)), api_name="/preprocess_image"))
    if not prepared:
        raise RuntimeError("Le détourage TRELLIS n'a renvoyé aucune image.")
    result = client.predict(
        image=handle_file(prepared), multiimages=[], seed=0,
        ss_guidance_strength=7.5, ss_sampling_steps=12, slat_guidance_strength=3.0, slat_sampling_steps=12,
        multiimage_algo="stochastic", mesh_simplify=0.95, texture_size=1024, api_name="/generate_and_extract_glb",
    )
    glb = file_path_from_output(result[2])
    if not glb:
        raise RuntimeError("TRELLIS n'a renvoyé aucun GLB.")
    return glb


def _run_instantmesh(client, handle_file, photo: Path) -> str:
    prepared = file_path_from_output(
        client.predict(input_image=handle_file(str(photo)), do_remove_background=True, api_name="/preprocess")
    )
    if not prepared:
        raise RuntimeError("Le détourage InstantMesh n'a renvoyé aucune image.")
    client.predict(input_image=handle_file(prepared), sample_steps=75, sample_seed=42, api_name="/generate_mvs")
    _, glb_output = client.predict(api_name="/make3d")
    glb = file_path_from_output(glb_output)
    if not glb:
        raise RuntimeError("InstantMesh n'a renvoyé aucun GLB.")
    return glb


RUNNERS = {"sf3d": _run_sf3d, "trellis": _run_trellis, "instantmesh": _run_instantmesh}


def run_trial(model: str, photo: Path, output_dir: Path) -> dict:
    from gradio_client import Client, handle_file

    space = SPACES[model]
    client = Client(space, token=os.getenv("HF_TOKEN") or None, verbose=False)
    endpoints = set(client.view_api(return_format="dict", print_info=False)["named_endpoints"])
    missing = missing_functions(model, endpoints)
    if missing:
        raise RuntimeError(f"Contrat changé, fonctions absentes : {sorted(missing)}")
    started = time.perf_counter()
    glb_source = RUNNERS[model](client, handle_file, photo)
    elapsed = time.perf_counter() - started
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{photo.stem}-{model}.glb"
    shutil.copyfile(glb_source, target)
    return {"photo": photo.name, "model": model, "space": space, "seconds": round(elapsed, 1),
            "glb": str(target), **measure_glb(target.read_bytes())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Essais comparatifs image-vers-3D.")
    parser.add_argument("photos", nargs="+", type=Path)
    parser.add_argument("--models", default="sf3d,trellis,instantmesh")
    parser.add_argument("--out", type=Path, default=ROOT / "backend" / "data" / "trials")
    args = parser.parse_args()
    for model in [m.strip() for m in args.models.split(",") if m.strip()]:
        for photo in args.photos:
            try:
                print(json.dumps(run_trial(model, photo, args.out), ensure_ascii=False), flush=True)
            except Exception as error:  # échec consigné tel quel
                message = f"{type(error).__name__}: {error}"
                print(json.dumps({"photo": photo.name, "model": model, "error": message}, ensure_ascii=False), flush=True)
                if "quota" in message.lower():
                    print(json.dumps({"stop": "quota atteint, essais arrêtés"}, ensure_ascii=False), flush=True)
                    return


if __name__ == "__main__":
    main()

# Commande (PowerShell, racine du dépôt) :
#   backend\.venv\Scripts\python.exe tools\trials\trial_models.py --models sf3d,trellis backend\data\feasibility-inputs\chair-bentwood.jpg
