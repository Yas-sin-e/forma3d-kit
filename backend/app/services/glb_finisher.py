# Rôle : complète un GLB généré qui n'a ni matériau ni normales, sans toucher à sa géométrie.
# Exécution : GenerationService l'appelle juste avant d'enregistrer le GLB renvoyé par le fournisseur.
"""Finition d'un GLB 2.0 : matériau produit mat et normales lissées par sommet.

Pourquoi : les GLB de TripoSR ne contiennent que des positions et une couleur par sommet.
Sans matériau, la norme glTF impose un matériau 100 % métallique qui assombrit le modèle ;
sans normales, chaque viewer calcule des faces plates (aspect facetté). On ajoute donc :
- un matériau `forma3d-product` (metallic 0, roughness 0,8) aux primitives qui n'en ont pas ;
- un attribut NORMAL calculé à partir des triangles (moyenne pondérée par l'aire) ;
- metallicFactor = 0 quand un matériau texturé l'omet (cas TRELLIS : la norme vaudrait 1).

Les positions, les indices et les couleurs ne sont jamais modifiés. En cas de structure
inattendue, la fonction renvoie le fichier d'origine inchangé : la finition ne doit jamais
faire échouer une génération.
"""

from __future__ import annotations

import json
import logging
import math
# struct (standard) : lit et écrit des nombres binaires (« <II » = deux entiers 32 bits, « <3f » = trois décimaux).
# Indispensable ici car un GLB est un fichier binaire. Équivalent de ByteBuffer en Java.
import struct
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_GLB_MAGIC = b"glTF"
_JSON_CHUNK = 0x4E4F534A
_BIN_CHUNK = 0x004E4942
_FLOAT = 5126
_INDEX_FORMATS = {5121: "B", 5123: "H", 5125: "I"}
_TRIANGLES = 4
PRODUCT_MATERIAL = {
    "name": "forma3d-product",
    "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.8},
}


@dataclass(frozen=True, slots=True)
class FinishReport:
    """Résumé de la finition, utile aux journaux et aux tests."""

    changed: bool
    normals_added: int = 0
    materials_added: int = 0
    metallic_fixed: int = 0
    reason: str = ""


class _Unsupported(Exception):
    """Structure GLB hors du cas simple géré : on rend le fichier tel quel."""


