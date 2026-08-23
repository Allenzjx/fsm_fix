"""Generate locked-test tables, plots, claims audit, and resume wording."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .aggregate_results import episode_height_mm, summarize_episode_rows
from .config_io import differing_leaf_paths, load_config, write_json
from .locked_test_guard import audit_locked_campaign
from .method_freeze import verify_method_freeze
from .source_audit import sha256_file
from .statistics import (
    describe,
    stratified_bootstrap_mean_ci,
    wilson_interval,
)

HEIGHTS = (50, 75, 100)
SEEDS = (11, 29, 47)
METHOD_LABELS = {
    "fsm": "FSM-only",
    "B": "FSM + residual PPO without CoM reward",
    "C": "FSM + CoM-guided residual PPO",
}
METHOD_REPORT_KEYS = {
    "fsm": "fsm",
    "B": "residual_ppo_without_com",
    "C": "residual_ppo_with_com",
}
SECONDARY_METRICS = {
    "negative_margin_duration_s": "negative_margin_duration",
    "max_abs_pitch_rad": "maximum_absolute_pitch",
    "pitch_rms_rad": "pitch_rms",
    "peak_abs_pitch_rate_rad_s": "peak_pitch_rate",
    "traversal_time_s": "traversal_time",
    "wheel_slip_distance_m": "wheel_slip_distance",
    "wheel_slip_ratio": "wheel_slip_ratio",
    "residual_saturation_rate": "residual_saturation",
    "wheel_speed_saturation_rate": "wheel_speed_saturation",
    "executed_residual_command_variation_l2": "control_command_variation",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_evaluation_rows(result_path: Path) -> list[dict[str, Any]]:
    result = _load_json(result_path)
    episodes = Path(result["artifacts"]["episodes"])
    if sha256_file(episodes) != result["artifacts"]["episodes_sha256"]:
        raise ValueError(f"Episode hash drift during report generation: {episodes}")
    return _load_jsonl(episodes)


def _campaign_rows(run_root: Path) -> dict[tuple[str, int | None], list[dict[str, Any]]]:
    data: dict[tuple[str, int | None], list[dict[str, Any]]] = {}
    fsm_rows: list[dict[str, Any]] = []
    for height in HEIGHTS:
        fsm_rows.extend(
            _read_evaluation_rows(
                run_root / "fsm" / f"height-{height}mm" / "result.json"
            )
        )
    data[("fsm", None)] = [
        {**row, "training_seed": None, "method": "fsm"} for row in fsm_rows
    ]
    for method in ("B", "C"):
        for seed in SEEDS:
            rows: list[dict[str, Any]] = []
            for height in HEIGHTS:
                rows.extend(
                    _read_evaluation_rows(
                        run_root
                        / f"method-{method}"
                        / f"seed-{seed}"
                        / f"height-{height}mm"
                        / "result.json"
                    )
                )
            data[(method, seed)] = [
                {**row, "training_seed": seed, "method": method} for row in rows
            ]
    return data


def _aggregate_rows(
    data: dict[tuple[str, int | None], list[dict[str, Any]]],
    method: str,
) -> list[dict[str, Any]]:
    if method == "fsm":
        return list(data[("fsm", None)])
    return [
        row
        for seed in SEEDS
        for row in data[(method, seed)]
    ]


def _stratified_metric(
    rows: Iterable[dict[str, Any]],
    field: str,
    *,
    successful_only: bool = False,
) -> dict[str, Any]:
    by_height: dict[int, list[float]] = defaultdict(list)
    missing_by_height: Counter[int] = Counter()
    for row in rows:
        height = episode_height_mm(row)
        if successful_only and not bool(row["success"]):
            continue
        value = row.get(field)
        if value is None:
            missing_by_height[height] += 1
            continue
        numeric = float(value)
        if not math.isfinite(numeric):
            missing_by_height[height] += 1
            continue
        by_height[height].append(numeric)
    if any(not by_height[height] for height in HEIGHTS):
        return {
            "count": sum(len(values) for values in by_height.values()),
            "missing_by_height": {
                str(height): missing_by_height[height] for height in HEIGHTS
            },
            "equal_height_mean": None,
            "stratified_bootstrap_95_ci": None,
        }
    values = [value for height in HEIGHTS for value in by_height[height]]
    return {
        **describe(values),
        "missing_by_height": {
            str(height): missing_by_height[height] for height in HEIGHTS
        },
        "equal_height_mean": mean(mean(by_height[height]) for height in HEIGHTS),
        "stratified_bootstrap_95_ci": list(
            stratified_bootstrap_mean_ci(
                {height: by_height[height] for height in HEIGHTS},
                draws=10_000,
                seed=20260729,
            )
        ),
    }


def _method_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = summarize_episode_rows(rows)
    success_count = sum(bool(row["success"]) for row in rows)
    total = len(rows)
    result = {
        "episode_count": total,
        "success_count": success_count,
        "success_rate": success_count / total,
        "success_wilson_95_ci": list(wilson_interval(success_count, total)),
        "equal_height_weighted_success_rate": primary["aggregate"][
            "equal_height_weighted_success_rate"
        ],
        "minimum_margin_all": _stratified_metric(
            rows, "min_longitudinal_support_margin_m"
        ),
        "minimum_margin_successful_only": _stratified_metric(
            rows,
            "min_longitudinal_support_margin_m",
            successful_only=True,
        ),
        "pitch_rate_rms_all": _stratified_metric(
            rows, "pitch_rate_rms_rad_s"
        ),
        "pitch_rate_rms_successful_only": _stratified_metric(
            rows,
            "pitch_rate_rms_rad_s",
            successful_only=True,
        ),
        "wheel_slip_distance_all": _stratified_metric(
            rows, "wheel_slip_distance_m"
        ),
        "residual_saturation_all": _stratified_metric(
            rows, "residual_saturation_rate"
        ),
        "failure_counts": dict(
            sorted(
                Counter(
                    str(row["failure_reason"])
                    for row in rows
                    if row.get("failure_reason")
                ).items()
            )
        ),
        "per_height": primary["per_height"],
    }
    result["secondary_metrics_all"] = {
        report_name: _stratified_metric(rows, field)
        for field, report_name in SECONDARY_METRICS.items()
    }
    result["body_collision_rate"] = (
        sum(
            str(row.get("failure_reason", "")) == "BODY_OR_LINK_COLLISION"
            for row in rows
        )
        / total
    )
    result["joint_limit_rate"] = (
        sum(
            str(row.get("failure_reason", "")) == "JOINT_LIMIT"
            or bool(row.get("terminal_joint_limit_diagnostic", {}))
            for row in rows
        )
        / total
    )
    return result


def _paired_rows(
    data: dict[tuple[str, int | None], list[dict[str, Any]]],
    baseline: str,
    candidate: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    if baseline == "fsm":
        baseline_by_id = {
            str(row["scenario_id"]): row for row in data[("fsm", None)]
        }
        for seed in SEEDS:
            for candidate_row in data[(candidate, seed)]:
                pairs.append(
                    (
                        baseline_by_id[str(candidate_row["scenario_id"])],
                        candidate_row,
                    )
                )
        return pairs
    for seed in SEEDS:
        baseline_by_id = {
            str(row["scenario_id"]): row for row in data[(baseline, seed)]
        }
        candidate_by_id = {
            str(row["scenario_id"]): row for row in data[(candidate, seed)]
        }
        if set(baseline_by_id) != set(candidate_by_id):
            raise ValueError(
                f"Paired method scenario mismatch: {baseline} vs {candidate}, seed {seed}"
            )
        for scenario_id in sorted(baseline_by_id):
            pairs.append(
                (baseline_by_id[scenario_id], candidate_by_id[scenario_id])
            )
    return pairs


def _paired_metric(
    pairs: Iterable[tuple[dict[str, Any], dict[str, Any]]],
    field: str,
    *,
    successful_only: bool = False,
) -> dict[str, Any]:
    deltas_by_height: dict[int, list[float]] = defaultdict(list)
    missing: list[str] = []
    for baseline, candidate in pairs:
        seed = candidate.get("training_seed")
        scenario = str(candidate["scenario_id"])
        if successful_only and not (
            bool(baseline["success"]) and bool(candidate["success"])
        ):
            continue
        left = baseline.get(field)
        right = candidate.get(field)
        if left is None or right is None:
            missing.append(f"{seed}:{scenario}")
            continue
        left_value = float(left)
        right_value = float(right)
        if not math.isfinite(left_value) or not math.isfinite(right_value):
            missing.append(f"{seed}:{scenario}")
            continue
        deltas_by_height[episode_height_mm(candidate)].append(
            right_value - left_value
        )
    pair_count = sum(len(values) for values in deltas_by_height.values())
    if any(not deltas_by_height[height] for height in HEIGHTS):
        return {
            "metric": field,
            "scope": "both_successful" if successful_only else "all_complete_pairs",
            "pair_count": pair_count,
            "missing_pair_count": len(missing),
            "missing_pair_ids": missing,
            "equal_height_mean_delta": None,
            "stratified_bootstrap_95_ci": None,
        }
    all_deltas = [
        value for height in HEIGHTS for value in deltas_by_height[height]
    ]
    return {
        "metric": field,
        "scope": "both_successful" if successful_only else "all_complete_pairs",
        "pair_count": pair_count,
        "missing_pair_count": len(missing),
        "missing_pair_ids": missing,
        "delta_distribution": describe(all_deltas),
        "per_height_mean_delta": {
            str(height): mean(deltas_by_height[height]) for height in HEIGHTS
        },
        "equal_height_mean_delta": mean(
            mean(deltas_by_height[height]) for height in HEIGHTS
        ),
        "stratified_bootstrap_95_ci": list(
            stratified_bootstrap_mean_ci(
                {height: deltas_by_height[height] for height in HEIGHTS},
                draws=10_000,
                seed=20260729,
            )
        ),
        "deltas": all_deltas,
    }


def _comparison_summary(
    data: dict[tuple[str, int | None], list[dict[str, Any]]],
    baseline: str,
    candidate: str,
) -> dict[str, Any]:
    pairs = _paired_rows(data, baseline, candidate)
    metrics: dict[str, Any] = {}
    for field in (
        "success",
        "min_longitudinal_support_margin_m",
        "pitch_rate_rms_rad_s",
    ):
        metrics[field] = _paired_metric(pairs, field)
        metrics[f"{field}_successful_only"] = _paired_metric(
            pairs, field, successful_only=True
        )
    return {
        "baseline": baseline,
        "candidate": candidate,
        "pair_count": len(pairs),
        "metrics": metrics,
    }


def _claim_status(
    *,
    exact: bool,
    direction_supported: bool,
) -> str:
    if exact and direction_supported:
        return "VERIFIED"
    if direction_supported:
        return "PARTIALLY_VERIFIED"
    return "NOT_VERIFIED"


def _resume_interpretation(
    *,
    success_delta_pp: float,
    success_direction_supported: bool,
    margin_direction_supported: bool,
    pitch_direction_supported: bool,
) -> tuple[str, str]:
    stability_supported = (
        margin_direction_supported and pitch_direction_supported
    )
    if (
        success_delta_pp > 2.0
        and success_direction_supported
        and stability_supported
    ):
        return (
            "JOINT_SUCCESS_AND_STABILITY_IMPROVEMENT",
            "配对置信区间支持成功率与两项平稳性指标共同改善",
        )
    if abs(success_delta_pp) <= 2.0 and stability_supported:
        return (
            "STABILITY_IMPROVEMENT_AT_SIMILAR_SUCCESS",
            "成功率点估计保持相近，配对置信区间支持两项平稳性指标改善",
        )
    if success_delta_pp < -2.0 and stability_supported:
        return (
            "SUCCESS_STABILITY_TRADEOFF",
            "成功率点估计下降而两项平稳性指标获配对置信区间支持，体现成功率与平稳性之间的权衡",
        )
    if success_delta_pp > 2.0 and stability_supported:
        return (
            "SUCCESS_POINT_ESTIMATE_UP_STABILITY_SUPPORTED",
            "成功率点估计上升但其配对置信区间未排除零；两项平稳性改善获配对置信区间支持",
        )
    return (
        "COMBINED_IMPROVEMENT_NOT_SUPPORTED",
        "当前配对置信区间未同时支持成功率与两项平稳性共同改善，未观察到获统计支持的稳定改善",
    )


def _claims(
    protocol: dict[str, Any],
    method_summaries: dict[str, dict[str, Any]],
    c_vs_a: dict[str, Any],
) -> dict[str, Any]:
    fsm = method_summaries["fsm"]
    ppo = method_summaries["C"]
    success_metric = c_vs_a["metrics"]["success"]
    success_ci = success_metric["stratified_bootstrap_95_ci"]
    success_cfg = protocol["success_claim"]
    success_exact = (
        abs(fsm["success_rate"] - float(success_cfg["baseline_target_rate"]))
        <= float(success_cfg["absolute_rate_tolerance"])
        and abs(ppo["success_rate"] - float(success_cfg["ppo_target_rate"]))
        <= float(success_cfg["absolute_rate_tolerance"])
    )
    success_direction = success_ci is not None and success_ci[0] > 0.0

    margin_metric = c_vs_a["metrics"][
        "min_longitudinal_support_margin_m"
    ]
    margin_delta_mm = (
        margin_metric["equal_height_mean_delta"] * 1000.0
        if margin_metric["equal_height_mean_delta"] is not None
        else None
    )
    margin_ci = margin_metric["stratified_bootstrap_95_ci"]
    margin_cfg = protocol["margin_claim"]
    margin_exact = (
        margin_delta_mm is not None
        and abs(
            margin_delta_mm - float(margin_cfg["target_improvement_mm"])
        )
        <= float(margin_cfg["absolute_tolerance_mm"])
    )
    margin_direction = margin_ci is not None and margin_ci[0] > 0.0

    fsm_pitch = fsm["pitch_rate_rms_all"]["equal_height_mean"]
    ppo_pitch = ppo["pitch_rate_rms_all"]["equal_height_mean"]
    pitch_cfg = protocol["pitch_claim"]
    near_zero = float(pitch_cfg["near_zero_baseline_threshold_rad_s"])
    pitch_reduction = (
        (fsm_pitch - ppo_pitch) / fsm_pitch * 100.0
        if (
            fsm_pitch is not None
            and ppo_pitch is not None
            and abs(fsm_pitch) >= near_zero
        )
        else None
    )
    pitch_metric = c_vs_a["metrics"]["pitch_rate_rms_rad_s"]
    pitch_ci = pitch_metric["stratified_bootstrap_95_ci"]
    pitch_exact = (
        pitch_reduction is not None
        and abs(
            pitch_reduction - float(pitch_cfg["target_reduction_percent"])
        )
        <= float(pitch_cfg["absolute_tolerance_percentage_points"])
    )
    pitch_direction = pitch_ci is not None and pitch_ci[1] < 0.0
    return {
        "84_to_91_success": {
            "status": _claim_status(
                exact=success_exact,
                direction_supported=success_direction,
            ),
            "actual_fsm_rate": fsm["success_rate"],
            "actual_ppo_rate": ppo["success_rate"],
            "actual_delta_percentage_points": (
                ppo["success_rate"] - fsm["success_rate"]
            )
            * 100.0,
            "paired_delta_95_ci": success_ci,
            "numeric_target_match": success_exact,
            "direction_supported": success_direction,
        },
        "margin_plus_10mm": {
            "status": _claim_status(
                exact=margin_exact,
                direction_supported=margin_direction,
            ),
            "actual_paired_improvement_mm": margin_delta_mm,
            "paired_delta_95_ci_mm": (
                [value * 1000.0 for value in margin_ci]
                if margin_ci is not None
                else None
            ),
            "numeric_target_match": margin_exact,
            "direction_supported": margin_direction,
            "missing_pair_count": margin_metric["missing_pair_count"],
        },
        "pitch_rate_minus_31pct": {
            "status": _claim_status(
                exact=pitch_exact,
                direction_supported=pitch_direction,
            ),
            "actual_reduction_percent": pitch_reduction,
            "fsm_equal_height_mean_rad_s": fsm_pitch,
            "ppo_equal_height_mean_rad_s": ppo_pitch,
            "paired_delta_95_ci_rad_s": pitch_ci,
            "numeric_target_match": pitch_exact,
            "direction_supported": pitch_direction,
        },
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty required table: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _flat_method_row(method: str, summary: dict[str, Any]) -> dict[str, Any]:
    margin = summary["minimum_margin_all"]
    pitch = summary["pitch_rate_rms_all"]
    margin_success = summary["minimum_margin_successful_only"]
    pitch_success = summary["pitch_rate_rms_successful_only"]
    def distribution(prefix: str, values: dict[str, Any]) -> dict[str, Any]:
        interval = values.get("stratified_bootstrap_95_ci")
        return {
            f"{prefix}_count": values.get("count", 0),
            f"{prefix}_raw_mean": values.get("mean"),
            f"{prefix}_equal_height_mean": values.get("equal_height_mean"),
            f"{prefix}_median": values.get("median"),
            f"{prefix}_std_population": values.get("std_population"),
            f"{prefix}_q25": values.get("q25"),
            f"{prefix}_q75": values.get("q75"),
            f"{prefix}_equal_height_bootstrap_95_low": (
                interval[0] if interval else None
            ),
            f"{prefix}_equal_height_bootstrap_95_high": (
                interval[1] if interval else None
            ),
            f"{prefix}_missing_by_height_json": json.dumps(
                values.get("missing_by_height", {}),
                sort_keys=True,
            ),
        }

    row = {
        "method": METHOD_REPORT_KEYS[method],
        "method_label": METHOD_LABELS[method],
        "episode_count": summary["episode_count"],
        "success_count": summary["success_count"],
        "success_rate": summary["success_rate"],
        "success_wilson_95_low": summary["success_wilson_95_ci"][0],
        "success_wilson_95_high": summary["success_wilson_95_ci"][1],
        "all_episode_valid_margin_count": margin["count"],
        "all_episode_mean_min_margin_m": margin["equal_height_mean"],
        "all_episode_margin_bootstrap_95_low_m": (
            margin["stratified_bootstrap_95_ci"][0]
            if margin["stratified_bootstrap_95_ci"]
            else None
        ),
        "all_episode_margin_bootstrap_95_high_m": (
            margin["stratified_bootstrap_95_ci"][1]
            if margin["stratified_bootstrap_95_ci"]
            else None
        ),
        "all_episode_mean_pitch_rate_rms_rad_s": pitch["equal_height_mean"],
        "all_episode_pitch_bootstrap_95_low_rad_s": (
            pitch["stratified_bootstrap_95_ci"][0]
            if pitch["stratified_bootstrap_95_ci"]
            else None
        ),
        "all_episode_pitch_bootstrap_95_high_rad_s": (
            pitch["stratified_bootstrap_95_ci"][1]
            if pitch["stratified_bootstrap_95_ci"]
            else None
        ),
        "successful_only_valid_margin_count": margin_success["count"],
        "successful_only_mean_min_margin_m": margin_success[
            "equal_height_mean"
        ],
        "successful_only_mean_pitch_rate_rms_rad_s": pitch_success[
            "equal_height_mean"
        ],
        "mean_wheel_slip_distance_m": summary["wheel_slip_distance_all"][
            "equal_height_mean"
        ],
        "mean_residual_saturation_rate": summary["residual_saturation_all"][
            "equal_height_mean"
        ],
        "body_collision_rate": summary["body_collision_rate"],
        "joint_limit_rate": summary["joint_limit_rate"],
    }
    row.update(distribution("all_episode_min_margin_m", margin))
    row.update(distribution("all_episode_pitch_rate_rms_rad_s", pitch))
    row.update(
        distribution("successful_only_min_margin_m", margin_success)
    )
    row.update(
        distribution(
            "successful_only_pitch_rate_rms_rad_s",
            pitch_success,
        )
    )
    for name, metric in summary["secondary_metrics_all"].items():
        row.update(distribution(f"secondary_{name}", metric))
    return row


def _write_plots(
    *,
    plot_dir: Path,
    project_root: Path,
    freeze: dict[str, Any],
    data: dict[tuple[str, int | None], list[dict[str, Any]]],
    method_summaries: dict[str, dict[str, Any]],
    comparisons: dict[str, dict[str, Any]],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"fsm": "#4c566a", "B": "#d08770", "C": "#5e81ac"}
    method_order = ("fsm", "B", "C")

    # Real TensorBoard episode-return series from every completed training run.
    from tensorboard.backend.event_processing.event_accumulator import (
        EventAccumulator,
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    return_series = 0
    for run in freeze["all_matching_training_runs"]:
        if run.get("status") != "COMPLETED":
            continue
        run_dir = Path(run["training_result"]).parent
        event_files = sorted(run_dir.glob("events.out.tfevents.*"))
        if not event_files:
            continue
        accumulator = EventAccumulator(
            str(run_dir),
            size_guidance={"scalars": 0},
        )
        accumulator.Reload()
        tag = "Reward / Total reward (mean)"
        if tag not in accumulator.Tags().get("scalars", []):
            continue
        events = accumulator.Scalars(tag)
        if not events:
            continue
        return_series += 1
        label = (
            f"{run['method']} s{run['seed']} "
            f"{run['height_mm']}mm {run['run_name'].split('_attempt')[-1]}"
        )
        ax.plot(
            [event.step for event in events],
            [event.value for event in events],
            linewidth=1.0,
            alpha=0.75,
            label=label,
        )
    if return_series == 0:
        raise ValueError("No real TensorBoard total-return series found")
    ax.set_title("Formal training episode return (all completed runs)")
    ax.set_xlabel("Local control timesteps")
    ax.set_ylabel("Mean completed-episode return")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(plot_dir / "training_return.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 6))
    x = 0
    ticks: list[int] = []
    labels: list[str] = []
    for selection in freeze["selections"]:
        method = selection["method"]
        for summary_path in selection["candidate_summaries"]:
            summary = _load_json(Path(summary_path))
            selected = (
                summary["checkpoint_sha256"]
                == selection["selected_checkpoint_sha256"]
            )
            ax.scatter(
                x,
                summary["selection_metrics"]["success_rate"],
                color=colors[method],
                marker="*" if selected else "o",
                s=120 if selected else 35,
            )
            ticks.append(x)
            labels.append(
                f"{method}{selection['seed']}\n"
                f"{Path(summary['checkpoint']).parent.parent.name.split('_stage-')[-1].split('_attempt')[0]}"
            )
            x += 1
    ax.axhline(
        _load_json(Path(freeze["fsm_validation_summary"]))[
            "selection_metrics"
        ]["success_rate"],
        color=colors["fsm"],
        linestyle="--",
        label="FSM validation floor",
    )
    ax.set_xticks(ticks, labels, rotation=75, fontsize=7)
    ax.set_ylabel("Equal-height validation success rate")
    ax.set_title("All pre-registered validation candidates (* selected)")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_dir / "validation_success.png", dpi=180)
    plt.close(fig)

    x_positions = list(range(len(HEIGHTS)))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9, 6))
    for offset, method in enumerate(method_order):
        rates = [
            method_summaries[method]["per_height"][str(height)]["success_rate"]
            for height in HEIGHTS
        ]
        ax.bar(
            [value + (offset - 1) * width for value in x_positions],
            rates,
            width,
            color=colors[method],
            label=METHOD_LABELS[method],
        )
    ax.set_xticks(x_positions, [f"{height} mm" for height in HEIGHTS])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Success rate")
    ax.set_title("Locked-test success by height")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(plot_dir / "success_by_height.png", dpi=180)
    plt.close(fig)

    for field, filename, ylabel, title in (
        (
            "min_longitudinal_support_margin_m",
            "margin_by_method.png",
            "Episode minimum margin (m)",
            "Locked-test longitudinal quasi-static margin",
        ),
        (
            "pitch_rate_rms_rad_s",
            "pitch_rate_by_method.png",
            "Support-transfer pitch-rate RMS (rad/s)",
            "Locked-test pitch-rate RMS",
        ),
        (
            "residual_saturation_rate",
            "action_saturation.png",
            "Residual saturation rate",
            "Locked-test residual saturation",
        ),
    ):
        fig, ax = plt.subplots(figsize=(9, 6))
        values = [
            [
                float(row[field])
                for row in _aggregate_rows(data, method)
                if row.get(field) is not None
            ]
            for method in method_order
        ]
        missing_methods = [
            METHOD_REPORT_KEYS[method]
            for method, method_values in zip(method_order, values)
            if not method_values
        ]
        plot_values = [
            method_values if method_values else [math.nan]
            for method_values in values
        ]
        ax.boxplot(
            plot_values,
            tick_labels=[METHOD_REPORT_KEYS[m] for m in method_order],
            showfliers=False,
        )
        if missing_methods:
            ax.text(
                0.01,
                0.01,
                "No valid values: " + ", ".join(missing_methods),
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="bottom",
            )
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(plot_dir / filename, dpi=180)
        plt.close(fig)

    for metric, comparison_key, filename, xlabel, title in (
        (
            "min_longitudinal_support_margin_m",
            "C_vs_A",
            "paired_margin_delta.png",
            "C - FSM margin delta (m)",
            "Paired locked-test margin differences",
        ),
        (
            "pitch_rate_rms_rad_s",
            "C_vs_A",
            "paired_pitch_delta.png",
            "C - FSM pitch-rate RMS delta (rad/s)",
            "Paired locked-test pitch-rate differences",
        ),
    ):
        deltas = comparisons[comparison_key]["metrics"][metric].get(
            "deltas", []
        )
        fig, ax = plt.subplots(figsize=(9, 6))
        if deltas:
            ax.hist(deltas, bins=35, color=colors["C"], alpha=0.8)
            ax.axvline(0.0, color="black", linewidth=1)
            ax.axvline(
                mean(deltas),
                color="#bf616a",
                linestyle="--",
                label="mean",
            )
            ax.legend()
        else:
            ax.text(
                0.5,
                0.5,
                "Metric unavailable: no complete paired values.\n"
                "See paired_differences.csv for missing-pair counts.",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
            )
            ax.set_xticks([])
            ax.set_yticks([])
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Paired episodes")
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(plot_dir / filename, dpi=180)
        plt.close(fig)

    reasons = sorted(
        {
            reason
            for method in method_order
            for reason in method_summaries[method]["failure_counts"]
        }
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    bottoms = [0] * len(method_order)
    for reason in reasons:
        counts = [
            method_summaries[method]["failure_counts"].get(reason, 0)
            for method in method_order
        ]
        ax.bar(
            range(len(method_order)),
            counts,
            bottom=bottoms,
            label=reason,
        )
        bottoms = [bottom + count for bottom, count in zip(bottoms, counts)]
    ax.set_xticks(range(len(method_order)), [METHOD_REPORT_KEYS[m] for m in method_order])
    ax.set_ylabel("Failed episodes")
    ax.set_title("Locked-test failure distribution")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(plot_dir / "failure_distribution.png", dpi=180)
    plt.close(fig)


def generate_reports(
    *,
    project_root: Path,
    freeze_path: Path,
    authorization_path: Path,
    locked_run_root: Path,
    audit_path: Path,
    video_inventory_path: Path,
    reports_root: Path,
    unit_test_xml: Path,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    freeze_path = freeze_path.resolve()
    authorization_path = authorization_path.resolve()
    locked_run_root = locked_run_root.resolve()
    audit_path = audit_path.resolve()
    video_inventory_path = video_inventory_path.resolve()
    reports_root = reports_root.resolve()
    freeze = _load_json(freeze_path)
    freeze_failures = verify_method_freeze(freeze)
    if freeze_failures:
        raise RuntimeError("Method freeze drift: " + " | ".join(freeze_failures))
    recorded_audit = _load_json(audit_path)
    fresh_audit = audit_locked_campaign(
        freeze_path=freeze_path,
        authorization_path=authorization_path,
        run_root=locked_run_root,
    )
    for key in (
        "method_freeze_sha256",
        "locked_manifest_sha256",
        "evaluation_count",
        "episode_count",
        "paired_scenario_coverage_complete",
    ):
        if fresh_audit[key] != recorded_audit[key]:
            raise ValueError(f"Locked audit does not reproduce for key {key}")
    if not fresh_audit["paired_scenario_coverage_complete"]:
        raise ValueError("Locked paired coverage is incomplete")
    video_inventory = _load_json(video_inventory_path)
    if (
        video_inventory.get("schema")
        != "resume_validation.video_inventory.v1"
        or int(video_inventory.get("video_count", 0)) <= 0
    ):
        raise ValueError("Video inventory is absent or invalid")
    for video in video_inventory["videos"]:
        path = Path(video["video"])
        if (
            not path.is_file()
            or sha256_file(path) != video["video_sha256"]
        ):
            raise ValueError(f"Video evidence hash mismatch: {path}")

    tree = ET.parse(unit_test_xml)
    testsuites = tree.getroot()
    test_count = int(testsuites.attrib.get("tests", "0"))
    failure_count = int(testsuites.attrib.get("failures", "0"))
    error_count = int(testsuites.attrib.get("errors", "0"))
    if test_count <= 0 or failure_count or error_count:
        raise ValueError("Final unit-test audit is absent or failed")

    claims_protocol_path = project_root / "configs" / "claims_audit_protocol.json"
    claims_protocol = _load_json(claims_protocol_path)
    if not claims_protocol.get("frozen_before_locked_test", False):
        raise ValueError("Claims-audit protocol was not frozen before locked test")
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
    claims = _claims(claims_protocol, method_summaries, comparisons["C_vs_A"])

    required_outputs = [
        reports_root / "locked_test_report.md",
        reports_root / "claims_audit.md",
        reports_root / "final_resume_wording_zh.md",
        reports_root / "resume_metrics.json",
        reports_root / "failure_analysis.md",
    ]
    if any(path.exists() for path in required_outputs):
        raise FileExistsError("Refusing to overwrite an existing final report")
    stage_root = Path(
        tempfile.mkdtemp(prefix=".report_stage_", dir=str(reports_root))
    )
    table_dir = stage_root / "tables"
    plot_dir = stage_root / "plots"
    table_dir.mkdir(parents=True)
    plot_dir.mkdir(parents=True)

    method_table = [
        _flat_method_row(method, method_summaries[method])
        for method in ("fsm", "B", "C")
    ]
    per_height_rows: list[dict[str, Any]] = []
    for method in ("fsm", "B", "C"):
        rows = _aggregate_rows(data, method)
        for height in HEIGHTS:
            group = [row for row in rows if episode_height_mm(row) == height]
            success_count = sum(bool(row["success"]) for row in group)
            interval = wilson_interval(success_count, len(group))
            margin_values = [
                float(row["min_longitudinal_support_margin_m"])
                for row in group
                if row.get("min_longitudinal_support_margin_m") is not None
            ]
            pitch_values = [
                float(row["pitch_rate_rms_rad_s"])
                for row in group
                if row.get("pitch_rate_rms_rad_s") is not None
            ]
            margin_distribution = describe(margin_values)
            pitch_distribution = describe(pitch_values)
            per_height_rows.append(
                {
                    "method": METHOD_REPORT_KEYS[method],
                    "height_mm": height,
                    "episode_count": len(group),
                    "success_count": success_count,
                    "success_rate": success_count / len(group),
                    "success_wilson_95_low": interval[0],
                    "success_wilson_95_high": interval[1],
                    "valid_margin_count": len(margin_values),
                    "mean_min_margin_m": (
                        mean(margin_values)
                        if margin_values
                        else None
                    ),
                    "median_min_margin_m": margin_distribution.get("median"),
                    "std_min_margin_m": margin_distribution.get(
                        "std_population"
                    ),
                    "q25_min_margin_m": margin_distribution.get("q25"),
                    "q75_min_margin_m": margin_distribution.get("q75"),
                    "margin_bootstrap_95_low_m": (
                        margin_distribution.get("bootstrap_95_ci", [None, None])[0]
                    ),
                    "margin_bootstrap_95_high_m": (
                        margin_distribution.get("bootstrap_95_ci", [None, None])[1]
                    ),
                    "mean_pitch_rate_rms_rad_s": (
                        mean(pitch_values)
                        if pitch_values
                        else None
                    ),
                    "median_pitch_rate_rms_rad_s": pitch_distribution.get(
                        "median"
                    ),
                    "std_pitch_rate_rms_rad_s": pitch_distribution.get(
                        "std_population"
                    ),
                    "q25_pitch_rate_rms_rad_s": pitch_distribution.get("q25"),
                    "q75_pitch_rate_rms_rad_s": pitch_distribution.get("q75"),
                    "pitch_bootstrap_95_low_rad_s": (
                        pitch_distribution.get("bootstrap_95_ci", [None, None])[0]
                    ),
                    "pitch_bootstrap_95_high_rad_s": (
                        pitch_distribution.get("bootstrap_95_ci", [None, None])[1]
                    ),
                }
            )
    per_seed_rows = [
        {
            **_flat_method_row("fsm", method_summaries["fsm"]),
            "training_seed": "not_applicable",
        }
    ]
    for method in ("B", "C"):
        for seed in SEEDS:
            per_seed_rows.append(
                {
                    **_flat_method_row(
                        method, _method_summary(data[(method, seed)])
                    ),
                    "training_seed": seed,
                    "selection_status": next(
                        selection["selection_status"]
                        for selection in freeze["selections"]
                        if selection["method"] == method
                        and int(selection["seed"]) == seed
                    ),
                }
            )
    paired_table: list[dict[str, Any]] = []
    for comparison_name, comparison in comparisons.items():
        for metric_name, metric in comparison["metrics"].items():
            if metric_name.endswith("_successful_only"):
                base_metric = metric_name.removesuffix("_successful_only")
            else:
                base_metric = metric_name
            interval = metric.get("stratified_bootstrap_95_ci")
            paired_table.append(
                {
                    "comparison": comparison_name,
                    "baseline": comparison["baseline"],
                    "candidate": comparison["candidate"],
                    "metric": base_metric,
                    "scope": metric["scope"],
                    "pair_count": metric["pair_count"],
                    "missing_pair_count": metric["missing_pair_count"],
                    "missing_pair_ids_json": json.dumps(
                        metric.get("missing_pair_ids", []),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "equal_height_mean_candidate_minus_baseline": metric[
                        "equal_height_mean_delta"
                    ],
                    "bootstrap_95_low": interval[0] if interval else None,
                    "bootstrap_95_high": interval[1] if interval else None,
                }
            )
    failure_rows: list[dict[str, Any]] = []
    for (method, seed), rows in data.items():
        for height in HEIGHTS:
            counts = Counter(
                str(row["failure_reason"])
                for row in rows
                if episode_height_mm(row) == height and row.get("failure_reason")
            )
            for reason, count in sorted(counts.items()):
                failure_rows.append(
                    {
                        "method": METHOD_REPORT_KEYS[method],
                        "training_seed": seed,
                        "height_mm": height,
                        "failure_reason": reason,
                        "count": count,
                    }
                )
    scenario_rows: list[dict[str, Any]] = []
    scenario_fields = (
        "scenario_id",
        "success",
        "failure_reason",
        "min_longitudinal_support_margin_m",
        "pitch_rate_rms_rad_s",
        "pitch_rms_rad",
        "negative_margin_duration_s",
        "max_abs_pitch_rad",
        "peak_abs_pitch_rate_rad_s",
        "wheel_slip_distance_m",
        "wheel_slip_ratio",
        "residual_saturation_rate",
        "wheel_speed_saturation_rate",
        "executed_residual_command_variation_l2",
        "traversal_time_s",
        "forward_progress_m",
        "valid_margin_samples",
        "invalid_margin_samples",
    )
    for (method, seed), rows in data.items():
        for row in rows:
            scenario_rows.append(
                {
                    "method": METHOD_REPORT_KEYS[method],
                    "training_seed": seed,
                    "height_mm": episode_height_mm(row),
                    **{field: row.get(field) for field in scenario_fields},
                }
            )
    _write_csv(table_dir / "method_comparison.csv", method_table)
    _write_csv(table_dir / "per_height_comparison.csv", per_height_rows)
    _write_csv(table_dir / "per_seed_results.csv", per_seed_rows)
    _write_csv(table_dir / "paired_differences.csv", paired_table)
    _write_csv(table_dir / "failure_reasons.csv", failure_rows or [{"count": 0}])
    _write_csv(table_dir / "scenario_results.csv", scenario_rows)
    _write_plots(
        plot_dir=plot_dir,
        project_root=project_root,
        freeze=freeze,
        data=data,
        method_summaries=method_summaries,
        comparisons=comparisons,
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
    pitch_reduction = claims["pitch_rate_minus_31pct"][
        "actual_reduction_percent"
    ]
    resume_success_delta_pp = (
        ppo["success_rate"] - fsm["success_rate"]
    ) * 100.0
    (
        resume_interpretation_code,
        resume_interpretation_text,
    ) = _resume_interpretation(
        success_delta_pp=resume_success_delta_pp,
        success_direction_supported=claims["84_to_91_success"][
            "direction_supported"
        ],
        margin_direction_supported=claims["margin_plus_10mm"][
            "direction_supported"
        ],
        pitch_direction_supported=claims["pitch_rate_minus_31pct"][
            "direction_supported"
        ],
    )
    asset_evidence = (
        project_root
        / "assets"
        / "validation"
        / "isaac_integration_converted_classified_004.json"
    )
    asset_payload = _load_json(asset_evidence)
    required_technical_sources = {
        "actuator_mapping.py",
        "com_estimator.py",
        "contact_processing.py",
        "evaluate_controller.py",
        "fsm_controller.py",
        "fsm_trajectory.py",
        "kinematics.py",
        "metrics.py",
        "residual_action.py",
        "residual_rl_env.py",
        "support_margin.py",
        "telemetry_schema.py",
    }
    frozen_source_names = {
        str(name) for name in freeze.get("critical_source_names", [])
    }
    frozen_paths = {
        str(Path(record["path"]).resolve()).lower()
        for record in freeze.get("immutable_files", [])
    }
    required_technical_evidence = {
        (
            project_root
            / "assets"
            / "manifests"
            / "wlr_robot_validation.json"
        ).resolve(),
        (
            project_root
            / "assets"
            / "validation"
            / "urdf_validation.json"
        ).resolve(),
        (
            project_root
            / "assets"
            / "validation"
            / "usd_candidate_comparison.json"
        ).resolve(),
        asset_evidence.resolve(),
    }
    technical_freeze_coverage = (
        required_technical_sources <= frozen_source_names
        and all(
            str(path).lower() in frozen_paths
            for path in required_technical_evidence
        )
    )
    technical_verified = (
        asset_payload.get("passed") is True
        and asset_payload.get("robot_usd_sha256")
        == sha256_file(
            project_root
            / "assets"
            / "converted"
            / "wlr_robot_validation.usd"
        )
        and recorded_audit["paired_scenario_coverage_complete"]
        and test_count > 0
        and failure_count == 0
        and error_count == 0
        and freeze.get("prevalidation_video_smoke") is not None
        and freeze.get("ablation_config_differences")
        == ["method", "reward.com_margin_weight"]
        and technical_freeze_coverage
    )
    resume_metrics = {
        "protocol_version": load_config(
            project_root / "configs" / "experiment_protocol.yaml"
        )["protocol_version"],
        "asset_sha256": sha256_file(
            project_root / "assets" / "converted" / "wlr_robot_validation.usd"
        ),
        "fsm_config_sha256": sha256_file(
            project_root / "configs" / "fsm.yaml"
        ),
        "ppo_config_sha256": {
            "common": sha256_file(project_root / "configs" / "ppo_common.yaml"),
            "without_com": sha256_file(
                project_root / "configs" / "ppo_without_com.yaml"
            ),
            "with_com": sha256_file(
                project_root / "configs" / "ppo_with_com.yaml"
            ),
        },
        "locked_test_manifest_sha256": recorded_audit[
            "locked_manifest_sha256"
        ],
        "method_freeze_sha256": sha256_file(freeze_path),
        "methods": {
            METHOD_REPORT_KEYS[method]: method_summaries[method]
            for method in ("fsm", "B", "C")
        },
        "aggregate": {
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
            "pitch_rate_reduction_percent": pitch_reduction,
        },
        "confidence_intervals": {
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
        },
        "per_height": {
            METHOD_REPORT_KEYS[method]: method_summaries[method]["per_height"]
            for method in ("fsm", "B", "C")
        },
        "ablation": comparisons["C_vs_B"],
        "comparisons": comparisons,
        "claims": {
            key: value["status"] for key, value in claims.items()
        },
        "claim_details": claims,
        "resume_interpretation": {
            "code": resume_interpretation_code,
            "text_zh": resume_interpretation_text,
            "similar_success_absolute_threshold_percentage_points": 2.0,
        },
        "technical_claims_verified": technical_verified,
        "technical_freeze_coverage": {
            "verified": technical_freeze_coverage,
            "required_source_names": sorted(required_technical_sources),
            "required_evidence_paths": sorted(
                str(path) for path in required_technical_evidence
            ),
        },
        "selection_disclosure": [
            {
                "method": row["method"],
                "seed": row["seed"],
                "status": row["selection_status"],
                "passed_validation_gate": row["passed_validation_gate"],
            }
            for row in freeze["selections"]
        ],
        "unit_test_audit": {
            "path": str(unit_test_xml.resolve()),
            "sha256": sha256_file(unit_test_xml),
            "tests": test_count,
            "failures": failure_count,
            "errors": error_count,
        },
        "video_evidence": {
            "inventory": str(video_inventory_path),
            "inventory_sha256": sha256_file(video_inventory_path),
            "video_count": video_inventory["video_count"],
            "all_replay_outcomes_reproduced": video_inventory[
                "all_replay_outcomes_reproduced"
            ],
        },
        "report_generator_sha256": sha256_file(Path(__file__)),
    }
    write_json(stage_root / "resume_metrics.json", resume_metrics)

    def pct(value: float) -> str:
        return f"{value * 100.0:.2f}%"

    def optional_metric(
        value: float | None,
        *,
        scale: float = 1.0,
        decimals: int = 3,
        unit: str = "",
    ) -> str:
        if value is None or not math.isfinite(float(value)):
            return "不可计算（有效数据不足）"
        suffix = f" {unit}" if unit else ""
        return f"{float(value) * scale:.{decimals}f}{suffix}"

    margin_text = (
        f"{margin_delta * 1000.0:+.3f} mm" if margin_delta is not None else "不可计算"
    )
    pitch_text = (
        f"{pitch_reduction:+.2f}%" if pitch_reduction is not None else "仅报告绝对差"
    )
    secondary_units = {
        "negative_margin_duration": "s",
        "maximum_absolute_pitch": "rad",
        "pitch_rms": "rad",
        "peak_pitch_rate": "rad/s",
        "traversal_time": "s",
        "wheel_slip_distance": "m",
        "wheel_slip_ratio": "",
        "residual_saturation": "",
        "wheel_speed_saturation": "",
        "control_command_variation": "L2/control-step",
    }
    secondary_lines = [
        "| Metric | FSM | Residual PPO without CoM | CoM-guided residual PPO |",
        "|---|---:|---:|---:|",
    ]
    for metric_name, unit in secondary_units.items():
        secondary_lines.append(
            "| "
            + metric_name.replace("_", " ")
            + " | "
            + " | ".join(
                optional_metric(
                    method_summaries[method]["secondary_metrics_all"][
                        metric_name
                    ]["equal_height_mean"],
                    decimals=6,
                    unit=unit,
                )
                for method in ("fsm", "B", "C")
            )
            + " |"
        )
    secondary_lines.extend(
        [
            (
                "| body collision rate | "
                + " | ".join(
                    pct(method_summaries[method]["body_collision_rate"])
                    for method in ("fsm", "B", "C")
                )
                + " |"
            ),
            (
                "| joint-limit rate | "
                + " | ".join(
                    pct(method_summaries[method]["joint_limit_rate"])
                    for method in ("fsm", "B", "C")
                )
                + " |"
            ),
        ]
    )
    secondary_table = "\n".join(secondary_lines)
    selection_warning = any(
        not row["passed_validation_gate"] for row in freeze["selections"]
    )
    report = f"""# Locked-test report

