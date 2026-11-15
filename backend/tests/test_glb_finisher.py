# Rôle : vérifie la finition des GLB générés (matériau mat, normales) et son branchement dans le service.
# Exécution : pytest ; GLB minimaux construits en mémoire, aucun fournisseur ni réseau.
"""Tests de app/services/glb_finisher.py (sous-étape B)."""

import json
import math
import struct
from pathlib import Path

from PIL import Image

from app.models import GenerationStatus, ProductCategory
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.services.demo_gallery import DemoGallery
from app.services.generation_service import GenerationService
from app.services.glb_finisher import compute_vertex_normals, finish_glb
from app.services.upload_validator import ValidatedUpload
from app.storage.local_storage import LocalStorage


def _glb(document: dict, binary: bytes) -> bytes:
    """Fabrique en mémoire un petit GLB de test (document JSON + données binaires)."""
    json_bytes = json.dumps(document).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    binary += b"\x00" * (-len(binary) % 4)
    total = 12 + 8 + len(json_bytes) + 8 + len(binary)
    return (b"glTF" + struct.pack("<II", 2, total) + struct.pack("<II", len(json_bytes), 0x4E4F534A)
            + json_bytes + struct.pack("<II", len(binary), 0x004E4942) + binary)


def _raw_triangle_glb(with_material: bool = False, with_normals: bool = False) -> bytes:
    """Un triangle dans le plan XY, avec couleurs par sommet, comme une sortie TripoSR simplifiée."""
    positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    colors = struct.pack("<12f", *([0.2, 0.15, 0.1, 1.0] * 3))
    indices = struct.pack("<3H", 0, 1, 2) + b"\x00\x00"
    normals = struct.pack("<9f", *([0, 0, 1] * 3))
    binary = positions + colors + indices + (normals if with_normals else b"")
    views = [
        {"buffer": 0, "byteOffset": 0, "byteLength": 36},
        {"buffer": 0, "byteOffset": 36, "byteLength": 48},
        {"buffer": 0, "byteOffset": 84, "byteLength": 6},
    ]
    accessors = [
        {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]},
        {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC4"},
        {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
    ]
    attributes = {"POSITION": 0, "COLOR_0": 1}
    if with_normals:
        views.append({"buffer": 0, "byteOffset": 92, "byteLength": 36})
        accessors.append({"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"})
        attributes["NORMAL"] = 3
    primitive = {"attributes": attributes, "indices": 2}
    document = {
        "asset": {"version": "2.0"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [primitive]}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views, "accessors": accessors,
    }
    if with_material:
        document["materials"] = [{"name": "auteur"}]
        primitive["material"] = 0
    return _glb(document, binary)


def _parse(content: bytes) -> tuple[dict, bytes]:
    """Relit un GLB produit par le test et renvoie son document JSON et ses données binaires."""
    json_length = struct.unpack_from("<I", content, 12)[0]
    document = json.loads(content[20:20 + json_length])
    bin_offset = 20 + json_length
    bin_length = struct.unpack_from("<I", content, bin_offset)[0]
    return document, content[bin_offset + 8: bin_offset + 8 + bin_length]


def test_raw_glb_receives_matte_material_and_unit_normals_without_touching_geometry() -> None:
    """Prouve qu'un GLB brut reçoit un matériau mat et des normales unitaires, sans changer la géométrie."""
    raw = _raw_triangle_glb()
    finished, report = finish_glb(raw)

    assert report.changed and report.normals_added == 1 and report.materials_added == 1
    assert DemoGallery.is_valid_glb_2(finished)
    document, binary = _parse(finished)
    primitive = document["meshes"][0]["primitives"][0]
    material = document["materials"][primitive["material"]]
    assert material["pbrMetallicRoughness"]["metallicFactor"] == 0.0
    assert material["pbrMetallicRoughness"]["roughnessFactor"] == 0.8
    normal_accessor = document["accessors"][primitive["attributes"]["NORMAL"]]
    view = document["bufferViews"][normal_accessor["bufferView"]]
    assert view["byteOffset"] % 4 == 0
    normals = [struct.unpack_from("<3f", binary, view["byteOffset"] + 12 * i) for i in range(3)]
    assert all(math.isclose(n[2], 1.0) and math.isclose(n[0], 0.0, abs_tol=1e-7) for n in normals)
    # Positions, couleurs et indices restent identiques octet pour octet.
    _, raw_binary = _parse(raw)
    assert binary[:90] == raw_binary[:90]
    assert primitive["attributes"]["POSITION"] == 0 and primitive["attributes"]["COLOR_0"] == 1
    assert document["buffers"][0]["byteLength"] == view["byteOffset"] + view["byteLength"]


def test_complete_glb_is_returned_unchanged() -> None:
    """Prouve qu'un GLB déjà complet est renvoyé tel quel."""
    complete = _raw_triangle_glb(with_material=True, with_normals=True)
    finished, report = finish_glb(complete)
    assert finished == complete
    assert not report.changed


def test_existing_author_material_is_kept_and_only_normals_are_added() -> None:
    """Prouve qu'un matériau existant est conservé et que seules les normales manquantes sont ajoutées."""
    finished, report = finish_glb(_raw_triangle_glb(with_material=True))
    document, _ = _parse(finished)
    assert report.materials_added == 0 and report.normals_added == 1
    assert document["materials"] == [{"name": "auteur"}]


def test_invalid_or_unsupported_files_are_returned_unchanged() -> None:
    """Prouve qu'un fichier invalide ou non géré est renvoyé inchangé (la finition ne fait jamais échouer une génération)."""
    for content in (b"", b"not a glb at all", b"glTF" + b"\x00" * 30):
        finished, report = finish_glb(content)
        assert finished == content and not report.changed


def test_normals_are_area_weighted_and_degenerate_vertices_point_up() -> None:
    """Prouve que les normales sont pondérées par l'aire et qu'un sommet isolé pointe vers le haut."""
    positions = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (5, 5, 5)]
    normals = compute_vertex_normals(positions, [0, 1, 2])
    assert normals[0] == (0.0, 0.0, 1.0)
    assert normals[3] == (0.0, 1.0, 0.0)


def test_generation_service_stores_the_finished_glb(tmp_path: Path) -> None:
    """Prouve que le service enregistre bien le GLB fini, et non le GLB brut."""
    raw = _raw_triangle_glb()

    class RawGlbProvider:
        """Faux fournisseur qui renvoie un GLB brut, sans matériau ni normales."""
        def generate(self, image_path: Path) -> bytes:
            """Faux fournisseur : remplace l'appel au service d'IA (aucun réseau, aucune vraie génération)."""
            return raw

    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = GenerationService(RawGlbProvider(), LocalStorage(tmp_path), repository)
    photo = tmp_path / "photo.png"
    Image.new("RGB", (64, 64), "white").save(photo)
    upload = ValidatedUpload(filename="chair.png", content_type="image/png", size_bytes=photo.stat().st_size)
    record = service.create_generation(upload, photo.read_bytes(), ProductCategory.CHAIR)

    service.run(record.id)

    assert service.get_generation(record.id).status is GenerationStatus.DONE
    stored = service.get_model_path(record.id).read_bytes()
    document, _ = _parse(stored)
    assert stored != raw
    assert document["materials"][0]["name"] == "forma3d-product"
    assert "NORMAL" in document["meshes"][0]["primitives"][0]["attributes"]
