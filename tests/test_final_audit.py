from __future__ import annotations

import csv
import json
from pathlib import Path

from resume_validation import final_audit
from resume_validation.source_audit import sha256_file


def _json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_final_audit_binds_video_selection_and_inventory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "project"
    reports = project / "reports"
    tables = reports / "tables"
    plots = reports / "plots"
    reports.mkdir(parents=True)
    tables.mkdir()
    plots.mkdir()

    freeze = project / "configs" / "method_freeze.json"
    _json(freeze, {"schema": "test"})
    freeze_hash = sha256_file(freeze)
    monkeypatch.setattr(final_audit, "verify_method_freeze", lambda payload: [])

    evidence = project / "locked" / "evidence.json"
    _json(evidence, {"passed": True})
    fresh_audit = {
        "method_freeze_sha256": freeze_hash,
        "locked_manifest_sha256": "locked-hash",
        "evaluation_count": 21,
        "episode_count": 2100,
        "paired_scenario_coverage_complete": True,
        "evidence": [
            {"path": str(evidence), "sha256": sha256_file(evidence)}
        ],
    }
    monkeypatch.setattr(
        final_audit,
        "audit_locked_campaign",
        lambda **kwargs: fresh_audit,
    )
    monkeypatch.setattr(
        final_audit,
        "_recompute_numeric_evidence",
        lambda project_root, locked_run_root: {},
    )
    recorded_audit = project / "locked" / "paired_coverage_audit.json"
    _json(recorded_audit, fresh_audit)

    authorization = project / "locked" / "authorization.json"
    locked_root = project / "locked"
    _json(authorization, {"authorized": True})
    unit_xml = reports / "unit_test_results.xml"
    unit_xml.write_text(
        '<testsuites tests="185" failures="0" errors="0"/>',
        encoding="utf-8",
    )
    report_source = project / "src" / "resume_validation" / "report_generator.py"
    report_source.parent.mkdir(parents=True)
    report_source.write_text("# frozen report generator\n", encoding="utf-8")

    checkpoint = project / "checkpoints" / "agent.pt"
    checkpoint.parent.mkdir()
    checkpoint.write_bytes(b"checkpoint")
    locked_result = project / "locked" / "result.json"
    locked_episodes = project / "locked" / "episodes.jsonl"
    replay_result = project / "videos" / "replay-result.json"
    video = project / "videos" / "replay.mp4"
    _json(locked_result, {"passed_execution": True})
    locked_episodes.write_text('{"success": true}\n', encoding="utf-8")
    _json(replay_result, {"passed_execution": True})
    video.write_bytes(b"real-video-evidence")

    requirements = []
    selections = []
    inventory_rows = []
    for method in ("fsm", "B", "C"):
        for height in (50, 75, 100):
            categories = [
                "highest_pitch_rate",
                "typical_failure",
                "typical_success",
                "worst_margin",
            ]
            requirements.append(
                {
                    "method": method,
                    "height_mm": height,
                    "required_categories": categories,
                }
            )
            selected = {
                "method": method,
                "height_mm": height,
                "training_seed": None if method == "fsm" else 11,
                "scenario_id": f"{method}-{height}",
                "locked_success": True,
                "categories": categories,
                "locked_result": str(locked_result),
                "locked_result_sha256": sha256_file(locked_result),
                "locked_episodes": str(locked_episodes),
                "locked_episodes_sha256": sha256_file(locked_episodes),
                "checkpoint": None if method == "fsm" else str(checkpoint),
                "checkpoint_sha256": (
                    None if method == "fsm" else sha256_file(checkpoint)
                ),
            }
            selections.append(selected)
            inventory_rows.append(
                {
                    **selected,
                    "replay_result": str(replay_result),
                    "replay_result_sha256": sha256_file(replay_result),
                    "video": str(video),
                    "video_sha256": sha256_file(video),
                    "video_frame_count": 10,
                    "video_decode_probe": {
                        "decoded": True,
                        "width": 960,
                        "height": 540,
                        "fps": 20.0,
                        "codec": "h264",
                        "decoded_frame_count": 10,
                    },
                }
            )

    selection_path = project / "videos" / "video_selection.json"
    _json(
        selection_path,
        {
            "schema": "resume_validation.video_selection.v1",
            "method_freeze_sha256": freeze_hash,
            "locked_manifest_sha256": "locked-hash",
            "locked_episode_count_considered": 2100,
            "group_category_requirements": requirements,
            "selections": selections,
        },
    )
    inventory_path = project / "videos" / "video_inventory.json"
    _json(
        inventory_path,
        {
            "schema": "resume_validation.video_inventory.v1",
            "selection": str(selection_path),
            "selection_sha256": sha256_file(selection_path),
            "video_count": len(inventory_rows),
            "all_replay_outcomes_reproduced": True,
            "videos": inventory_rows,
        },
    )

    for name in (
        "locked_test_report.md",
        "failure_analysis.md",
    ):
        (reports / name).write_text("audited\n", encoding="utf-8")
    (reports / "claims_audit.md").write_text(
        "claim: **VERIFIED**\n",
        encoding="utf-8",
    )
    (reports / "final_resume_wording_zh.md").write_text(
        "点估计；纵向准静态\n",
        encoding="utf-8",
    )
    metrics = {
        "method_freeze_sha256": freeze_hash,
        "locked_test_manifest_sha256": "locked-hash",
        "unit_test_audit": {
            "path": str(unit_xml),
            "sha256": sha256_file(unit_xml),
            "tests": 185,
            "failures": 0,
            "errors": 0,
        },
        "report_generator_sha256": sha256_file(report_source),
        "video_evidence": {
            "inventory": str(inventory_path),
            "inventory_sha256": sha256_file(inventory_path),
            "video_count": len(inventory_rows),
            "all_replay_outcomes_reproduced": True,
        },
        "methods": {
            "fsm": {"episode_count": 300},
            "residual_ppo_without_com": {"episode_count": 900},
            "residual_ppo_with_com": {"episode_count": 900},
        },
        "claims": {"test_claim": "VERIFIED"},
        "selection_disclosure": [],
        "technical_claims_verified": True,
        "technical_freeze_coverage": {"verified": True},
    }
    _json(reports / "resume_metrics.json", metrics)

    scenario_rows = []
    for method, seeds in (
        ("fsm", ("",)),
        ("residual_ppo_without_com", (11, 29, 47)),
        ("residual_ppo_with_com", (11, 29, 47)),
    ):
        for seed in seeds:
            for height in (50, 75, 100):
                for index in range(100):
                    scenario_rows.append(
                        {
                            "method": method,
                            "training_seed": seed,
                            "height_mm": height,
                            "scenario_id": f"h{height}-{index}",
                        }
                    )
    _csv(
        tables / "scenario_results.csv",
        ["method", "training_seed", "height_mm", "scenario_id"],
        scenario_rows,
    )
    for name, count in (
        ("method_comparison.csv", 3),
        ("per_height_comparison.csv", 9),
        ("per_seed_results.csv", 7),
        ("paired_differences.csv", 18),
        ("failure_reasons.csv", 1),
    ):
        _csv(
            tables / name,
            ["row"],
            [{"row": index} for index in range(count)],
        )
    for name in final_audit.REQUIRED_PLOTS:
        (plots / name).write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 1024)

    ledger_artifact = project / "ledger-artifact.txt"
    ledger_artifact.write_text("evidence", encoding="utf-8")
    _csv(
        project / "experiment_ledger.csv",
        [
            "timestamp_utc",
            "experiment_id",
            "parent_experiment_id",
            "stage",
            "method",
            "seed",
            "hypothesis",
            "changed_parameters",
            "unchanged_controls",
            "expected_effect",
            "actual_effect",
            "result",
            "next_action",
            "artifact_path",
        ],
        [
            {
                "timestamp_utc": "2026-07-30T00:00:00Z",
                "experiment_id": "audit",
                "parent_experiment_id": "root",
                "stage": "FINAL",
                "method": "all",
                "seed": 0,
                "hypothesis": "hash chain is complete",
                "changed_parameters": "none",
                "unchanged_controls": "all",
                "expected_effect": "pass",
                "actual_effect": "pass",
                "result": "PASS",
                "next_action": "publish",
                "artifact_path": str(ledger_artifact),
            }
        ],
    )

    kwargs = {
        "project_root": project,
        "freeze_path": freeze,
        "authorization_path": authorization,
        "locked_run_root": locked_root,
        "recorded_audit_path": recorded_audit,
        "video_inventory_path": inventory_path,
        "reports_root": reports,
    }
    assert final_audit.run_final_audit(**kwargs)["status"] == "PASS"

    monkeypatch.setattr(
        final_audit,
        "_recompute_numeric_evidence",
        lambda project_root, locked_run_root: {
            "claims": {"test_claim": "NOT_VERIFIED"}
        },
    )
    numeric_drift = final_audit.run_final_audit(**kwargs)
    assert numeric_drift["status"] == "FAILED"
    assert any(
        "raw recomputation mismatch: claims" in item
        for item in numeric_drift["failures"]
    )
    monkeypatch.setattr(
        final_audit,
        "_recompute_numeric_evidence",
        lambda project_root, locked_run_root: {},
    )
    selection_path.write_text("{}", encoding="utf-8")
    drifted = final_audit.run_final_audit(**kwargs)
    assert drifted["status"] == "FAILED"
    assert any("video selection evidence" in item for item in drifted["failures"])
