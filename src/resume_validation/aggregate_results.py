"""Pure aggregation primitives for paired validation and locked-test episodes."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, Iterable

from .statistics import describe, paired_bootstrap_ci, wilson_interval


def episode_height_mm(row: dict[str, Any]) -> int:
    if "height_mm" in row:
        return int(row["height_mm"])
    return int(round(float(row["obstacle_height_m"]) * 1000.0))


def summarize_episode_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(rows)
    if not records:
        raise ValueError("At least one episode is required")
    by_height: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_height[episode_height_mm(row)].append(row)
    if set(by_height) != {50, 75, 100}:
        raise ValueError(
            f"Expected complete 50/75/100 mm evidence, got {sorted(by_height)}"
        )

    def summarize_group(group: list[dict[str, Any]]) -> dict[str, Any]:
        success_count = sum(bool(row["success"]) for row in group)
        total = len(group)
        margin_all = [
            float(row["min_longitudinal_support_margin_m"])
            for row in group
            if row.get("min_longitudinal_support_margin_m") is not None
        ]
        pitch_all = [
            float(row["pitch_rate_rms_rad_s"])
            for row in group
            if row.get("pitch_rate_rms_rad_s") is not None
        ]
        successful = [row for row in group if bool(row["success"])]
        margin_success = [
            float(row["min_longitudinal_support_margin_m"])
            for row in successful
            if row.get("min_longitudinal_support_margin_m") is not None
        ]
        pitch_success = [
            float(row["pitch_rate_rms_rad_s"])
            for row in successful
            if row.get("pitch_rate_rms_rad_s") is not None
        ]
        return {
            "episode_count": total,
            "success_count": success_count,
            "success_rate": success_count / total,
            "success_wilson_95_ci": list(wilson_interval(success_count, total)),
            "all_episodes": {
                "minimum_margin_m": describe(margin_all),
                "pitch_rate_rms_rad_s": describe(pitch_all),
            },
            "successful_episodes_only": {
                "minimum_margin_m": describe(margin_success),
                "pitch_rate_rms_rad_s": describe(pitch_success),
            },
        }

    per_height = {
        str(height): summarize_group(by_height[height])
        for height in (50, 75, 100)
    }
    equal_height_success = mean(
        per_height[str(height)]["success_rate"] for height in (50, 75, 100)
    )
    aggregate = summarize_group(records)
    aggregate["equal_height_weighted_success_rate"] = equal_height_success
    margin_height_groups = [
        per_height[str(height)]["all_episodes"]["minimum_margin_m"]
        for height in (50, 75, 100)
    ]
    pitch_height_groups = [
        per_height[str(height)]["all_episodes"]["pitch_rate_rms_rad_s"]
        for height in (50, 75, 100)
    ]
    aggregate["equal_height_weighted_mean_minimum_margin_m"] = (
        mean(group["mean"] for group in margin_height_groups)
        if all(group["count"] > 0 for group in margin_height_groups)
        else None
    )
    aggregate["equal_height_weighted_pitch_rate_rms_rad_s"] = (
        mean(group["mean"] for group in pitch_height_groups)
        if all(group["count"] > 0 for group in pitch_height_groups)
        else None
    )
    return {"aggregate": aggregate, "per_height": per_height}


def paired_metric_summary(
    baseline_rows: Iterable[dict[str, Any]],
    candidate_rows: Iterable[dict[str, Any]],
    *,
    metric: str,
    bootstrap_seed: int = 20260729,
) -> dict[str, Any]:
    baseline_records = list(baseline_rows)
    candidate_records = list(candidate_rows)
    baseline = {str(row["scenario_id"]): row for row in baseline_records}
    candidate = {str(row["scenario_id"]): row for row in candidate_records}
    if len(baseline) != len(baseline_records) or len(candidate) != len(
        candidate_records
    ):
        raise ValueError("Paired inputs contain duplicate scenario IDs")
    if set(baseline) != set(candidate):
        raise ValueError("Paired methods must contain exactly the same scenario IDs")
    scenario_ids = sorted(baseline)
    pairs = [
        (
            float(baseline[scenario_id][metric]),
            float(candidate[scenario_id][metric]),
        )
        for scenario_id in scenario_ids
        if baseline[scenario_id].get(metric) is not None
        and candidate[scenario_id].get(metric) is not None
    ]
    if len(pairs) != len(scenario_ids):
        raise ValueError(f"Metric {metric} is missing from one or more paired episodes")
    left = [pair[0] for pair in pairs]
    right = [pair[1] for pair in pairs]
    deltas = [candidate_value - baseline_value for baseline_value, candidate_value in pairs]
    return {
        "metric": metric,
        "pair_count": len(pairs),
        "candidate_minus_baseline": describe(deltas),
        "paired_bootstrap_95_ci": list(
            paired_bootstrap_ci(
                left,
                right,
                draws=10_000,
                seed=bootstrap_seed,
            )
        ),
    }
