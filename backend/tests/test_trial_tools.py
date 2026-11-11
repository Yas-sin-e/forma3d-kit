# Rôle : vérifie les mesures automatiques de l'outil d'essai fournisseur (tools/trials/trial_trellis.py).
# Exécution : pytest ; aucun appel réseau, GLB minimal construit par les tests de finition.
"""Tests de measure_glb(), utilisée pour remplir la grille de docs/QUALITE-3D.md."""

import importlib.util
from pathlib import Path

from test_glb_finisher import _raw_triangle_glb

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "trials" / "trial_trellis.py"
_spec = importlib.util.spec_from_file_location("trial_trellis", _SCRIPT)
trial_trellis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trial_trellis)


def test_measure_glb_reports_grid_values_for_a_valid_glb() -> None:
    report = trial_trellis.measure_glb(_raw_triangle_glb())
    assert report["valid_glb2"] is True
    assert report["vertices"] == 3 and report["triangles"] == 1
    assert report["materials"] == 0 and report["textures"] == 0
    assert report["has_normals"] is False
    assert report["bbox_xyz"] == [1, 1, 0]


def test_measure_glb_stops_at_validity_for_invalid_content() -> None:
    assert trial_trellis.measure_glb(b"pas un glb") == {"bytes": 10, "valid_glb2": False}