def _read_glb(content: bytes) -> tuple[dict, bytearray]:
    """Découpe un GLB en (document JSON, données binaires).

    Lit l'en-tête de 12 octets puis chaque bloc (« chunk ») : longueur, type, contenu.
    Lève _Unsupported si la structure n'est pas un GLB 2.0 simple.
    """
    if len(content) < 20 or content[:4] != _GLB_MAGIC:
        raise _Unsupported("en-tête GLB absent")
    version, total_length = struct.unpack_from("<II", content, 4)
    if version != 2 or total_length != len(content):
        raise _Unsupported("version ou longueur GLB inattendue")
    offset = 12
    document: dict | None = None
    binary = bytearray()
    while offset + 8 <= len(content):
        chunk_length, chunk_type = struct.unpack_from("<II", content, offset)
        chunk = content[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == _JSON_CHUNK and document is None:
            document = json.loads(chunk.decode("utf-8"))
        elif chunk_type == _BIN_CHUNK and not binary:
            binary = bytearray(chunk)
        offset += 8 + chunk_length
    if document is None:
        raise _Unsupported("bloc JSON absent")
    return document, binary


def _write_glb(document: dict, binary: bytearray) -> bytes:
    """Reconstruit un fichier GLB à partir du document JSON et du binaire.

    Chaque bloc est complété pour que sa taille soit un multiple de 4 octets (règle du format).
    """
    json_bytes = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    binary = bytes(binary) + b"\x00" * (-len(binary) % 4)
    total = 12 + 8 + len(json_bytes) + (8 + len(binary) if binary else 0)
    parts = [_GLB_MAGIC, struct.pack("<II", 2, total), struct.pack("<II", len(json_bytes), _JSON_CHUNK), json_bytes]
    if binary:
        parts += [struct.pack("<II", len(binary), _BIN_CHUNK), binary]
    return b"".join(parts)


def _accessor_view(document: dict, binary: bytearray, accessor_index: int) -> tuple[dict, int, int]:
    """Renvoie (accesseur, début dans le BIN, pas entre éléments) pour un accesseur non creux."""
    accessor = document["accessors"][accessor_index]
    if "sparse" in accessor or "bufferView" not in accessor:
        raise _Unsupported("accesseur creux ou sans bufferView")
    view = document["bufferViews"][accessor["bufferView"]]
    if view.get("buffer", 0) != 0:
        raise _Unsupported("plusieurs buffers")
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return accessor, start, view.get("byteStride", 0)


def _read_positions(document: dict, binary: bytearray, accessor_index: int) -> list[tuple[float, float, float]]:
    """Lit la liste des sommets (x, y, z) décrite par un accesseur glTF.

    Lève _Unsupported si ce ne sont pas des triplets de décimaux ou si les données dépassent le binaire.
    """
    accessor, start, stride = _accessor_view(document, binary, accessor_index)
    if accessor.get("componentType") != _FLOAT or accessor.get("type") != "VEC3":
        raise _Unsupported("positions non float VEC3")
    stride = stride or 12
    count = accessor["count"]
    if start + stride * (count - 1) + 12 > len(binary):
        raise _Unsupported("positions hors du BIN")
    return [struct.unpack_from("<3f", binary, start + i * stride) for i in range(count)]


def _read_indices(document: dict, binary: bytearray, primitive: dict, vertex_count: int) -> list[int]:
    """Lit la liste des indices de triangles ; sans indices, les sommets sont pris dans l'ordre (0, 1, 2…)."""
    if "indices" not in primitive:
        return list(range(vertex_count))
    accessor, start, stride = _accessor_view(document, binary, primitive["indices"])
    fmt = _INDEX_FORMATS.get(accessor.get("componentType"))
    if fmt is None or accessor.get("type") != "SCALAR":
        raise _Unsupported("indices de type inattendu")
    size = struct.calcsize(fmt)
    count = accessor["count"]
    if stride in (0, size):
        if start + size * count > len(binary):
            raise _Unsupported("indices hors du BIN")
        return list(struct.unpack_from(f"<{count}{fmt}", binary, start))
    return [struct.unpack_from(f"<{fmt}", binary, start + i * stride)[0] for i in range(count)]


def compute_vertex_normals(positions: list[tuple[float, float, float]], indices: list[int]) -> list[tuple[float, float, float]]:
    """Moyenne des normales des triangles adjacents, pondérée par leur aire (produit vectoriel brut)."""
    sums = [[0.0, 0.0, 0.0] for _ in positions]
    vertex_count = len(positions)
    for i in range(0, len(indices) - 2, 3):
        a, b, c = indices[i], indices[i + 1], indices[i + 2]
        if a >= vertex_count or b >= vertex_count or c >= vertex_count:
            raise _Unsupported("indice hors des sommets")
        ax, ay, az = positions[a]
        bx, by, bz = positions[b]
        cx, cy, cz = positions[c]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        # Produit vectoriel de deux côtés du triangle : un vecteur perpendiculaire à sa surface,
        # dont la longueur est proportionnelle à l'aire (les grands triangles pèsent donc plus).
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        for vertex in (a, b, c):
            total = sums[vertex]
            total[0] += nx
            total[1] += ny
            total[2] += nz
    normals = []
    for x, y, z in sums:
        length = math.sqrt(x * x + y * y + z * z)
        # Sommet isolé ou dégénéré : normale arbitraire vers le haut, pour rester un vecteur unitaire valide.
        normals.append((x / length, y / length, z / length) if length > 1e-12 else (0.0, 1.0, 0.0))
    return normals


def finish_glb(content: bytes) -> tuple[bytes, FinishReport]:
    """Ajoute matériau et normales manquants ; renvoie (octets, rapport). Ne lève jamais d'exception."""
    try:
        document, binary = _read_glb(content)
        buffers = document.get("buffers", [])
        if len(buffers) > 1 or (buffers and "uri" in buffers[0]):
            raise _Unsupported("buffer externe")
        primitives = [p for mesh in document.get("meshes", []) for p in mesh.get("primitives", [])]
        needs_normals = [p for p in primitives if "NORMAL" not in p.get("attributes", {})]
        needs_material = [p for p in primitives if "material" not in p]
        implicit_metal = [
            m for m in document.get("materials", [])
            if isinstance(m.get("pbrMetallicRoughness"), dict)
            and "metallicFactor" not in m["pbrMetallicRoughness"]
            and "metallicRoughnessTexture" not in m["pbrMetallicRoughness"]
        ]
        if not needs_normals and not needs_material and not implicit_metal:
            return content, FinishReport(changed=False, reason="déjà complet")
        if any(p.get("mode", _TRIANGLES) != _TRIANGLES for p in needs_normals):
            raise _Unsupported("primitive autre que triangles")

        for primitive in needs_normals:
            positions = _read_positions(document, binary, primitive["attributes"]["POSITION"])
            indices = _read_indices(document, binary, primitive, len(positions))
            normals = compute_vertex_normals(positions, indices)
            binary.extend(b"\x00" * (-len(binary) % 4))
            byte_offset = len(binary)
            binary.extend(b"".join(struct.pack("<3f", *normal) for normal in normals))
            document.setdefault("bufferViews", []).append(
                {"buffer": 0, "byteOffset": byte_offset, "byteLength": 12 * len(normals), "target": 34962}
            )
            document["accessors"].append(
                {"bufferView": len(document["bufferViews"]) - 1, "componentType": _FLOAT, "count": len(normals), "type": "VEC3"}
            )
            primitive["attributes"]["NORMAL"] = len(document["accessors"]) - 1

        # TRELLIS omet metallicFactor : la norme vaut alors 1 (métal), ce qui assombrit la texture.
        for material in implicit_metal:
            material["pbrMetallicRoughness"]["metallicFactor"] = 0.0

        materials_added = 0
        if needs_material:
            document.setdefault("materials", []).append(dict(PRODUCT_MATERIAL))
            material_index = len(document["materials"]) - 1
            for primitive in needs_material:
                primitive["material"] = material_index
            materials_added = 1

        if not buffers:
            document["buffers"] = [{}]
        document["buffers"][0]["byteLength"] = len(binary)
        return _write_glb(document, binary), FinishReport(
            changed=True, normals_added=len(needs_normals), materials_added=materials_added,
            metallic_fixed=len(implicit_metal),
        )
    except (_Unsupported, ValueError, KeyError, IndexError, TypeError, struct.error) as error:
        logger.info("Finition GLB ignorée : %s", error)
        return content, FinishReport(changed=False, reason=str(error))
