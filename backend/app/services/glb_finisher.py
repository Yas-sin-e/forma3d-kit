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

# Les annotations de type restent du texte.
from __future__ import annotations

# json : lit et réécrit le document JSON du GLB.
import json
# logging : journal du serveur.
import logging
# math : racine carrée pour normaliser les vecteurs.
import math
# struct (standard) : lit et écrit des nombres binaires (« <II » = deux entiers 32 bits, « <3f » = trois décimaux).
# Indispensable ici car un GLB est un fichier binaire. Équivalent de ByteBuffer en Java.
import struct
# Classe de données immuable pour le rapport.
from dataclasses import dataclass

# Journal de ce module.
logger = logging.getLogger(__name__)

# Les 4 premiers octets de tout GLB.
_GLB_MAGIC = b"glTF"
# Code du type de bloc « JSON ».
_JSON_CHUNK = 0x4E4F534A
# Code du type de bloc « BIN » (données binaires).
_BIN_CHUNK = 0x004E4942
# Code glTF du type « nombre décimal 32 bits ».
_FLOAT = 5126
# Codes glTF des types d'indices -> format struct (octet, entier 16 bits, entier 32 bits).
_INDEX_FORMATS = {5121: "B", 5123: "H", 5125: "I"}
# Code glTF du mode « triangles ».
_TRIANGLES = 4
# Matériau ajouté aux modèles qui n'en ont pas...
PRODUCT_MATERIAL = {
    # ...son nom...
    "name": "forma3d-product",
    # ...blanc, non métallique, plutôt mat.
    "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.8},
}


# Décorateur : rapport immuable.
@dataclass(frozen=True, slots=True)
# Rapport de la finition.
class FinishReport:
    """Résumé de la finition, utile aux journaux et aux tests."""

    # Vrai si le fichier a été modifié.
    changed: bool
    # Nombre de primitives qui ont reçu des normales.
    normals_added: int = 0
    # Nombre de matériaux ajoutés.
    materials_added: int = 0
    # Nombre de matériaux dont le facteur métallique a été corrigé.
    metallic_fixed: int = 0
    # Raison d'une absence de changement.
    reason: str = ""


# Erreur interne : structure non gérée, le fichier sera rendu tel quel.
class _Unsupported(Exception):
    """Structure GLB hors du cas simple géré : on rend le fichier tel quel."""


# Découpe un GLB en JSON et binaire.
def _read_glb(content: bytes) -> tuple[dict, bytearray]:
    """Découpe un GLB en (document JSON, données binaires).

    Lit l'en-tête de 12 octets puis chaque bloc (« chunk ») : longueur, type, contenu.
    Lève _Unsupported si la structure n'est pas un GLB 2.0 simple.
    """
    # Trop court ou sans « glTF » au début...
    if len(content) < 20 or content[:4] != _GLB_MAGIC:
        # ...structure non gérée.
        raise _Unsupported("en-tête GLB absent")
    # Lit la version et la longueur totale (deux entiers 32 bits little-endian à partir de l'octet 4).
    version, total_length = struct.unpack_from("<II", content, 4)
    # Version différente de 2 ou longueur incorrecte...
    if version != 2 or total_length != len(content):
        # ...structure non gérée.
        raise _Unsupported("version ou longueur GLB inattendue")
    # Les blocs commencent après l'en-tête de 12 octets.
    offset = 12
    # Document JSON (pas encore lu).
    document: dict | None = None
    # Données binaires (vides pour l'instant).
    binary = bytearray()
    # Tant qu'il reste au moins un en-tête de bloc...
    while offset + 8 <= len(content):
        # ...lit la longueur et le type du bloc...
        chunk_length, chunk_type = struct.unpack_from("<II", content, offset)
        # ...extrait son contenu...
        chunk = content[offset + 8 : offset + 8 + chunk_length]
        # ...premier bloc JSON...
        if chunk_type == _JSON_CHUNK and document is None:
            # ...on le décode.
            document = json.loads(chunk.decode("utf-8"))
        # Premier bloc binaire...
        elif chunk_type == _BIN_CHUNK and not binary:
            # ...on le copie dans un tableau modifiable.
            binary = bytearray(chunk)
        # Passe au bloc suivant.
        offset += 8 + chunk_length
    # Aucun bloc JSON...
    if document is None:
        # ...structure non gérée.
        raise _Unsupported("bloc JSON absent")
    # Renvoie le document et le binaire.
    return document, binary


