"""Static regressions for the Isaac-only training entrypoint."""

from __future__ import annotations

import ast
from pathlib import Path


TRAINING_ENTRYPOINT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "resume_validation"
    / "train_residual_ppo.py"
)


def test_action_dimension_is_imported_before_zero_action_preflight() -> None:
    tree = ast.parse(TRAINING_ENTRYPOINT.read_text(encoding="utf-8"))
    imported_names = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    loaded_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    assert "ACTION_DIM" in loaded_names
    assert "ACTION_DIM" in imported_names


def test_training_threshold_validation_imports_math() -> None:
    tree = ast.parse(TRAINING_ENTRYPOINT.read_text(encoding="utf-8"))
    imported_modules = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    math_attribute_loads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "math"
    ]
    assert math_attribute_loads
    assert "math" in imported_modules


def test_training_uses_local_display_tracker_repair() -> None:
    source = TRAINING_ENTRYPOINT.read_text(encoding="utf-8")
    assert "class AuditablePPO(PPO):" in source
    assert "super().record_transition(**kwargs)" in source
    assert "advance_episode_accumulators(" in source
    assert "agent = AuditablePPO(" in source