This report is generated only from the post-freeze paired locked campaign.

- Method freeze SHA256: `{sha256_file(freeze_path)}`
- Locked manifest SHA256: `{recorded_audit['locked_manifest_sha256']}`
- Paired coverage: {recorded_audit['evaluation_count']} evaluations, {recorded_audit['episode_count']} episodes
- Unit regression: {test_count} tests, {failure_count} failures, {error_count} errors
- Bootstrap: 10,000 stratified draws with equal 50/75/100 mm weight
- Validation fallback present: {str(selection_warning).lower()}
- Video evidence: {video_inventory['video_count']} deterministic replays; locked outcomes all reproduced: {str(video_inventory['all_replay_outcomes_reproduced']).lower()}

## Primary C vs FSM result

| Metric | FSM | CoM-guided residual PPO | Change |
|---|---:|---:|---:|
| Success | {fsm['success_count']}/{fsm['episode_count']} ({pct(fsm['success_rate'])}) | {ppo['success_count']}/{ppo['episode_count']} ({pct(ppo['success_rate'])}) | {(ppo['success_rate']-fsm['success_rate'])*100:+.2f} pp |
| Equal-height mean minimum margin | {optional_metric(fsm['minimum_margin_all']['equal_height_mean'], scale=1000.0, unit='mm')} | {optional_metric(ppo['minimum_margin_all']['equal_height_mean'], scale=1000.0, unit='mm')} | {margin_text} paired |
| Equal-height pitch-rate RMS | {optional_metric(fsm['pitch_rate_rms_all']['equal_height_mean'], decimals=6, unit='rad/s')} | {optional_metric(ppo['pitch_rate_rms_all']['equal_height_mean'], decimals=6, unit='rad/s')} | {pitch_text} |

