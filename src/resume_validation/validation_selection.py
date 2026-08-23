"""Validation-only checkpoint summaries and frozen per-seed selection.

This module deliberately has no locked-test argument or path. It accepts only
completed validation evaluations, verifies their raw episode artifacts against
the registered validation manifest, and produces deterministic selection
evidence suitable for the later method-freeze gate.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .aggregate_results import episode_height_mm, summarize_episode_rows
from .checkpoint_selection import select_checkpoint_with_disclosed_fallback
from .config_io import write_json
from .source_audit import sha256_file

HEIGHTS = (50, 75, 100)
SEVERE_FAILURE_REASONS = frozenset({"NUMERICAL_ERROR", "JOINT_LIMIT"})
SELECTION_RULE = {
    "version": "validation-lexicographic-v1",
    "success_floor": (
        "frozen-FSM equal-height-weighted success rate on the same validation "
        "manifest"
    ),
    "eligibility": "success_rate >= success_floor and safety_violations == 0",
    "eligible_order": [
        "maximize equal-height mean episode minimum margin",
        "minimize equal-height mean episode pitch-rate RMS",
        "minimize equal-height mean slip distance when available",
        "minimize equal-height mean residual saturation rate",
        "deterministic checkpoint SHA256 tie break",
    ],
    "fallback": (
        "if no eligible candidate exists, retain the highest-validation-success "
        "safety-clean checkpoint for a disclosed confirmatory comparison; if "
        "none is safety-clean, retain the least-violating candidate; fallback "
        "status cannot be represented as passing validation"
    ),
    "severe_safety_failures": sorted(SEVERE_FAILURE_REASONS),
    "body_collision_policy": (
        "body/link collision remains an episode failure and is reported, but "
        "is not reclassified as a policy-integrity violation"
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row {line_number} is not an object: {path}")
        rows.append(row)
    return rows


def _manifest_ids_by_height(manifest: dict[str, Any]) -> dict[int, set[str]]:
    result: dict[int, set[str]] = defaultdict(set)
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("Validation manifest scenarios must be a list")
    for scenario in scenarios:
        height = episode_height_mm(scenario)
        scenario_id = str(scenario["scenario_id"])
        if scenario_id in result[height]:
            raise ValueError(f"Duplicate validation scenario ID: {scenario_id}")
        result[height].add(scenario_id)
    if set(result) != set(HEIGHTS):
        raise ValueError(
            f"Validation manifest must contain 50/75/100 mm, got {sorted(result)}"
        )
    return dict(result)


def _equal_height_mean(
    rows: Iterable[dict[str, Any]],
    field: str,
) -> float | None:
    groups: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is not None:
            numeric = float(value)
            if math.isfinite(numeric):
                groups[episode_height_mm(row)].append(numeric)
    if any(not groups[height] for height in HEIGHTS):
        return None
    return mean(mean(groups[height]) for height in HEIGHTS)


def _safety_violation_count(rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        severe_failure = str(row.get("failure_reason", "")) in SEVERE_FAILURE_REASONS
        baseline_ik_invalid = (
            int(row.get("terminal_fsm_baseline_ik_invalid_count", 0)) > 0
        )
        joint_diagnostic = bool(
            row.get("terminal_joint_limit_diagnostic", {})
        )
        if severe_failure or baseline_ik_invalid or joint_diagnostic:
            count += 1
    return count


def build_validation_summary(
    *,
    controller: str,
    evaluation_paths: Iterable[Path],
    validation_manifest_path: Path,
    seed: int | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    if controller not in {"fsm", "B", "C"}:
        raise ValueError(f"Unsupported controller: {controller}")
    if controller == "fsm":
        if seed is not None or checkpoint_path is not None:
            raise ValueError("FSM validation has neither training seed nor checkpoint")
    elif seed not in {11, 29, 47} or checkpoint_path is None:
        raise ValueError("PPO validation requires a registered seed and checkpoint")

    manifest_path = validation_manifest_path.resolve()
    manifest = _load_json(manifest_path)
    manifest_hash = sha256_file(manifest_path)
    expected_ids = _manifest_ids_by_height(manifest)
    checkpoint = checkpoint_path.resolve() if checkpoint_path else None
    checkpoint_hash = sha256_file(checkpoint) if checkpoint else None

    evaluations: dict[int, dict[str, Any]] = {}
    episode_rows: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for supplied_path in evaluation_paths:
        evaluation_path = supplied_path.resolve()
        evaluation = _load_json(evaluation_path)
        if not bool(evaluation.get("passed_execution", False)):
            raise ValueError(f"Evaluation did not pass execution: {evaluation_path}")
        if evaluation.get("controller") != controller:
            raise ValueError(f"Controller mismatch in {evaluation_path}")
        height = int(evaluation.get("height_mm", -1))
        if height not in HEIGHTS or height in evaluations:
            raise ValueError(f"Missing, duplicate, or invalid height: {height}")
        provenance = evaluation.get("provenance", {})
        if provenance.get("manifest_sha256") != manifest_hash:
            raise ValueError(f"Validation manifest hash mismatch in {evaluation_path}")
        if controller != "fsm" and provenance.get("checkpoint_sha256") != checkpoint_hash:
            raise ValueError(f"Checkpoint hash mismatch in {evaluation_path}")
        if controller == "fsm" and provenance.get("checkpoint_sha256") is not None:
            raise ValueError(f"FSM evaluation unexpectedly records a checkpoint: {evaluation_path}")

        artifact = evaluation.get("artifacts", {})
        episodes_path = Path(str(artifact["episodes"])).resolve()
        if sha256_file(episodes_path) != artifact.get("episodes_sha256"):
            raise ValueError(f"Episode artifact hash mismatch: {episodes_path}")
        rows = _load_jsonl(episodes_path)
        actual_ids = [str(row["scenario_id"]) for row in rows]
        if len(actual_ids) != len(set(actual_ids)):
            raise ValueError(f"Duplicate episode scenario IDs: {episodes_path}")
        if set(actual_ids) != expected_ids[height]:
            raise ValueError(
                f"Validation scenario coverage mismatch for {height} mm: "
                f"expected {len(expected_ids[height])}, got {len(actual_ids)}"
            )
        if any(episode_height_mm(row) != height for row in rows):
            raise ValueError(f"Cross-height episode in {episodes_path}")
        if any(row.get("controller") != controller for row in rows):
            raise ValueError(f"Episode controller mismatch in {episodes_path}")
        aggregate = evaluation.get("aggregate", {})
        if int(aggregate.get("episode_count", -1)) != len(rows):
            raise ValueError(f"Evaluation episode count mismatch: {evaluation_path}")
        if int(aggregate.get("success_count", -1)) != sum(
            bool(row["success"]) for row in rows
        ):
            raise ValueError(f"Evaluation success count mismatch: {evaluation_path}")

        evaluations[height] = evaluation
        episode_rows.extend(rows)
        evidence.append(
            {
                "height_mm": height,
                "evaluation": str(evaluation_path),
                "evaluation_sha256": sha256_file(evaluation_path),
                "episodes": str(episodes_path),
                "episodes_sha256": sha256_file(episodes_path),
                "episode_count": len(rows),
            }
        )

    if set(evaluations) != set(HEIGHTS):
        raise ValueError(
            f"Exactly one evaluation per height is required, got {sorted(evaluations)}"
        )
    summary = summarize_episode_rows(episode_rows)
    aggregate = summary["aggregate"]
    slip_distance = _equal_height_mean(
        episode_rows,
        "wheel_slip_distance_m",
    )
    saturation_rate = _equal_height_mean(
        episode_rows,
        "residual_saturation_rate",
    )
    selection_metrics = {
        "success_rate": float(
            aggregate["equal_height_weighted_success_rate"]
        ),
        "mean_min_margin_m": aggregate[
            "equal_height_weighted_mean_minimum_margin_m"
        ],
        "pitch_rate_rms_rad_s": aggregate[
            "equal_height_weighted_pitch_rate_rms_rad_s"
        ],
        "slip_distance_m": slip_distance,
        "saturation_rate": saturation_rate,
        "safety_violations": _safety_violation_count(episode_rows),
    }
    if (
        selection_metrics["mean_min_margin_m"] is None
        or selection_metrics["pitch_rate_rms_rad_s"] is None
    ):
        raise ValueError("Primary validation stability metrics are incomplete")
    return {
        "schema": "resume_validation.validation_summary.v1",
        "controller": controller,
        "seed": seed,
        "checkpoint": str(checkpoint) if checkpoint else None,
        "checkpoint_sha256": checkpoint_hash,
        "validation_manifest": str(manifest_path),
        "validation_manifest_sha256": manifest_hash,
        "selection_metrics": selection_metrics,
        "summary": summary,
        "failure_counts": {
            reason: sum(
                str(row.get("failure_reason", "")) == reason
                for row in episode_rows
            )
            for reason in sorted(
                {
                    str(row.get("failure_reason", ""))
                    for row in episode_rows
                    if row.get("failure_reason")
                }
            )
        },
        "evidence": sorted(evidence, key=lambda row: row["height_mm"]),
        "episode_count": len(episode_rows),
        "selection_rule": SELECTION_RULE,
    }


def select_seed_checkpoint(
    *,
    method: str,
    seed: int,
    fsm_summary: dict[str, Any],
    candidate_summaries: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    if method not in {"B", "C"} or seed not in {11, 29, 47}:
        raise ValueError("Selection requires a registered method and seed")
    if fsm_summary.get("controller") != "fsm":
        raise ValueError("FSM validation summary is invalid")
    candidates = list(candidate_summaries)
    if not candidates:
        raise ValueError("At least one candidate summary is required")
    manifest_hash = fsm_summary.get("validation_manifest_sha256")
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("controller") != method:
            raise ValueError("Candidate method mismatch")
        if int(candidate.get("seed", -1)) != seed:
            raise ValueError("Candidate seed mismatch")
        if candidate.get("validation_manifest_sha256") != manifest_hash:
            raise ValueError("Candidate and FSM validation manifests differ")
        metrics = dict(candidate["selection_metrics"])
        metrics.update(
            {
                "checkpoint": candidate["checkpoint"],
                "checkpoint_sha256": candidate["checkpoint_sha256"],
            }
        )
        rows.append(metrics)
    checkpoint_hashes = [str(row["checkpoint_sha256"]) for row in rows]
    if len(checkpoint_hashes) != len(set(checkpoint_hashes)):
        raise ValueError("Duplicate checkpoint candidate hashes")
    minimum_success_rate = float(
        fsm_summary["selection_metrics"]["success_rate"]
    )
    selected, status = select_checkpoint_with_disclosed_fallback(
        rows,
        minimum_success_rate=minimum_success_rate,
    )
    return {
        "schema": "resume_validation.validation_checkpoint_selection.v1",
        "method": method,
        "seed": seed,
        "validation_manifest": fsm_summary["validation_manifest"],
        "validation_manifest_sha256": manifest_hash,
        "minimum_success_rate": minimum_success_rate,
        "minimum_success_rate_source": "frozen FSM validation summary",
        "selection_status": status,
        "passed_validation_gate": status == "ELIGIBLE",
        "selected_checkpoint": selected["checkpoint"],
        "selected_checkpoint_sha256": selected["checkpoint_sha256"],
        "selected_metrics": {
            name: selected.get(name)
            for name in (
                "success_rate",
                "mean_min_margin_m",
                "pitch_rate_rms_rad_s",
                "slip_distance_m",
                "saturation_rate",
                "safety_violations",
            )
        },
        "candidate_count": len(rows),
        "candidates": rows,
        "selection_rule": SELECTION_RULE,
    }


def _main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--controller", choices=("fsm", "B", "C"), required=True)
    summarize.add_argument("--seed", type=int)
    summarize.add_argument("--checkpoint", type=Path)
    summarize.add_argument("--validation_manifest", type=Path, required=True)
    summarize.add_argument("--evaluations", nargs=3, type=Path, required=True)
    summarize.add_argument("--output", type=Path, required=True)

    select = subparsers.add_parser("select")
    select.add_argument("--method", choices=("B", "C"), required=True)
    select.add_argument("--seed", type=int, choices=(11, 29, 47), required=True)
    select.add_argument("--fsm_summary", type=Path, required=True)
    select.add_argument("--candidate_summaries", nargs="+", type=Path, required=True)
    select.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "summarize":
        payload = build_validation_summary(
            controller=args.controller,
            seed=args.seed,
            checkpoint_path=args.checkpoint,
            evaluation_paths=args.evaluations,
            validation_manifest_path=args.validation_manifest,
        )
    else:
        payload = select_seed_checkpoint(
            method=args.method,
            seed=args.seed,
            fsm_summary=_load_json(args.fsm_summary),
            candidate_summaries=[
                _load_json(path) for path in args.candidate_summaries
            ],
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite evidence: {args.output}")
    write_json(args.output, payload)
    print(json.dumps({"output": str(args.output.resolve()), "schema": payload["schema"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