# Reconstruit un fichier GLB.
def _write_glb(document: dict, binary: bytearray) -> bytes:
    """Reconstruit un fichier GLB à partir du document JSON et du binaire.

    Chaque bloc est complété pour que sa taille soit un multiple de 4 octets (règle du format).
    """
    # Sérialise le JSON de façon compacte en UTF-8.
    json_bytes = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    # Complète le JSON avec des espaces jusqu'à un multiple de 4 octets.
    json_bytes += b" " * (-len(json_bytes) % 4)
    # Complète le binaire avec des zéros jusqu'à un multiple de 4 octets.
    binary = bytes(binary) + b"\x00" * (-len(binary) % 4)
    # Taille totale : en-tête + bloc JSON + bloc binaire éventuel.
    total = 12 + 8 + len(json_bytes) + (8 + len(binary) if binary else 0)
    # Morceaux du fichier : « glTF », version et taille, en-tête JSON, JSON.
    parts = [_GLB_MAGIC, struct.pack("<II", 2, total), struct.pack("<II", len(json_bytes), _JSON_CHUNK), json_bytes]
    # S'il y a des données binaires...
    if binary:
        # ...on ajoute l'en-tête BIN et les données.
        parts += [struct.pack("<II", len(binary), _BIN_CHUNK), binary]
    # Assemble tous les morceaux.
    return b"".join(parts)


# Localise les données d'un accesseur dans le binaire.
def _accessor_view(document: dict, binary: bytearray, accessor_index: int) -> tuple[dict, int, int]:
    """Renvoie (accesseur, début dans le BIN, pas entre éléments) pour un accesseur non creux."""
    # Lit l'accesseur demandé.
    accessor = document["accessors"][accessor_index]
    # Accesseur creux ou sans vue...
    if "sparse" in accessor or "bufferView" not in accessor:
        # ...structure non gérée.
        raise _Unsupported("accesseur creux ou sans bufferView")
    # Lit la vue (tranche du binaire) de l'accesseur.
    view = document["bufferViews"][accessor["bufferView"]]
    # Les données sont dans un autre buffer que le premier...
    if view.get("buffer", 0) != 0:
        # ...structure non gérée.
        raise _Unsupported("plusieurs buffers")
    # Position de départ : décalage de la vue + décalage de l'accesseur.
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    # Renvoie l'accesseur, le départ et le pas (0 = éléments collés).
    return accessor, start, view.get("byteStride", 0)


# Lit les positions des sommets.
def _read_positions(document: dict, binary: bytearray, accessor_index: int) -> list[tuple[float, float, float]]:
    """Lit la liste des sommets (x, y, z) décrite par un accesseur glTF.

    Lève _Unsupported si ce ne sont pas des triplets de décimaux ou si les données dépassent le binaire.
    """
    # Localise les données.
    accessor, start, stride = _accessor_view(document, binary, accessor_index)
    # Pas des triplets de décimaux 32 bits...
    if accessor.get("componentType") != _FLOAT or accessor.get("type") != "VEC3":
        # ...structure non gérée.
        raise _Unsupported("positions non float VEC3")
    # Pas par défaut : 12 octets (3 décimaux de 4 octets).
    stride = stride or 12
    # Nombre de sommets.
    count = accessor["count"]
    # Le dernier sommet dépasserait la fin du binaire...
    if start + stride * (count - 1) + 12 > len(binary):
        # ...structure non gérée.
        raise _Unsupported("positions hors du BIN")
    # Lit chaque sommet (x, y, z).
    return [struct.unpack_from("<3f", binary, start + i * stride) for i in range(count)]


