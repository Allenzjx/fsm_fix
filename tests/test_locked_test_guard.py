from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from resume_validation.locked_test_guard import (
    _load_evaluation,
    authorize_locked_test,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_locked_authorization_reads_manifest_only_after_valid_freeze(
    tmp_path: Path,
) -> None:
    immutable = tmp_path / "immutable.txt"
    immutable.write_text("frozen\n", encoding="utf-8")
    locked = tmp_path / "locked.json"
    locked.write_text('{"metadata": {}, "scenarios": []}\n', encoding="utf-8")
    locked.with_suffix(".json.sha256").write_text(
        f"{_sha(locked)}  {locked.name}\n",
        encoding="ascii",
    )
    freeze = tmp_path / "method_freeze.json"
    freeze.write_text(
        json.dumps(
            {
                "schema": "resume_validation.method_freeze.v1",
                "frozen": True,
                "locked_test_authorization": {
                    "manifest_registered_path": "locked.json",
                    "manifest_registered_sha256": _sha(locked),
                    "manifest_read_or_hashed_during_freeze": False,
                },
                "immutable_files": [
                    {
                        "role": "test",
                        "path": str(immutable),
                        "sha256": _sha(immutable),
                    }
                ],
                "selections": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = authorize_locked_test(
        freeze_path=freeze,
        project_root=tmp_path,
    )
    assert result["method_freeze_verified"]
    assert result["locked_manifest_sidecar_verified"]


def test_locked_authorization_refuses_drift_before_manifest_access(
    tmp_path: Path,
) -> None:
    immutable = tmp_path / "immutable.txt"
    immutable.write_text("changed\n", encoding="utf-8")
    freeze = tmp_path / "method_freeze.json"
    freeze.write_text(
        json.dumps(
            {
                "schema": "resume_validation.method_freeze.v1",
                "frozen": True,
                "locked_test_authorization": {
                    "manifest_registered_path": "must-not-be-read.json",
                    "manifest_registered_sha256": "0" * 64,
                    "manifest_read_or_hashed_during_freeze": False,
                },
                "immutable_files": [
                    {
                        "role": "test",
                        "path": str(immutable),
                        "sha256": "1" * 64,
                    }
                ],
                "selections": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="freeze verification failed"):
        authorize_locked_test(
            freeze_path=freeze,
            project_root=tmp_path,
        )


def test_locked_evaluation_audit_rejects_telemetry_hash_drift(
    tmp_path: Path,
) -> None:
    scenario_ids = {f"scenario-{index:03d}" for index in range(100)}
    episodes = tmp_path / "episodes.jsonl"
    episodes.write_text(
        "".join(
            json.dumps(
                {
                    "scenario_id": scenario_id,
                    "controller": "fsm",
                    "obstacle_height_m": 0.05,
                    "success": True,
                }
            )
            + "\n"
            for scenario_id in sorted(scenario_ids)
        ),
        encoding="utf-8",
    )
    telemetry = tmp_path / "telemetry.csv"
    telemetry.write_text("time_s\n0.0\n", encoding="utf-8")
    status = tmp_path / "status.json"
    status.write_text("{}\n", encoding="utf-8")
    result = tmp_path / "result.json"
    result.write_text(
        json.dumps(
            {
                "passed_execution": True,
                "controller": "fsm",
                "height_mm": 50,
                "provenance": {
                    "manifest_sha256": "a" * 64,
                    "checkpoint_sha256": None,
                },
                "aggregate": {
                    "episode_count": 100,
                    "success_count": 100,
                },
                "artifacts": {
                    "episodes": str(episodes),
                    "episodes_sha256": _sha(episodes),
                    "telemetry": str(telemetry),
                    "telemetry_sha256": "0" * 64,
                    "status": str(status),
                    "status_sha256": _sha(status),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="telemetry artifact hash mismatch"):
        _load_evaluation(
            result_path=result,
            controller="fsm",
            height=50,
            expected_ids=scenario_ids,
            manifest_hash="a" * 64,
            checkpoint_hash=None,
        )

    telemetry.write_text(
        "time_s,env_id,base_x_m,pitch_rad,pitch_rate_rad_s,"
        "margin_m,fsm_phase\n"
        + "".join(
            f"0.0,{env_id},0.0,0.0,0.0,0.0,0\n"
            for env_id in range(100)
        ),
        encoding="utf-8",
    )
    status.write_text(
        json.dumps(
            {
                "schema": "resume_validation.controller_status.v1",
                "active_count": 0,
                "completed_count": 100,
                "success_count": 100,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = json.loads(result.read_text(encoding="utf-8"))
    payload["artifacts"]["telemetry_sha256"] = _sha(telemetry)
    payload["artifacts"]["status_sha256"] = _sha(status)
    result.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    expected_scenarios = {
        scenario_id: {
            "scenario_id": scenario_id,
            "obstacle_height_m": 0.05,
        }
        for scenario_id in scenario_ids
    }
    _, rows, _ = _load_evaluation(
        result_path=result,
        controller="fsm",
        height=50,
        expected_ids=scenario_ids,
        manifest_hash="a" * 64,
        checkpoint_hash=None,
        expected_scenarios=expected_scenarios,
    )
    assert len(rows) == 100

    expected_scenarios["scenario-000"]["friction"] = 1.0
    with pytest.raises(ValueError, match="scenario parameter mismatch"):
        _load_evaluation(
            result_path=result,
            controller="fsm",
            height=50,
            expected_ids=scenario_ids,
            manifest_hash="a" * 64,
            checkpoint_hash=None,
            expected_scenarios=expected_scenarios,
        )
