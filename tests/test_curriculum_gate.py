"""Unit tests for the pre-registered PPO curriculum promotion gate."""

from __future__ import annotations

from pathlib import Path

from resume_validation.config_io import load_config
from resume_validation.curriculum_gate import decide_curriculum_gate


COMMON_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "ppo_common.yaml"


def _evaluation(success_rate: float, episode_count: int = 20) -> dict:
    return {
        "passed_execution": True,
        "controller": "B",
        "height_mm": 50,
        "aggregate": {
            "episode_count": episode_count,
            "success_rate": success_rate,
        },
        "provenance": {"checkpoint_sha256": "abc"},
    }


def test_curriculum_gate_promotes_only_at_registered_threshold() -> None:
    common = load_config(COMMON_CONFIG)
    passing = decide_curriculum_gate(
        _evaluation(0.80),
        common,
        method="B",
        seed=11,
        height_mm=50,
        checkpoint_sha256="abc",
    )
    failing = decide_curriculum_gate(
        _evaluation(0.75),
        common,
        method="B",
        seed=11,
        height_mm=50,
        checkpoint_sha256="abc",
    )
    assert passing["promote"] is True
    assert failing["promote"] is False
    assert failing["checks"]["success_rate_sufficient"] is False


def test_curriculum_gate_rejects_incomplete_or_mismatched_evidence() -> None:
    common = load_config(COMMON_CONFIG)
    decision = decide_curriculum_gate(
        _evaluation(1.0, episode_count=19),
        common,
        method="C",
        seed=29,
        height_mm=50,
        checkpoint_sha256="different",
    )
    assert decision["promote"] is False
    assert decision["checks"]["controller_matches"] is False
    assert decision["checks"]["episode_count_sufficient"] is False
    assert decision["checks"]["checkpoint_hash_matches"] is False