# Lit les indices des triangles.
def _read_indices(document: dict, binary: bytearray, primitive: dict, vertex_count: int) -> list[int]:
    """Lit la liste des indices de triangles ; sans indices, les sommets sont pris dans l'ordre (0, 1, 2…)."""
    # Pas d'indices...
    if "indices" not in primitive:
        # ...les sommets sont pris dans l'ordre.
        return list(range(vertex_count))
    # Localise les données des indices.
    accessor, start, stride = _accessor_view(document, binary, primitive["indices"])
    # Format struct correspondant au type d'indice.
    fmt = _INDEX_FORMATS.get(accessor.get("componentType"))
    # Type inconnu ou pas des valeurs simples...
    if fmt is None or accessor.get("type") != "SCALAR":
        # ...structure non gérée.
        raise _Unsupported("indices de type inattendu")
    # Taille d'un indice en octets.
    size = struct.calcsize(fmt)
    # Nombre d'indices.
    count = accessor["count"]
    # Indices collés les uns aux autres...
    if stride in (0, size):
        # ...dépassement du binaire...
        if start + size * count > len(binary):
            # ...structure non gérée.
            raise _Unsupported("indices hors du BIN")
        # Lit tous les indices d'un coup.
        return list(struct.unpack_from(f"<{count}{fmt}", binary, start))
    # Sinon lit chaque indice en tenant compte du pas.
    return [struct.unpack_from(f"<{fmt}", binary, start + i * stride)[0] for i in range(count)]


# Calcule une normale lissée par sommet.
def compute_vertex_normals(positions: list[tuple[float, float, float]], indices: list[int]) -> list[tuple[float, float, float]]:
    """Moyenne des normales des triangles adjacents, pondérée par leur aire (produit vectoriel brut)."""
    # Somme des normales pour chaque sommet (au départ : zéro).
    sums = [[0.0, 0.0, 0.0] for _ in positions]
    # Nombre de sommets.
    vertex_count = len(positions)
    # Parcourt les indices trois par trois (un triangle)...
    for i in range(0, len(indices) - 2, 3):
        # ...les trois sommets du triangle...
        a, b, c = indices[i], indices[i + 1], indices[i + 2]
        # ...un indice hors limites...
        if a >= vertex_count or b >= vertex_count or c >= vertex_count:
            # ...structure non gérée.
            raise _Unsupported("indice hors des sommets")
        # Coordonnées du sommet a.
        ax, ay, az = positions[a]
        # Coordonnées du sommet b.
        bx, by, bz = positions[b]
        # Coordonnées du sommet c.
        cx, cy, cz = positions[c]
        # Vecteur du côté a -> b.
        ux, uy, uz = bx - ax, by - ay, bz - az
        # Vecteur du côté a -> c.
        vx, vy, vz = cx - ax, cy - ay, cz - az
        # Produit vectoriel de deux côtés du triangle : un vecteur perpendiculaire à sa surface,
        # dont la longueur est proportionnelle à l'aire (les grands triangles pèsent donc plus).
        # Produit vectoriel des deux côtés.
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        # Pour chacun des trois sommets...
        for vertex in (a, b, c):
            # ...sa somme courante...
            total = sums[vertex]
            # ...ajoute la composante x...
            total[0] += nx
            # ...la composante y...
            total[1] += ny
            # ...la composante z.
            total[2] += nz
    # Liste des normales finales.
    normals = []
    # Pour chaque somme...
    for x, y, z in sums:
        # ...sa longueur...
        length = math.sqrt(x * x + y * y + z * z)
        # Sommet isolé ou dégénéré : normale arbitraire vers le haut, pour rester un vecteur unitaire valide.
        # ...normale de longueur 1 (ou vers le haut si la somme est nulle).
        normals.append((x / length, y / length, z / length) if length > 1e-12 else (0.0, 1.0, 0.0))
    # Renvoie les normales.
    return normals


