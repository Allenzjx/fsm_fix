"""Post-freeze authorization and paired-coverage audit for locked testing."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config_io import write_json
from .method_freeze import verify_method_freeze
from .scenario_manifest import verify_manifest
from .source_audit import sha256_file

HEIGHTS = (50, 75, 100)
SEEDS = (11, 29, 47)
SCENARIO_FIELDS = (
    "scenario_id",
    "obstacle_height_m",
    "obstacle_front_x_m",
    "initial_distance_m",
    "initial_pitch_rad",
    "friction",
    "actuator_delay_steps",
    "sensor_noise_std",
    "environment_seed",
    "noise_seed",
)
REQUIRED_TELEMETRY_COLUMNS = {
    "time_s",
    "env_id",
    "base_x_m",
    "pitch_rad",
    "pitch_rate_rad_s",
    "margin_m",
    "fsm_phase",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def authorize_locked_test(
    *,
    freeze_path: Path,
    project_root: Path,
) -> dict[str, Any]:
    freeze_path = freeze_path.resolve()
    project_root = project_root.resolve()
    freeze = _load_json(freeze_path)
    failures = verify_method_freeze(freeze)
    if failures:
        raise RuntimeError(
            "Method freeze verification failed before locked access: "
            + " | ".join(failures)
        )
    registered = freeze["locked_test_authorization"]
    relative = Path(str(registered["manifest_registered_path"]))
    if relative.is_absolute():
        raise ValueError("Locked manifest registration must be project-relative")
    manifest = (project_root / relative).resolve()
    try:
        manifest.relative_to(project_root)
    except ValueError as exc:
        raise ValueError("Locked manifest escapes the isolated project") from exc

    # This is the first authorized locked-manifest read in the workflow.
    actual_hash = sha256_file(manifest)
    expected_hash = str(registered["manifest_registered_sha256"])
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"Locked manifest hash mismatch: {actual_hash} != {expected_hash}"
        )
    if not verify_manifest(manifest):
        raise RuntimeError("Locked manifest sidecar verification failed")
    return {
        "schema": "resume_validation.locked_test_authorization.v1",
        "authorized_at_utc": datetime.now(timezone.utc).isoformat(),
        "method_freeze": str(freeze_path),
        "method_freeze_sha256": sha256_file(freeze_path),
        "method_freeze_verified": True,
        "immutable_file_count": len(freeze["immutable_files"]),
        "locked_manifest": str(manifest),
        "locked_manifest_sha256": actual_hash,
        "locked_manifest_sidecar_verified": True,
        "access_order": "method freeze verified before locked manifest read/hash",
    }


def _manifest_ids(manifest_path: Path) -> dict[int, set[str]]:
    manifest = _load_json(manifest_path)
    by_height = {height: set() for height in HEIGHTS}
    for scenario in manifest["scenarios"]:
        height = int(round(float(scenario["obstacle_height_m"]) * 1000.0))
        if height not in by_height:
            raise ValueError(f"Unexpected locked-test height: {height}")
        scenario_id = str(scenario["scenario_id"])
        if scenario_id in by_height[height]:
            raise ValueError(f"Duplicate locked scenario ID: {scenario_id}")
        by_height[height].add(scenario_id)
    if any(len(by_height[height]) != 100 for height in HEIGHTS):
        raise ValueError(
            "Locked manifest must contain exactly 100 scenarios per height"
        )
    return by_height


def _manifest_rows(
    manifest_path: Path,
) -> dict[int, dict[str, dict[str, Any]]]:
    manifest = _load_json(manifest_path)
    by_height: dict[int, dict[str, dict[str, Any]]] = {
        height: {} for height in HEIGHTS
    }
    for scenario in manifest["scenarios"]:
        height = int(round(float(scenario["obstacle_height_m"]) * 1000.0))
        scenario_id = str(scenario["scenario_id"])
        by_height[height][scenario_id] = scenario
    return by_height


def _load_evaluation(
    *,
    result_path: Path,
    controller: str,
    height: int,
    expected_ids: set[str],
    manifest_hash: str,
    checkpoint_hash: str | None,
    expected_scenarios: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    result = _load_json(result_path)
    if (
        not result.get("passed_execution", False)
        or result.get("controller") != controller
        or int(result.get("height_mm", -1)) != height
    ):
        raise ValueError(f"Invalid locked evaluation: {result_path}")
    provenance = result["provenance"]
    if provenance.get("manifest_sha256") != manifest_hash:
        raise ValueError(f"Locked manifest provenance mismatch: {result_path}")
    if provenance.get("checkpoint_sha256") != checkpoint_hash:
        raise ValueError(f"Locked checkpoint provenance mismatch: {result_path}")
    artifact = result["artifacts"]
    episodes_path = Path(artifact["episodes"]).resolve()
    if sha256_file(episodes_path) != artifact["episodes_sha256"]:
        raise ValueError(f"Locked episode artifact hash mismatch: {episodes_path}")
    rows = [
        json.loads(line)
        for line in episodes_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = [str(row["scenario_id"]) for row in rows]
    if (
        len(ids) != 100
        or len(set(ids)) != 100
        or set(ids) != expected_ids
    ):
        raise ValueError(f"Locked paired coverage mismatch: {episodes_path}")
    if any(
        row.get("controller") != controller
        or int(round(float(row["obstacle_height_m"]) * 1000.0)) != height
        for row in rows
    ):
        raise ValueError(f"Locked episode metadata mismatch: {episodes_path}")
    if expected_scenarios is not None:
        for row in rows:
            scenario_id = str(row["scenario_id"])
            expected = expected_scenarios[scenario_id]
            if any(row.get(field) != expected.get(field) for field in SCENARIO_FIELDS):
                raise ValueError(
                    f"Locked scenario parameter mismatch: "
                    f"{episodes_path}:{scenario_id}"
                )
    if (
        int(result["aggregate"]["episode_count"]) != 100
        or int(result["aggregate"]["success_count"])
        != sum(bool(row["success"]) for row in rows)
    ):
        raise ValueError(f"Locked aggregate mismatch: {result_path}")
    telemetry_path = Path(artifact["telemetry"]).resolve()
    telemetry_hash = sha256_file(telemetry_path)
    if telemetry_hash != artifact["telemetry_sha256"]:
        raise ValueError(
            f"Locked telemetry artifact hash mismatch: {telemetry_path}"
        )
    with telemetry_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or [])
        if not REQUIRED_TELEMETRY_COLUMNS <= columns:
            raise ValueError(
                f"Locked telemetry schema is incomplete: {telemetry_path}"
            )
        telemetry_env_ids: set[int] = set()
        telemetry_row_count = 0
        for telemetry_row in reader:
            try:
                env_id = int(telemetry_row["env_id"])
                time_s = float(telemetry_row["time_s"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Locked telemetry contains invalid index/time: "
                    f"{telemetry_path}"
                ) from exc
            if env_id < 0 or env_id >= 100 or not math.isfinite(time_s):
                raise ValueError(
                    f"Locked telemetry contains out-of-range index/time: "
                    f"{telemetry_path}"
                )
            telemetry_env_ids.add(env_id)
            telemetry_row_count += 1
    if telemetry_row_count == 0 or telemetry_env_ids != set(range(100)):
        raise ValueError(
            f"Locked telemetry lacks complete environment coverage: "
            f"{telemetry_path}"
        )
    status_path = Path(artifact["status"]).resolve()
    status_hash = sha256_file(status_path)
    if status_hash != artifact["status_sha256"]:
        raise ValueError(f"Locked status artifact hash mismatch: {status_path}")
    status = _load_json(status_path)
    active_count = int(status.get("active_count", -1))
    completed_count = int(status.get("completed_count", -1))
    success_count = int(status.get("success_count", -1))
    if (
        status.get("schema") != "resume_validation.controller_status.v1"
        or active_count < 0
        or completed_count < 0
        or active_count + completed_count != 100
        or success_count < 0
        or success_count > completed_count
    ):
        raise ValueError(f"Locked status artifact is invalid: {status_path}")
    files = [
        {
            "role": f"locked_result:{controller}:{height}",
            "path": str(result_path.resolve()),
            "sha256": sha256_file(result_path),
        },
        {
            "role": f"locked_episodes:{controller}:{height}",
            "path": str(episodes_path),
            "sha256": sha256_file(episodes_path),
        },
        {
            "role": f"locked_telemetry:{controller}:{height}",
            "path": str(telemetry_path),
            "sha256": telemetry_hash,
        },
        {
            "role": f"locked_status:{controller}:{height}",
            "path": str(status_path),
            "sha256": status_hash,
        },
    ]
    return result, rows, files


def audit_locked_campaign(
    *,
    freeze_path: Path,
    authorization_path: Path,
    run_root: Path,
) -> dict[str, Any]:
    freeze = _load_json(freeze_path)
    failures = verify_method_freeze(freeze)
    if failures:
        raise RuntimeError("Method freeze drift: " + " | ".join(failures))
    authorization = _load_json(authorization_path)
    if (
        not authorization.get("method_freeze_verified", False)
        or authorization.get("method_freeze_sha256")
        != sha256_file(freeze_path)
    ):
        raise ValueError("Locked authorization does not match the method freeze")
    manifest_path = Path(authorization["locked_manifest"]).resolve()
    manifest_hash = sha256_file(manifest_path)
    if (
        manifest_hash != authorization["locked_manifest_sha256"]
        or not verify_manifest(manifest_path)
    ):
        raise ValueError("Locked manifest changed after authorization")
    expected_ids = _manifest_ids(manifest_path)
    expected_scenarios = _manifest_rows(manifest_path)
    run_root = run_root.resolve()
    evidence: list[dict[str, str]] = []
    evaluation_count = 0
    episode_count = 0

    for height in HEIGHTS:
        result_path = run_root / "fsm" / f"height-{height}mm" / "result.json"
        _, rows, files = _load_evaluation(
            result_path=result_path,
            controller="fsm",
            height=height,
            expected_ids=expected_ids[height],
            manifest_hash=manifest_hash,
            checkpoint_hash=None,
            expected_scenarios=expected_scenarios[height],
        )
        evidence.extend(files)
        evaluation_count += 1
        episode_count += len(rows)

    selection_by_method_seed = {
        (str(row["method"]), int(row["seed"])): row
        for row in freeze["selections"]
    }
    selection_statuses: list[dict[str, Any]] = []
    for method in ("B", "C"):
        for seed in SEEDS:
            selection = selection_by_method_seed[(method, seed)]
            checkpoint_hash = selection["selected_checkpoint_sha256"]
            selection_statuses.append(
                {
                    "method": method,
                    "seed": seed,
                    "selection_status": selection["selection_status"],
                    "passed_validation_gate": selection[
                        "passed_validation_gate"
                    ],
                    "checkpoint_sha256": checkpoint_hash,
                }
            )
            for height in HEIGHTS:
                result_path = (
                    run_root
                    / f"method-{method}"
                    / f"seed-{seed}"
                    / f"height-{height}mm"
                    / "result.json"
                )
                _, rows, files = _load_evaluation(
                    result_path=result_path,
                    controller=method,
                    height=height,
                    expected_ids=expected_ids[height],
                    manifest_hash=manifest_hash,
                    checkpoint_hash=checkpoint_hash,
                    expected_scenarios=expected_scenarios[height],
                )
                evidence.extend(files)
                evaluation_count += 1
                episode_count += len(rows)
    return {
        "schema": "resume_validation.locked_paired_coverage_audit.v1",
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "method_freeze": str(freeze_path.resolve()),
        "method_freeze_sha256": sha256_file(freeze_path),
        "authorization": str(authorization_path.resolve()),
        "authorization_sha256": sha256_file(authorization_path),
        "locked_manifest": str(manifest_path),
        "locked_manifest_sha256": manifest_hash,
        "heights_mm": list(HEIGHTS),
        "scenarios_per_height": 100,
        "evaluation_count": evaluation_count,
        "episode_count": episode_count,
        "expected_evaluation_count": 21,
        "expected_episode_count": 2100,
        "paired_scenario_coverage_complete": (
            evaluation_count == 21 and episode_count == 2100
        ),
        "selection_statuses": selection_statuses,
        "evidence": sorted(evidence, key=lambda row: row["path"].lower()),
    }


def _main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--freeze", type=Path, required=True)
    authorize.add_argument("--project_root", type=Path, required=True)
    authorize.add_argument("--output", type=Path, required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("--freeze", type=Path, required=True)
    audit.add_argument("--authorization", type=Path, required=True)
    audit.add_argument("--run_root", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite evidence: {args.output}")
    if args.command == "authorize":
        payload = authorize_locked_test(
            freeze_path=args.freeze,
            project_root=args.project_root,
        )
    else:
        payload = audit_locked_campaign(
            freeze_path=args.freeze,
            authorization_path=args.authorization,
            run_root=args.run_root,
        )
        if not payload["paired_scenario_coverage_complete"]:
            raise RuntimeError("Locked-test paired coverage is incomplete")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "schema": payload["schema"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
