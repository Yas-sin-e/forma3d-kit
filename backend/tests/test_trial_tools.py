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
    """Prouve que l'outil d'essai mesure correctement un GLB valide."""
    report = trial_trellis.measure_glb(_raw_triangle_glb())
    assert report["valid_glb2"] is True
    assert report["vertices"] == 3 and report["triangles"] == 1
    assert report["materials"] == 0 and report["textures"] == 0
    assert report["has_normals"] is False
    assert report["bbox_xyz"] == [1, 1, 0]


def test_measure_glb_stops_at_validity_for_invalid_content() -> None:
    """Prouve que l'outil d'essai s'arrête à la validité pour un contenu invalide."""
    assert trial_trellis.measure_glb(b"pas un glb") == {"bytes": 10, "valid_glb2": False}


_MODELS_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "trials" / "trial_models.py"
_models_spec = importlib.util.spec_from_file_location("trial_models", _MODELS_SCRIPT)
trial_models = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(trial_models)


def test_file_path_from_output_accepts_gradio_shapes() -> None:
    """Prouve que l'outil d'essai comprend les formes de sortie Gradio."""
    assert trial_models.file_path_from_output("C:/tmp/a.glb") == "C:/tmp/a.glb"
    assert trial_models.file_path_from_output({"path": "/tmp/b.glb", "url": None}) == "/tmp/b.glb"
    assert trial_models.file_path_from_output({"value": "/tmp/c.glb"}) == "/tmp/c.glb"
    assert trial_models.file_path_from_output(None) is None
    assert trial_models.file_path_from_output("") is None
    assert trial_models.file_path_from_output({"path": None}) is None


def test_missing_functions_stops_when_contract_changes() -> None:
    """Prouve que l'outil d'essai s'arrête si des fonctions attendues manquent."""
    sf3d_contract = {"/requires_bg_remove", "/run_button", "/lambda"}
    assert trial_models.missing_functions("sf3d", sf3d_contract) == set()
    assert trial_models.missing_functions("trellis", {"/start_session"}) == {"/preprocess_image", "/generate_and_extract_glb"}
    assert set(trial_models.SPACES) == set(trial_models.REQUIRED_FUNCTIONS) == set(trial_models.RUNNERS)