# Fonction publique appelée par GenerationService.
def finish_glb(content: bytes) -> tuple[bytes, FinishReport]:
    """Ajoute matériau et normales manquants ; renvoie (octets, rapport). Ne lève jamais d'exception."""
    # Essaie la finition...
    try:
        # ...découpe le GLB...
        document, binary = _read_glb(content)
        # ...liste des buffers...
        buffers = document.get("buffers", [])
        # Plusieurs buffers ou un buffer dans un fichier externe...
        if len(buffers) > 1 or (buffers and "uri" in buffers[0]):
            # ...structure non gérée.
            raise _Unsupported("buffer externe")
        # Toutes les primitives de tous les maillages.
        primitives = [p for mesh in document.get("meshes", []) for p in mesh.get("primitives", [])]
        # Primitives sans normales.
        needs_normals = [p for p in primitives if "NORMAL" not in p.get("attributes", {})]
        # Primitives sans matériau.
        needs_material = [p for p in primitives if "material" not in p]
        # Matériaux sans facteur métallique explicite (donc métalliques selon la norme)...
        implicit_metal = [
            # ...parmi tous les matériaux...
            m for m in document.get("materials", [])
            # ...qui ont un bloc PBR...
            if isinstance(m.get("pbrMetallicRoughness"), dict)
            # ...sans metallicFactor...
            and "metallicFactor" not in m["pbrMetallicRoughness"]
            # ...et sans texture métallique.
            and "metallicRoughnessTexture" not in m["pbrMetallicRoughness"]
        ]
        # Rien à compléter...
        if not needs_normals and not needs_material and not implicit_metal:
            # ...on rend le fichier tel quel.
            return content, FinishReport(changed=False, reason="déjà complet")
        # Une primitive à compléter n'est pas faite de triangles...
        if any(p.get("mode", _TRIANGLES) != _TRIANGLES for p in needs_normals):
            # ...structure non gérée.
            raise _Unsupported("primitive autre que triangles")

        # Pour chaque primitive sans normales...
        for primitive in needs_normals:
            # ...lit ses positions...
            positions = _read_positions(document, binary, primitive["attributes"]["POSITION"])
            # ...lit ses indices...
            indices = _read_indices(document, binary, primitive, len(positions))
            # ...calcule les normales...
            normals = compute_vertex_normals(positions, indices)
            # ...aligne le binaire sur 4 octets...
            binary.extend(b"\x00" * (-len(binary) % 4))
            # ...position où commencent les normales...
            byte_offset = len(binary)
            # ...ajoute les normales au binaire...
            binary.extend(b"".join(struct.pack("<3f", *normal) for normal in normals))
            # ...déclare une nouvelle vue sur ces octets...
            document.setdefault("bufferViews", []).append(
                {"buffer": 0, "byteOffset": byte_offset, "byteLength": 12 * len(normals), "target": 34962}
            )
            # ...déclare un nouvel accesseur qui lit cette vue...
            document["accessors"].append(
                {"bufferView": len(document["bufferViews"]) - 1, "componentType": _FLOAT, "count": len(normals), "type": "VEC3"}
            )
            # ...et branche les normales sur la primitive.
            primitive["attributes"]["NORMAL"] = len(document["accessors"]) - 1

        # TRELLIS omet metallicFactor : la norme vaut alors 1 (métal), ce qui assombrit la texture.
        # Pour chaque matériau implicitement métallique...
        for material in implicit_metal:
            # ...on le rend non métallique.
            material["pbrMetallicRoughness"]["metallicFactor"] = 0.0

        # Nombre de matériaux ajoutés.
        materials_added = 0
        # S'il y a des primitives sans matériau...
        if needs_material:
            # ...ajoute le matériau produit...
            document.setdefault("materials", []).append(dict(PRODUCT_MATERIAL))
            # ...son index...
            material_index = len(document["materials"]) - 1
            # ...pour chaque primitive concernée...
            for primitive in needs_material:
                # ...on lui attribue ce matériau.
                primitive["material"] = material_index
            # Un matériau a été ajouté.
            materials_added = 1

        # Pas de buffer déclaré...
        if not buffers:
            # ...on en crée un.
            document["buffers"] = [{}]
        # Met à jour la taille du binaire.
        document["buffers"][0]["byteLength"] = len(binary)
        # Reconstruit le fichier et renvoie le rapport.
        return _write_glb(document, binary), FinishReport(
            changed=True, normals_added=len(needs_normals), materials_added=materials_added,
            metallic_fixed=len(implicit_metal),
        )
    # Structure inattendue...
    except (_Unsupported, ValueError, KeyError, IndexError, TypeError, struct.error) as error:
        # ...on le note dans le journal...
        logger.info("Finition GLB ignorée : %s", error)
        # ...et on rend le fichier d'origine.
        return content, FinishReport(changed=False, reason=str(error))
