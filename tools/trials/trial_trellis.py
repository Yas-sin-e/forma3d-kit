# Rôle : essai reproductible d'un Space TRELLIS sur les photos de faisabilité, avec mesures selon docs/QUALITE-3D.md.
# Exécution : à la main depuis la racine du dépôt (voir la commande en bas) ; hors de l'application, aucun fichier versionné produit.
"""Essai de fournisseur image-vers-3D (sous-étape C).

Le script :
1. lit le contrat réel du Space avec view_api() et s'arrête si la fonction attendue est absente ;
2. ouvre une session (`/start_session`, nécessaire pour ce Space) ;
3. envoie une photo, mesure la durée, copie le GLB obtenu dans backend/data/trials/ (ignoré par Git) ;
4. imprime les mesures automatiques de la grille (validité, taille, sommets, matériaux, textures, boîte).

Quota : les Spaces ZeroGPU ont un quota journalier. Anonyme, il est très faible ; avec un jeton gratuit
Hugging Face défini dans la variable HF_TOKEN de VOTRE terminal, il est plus élevé. Le jeton n'est envoyé
qu'à huggingface.co. En cas de message de quota : arrêter et réessayer plus tard, sans contournement.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.demo_gallery import DemoGallery  # noqa: E402

SPACE_FUNCTION = "/generate_and_extract_glb"


def measure_glb(data: bytes) -> dict:
    """Mesures automatiques de la grille (critères 1, 2, 4 et 5) pour un contenu GLB."""
    report: dict = {"bytes": len(data), "valid_glb2": DemoGallery.is_valid_glb_2(data)}
    if not report["valid_glb2"]:
        return report
    json_length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    primitives = [p for mesh in document.get("meshes", []) for p in mesh.get("primitives", [])]
    accessors = document.get("accessors", [])
    report["vertices"] = sum(accessors[p["attributes"]["POSITION"]]["count"] for p in primitives)
    report["triangles"] = sum(accessors[p["indices"]]["count"] // 3 for p in primitives if "indices" in p)
    report["materials"] = len(document.get("materials", []))
    report["textures"] = len(document.get("textures", []))
    report["has_normals"] = all("NORMAL" in p["attributes"] for p in primitives)
    mins, maxs = [], []
    for primitive in primitives:
        position = accessors[primitive["attributes"]["POSITION"]]
        if "min" in position and "max" in position:
            mins.append(position["min"])
            maxs.append(position["max"])
    if mins:
        report["bbox_xyz"] = [round(max(m[i] for m in maxs) - min(m[i] for m in mins), 3) for i in range(3)]
    return report


def run_trial(space: str, photo: Path, output_dir: Path) -> dict:
    from gradio_client import Client, handle_file

    token = os.getenv("HF_TOKEN") or None
    client = Client(space, hf_token=token, verbose=False)
    endpoints = client.view_api(return_format="dict", print_info=False)["named_endpoints"]
    if SPACE_FUNCTION not in endpoints:
        raise SystemExit(f"Contrat changé : {SPACE_FUNCTION} absent ({sorted(endpoints)}).")
    client.predict(api_name="/start_session")
    started = time.perf_counter()
    result = client.predict(
        image=handle_file(str(photo)), multiimages=[], seed=0,
        ss_guidance_strength=7.5, ss_sampling_steps=12,
        slat_guidance_strength=3.0, slat_sampling_steps=12,
        multiimage_algo="stochastic", mesh_simplify=0.95, texture_size=1024,
        api_name=SPACE_FUNCTION,
    )
    elapsed = time.perf_counter() - started
    glb_source = result[2] if isinstance(result[2], str) else result[2]["value"]
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{photo.stem}-{space.replace('/', '_')}.glb"
    shutil.copyfile(glb_source, target)
    return {"photo": photo.name, "space": space, "seconds": round(elapsed, 1), "glb": str(target), **measure_glb(target.read_bytes())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Essai TRELLIS sur des photos de faisabilité.")
    parser.add_argument("photos", nargs="+", type=Path)
    parser.add_argument("--space", default="trellis-community/TRELLIS")
    parser.add_argument("--out", type=Path, default=ROOT / "backend" / "data" / "trials")
    args = parser.parse_args()
    for photo in args.photos:
        try:
            print(json.dumps(run_trial(args.space, photo, args.out), ensure_ascii=False))
        except Exception as error:  # chaque échec est consigné tel quel, puis l'essai s'arrête
            print(json.dumps({"photo": photo.name, "space": args.space, "error": f"{type(error).__name__}: {error}"}, ensure_ascii=False))
            if "quota" in str(error).lower():
                break


if __name__ == "__main__":
    main()

# Commande (PowerShell, racine du dépôt) :
#   $env:HF_TOKEN = "<votre jeton gratuit, facultatif>"
#   backend\.venv\Scripts\python.exe tools\trials\trial_trellis.py backend\data\feasibility-inputs\chair-bentwood.jpg