The support margin is a longitudinal quasi-static metric, not a proof of
dynamic stability. Invalid margin episodes are never imputed; the paired
margin table discloses all missing pair IDs and counts.

## Secondary metrics

{secondary_table}

No estimated energy/effort is reported because the available command and
state telemetry is not a calibrated electrical or mechanical energy
measurement.

## Confidence intervals

- C−FSM success delta 95% stratified bootstrap:
  `{c_vs_a['metrics']['success']['stratified_bootstrap_95_ci']}`
- C−FSM margin delta 95% stratified bootstrap (m):
  `{c_vs_a['metrics']['min_longitudinal_support_margin_m']['stratified_bootstrap_95_ci']}`
- C−FSM pitch-rate RMS delta 95% stratified bootstrap (rad/s):
  `{c_vs_a['metrics']['pitch_rate_rms_rad_s']['stratified_bootstrap_95_ci']}`

## Required disclosures

- All seeds 11/29/47 are retained in the B and C aggregates and per-seed table.
- FSM is evaluated once on 300 unique scenarios and is duplicated only for
  seed-keyed paired inference against each PPO training seed.
- All validation selection statuses are stored in `resume_metrics.json`.
- All successful and failed locked episodes are present in
  `tables/scenario_results.csv`.
- Typical success/failure (when present), worst-margin, and highest-pitch
  video categories are indexed in `{video_inventory_path}`; category
  deduplication is disclosed.
