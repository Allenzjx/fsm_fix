from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from resume_validation.validation_selection import (
    build_validation_summary,
    select_seed_checkpoint,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_evidence(root: Path, controller: str, checkpoint: Path | None):
    scenarios = []
    for height in (50, 75, 100):
        for index in range(2):
            scenarios.append(
                {
                    "scenario_id": f"h{height:03d}-{index}",
                    "obstacle_height_m": height / 1000.0,
                }
            )
    manifest = root / "validation.json"
    _write_json(manifest, {"metadata": {"split": "validation"}, "scenarios": scenarios})
    evaluations = []
    for height in (50, 75, 100):
        rows = [
            {
                **scenario,
                "controller": controller,
                "success": scenario["scenario_id"].endswith("-0"),
                "failure_reason": (
                    "" if scenario["scenario_id"].endswith("-0") else "TIMEOUT"
                ),
                "min_longitudinal_support_margin_m": 0.01,
                "pitch_rate_rms_rad_s": 0.2,
                "wheel_slip_distance_m": 0.03,
                "residual_saturation_rate": 0.0,
                "terminal_fsm_baseline_ik_invalid_count": 0,
                "terminal_joint_limit_diagnostic": {},
            }
            for scenario in scenarios
            if round(scenario["obstacle_height_m"] * 1000) == height
        ]
        episodes = root / f"{controller}_{height}_episodes.jsonl"
        episodes.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        evaluation = root / f"{controller}_{height}_result.json"
        checkpoint_hash = _sha(checkpoint) if checkpoint else None
        _write_json(
            evaluation,
            {
                "passed_execution": True,
                "controller": controller,
                "height_mm": height,
                "provenance": {
                    "manifest_sha256": _sha(manifest),
                    "checkpoint_sha256": checkpoint_hash,
                },
                "aggregate": {"episode_count": 2, "success_count": 1},
                "artifacts": {
                    "episodes": str(episodes),
                    "episodes_sha256": _sha(episodes),
                },
            },
        )
        evaluations.append(evaluation)
    return manifest, evaluations


def test_summary_recomputes_complete_validation_artifacts(tmp_path: Path) -> None:
    checkpoint = tmp_path / "agent.pt"
    checkpoint.write_bytes(b"real checkpoint bytes")
    manifest, evaluations = _make_evidence(tmp_path, "B", checkpoint)
    result = build_validation_summary(
        controller="B",
        seed=11,
        checkpoint_path=checkpoint,
        evaluation_paths=evaluations,
        validation_manifest_path=manifest,
    )
    assert result["episode_count"] == 6
    assert result["selection_metrics"]["success_rate"] == pytest.approx(0.5)
    assert result["selection_metrics"]["slip_distance_m"] == pytest.approx(0.03)


def test_selection_uses_fsm_floor_and_discloses_fallback(tmp_path: Path) -> None:
    fsm = {
        "controller": "fsm",
        "validation_manifest": "validation.json",
        "validation_manifest_sha256": "manifest-hash",
        "selection_metrics": {"success_rate": 0.6},
    }
    candidate = {
        "controller": "C",
        "seed": 29,
        "validation_manifest_sha256": "manifest-hash",
        "checkpoint": str(tmp_path / "agent.pt"),
        "checkpoint_sha256": "checkpoint-hash",
        "selection_metrics": {
            "success_rate": 0.5,
            "mean_min_margin_m": 0.01,
            "pitch_rate_rms_rad_s": 0.2,
            "slip_distance_m": None,
            "saturation_rate": 0.0,
            "safety_violations": 0,
        },
    }
    result = select_seed_checkpoint(
        method="C",
        seed=29,
        fsm_summary=fsm,
        candidate_summaries=[candidate],
    )
    assert result["selection_status"] == "FALLBACK_BELOW_FSM_SUCCESS_FLOOR"
    assert not result["passed_validation_gate"]
