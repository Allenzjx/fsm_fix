"""Create and verify the post-validation, pre-locked-test method freeze.

The create operation intentionally does not open, parse, stat, or hash the
locked-test manifest. It records only the path and SHA256 already registered
in ``experiment_protocol.yaml``. The locked-test runner may access that path
only after this independent freeze verification succeeds.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .config_io import differing_leaf_paths, load_config, write_json
from .source_audit import sha256_file
from .validation_selection import (
    build_validation_summary,
    select_seed_checkpoint,
)

METHOD_FOLDERS = {"B": "ppo_without_com", "C": "ppo_with_com"}
SEEDS = (11, 29, 47)
HEIGHTS = (50, 75, 100)
CRITICAL_CONFIGS = (
    "robot.yaml",
    "actuator_limits.yaml",
    "environment.yaml",
    "fsm.yaml",
    "metrics.yaml",
    "ppo_common.yaml",
    "ppo_without_com.yaml",
    "ppo_with_com.yaml",
    "obstacle_train.yaml",
    "obstacle_validation.yaml",
    "obstacle_locked_test.yaml",
    "telemetry.yaml",
    "telemetry_contact.yaml",
    "validation_selection_protocol.json",
    "claims_audit_protocol.json",
    "video_selection_protocol.json",
)
CRITICAL_SOURCES = tuple(
    path.name
    for path in sorted(
        Path(__file__).resolve().parent.glob("*.py"),
        key=lambda path: path.name.lower(),
    )
)
CRITICAL_SCRIPTS = (
    "05_train_B.ps1",
    "06_train_C.ps1",
    "07_run_validation.ps1",
    "08_freeze_methods.ps1",
    "09_run_locked_test.ps1",
    "10_generate_videos.ps1",
    "11_generate_report.ps1",
    "12_final_audit.ps1",
    "train_curriculum.ps1",
    "prevalidation_video_smoke.ps1",
    "run_until_success.ps1",
    "full_pipeline_supervisor.ps1",
    "pipeline_keep_awake.ps1",
)
CRITICAL_EVIDENCE = (
    "system_inventory.json",
    "source_manifest.csv",
    "source_hashes.json",
    "assumptions.md",
    "requirements_local.md",
    "experiment_ledger.csv",
    "assets/manifests/wlr_robot_validation.json",
    "assets/validation/urdf_validation.json",
    "assets/validation/usd_candidate_comparison.json",
    "assets/validation/isaac_integration_converted_classified_004.json",
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _file_record(role: str, path: Path) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Freeze evidence is missing: {resolved}")
    return {
        "role": role,
        "path": str(resolved),
        "sha256": sha256_file(resolved),
    }


def _prevalidation_video_smoke(
    project_root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    diagnostics = project_root / "runs" / "diagnostics"
    directories = sorted(
        diagnostics.glob("prevalidation_video_smoke_attempt*")
    )
    records: list[dict[str, str]] = [
        _file_record(
            "prevalidation_video_smoke_script",
            project_root / "scripts" / "prevalidation_video_smoke.ps1",
        )
    ]
    development_manifest = (
        project_root / "data" / "scenario_manifests" / "development_v2.json"
    )
    development_manifest_hash = sha256_file(development_manifest)
    passed: list[dict[str, Any]] = []
    for directory in directories:
        result_path = directory / "result.json"
        if not result_path.is_file():
            continue
        result = _load_json(result_path)
        records.append(
            _file_record("prevalidation_video_smoke_result", result_path)
        )
        if not result.get("passed_execution", False):
            continue
        if (
            result.get("controller") != "fsm"
            or int(result.get("height_mm", -1)) != 50
            or result.get("video_replay", {}).get("scenario_id")
            != "development-h050-0000"
            or int(result.get("video_replay", {}).get("frame_count", 0)) < 1
            or result.get("provenance", {}).get("manifest_sha256")
            != development_manifest_hash
        ):
            raise ValueError(
                f"Prevalidation video smoke provenance is invalid: {result_path}"
            )
        provenance = result["provenance"]
        for entry in provenance.get("source_files", {}).values():
            source_path = Path(str(entry["path"]))
            if sha256_file(source_path) != entry["sha256"]:
                raise ValueError(
                    f"Prevalidation video smoke source drift: {source_path}"
                )
        for path_key, hash_key in (
            ("asset_path", "asset_sha256"),
            ("metrics_config", "metrics_config_sha256"),
            ("ppo_common_config", "ppo_common_config_sha256"),
            ("method_config", "method_config_sha256"),
        ):
            provenance_path = Path(str(provenance[path_key]))
            if sha256_file(provenance_path) != provenance[hash_key]:
                raise ValueError(
                    f"Prevalidation video smoke provenance drift: "
                    f"{provenance_path}"
                )
        artifacts = result.get("artifacts", {})
        artifact_records: list[dict[str, str]] = []
        for name in ("episodes", "telemetry", "status", "video"):
            path = Path(str(artifacts[name])).resolve()
            actual = sha256_file(path)
            if actual != artifacts[f"{name}_sha256"]:
                raise ValueError(
                    f"Prevalidation video smoke {name} hash mismatch: {path}"
                )
            artifact_records.append(
                _file_record(f"prevalidation_video_smoke_{name}", path)
            )
        episodes_path = Path(str(artifacts["episodes"]))
        rows = [
            json.loads(line)
            for line in episodes_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if (
            len(rows) != 1
            or rows[0].get("scenario_id") != "development-h050-0000"
            or rows[0].get("success") is not True
        ):
            raise ValueError(
                f"Prevalidation video smoke outcome mismatch: {episodes_path}"
            )
        probe_path = directory / "video_probe.json"
        probe = _load_json(probe_path)
        if (
            probe.get("schema")
            != "resume_validation.video_decode_probe.v1"
            or probe.get("decoded") is not True
            or int(probe.get("width", -1)) != 960
            or int(probe.get("height", -1)) != 540
            or not math.isclose(
                float(probe.get("fps", math.nan)),
                20.0,
                abs_tol=0.05,
            )
            or int(probe.get("decoded_frame_count", -1))
            != int(result["video_replay"]["frame_count"])
            or probe.get("video_sha256") != artifacts["video_sha256"]
        ):
            raise ValueError(
                f"Prevalidation video decode probe is invalid: {probe_path}"
            )
        artifact_records.append(
            _file_record(
                "prevalidation_video_smoke_decode_probe",
                probe_path,
            )
        )
        passed.append(
            {
                "attempt_directory": str(directory.resolve()),
                "result": str(result_path.resolve()),
                "result_sha256": sha256_file(result_path),
                "video": str(Path(str(artifacts["video"])).resolve()),
                "video_sha256": artifacts["video_sha256"],
                "video_decode_probe": str(probe_path.resolve()),
                "video_decode_probe_sha256": sha256_file(probe_path),
                "frame_count": int(result["video_replay"]["frame_count"]),
                "scenario_id": "development-h050-0000",
                "development_manifest_sha256": development_manifest_hash,
                "artifact_records": artifact_records,
            }
        )
    if not passed:
        raise ValueError(
            "No passing real-Isaac prevalidation camera/encoder smoke exists"
        )
    selected = passed[0]
    records.extend(selected.pop("artifact_records"))
    return selected, records


def _deduplicate_file_records(
    records: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    by_path: dict[str, dict[str, str]] = {}
    for record in records:
        path = str(Path(record["path"]).resolve())
        prior = by_path.get(path)
        if prior is not None and prior["sha256"] != record["sha256"]:
            raise ValueError(f"Conflicting hashes for freeze evidence: {path}")
        if prior is None:
            by_path[path] = {**record, "path": path}
        elif record["role"] not in prior["role"].split(";"):
            prior["role"] = f"{prior['role']};{record['role']}"
    return sorted(by_path.values(), key=lambda row: row["path"].lower())


def _discover_training(
    project_root: Path,
    runtime_version: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_runs: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    for method, folder in METHOD_FOLDERS.items():
        training_root = project_root / "runs" / folder / "training"
        pattern = f"method-{method}-{runtime_version}_seed-*_stage-*mm_attempt*"
        for run_dir in sorted(training_root.glob(pattern)):
            if not run_dir.is_dir():
                continue
            result_path = run_dir / "training_result.json"
            if not result_path.is_file():
                all_runs.append(
                    {
                        "method": method,
                        "run_name": run_dir.name,
                        "status": "MISSING_TRAINING_RESULT",
                    }
                )
                continue
            result = _load_json(result_path)
            record: dict[str, Any] = {
                "method": method,
                "seed": int(result["seed"]),
                "height_mm": int(result["height_mm"]),
                "run_name": run_dir.name,
                "status": str(result["status"]),
                "training_result": str(result_path.resolve()),
                "training_result_sha256": sha256_file(result_path),
            }
            if result["status"] == "COMPLETED":
                checkpoint = run_dir / "checkpoints" / "final_agent.pt"
                checkpoint_hash = sha256_file(checkpoint)
                if checkpoint_hash != result["final_checkpoint"]["sha256"]:
                    raise ValueError(f"Training checkpoint hash mismatch: {checkpoint}")
                record.update(
                    {
                        "checkpoint": str(checkpoint.resolve()),
                        "checkpoint_sha256": checkpoint_hash,
                    }
                )
                completed.append(record)
            all_runs.append(record)
    return all_runs, completed


def _candidate_identity(row: dict[str, Any]) -> tuple[str, int, int, str, str]:
    return (
        str(row["method"]),
        int(row["seed"]),
        int(row["height_mm"]),
        str(row["run_name"]),
        str(row["checkpoint_sha256"]),
    )


def _verify_training_provenance(
    project_root: Path,
    completed: Iterable[dict[str, Any]],
) -> None:
    for record in completed:
        result = _load_json(Path(record["training_result"]))
        provenance = result["provenance"]
        if sha256_file(Path(provenance["asset_path"])) != provenance["asset_sha256"]:
            raise ValueError(f"Training asset drift: {record['run_name']}")
        for entry in provenance["configs"].values():
            if sha256_file(Path(entry["path"])) != entry["sha256"]:
                raise ValueError(f"Training config drift: {entry['path']}")
        for entry in provenance["source_files"].values():
            if sha256_file(Path(entry["path"])) != entry["sha256"]:
                raise ValueError(f"Training source drift: {entry['path']}")
        expected_weight = 0.0 if record["method"] == "B" else 8.0
        actual_weight = float(
            provenance["effective_reward_weights"]["com_margin"]
        )
        if actual_weight != expected_weight:
            raise ValueError(
                f"Method {record['method']} has invalid CoM weight {actual_weight}"
            )


def _rebuild_summary(summary_path: Path) -> dict[str, Any]:
    recorded = _load_json(summary_path)
    rebuilt = build_validation_summary(
        controller=str(recorded["controller"]),
        seed=recorded.get("seed"),
        checkpoint_path=(
            Path(recorded["checkpoint"]) if recorded.get("checkpoint") else None
        ),
        validation_manifest_path=Path(recorded["validation_manifest"]),
        evaluation_paths=[
            Path(entry["evaluation"]) for entry in recorded["evidence"]
        ],
    )
    if rebuilt != recorded:
        raise ValueError(
            f"Validation summary does not reproduce from raw evidence: {summary_path}"
        )
    return recorded


def build_method_freeze(
    *,
    project_root: Path,
    validation_root: Path,
    runtime_version: str,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    validation_root = validation_root.resolve()
    protocol = load_config(project_root / "configs" / "experiment_protocol.yaml")
    selection_protocol_path = (
        project_root / "configs" / "validation_selection_protocol.json"
    )
    selection_protocol = _load_json(selection_protocol_path)
    if (
        not selection_protocol.get("frozen_before_validation", False)
        or selection_protocol.get("runtime_version") != runtime_version
    ):
        raise ValueError("Validation-selection protocol is not frozen for this runtime")
    formal = protocol.get("formal_v34")
    if not isinstance(formal, dict):
        raise ValueError("Formal-v34 experiment registration is missing")
    expected_formal_files = {
        "validation_selection_protocol": selection_protocol_path,
        "claims_audit_protocol": (
            project_root / "configs" / "claims_audit_protocol.json"
        ),
        "video_selection_protocol": (
            project_root / "configs" / "video_selection_protocol.json"
        ),
    }
    formal_checks = {
        "runtime_version": formal.get("active_method_version")
        == "runtime-v34-selected-phase9-bound-counter-yaw-skid-steer-emergency",
        "ppo_common_hash": formal.get("ppo_common_sha256")
        == sha256_file(project_root / "configs" / "ppo_common.yaml"),
        "validation_manifest_hash": formal.get("validation_manifest_sha256")
        == sha256_file(
            project_root / "data" / "scenario_manifests" / "validation_v2.json"
        ),
        "evaluator_hash": formal.get("prevalidation_evaluator_sha256")
        == sha256_file(
            project_root
            / "src"
            / "resume_validation"
            / "evaluate_controller.py"
        ),
        "seeds": tuple(int(value) for value in formal.get("training_seeds", []))
        == SEEDS,
        "heights": tuple(int(value) for value in formal.get("heights_mm", []))
        == HEIGHTS,
        "local_stage_budget": int(
            formal.get("local_timesteps_per_seed_height_stage", -1)
        )
        == 76_800,
        "transition_stage_budget": int(
            formal.get("transitions_per_seed_height_stage", -1)
        )
        == 4_915_200,
        "ablation_weights": (
            float(formal.get("without_com_weight", math.nan)) == 0.0
            and float(formal.get("with_com_weight", math.nan)) == 8.0
        ),
    }
    for registration_name, registered_path in expected_formal_files.items():
        registration = formal.get(registration_name, {})
        formal_checks[f"{registration_name}_path"] = (
            str(registration.get("path", "")).replace("\\", "/")
            == registered_path.relative_to(project_root).as_posix()
        )
        formal_checks[f"{registration_name}_hash"] = (
            registration.get("sha256") == sha256_file(registered_path)
        )
    failed_formal_checks = sorted(
        name for name, passed in formal_checks.items() if not passed
    )
    if failed_formal_checks:
        raise ValueError(
            "Formal-v34 registration drift: " + ", ".join(failed_formal_checks)
        )

    without_com = load_config(project_root / "configs" / "ppo_without_com.yaml")
    with_com = load_config(project_root / "configs" / "ppo_with_com.yaml")
    ablation_differences = differing_leaf_paths(without_com, with_com)
    if ablation_differences != {"method", "reward.com_margin_weight"}:
        raise ValueError(
            f"B/C config drift: {sorted(ablation_differences)}"
        )
    if (
        float(without_com["reward"]["com_margin_weight"]) != 0.0
        or float(with_com["reward"]["com_margin_weight"]) != 8.0
    ):
        raise ValueError("B/C CoM reward weights are not the registered 0/8 pair")

    config_freeze_path = project_root / "configs" / "config_freeze.json"
    config_freeze = _load_json(config_freeze_path)
    for name in ("fsm", "metrics"):
        entry = config_freeze["frozen"][f"{name}_sha256"]
        actual = sha256_file(project_root / "configs" / f"{name}.yaml")
        if actual != entry:
            raise ValueError(f"Frozen {name} hash drift: {actual} != {entry}")

    registry_path = validation_root / "candidate_registry.json"
    registry = _load_json(registry_path)
    if (
        registry.get("runtime_version") != runtime_version
        or registry.get("validation_manifest_sha256")
        != selection_protocol["validation_manifest_sha256"]
        or registry.get("selection_protocol_sha256")
        != sha256_file(selection_protocol_path)
    ):
        raise ValueError("Validation candidate registry/protocol mismatch")

    all_runs, completed = _discover_training(project_root, runtime_version)
    if any(row["status"] == "RUNNING" for row in all_runs):
        raise ValueError("Cannot freeze while a matching formal training run is active")
    registered_completed = list(registry["completed_candidates"])
    if {
        _candidate_identity(row) for row in completed
    } != {
        _candidate_identity(row) for row in registered_completed
    }:
        raise ValueError(
            "Completed formal checkpoints differ from the pre-validation registry"
        )
    for method in METHOD_FOLDERS:
        for seed in SEEDS:
            for height in HEIGHTS:
                if not any(
                    row["method"] == method
                    and int(row["seed"]) == seed
                    and int(row["height_mm"]) == height
                    for row in completed
                ):
                    raise ValueError(
                        f"Incomplete training: {method=} {seed=} {height=}"
                    )
    _verify_training_provenance(project_root, completed)

    immutable_files: list[dict[str, str]] = [
        _file_record("candidate_registry", registry_path),
        _file_record("config_freeze", config_freeze_path),
        _file_record("experiment_protocol", project_root / "configs" / "experiment_protocol.yaml"),
    ]
    immutable_files.extend(
        _file_record(f"config:{name}", project_root / "configs" / name)
        for name in CRITICAL_CONFIGS
    )
    immutable_files.extend(
        _file_record(
            f"source:{name}",
            project_root / "src" / "resume_validation" / name,
        )
        for name in CRITICAL_SOURCES
    )
    immutable_files.extend(
        _file_record(
            f"script:{name}",
            project_root / "scripts" / name,
        )
        for name in CRITICAL_SCRIPTS
    )
    immutable_files.extend(
        _file_record(
            f"evidence:{name}",
            project_root / Path(name),
        )
        for name in CRITICAL_EVIDENCE
    )
    asset_path = project_root / "assets" / "converted" / "wlr_robot_validation.usd"
    immutable_files.append(_file_record("robot_asset", asset_path))
    video_smoke, video_smoke_records = _prevalidation_video_smoke(
        project_root
    )
    immutable_files.extend(video_smoke_records)
    for row in completed:
        immutable_files.extend(
            (
                _file_record(
                    f"training_result:{row['run_name']}",
                    Path(row["training_result"]),
                ),
                _file_record(
                    f"candidate_checkpoint:{row['run_name']}",
                    Path(row["checkpoint"]),
                ),
            )
        )

    fsm_summary_path = validation_root / "fsm" / "validation_summary.json"
    fsm_summary = _rebuild_summary(fsm_summary_path)
    if (
        fsm_summary["validation_manifest_sha256"]
        != selection_protocol["validation_manifest_sha256"]
        or int(fsm_summary["episode_count"]) != 90
    ):
        raise ValueError("FSM validation summary coverage is invalid")
    immutable_files.append(_file_record("fsm_validation_summary", fsm_summary_path))
    for evidence in fsm_summary["evidence"]:
        immutable_files.extend(
            (
                _file_record("fsm_validation_result", Path(evidence["evaluation"])),
                _file_record("fsm_validation_episodes", Path(evidence["episodes"])),
            )
        )

    selections: list[dict[str, Any]] = []
    for method in METHOD_FOLDERS:
        for seed in SEEDS:
            candidate_rows = sorted(
                (
                    row
                    for row in completed
                    if row["method"] == method and int(row["seed"]) == seed
                ),
                key=lambda row: (int(row["height_mm"]), str(row["run_name"])),
            )
            summaries: list[dict[str, Any]] = []
            summary_paths: list[Path] = []
            for row in candidate_rows:
                summary_path = (
                    validation_root
                    / f"method-{method}"
                    / f"seed-{seed}"
                    / "candidates"
                    / str(row["run_name"])
                    / "validation_summary.json"
                )
                summary = _rebuild_summary(summary_path)
                summaries.append(summary)
                summary_paths.append(summary_path)
                immutable_files.append(
                    _file_record(
                        f"candidate_validation_summary:{method}:{seed}",
                        summary_path,
                    )
                )
                for evidence in summary["evidence"]:
                    immutable_files.extend(
                        (
                            _file_record(
                                f"candidate_validation_result:{method}:{seed}",
                                Path(evidence["evaluation"]),
                            ),
                            _file_record(
                                f"candidate_validation_episodes:{method}:{seed}",
                                Path(evidence["episodes"]),
                            ),
                        )
                    )
            selection_path = (
                validation_root
                / f"method-{method}"
                / f"seed-{seed}"
                / "checkpoint_selection.json"
            )
            recorded_selection = _load_json(selection_path)
            recomputed_selection = select_seed_checkpoint(
                method=method,
                seed=seed,
                fsm_summary=fsm_summary,
                candidate_summaries=summaries,
            )
            if recomputed_selection != recorded_selection:
                raise ValueError(
                    f"Checkpoint selection does not reproduce: {selection_path}"
                )
            selected_checkpoint = Path(
                recorded_selection["selected_checkpoint"]
            ).resolve()
            if (
                sha256_file(selected_checkpoint)
                != recorded_selection["selected_checkpoint_sha256"]
            ):
                raise ValueError(f"Selected checkpoint drift: {selected_checkpoint}")
            immutable_files.extend(
                (
                    _file_record(
                        f"checkpoint_selection:{method}:{seed}",
                        selection_path,
                    ),
                    _file_record(
                        f"selected_checkpoint:{method}:{seed}",
                        selected_checkpoint,
                    ),
                )
            )
            selections.append(
                {
                    "method": method,
                    "seed": seed,
                    "selection": str(selection_path.resolve()),
                    "selection_sha256": sha256_file(selection_path),
                    "selection_status": recorded_selection["selection_status"],
                    "passed_validation_gate": bool(
                        recorded_selection["passed_validation_gate"]
                    ),
                    "selected_checkpoint": str(selected_checkpoint),
                    "selected_checkpoint_sha256": sha256_file(
                        selected_checkpoint
                    ),
                    "selected_metrics": recorded_selection["selected_metrics"],
                    "candidate_count": len(summaries),
                    "candidate_summaries": [
                        str(path.resolve()) for path in summary_paths
                    ],
                }
            )

    locked_relative = Path(protocol["active_manifests"]["locked_test"])
    # Do not resolve or query the locked path here. Only the pre-registered
    # string and hash are copied into the freeze authorization record.
    return {
        "schema": "resume_validation.method_freeze.v1",
        "frozen": True,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_version": runtime_version,
        "validation_campaign": str(validation_root),
        "validation_manifest": fsm_summary["validation_manifest"],
        "validation_manifest_sha256": fsm_summary[
            "validation_manifest_sha256"
        ],
        "validation_episode_count_per_controller_checkpoint": 90,
        "candidate_registry": str(registry_path.resolve()),
        "candidate_registry_sha256": sha256_file(registry_path),
        "training_run_count": len(all_runs),
        "completed_candidate_count": len(completed),
        "critical_source_names": list(CRITICAL_SOURCES),
        "critical_script_names": list(CRITICAL_SCRIPTS),
        "critical_evidence_paths": list(CRITICAL_EVIDENCE),
        "all_matching_training_runs": all_runs,
        "fsm_validation_summary": str(fsm_summary_path.resolve()),
        "fsm_validation_summary_sha256": sha256_file(fsm_summary_path),
        "selections": selections,
        "all_seed_validation_gates_passed": all(
            row["passed_validation_gate"] for row in selections
        ),
        "ablation_config_differences": sorted(ablation_differences),
        "prevalidation_video_smoke": video_smoke,
        "locked_test_authorization": {
            "manifest_registered_path": locked_relative.as_posix(),
            "manifest_registered_sha256": protocol[
                "locked_test_manifest_sha256"
            ],
            "manifest_read_or_hashed_during_freeze": False,
            "access_condition": (
                "verify every immutable file below, then independently hash "
                "and sidecar-verify this registered locked manifest"
            ),
        },
        "immutable_files": _deduplicate_file_records(immutable_files),
    }


def verify_method_freeze(freeze: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if (
        freeze.get("schema") != "resume_validation.method_freeze.v1"
        or freeze.get("frozen") is not True
    ):
        failures.append("freeze schema/status invalid")
    authorization = freeze.get("locked_test_authorization", {})
    if authorization.get("manifest_read_or_hashed_during_freeze") is not False:
        failures.append("freeze does not attest pre-access locked isolation")
    if (
        "critical_source_names" in freeze
        and freeze.get("critical_source_names") != list(CRITICAL_SOURCES)
    ):
        failures.append("critical source inventory changed after freeze")
    if (
        "critical_script_names" in freeze
        and freeze.get("critical_script_names") != list(CRITICAL_SCRIPTS)
    ):
        failures.append("critical script inventory changed after freeze")
    if (
        "critical_evidence_paths" in freeze
        and freeze.get("critical_evidence_paths") != list(CRITICAL_EVIDENCE)
    ):
        failures.append("critical technical-evidence inventory changed after freeze")
    records = freeze.get("immutable_files")
    if not isinstance(records, list) or not records:
        failures.append("immutable file list missing")
        return failures
    seen: set[str] = set()
    for record in records:
        path = Path(str(record.get("path", "")))
        key = str(path.resolve())
        if key in seen:
            failures.append(f"duplicate immutable path: {key}")
            continue
        seen.add(key)
        if not path.is_file():
            failures.append(f"immutable file missing: {path}")
            continue
        actual = sha256_file(path)
        if actual != record.get("sha256"):
            failures.append(
                f"immutable hash mismatch: {path}: {actual} != {record.get('sha256')}"
            )
    for selection in freeze.get("selections", []):
        checkpoint = Path(selection["selected_checkpoint"])
        if not checkpoint.is_file():
            failures.append(f"selected checkpoint missing: {checkpoint}")
        elif sha256_file(checkpoint) != selection["selected_checkpoint_sha256"]:
            failures.append(f"selected checkpoint hash mismatch: {checkpoint}")
    return failures


def _main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--project_root", type=Path, required=True)
    create.add_argument("--validation_root", type=Path, required=True)
    create.add_argument("--runtime_version", default="v34")
    create.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--freeze", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "create":
        if args.output.exists():
            raise FileExistsError(f"Refusing to overwrite method freeze: {args.output}")
        freeze = build_method_freeze(
            project_root=args.project_root,
            validation_root=args.validation_root,
            runtime_version=args.runtime_version,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, freeze)
        failures = verify_method_freeze(freeze)
        if failures:
            raise RuntimeError(
                "New method freeze failed self-verification: "
                + " | ".join(failures)
            )
        print(
            json.dumps(
                {
                    "freeze": str(args.output.resolve()),
                    "freeze_sha256": sha256_file(args.output),
                    "selection_count": len(freeze["selections"]),
                    "all_seed_validation_gates_passed": freeze[
                        "all_seed_validation_gates_passed"
                    ],
                },
                indent=2,
            )
        )
        return 0

    freeze = _load_json(args.freeze)
    failures = verify_method_freeze(freeze)
    print(
        json.dumps(
            {
                "freeze": str(args.freeze.resolve()),
                "valid": not failures,
                "failures": failures,
            },
            indent=2,
        )
    )
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(_main())