- Continuous metrics are reported for all valid episodes plus
  successful-only sensitivity summaries.
"""
    (stage_root / "locked_test_report.md").write_text(report, encoding="utf-8")

    failure_lines = ["# Failure analysis", ""]
    for method in ("fsm", "B", "C"):
        failure_lines.append(f"## {METHOD_LABELS[method]}")
        failure_lines.append("")
        counts = method_summaries[method]["failure_counts"]
        if not counts:
            failure_lines.append("- No failed episodes.")
        else:
            for reason, count in counts.items():
                failure_lines.append(f"- {reason}: {count}")
        failure_lines.append("")
    failure_lines.extend(
        [
            "Failure episodes are retained in all primary success denominators.",
            "Missing margin values are disclosed rather than filled with zero.",
        ]
    )
    (stage_root / "failure_analysis.md").write_text(
        "\n".join(failure_lines) + "\n",
        encoding="utf-8",
    )

    technical_status = "VERIFIED" if technical_verified else "NOT_VERIFIED"
    claim_lines = [
        "# Claims audit",
        "",
        "## Technical implementation claims",
        "",
        f"- SolidWorks/URDF/USD/Isaac chain and corrected asset: **{technical_status}**. Evidence: `{asset_evidence}`, SHA256 `{sha256_file(asset_evidence)}`.",
        f"- Whole-robot CoM from rigid-body masses and local CoM poses: **{technical_status}**. Evidence: `src/resume_validation/com_estimator.py`, locked evaluator provenance, {test_count}-test audit.",
        f"- Force-supported longitudinal quasi-static interval excluding riser-only support: **{technical_status}**. Evidence: `src/resume_validation/contact_processing.py`, `support_margin.py`, locked telemetry.",
        f"- Phase FSM wheel-center/wheel-speed reference: **{technical_status}**. Evidence: frozen FSM hash `{resume_metrics['fsm_config_sha256']}`.",
        f"- Bounded residual PPO and analytic-IK articulation targets: **{technical_status}**. Evidence: frozen source/checkpoint hashes and paired campaign.",
        f"- Fair 50/75/100 mm FSM/B/C comparison: **{technical_status}**. Evidence: `{audit_path}`.",
        "",
        "The quasi-static margin must not be described as a strict dynamic-stability proof.",
        "",
        "## Numeric resume claims",
        "",
    ]
    for name, detail in claims.items():
        claim_lines.extend(
            [
                f"### {name}",
                "",
                f"- Status: **{detail['status']}**",
                f"- Actual result: `{json.dumps(detail, ensure_ascii=False, sort_keys=True)}`",
                f"- Definition/rule: `{json.dumps(claims_protocol, ensure_ascii=False, sort_keys=True)}`",
                f"- Raw data: `{locked_run_root}`",
                f"- Config/freeze hash: `{sha256_file(freeze_path)}`",
                "- Allowed wording: use only the actual point estimate and uncertainty above.",
                "- Prohibited wording: the original numeric claim when status is not VERIFIED; any dynamic-stability proof claim; any best-seed-only result.",
                "",
            ]
        )
    (stage_root / "claims_audit.md").write_text(
        "\n".join(claim_lines) + "\n",
        encoding="utf-8",
    )

    success_delta_pp = resume_success_delta_pp
    if margin_delta is None:
        margin_phrase = "因有效配对不足未报告"
    elif margin_delta > 0:
        margin_phrase = f"提高 {margin_delta * 1000.0:.2f} mm"
    elif margin_delta < 0:
        margin_phrase = f"降低 {abs(margin_delta) * 1000.0:.2f} mm"
    else:
        margin_phrase = "保持相近"
    if pitch_reduction is None and pitch_delta is None:
        pitch_phrase = "因有效配对不足未报告"
    elif pitch_reduction is None:
        pitch_phrase = f"绝对变化 {pitch_delta:+.6f} rad/s"
    elif pitch_reduction > 0:
        pitch_phrase = f"降低 {pitch_reduction:.2f}%"
    elif pitch_reduction < 0:
        pitch_phrase = f"增加 {abs(pitch_reduction):.2f}%"
    else:
        pitch_phrase = "保持相近"
    caveat = (
        "；validation 中存在未过 FSM 成功率门槛的预注册 fallback，"
        "故不得写成已通过全部 validation gate"
        if selection_warning
        else ""
    )
    interpretation_code = resume_interpretation_code
    interpretation_text = resume_interpretation_text
    wording = f"""# 最终中文简历表述

