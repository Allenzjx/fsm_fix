from __future__ import annotations

import hashlib
import json
from pathlib import Path

from resume_validation.method_freeze import (
    _prevalidation_video_smoke,
    verify_method_freeze,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_method_freeze_verifier_detects_immutable_drift(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    freeze = {
        "schema": "resume_validation.method_freeze.v1",
        "frozen": True,
        "locked_test_authorization": {
            "manifest_read_or_hashed_during_freeze": False,
        },
        "immutable_files": [
            {
                "role": "test",
                "path": str(evidence),
                "sha256": _sha(evidence),
            }
        ],
        "selections": [],
    }
    assert verify_method_freeze(freeze) == []
    evidence.write_text('{"changed": true}\n', encoding="utf-8")
    failures = verify_method_freeze(freeze)
    assert any("immutable hash mismatch" in failure for failure in failures)


def test_method_freeze_verifier_requires_preaccess_isolation(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    freeze = {
        "schema": "resume_validation.method_freeze.v1",
        "frozen": True,
        "locked_test_authorization": {
            "manifest_read_or_hashed_during_freeze": True,
        },
        "immutable_files": [
            {
                "role": "test",
                "path": str(evidence),
                "sha256": _sha(evidence),
            }
        ],
        "selections": [],
    }
    assert "freeze does not attest pre-access locked isolation" in verify_method_freeze(
        freeze
    )


def test_prevalidation_video_smoke_hash_chain_is_frozen(tmp_path: Path) -> None:
    def write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    script = tmp_path / "scripts" / "prevalidation_video_smoke.ps1"
    write(script, "Write-Output 'smoke'\n")
    manifest = (
        tmp_path / "data" / "scenario_manifests" / "development_v2.json"
    )
    write(manifest, '{"metadata": {}, "scenarios": []}\n')
    attempt = (
        tmp_path
        / "runs"
        / "diagnostics"
        / "prevalidation_video_smoke_attempt001"
    )
    episodes = attempt / "episodes.jsonl"
    write(
        episodes,
        json.dumps(
            {
                "scenario_id": "development-h050-0000",
                "success": True,
            }
        )
        + "\n",
    )
    telemetry = attempt / "telemetry.csv"
    write(telemetry, "time_s\n0.0\n")
    status = attempt / "status.json"
    write(status, "{}\n")
    video = attempt / "replay.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"encoded-video-bytes")
    probe = attempt / "video_probe.json"
    write(
        probe,
        json.dumps(
            {
                "schema": "resume_validation.video_decode_probe.v1",
                "decoded": True,
                "video": str(video),
                "video_sha256": _sha(video),
                "width": 960,
                "height": 540,
                "fps": 20.0,
                "codec": "h264",
                "decoded_frame_count": 5,
            }
        )
        + "\n",
    )
    asset = tmp_path / "assets" / "robot.usd"
    write(asset, "usd-bytes\n")
    metrics = tmp_path / "configs" / "metrics.yaml"
    common = tmp_path / "configs" / "ppo_common.yaml"
    method = tmp_path / "configs" / "ppo_without_com.yaml"
    write(metrics, "frozen: true\n")
    write(common, "method: common\n")
    write(method, "method: B\n")
    evaluator = tmp_path / "src" / "resume_validation" / "evaluate_controller.py"
    write(evaluator, "# evaluator\n")
    result = {
        "passed_execution": True,
        "controller": "fsm",
        "height_mm": 50,
        "provenance": {
            "manifest_sha256": _sha(manifest),
            "asset_path": str(asset),
            "asset_sha256": _sha(asset),
            "metrics_config": str(metrics),
            "metrics_config_sha256": _sha(metrics),
            "ppo_common_config": str(common),
            "ppo_common_config_sha256": _sha(common),
            "method_config": str(method),
            "method_config_sha256": _sha(method),
            "source_files": {
                "evaluate_controller.py": {
                    "path": str(evaluator),
                    "sha256": _sha(evaluator),
                }
            },
        },
        "video_replay": {
            "scenario_id": "development-h050-0000",
            "frame_count": 5,
        },
        "artifacts": {
            "episodes": str(episodes),
            "episodes_sha256": _sha(episodes),
            "telemetry": str(telemetry),
            "telemetry_sha256": _sha(telemetry),
            "status": str(status),
            "status_sha256": _sha(status),
            "video": str(video),
            "video_sha256": _sha(video),
        },
    }
    write(attempt / "result.json", json.dumps(result) + "\n")
    selected, records = _prevalidation_video_smoke(tmp_path)
    assert selected["scenario_id"] == "development-h050-0000"
    assert selected["frame_count"] == 5
    assert {record["role"] for record in records} >= {
        "prevalidation_video_smoke_script",
        "prevalidation_video_smoke_result",
        "prevalidation_video_smoke_video",
        "prevalidation_video_smoke_decode_probe",
    }
