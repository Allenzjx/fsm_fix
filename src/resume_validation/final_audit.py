"""Independent final delivery audit over frozen raw and published evidence."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .locked_test_guard import audit_locked_campaign
from .method_freeze import verify_method_freeze
from .report_generator import (
    METHOD_REPORT_KEYS,
    _aggregate_rows,
    _campaign_rows,
    _claims,
    _comparison_summary,
    _method_summary,
)
from .source_audit import sha256_file

REQUIRED_REPORTS = (
    "locked_test_report.md",
    "claims_audit.md",
    "final_resume_wording_zh.md",
    "resume_metrics.json",
    "failure_analysis.md",
    "unit_test_results.xml",
)
REQUIRED_TABLES = (
    "method_comparison.csv",
    "per_height_comparison.csv",
    "per_seed_results.csv",
    "paired_differences.csv",
    "failure_reasons.csv",
    "scenario_results.csv",
)
REQUIRED_PLOTS = (
    "training_return.png",
    "validation_success.png",
    "success_by_height.png",
    "margin_by_method.png",
    "pitch_rate_by_method.png",
    "action_saturation.png",
    "paired_margin_delta.png",
    "paired_pitch_delta.png",
    "failure_distribution.png",
)
METHOD_KEYS = {
    "fsm": "fsm",
    "residual_ppo_without_com": "B",
    "residual_ppo_with_com": "C",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _check_file(
    path: Path,
    failures: list[str],
    *,
    minimum_bytes: int = 1,
) -> None:
    if not path.is_file():
        failures.append(f"missing required file: {path}")
    elif path.stat().st_size < minimum_bytes:
        failures.append(f"required file is too small: {path}")


def _recompute_numeric_evidence(
    project_root: Path,
    locked_run_root: Path,
) -> dict[str, Any]:
    data = _campaign_rows(locked_run_root)
    method_summaries = {
        method: _method_summary(_aggregate_rows(data, method))
        for method in ("fsm", "B", "C")
    }
    comparisons = {
        "C_vs_A": _comparison_summary(data, "fsm", "C"),
        "C_vs_B": _comparison_summary(data, "B", "C"),
        "B_vs_A": _comparison_summary(data, "fsm", "B"),
    }
    claims_protocol = _load_json(
        project_root / "configs" / "claims_audit_protocol.json"
    )
    claim_details = _claims(
        claims_protocol,
        method_summaries,
        comparisons["C_vs_A"],
    )
    fsm = method_summaries["fsm"]
    ppo = method_summaries["C"]
    c_vs_a = comparisons["C_vs_A"]
    margin_delta = c_vs_a["metrics"][
        "min_longitudinal_support_margin_m"
    ]["equal_height_mean_delta"]
    pitch_delta = c_vs_a["metrics"]["pitch_rate_rms_rad_s"][
        "equal_height_mean_delta"
    ]
    aggregate = {
        "fsm_success_count": fsm["success_count"],
        "fsm_episode_count": fsm["episode_count"],
        "fsm_success_rate": fsm["success_rate"],
        "ppo_success_count": ppo["success_count"],
        "ppo_episode_count": ppo["episode_count"],
        "ppo_success_rate": ppo["success_rate"],
        "success_rate_delta_pp": (
            ppo["success_rate"] - fsm["success_rate"]
        )
        * 100.0,
        "fsm_mean_min_margin_mm": (
            fsm["minimum_margin_all"]["equal_height_mean"] * 1000.0
            if fsm["minimum_margin_all"]["equal_height_mean"] is not None
            else None
        ),
        "ppo_mean_min_margin_mm": (
            ppo["minimum_margin_all"]["equal_height_mean"] * 1000.0
            if ppo["minimum_margin_all"]["equal_height_mean"] is not None
            else None
        ),
        "margin_improvement_mm": (
            margin_delta * 1000.0 if margin_delta is not None else None
        ),
        "fsm_pitch_rate_rms": fsm["pitch_rate_rms_all"][
            "equal_height_mean"
        ],
        "ppo_pitch_rate_rms": ppo["pitch_rate_rms_all"][
            "equal_height_mean"
        ],
        "pitch_rate_absolute_delta_rad_s": pitch_delta,
        "pitch_rate_reduction_percent": claim_details[
            "pitch_rate_minus_31pct"
        ]["actual_reduction_percent"],
    }
    confidence_intervals = {
        "fsm_success_wilson_95": fsm["success_wilson_95_ci"],
        "ppo_success_wilson_95": ppo["success_wilson_95_ci"],
        "paired_success_delta_bootstrap_95": c_vs_a["metrics"]["success"][
            "stratified_bootstrap_95_ci"
        ],
        "paired_margin_delta_bootstrap_95_m": c_vs_a["metrics"][
            "min_longitudinal_support_margin_m"
        ]["stratified_bootstrap_95_ci"],
        "paired_pitch_delta_bootstrap_95_rad_s": c_vs_a["metrics"][
            "pitch_rate_rms_rad_s"
        ]["stratified_bootstrap_95_ci"],
    }
    return {
        "methods": {
            METHOD_REPORT_KEYS[method]: method_summaries[method]
            for method in ("fsm", "B", "C")
        },
        "aggregate": aggregate,
        "confidence_intervals": confidence_intervals,
        "per_height": {
            METHOD_REPORT_KEYS[method]: method_summaries[method]["per_height"]
            for method in ("fsm", "B", "C")
        },
        "ablation": comparisons["C_vs_B"],
        "comparisons": comparisons,
        "claims": {
            key: value["status"] for key, value in claim_details.items()
        },
        "claim_details": claim_details,
    }


def run_final_audit(
    *,
    project_root: Path,
    freeze_path: Path,
    authorization_path: Path,
    locked_run_root: Path,
    recorded_audit_path: Path,
    video_inventory_path: Path,
    reports_root: Path,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    freeze_path = freeze_path.resolve()
    reports_root = reports_root.resolve()
    failures: list[str] = []
    disclosures: list[str] = []

    freeze = _load_json(freeze_path)
    failures.extend(
        f"method freeze: {failure}"
        for failure in verify_method_freeze(freeze)
    )
    fresh_locked_audit = audit_locked_campaign(
        freeze_path=freeze_path,
        authorization_path=authorization_path,
        run_root=locked_run_root,
    )
    recorded_locked_audit = _load_json(recorded_audit_path)
    for key in (
        "method_freeze_sha256",
        "locked_manifest_sha256",
        "evaluation_count",
        "episode_count",
        "paired_scenario_coverage_complete",
    ):
        if fresh_locked_audit.get(key) != recorded_locked_audit.get(key):
            failures.append(f"locked audit mismatch: {key}")
    if (
        fresh_locked_audit["evaluation_count"] != 21
        or fresh_locked_audit["episode_count"] != 2100
        or not fresh_locked_audit["paired_scenario_coverage_complete"]
    ):
        failures.append("locked campaign is not exactly 21 evaluations / 2100 episodes")
    for evidence in fresh_locked_audit["evidence"]:
        path = Path(evidence["path"])
        if not path.is_file() or sha256_file(path) != evidence["sha256"]:
            failures.append(f"locked evidence hash drift: {path}")

    for name in REQUIRED_REPORTS:
        _check_file(reports_root / name, failures)
    for name in REQUIRED_TABLES:
        _check_file(reports_root / "tables" / name, failures)
    for name in REQUIRED_PLOTS:
        path = reports_root / "plots" / name
        _check_file(path, failures, minimum_bytes=1024)
        if path.is_file() and not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            failures.append(f"plot is not a PNG: {path}")

    video_inventory_path = video_inventory_path.resolve()
    video_inventory = _load_json(video_inventory_path)
    metrics_path = reports_root / "resume_metrics.json"
    metrics = _load_json(metrics_path) if metrics_path.is_file() else {}
    if metrics:
        recomputed = _recompute_numeric_evidence(
            project_root,
            locked_run_root.resolve(),
        )
        for key, expected in recomputed.items():
            if metrics.get(key) != expected:
                failures.append(
                    f"resume metrics raw recomputation mismatch: {key}"
                )
        if metrics.get("method_freeze_sha256") != sha256_file(freeze_path):
            failures.append("resume metrics method-freeze hash mismatch")
        if metrics.get("locked_test_manifest_sha256") != fresh_locked_audit[
            "locked_manifest_sha256"
        ]:
            failures.append("resume metrics locked-manifest hash mismatch")
        unit_audit = metrics.get("unit_test_audit", {})
        unit_path = Path(str(unit_audit.get("path", "")))
        if (
            unit_path.resolve() != (reports_root / "unit_test_results.xml")
            or not unit_path.is_file()
            or sha256_file(unit_path) != unit_audit.get("sha256")
            or int(unit_audit.get("tests", 0)) < 1
            or int(unit_audit.get("failures", -1)) != 0
            or int(unit_audit.get("errors", -1)) != 0
        ):
            failures.append("resume metrics unit-test audit is invalid")
        report_source = (
            project_root / "src" / "resume_validation" / "report_generator.py"
        )
        if metrics.get("report_generator_sha256") != sha256_file(report_source):
            failures.append("resume metrics report-generator hash mismatch")
        video_audit = metrics.get("video_evidence", {})
        video_audit_path = Path(str(video_audit.get("inventory", "")))
        if (
            video_audit_path.resolve() != video_inventory_path.resolve()
            or not video_audit_path.is_file()
            or sha256_file(video_audit_path)
            != video_audit.get("inventory_sha256")
            or int(video_audit.get("video_count", -1))
            != int(video_inventory.get("video_count", -2))
            or bool(video_audit.get("all_replay_outcomes_reproduced", False))
            != bool(
                video_inventory.get(
                    "all_replay_outcomes_reproduced",
                    False,
                )
            )
        ):
            failures.append("resume metrics video-evidence audit is invalid")
        method_counts = {
            "fsm": 300,
            "residual_ppo_without_com": 900,
            "residual_ppo_with_com": 900,
        }
        for method, expected in method_counts.items():
            actual = int(
                metrics.get("methods", {})
                .get(method, {})
                .get("episode_count", -1)
            )
            if actual != expected:
                failures.append(
                    f"resume metrics episode count mismatch: {method}={actual}"
                )
        claims = metrics.get("claims", {})
        for name, status in sorted(claims.items()):
            if status not in {"VERIFIED", "PARTIALLY_VERIFIED", "NOT_VERIFIED"}:
                failures.append(f"invalid claim status: {name}={status}")
            elif status != "VERIFIED":
                disclosures.append(f"numeric claim {name}: {status}")
        for selection in metrics.get("selection_disclosure", []):
            if not bool(selection.get("passed_validation_gate", False)):
                disclosures.append(
                    "validation fallback: "
                    f"{selection.get('method')}/seed{selection.get('seed')}/"
                    f"{selection.get('status')}"
                )
        if (
            metrics.get("technical_claims_verified", False)
            and not metrics.get("technical_freeze_coverage", {}).get(
                "verified",
                False,
            )
        ):
            failures.append(
                "technical claims are marked verified without complete "
                "frozen-source/evidence coverage"
            )

    scenario_path = reports_root / "tables" / "scenario_results.csv"
    if scenario_path.is_file():
        rows = _csv_rows(scenario_path)
        if len(rows) != 2100:
            failures.append(
                f"scenario_results.csv must have 2100 rows, got {len(rows)}"
            )
        method_counts = Counter(row.get("method", "") for row in rows)
        if method_counts != Counter(
            {
                "fsm": 300,
                "residual_ppo_without_com": 900,
                "residual_ppo_with_com": 900,
            }
        ):
            failures.append(
                f"scenario-results method coverage mismatch: {dict(method_counts)}"
            )
        keys = [
            (
                row.get("method"),
                row.get("training_seed"),
                row.get("height_mm"),
                row.get("scenario_id"),
            )
            for row in rows
        ]
        if len(set(keys)) != len(keys):
            failures.append("scenario_results.csv contains duplicate paired keys")
        for method_name in (
            "residual_ppo_without_com",
            "residual_ppo_with_com",
        ):
            seeds = {
                int(row["training_seed"])
                for row in rows
                if row.get("method") == method_name
            }
            if seeds != {11, 29, 47}:
                failures.append(
                    f"scenario-results seed coverage mismatch: {method_name}={seeds}"
                )

    expected_table_rows = {
        "method_comparison.csv": 3,
        "per_height_comparison.csv": 9,
        "per_seed_results.csv": 7,
        "paired_differences.csv": 18,
        "scenario_results.csv": 2100,
    }
    for name, expected in expected_table_rows.items():
        path = reports_root / "tables" / name
        if path.is_file() and len(_csv_rows(path)) != expected:
            failures.append(
                f"table row count mismatch: {name} "
                f"{len(_csv_rows(path))} != {expected}"
            )

    if video_inventory.get("schema") != "resume_validation.video_inventory.v1":
        failures.append("video inventory schema is invalid")
    videos = video_inventory.get("videos", [])
    if int(video_inventory.get("video_count", -1)) != len(videos) or not videos:
        failures.append("video inventory count is invalid")

    selection_path = Path(str(video_inventory.get("selection", "")))
    selection: dict[str, Any] = {}
    if (
        not selection_path.is_file()
        or sha256_file(selection_path)
        != video_inventory.get("selection_sha256")
    ):
        failures.append("video selection evidence is missing or hash-drifted")
    else:
        selection = _load_json(selection_path)
        if (
            selection.get("schema") != "resume_validation.video_selection.v1"
            or selection.get("method_freeze_sha256") != sha256_file(freeze_path)
            or selection.get("locked_manifest_sha256")
            != fresh_locked_audit["locked_manifest_sha256"]
            or int(selection.get("locked_episode_count_considered", -1))
            != 2100
        ):
            failures.append("video selection provenance is invalid")
        if len(selection.get("group_category_requirements", [])) != 9:
            failures.append("video selection lacks nine group requirements")
        if len(selection.get("selections", [])) != len(videos):
            failures.append("video selection/inventory row counts differ")

    categories_seen: dict[tuple[str, int], set[str]] = {}
    selection_rows = selection.get("selections", [])
    for index, row in enumerate(videos):
        video = Path(str(row.get("video", "")))
        if (
            not video.is_file()
            or video.stat().st_size <= 0
            or sha256_file(video) != row.get("video_sha256")
            or int(row.get("video_frame_count", 0)) < 1
        ):
            failures.append(f"video evidence is invalid: {video}")
        video_probe = row.get("video_decode_probe", {})
        try:
            probe_valid = (
                video_probe.get("decoded") is True
                and int(video_probe.get("width", -1)) == 960
                and int(video_probe.get("height", -1)) == 540
                and abs(float(video_probe.get("fps", -1.0)) - 20.0)
                <= 0.05
                and int(video_probe.get("decoded_frame_count", -1))
                == int(row.get("video_frame_count", -2))
            )
        except (TypeError, ValueError):
            probe_valid = False
        if not probe_valid:
            failures.append(f"video decode probe is invalid: {video}")
        if index < len(selection_rows):
            selected = selection_rows[index]
            for key in (
                "method",
                "height_mm",
                "training_seed",
                "scenario_id",
                "locked_success",
                "categories",
                "locked_result_sha256",
                "locked_episodes_sha256",
                "checkpoint_sha256",
            ):
                if row.get(key) != selected.get(key):
                    failures.append(
                        f"video inventory/selection mismatch at row {index}: {key}"
                    )
        method = str(row.get("method", ""))
        try:
            height = int(row.get("height_mm", -1))
        except (TypeError, ValueError):
            height = -1
        categories_seen.setdefault((method, height), set()).update(
            str(category) for category in row.get("categories", [])
        )
        for path_key, hash_key in (
            ("locked_result", "locked_result_sha256"),
            ("locked_episodes", "locked_episodes_sha256"),
            ("replay_result", "replay_result_sha256"),
        ):
            evidence_path = Path(str(row.get(path_key, "")))
            if (
                not evidence_path.is_file()
                or sha256_file(evidence_path) != row.get(hash_key)
            ):
                failures.append(
                    f"video source evidence is invalid: {path_key}={evidence_path}"
                )
        checkpoint_value = row.get("checkpoint")
        if checkpoint_value is not None:
            checkpoint = Path(str(checkpoint_value))
            if (
                not checkpoint.is_file()
                or sha256_file(checkpoint) != row.get("checkpoint_sha256")
            ):
                failures.append(
                    f"video checkpoint evidence is invalid: {checkpoint}"
                )

    for requirement in selection.get("group_category_requirements", []):
        try:
            key = (
                str(requirement["method"]),
                int(requirement["height_mm"]),
            )
            required = {
                str(category)
                for category in requirement["required_categories"]
            }
        except (KeyError, TypeError, ValueError):
            failures.append("video group requirement is malformed")
            continue
        if not required <= categories_seen.get(key, set()):
            failures.append(
                f"video categories are incomplete: {key} "
                f"required={sorted(required)} "
                f"actual={sorted(categories_seen.get(key, set()))}"
            )
    if not video_inventory.get("all_replay_outcomes_reproduced", False):
        disclosures.append(
            "one or more deterministic video replays did not reproduce the "
            "recorded locked outcome"
        )

    ledger_path = project_root / "experiment_ledger.csv"
    experiment_record_count = 0
    if not ledger_path.is_file():
        failures.append("experiment ledger is missing")
    else:
        with ledger_path.open("r", encoding="utf-8-sig", newline="") as stream:
            ledger_rows = list(csv.reader(stream))
        if not ledger_rows:
            failures.append("experiment ledger is empty")
        else:
            expected_columns = len(ledger_rows[0])
            header = ledger_rows[0]
            if expected_columns != 14:
                failures.append(
                    f"experiment ledger header has {expected_columns} columns"
                )
            for line_number, row in enumerate(ledger_rows[1:], start=2):
                if len(row) != expected_columns:
                    failures.append(
                        f"experiment ledger row {line_number} has "
                        f"{len(row)} columns"
                    )
                    continue
                record = dict(zip(header, row))
                for required_field in (
                    "experiment_id",
                    "stage",
                    "method",
                    "hypothesis",
                    "changed_parameters",
                    "unchanged_controls",
                    "expected_effect",
                    "actual_effect",
                    "result",
                    "next_action",
                    "artifact_path",
                ):
                    if not record.get(required_field, "").strip():
                        failures.append(
                            f"experiment ledger row {line_number} has empty "
                            f"{required_field}"
                        )
                artifact = Path(row[-1])
                if not artifact.exists():
                    failures.append(
                        f"experiment ledger artifact is missing at row "
                        f"{line_number}: {artifact}"
                    )
            experiment_record_count = len(ledger_rows) - 1

    wording_path = reports_root / "final_resume_wording_zh.md"
    if wording_path.is_file():
        wording = wording_path.read_text(encoding="utf-8")
        placeholders = ("[实际", "TODO", "TBD", "PLACEHOLDER")
        if any(token in wording for token in placeholders):
            failures.append("final resume wording contains a placeholder")
        if metrics.get("technical_claims_verified", False):
            if "点估计" not in wording or "纵向准静态" not in wording:
                failures.append(
                    "final resume wording lacks required caveat language"
                )
        elif "不得用于简历" not in wording:
            failures.append(
                "unverified technical evidence was not removed from resume wording"
            )
        else:
            disclosures.append(
                "technical implementation/comparison claims were removed from "
                "resume wording because their evidence was not fully verified"
            )

    claims_path = reports_root / "claims_audit.md"
    if claims_path.is_file() and metrics:
        claims_text = claims_path.read_text(encoding="utf-8")
        for status in metrics.get("claims", {}).values():
            if f"**{status}**" not in claims_text:
                failures.append(
                    f"claims_audit.md omits recorded status: {status}"
                )

    status = (
        "FAILED"
        if failures
        else ("PASS_WITH_DISCLOSURES" if disclosures else "PASS")
    )
    published_paths = [
        *(reports_root / name for name in REQUIRED_REPORTS),
        *(reports_root / "tables" / name for name in REQUIRED_TABLES),
        *(reports_root / "plots" / name for name in REQUIRED_PLOTS),
        video_inventory_path.resolve(),
        recorded_audit_path.resolve(),
        ledger_path,
    ]
    published_files = [
        {
            "path": str(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in published_paths
        if path.is_file()
    ]
    return {
        "schema": "resume_validation.final_delivery_audit.v1",
        "status": status,
        "failures": failures,
        "disclosures": sorted(set(disclosures)),
        "method_freeze": str(freeze_path),
        "method_freeze_sha256": sha256_file(freeze_path),
        "final_audit_source_sha256": sha256_file(Path(__file__)),
        "locked_evaluation_count": fresh_locked_audit["evaluation_count"],
        "locked_episode_count": fresh_locked_audit["episode_count"],
        "locked_evidence_file_count": len(fresh_locked_audit["evidence"]),
        "required_report_count": len(REQUIRED_REPORTS),
        "required_table_count": len(REQUIRED_TABLES),
        "required_plot_count": len(REQUIRED_PLOTS),
        "video_count": len(videos),
        "experiment_record_count": experiment_record_count,
        "claim_statuses": metrics.get("claims", {}),
        "selection_disclosure": metrics.get("selection_disclosure", []),
        "published_files": published_files,
    }


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--locked_run_root", type=Path, required=True)
    parser.add_argument("--recorded_audit", type=Path, required=True)
    parser.add_argument("--video_inventory", type=Path, required=True)
    parser.add_argument("--reports_root", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, required=True)
    parser.add_argument("--output_markdown", type=Path, required=True)
    args = parser.parse_args()
    if args.output_json.exists() or args.output_markdown.exists():
        raise FileExistsError("Refusing to overwrite final-delivery audit")
    result = run_final_audit(
        project_root=args.project_root,
        freeze_path=args.freeze,
        authorization_path=args.authorization,
        locked_run_root=args.locked_run_root,
        recorded_audit_path=args.recorded_audit,
        video_inventory_path=args.video_inventory,
        reports_root=args.reports_root,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Final delivery audit",
        "",
        f"- Status: **{result['status']}**",
        f"- Locked evaluations: {result['locked_evaluation_count']}",
        f"- Locked episodes: {result['locked_episode_count']}",
        f"- Videos: {result['video_count']}",
        f"- Method freeze SHA256: `{result['method_freeze_sha256']}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend(
        [f"- {failure}" for failure in result["failures"]]
        or ["- None."]
    )
    lines.extend(["", "## Required disclosures", ""])
    lines.extend(
        [f"- {item}" for item in result["disclosures"]]
        or ["- None."]
    )
    args.output_markdown.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["status"] == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(_main())