FSM 基线与残差 PPO：由 FSM 按越障阶段生成轮心轨迹与轮速基准；
基于 Isaac Lab 构建训练环境，采用 PPO 以台阶相对状态、FSM 阶段及本体
反馈为观测，学习有界轮心位移与轮速残差。轮心残差经工作空间约束和解析
IK 转换为关节位置目标，轮速残差叠加至车轮速度基准；在 50/75/100 mm
台阶锁定测试中，相较 FSM 基线，CoM 引导残差 PPO 的越障成功率点估计
由 {pct(fsm['success_rate'])} 变化至 {pct(ppo['success_rate'])}
（{success_delta_pp:+.2f} 个百分点），平均最小纵向准静态 CoM 支撑裕度
点估计 {margin_phrase}，支撑转移阶段俯仰角速度 RMS 点估计
{pitch_phrase}。证据解释（`{interpretation_code}`）：{interpretation_text}{caveat}。

不得把“纵向准静态 CoM 支撑裕度”改写为严格动态稳定性证明。若
`claims_audit.md` 将原 84%→91%、+10 mm 或 −31% 标为非 VERIFIED，
不得继续使用对应旧数字。
"""
    if not technical_verified:
        wording = """# 最终中文简历表述

技术实现或公平对比证据未通过完整核验，因此不生成包含解析 IK、CoM
接触/支撑裕度或 FSM/PPO 对比数字的可用简历句子。当前结果不得用于简历；
请仅依据 `claims_audit.md` 和 `failure_analysis.md` 继续诊断。
"""
    (stage_root / "final_resume_wording_zh.md").write_text(
        wording,
        encoding="utf-8",
    )

    # Publish only after every required artifact has been generated.
    reports_root.mkdir(parents=True, exist_ok=True)
    for name in (
        "locked_test_report.md",
        "claims_audit.md",
        "final_resume_wording_zh.md",
        "resume_metrics.json",
        "failure_analysis.md",
    ):
        shutil.move(str(stage_root / name), str(reports_root / name))
    for directory in ("tables", "plots"):
        destination = reports_root / directory
        destination.mkdir(parents=True, exist_ok=True)
        for source in (stage_root / directory).iterdir():
            target = destination / source.name
            if target.exists():
                raise FileExistsError(f"Refusing to overwrite final artifact: {target}")
            shutil.move(str(source), str(target))
    stage_root.rmdir()
    return {
        "schema": "resume_validation.final_report_generation.v1",
        "reports_root": str(reports_root),
        "resume_metrics": str(reports_root / "resume_metrics.json"),
        "claims": {
            key: value["status"] for key, value in claims.items()
        },
        "locked_episode_count": recorded_audit["episode_count"],
        "unit_test_count": test_count,
    }


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--locked_run_root", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--video_inventory", type=Path, required=True)
    parser.add_argument("--reports_root", type=Path, required=True)
    parser.add_argument("--unit_test_xml", type=Path, required=True)
    args = parser.parse_args()
    payload = generate_reports(
        project_root=args.project_root,
        freeze_path=args.freeze,
        authorization_path=args.authorization,
        locked_run_root=args.locked_run_root,
        audit_path=args.audit,
        video_inventory_path=args.video_inventory,
        reports_root=args.reports_root,
        unit_test_xml=args.unit_test_xml,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
