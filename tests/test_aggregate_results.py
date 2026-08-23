"""Aggregation, equal-height weighting, and paired-difference regressions."""

from __future__ import annotations

import pytest

from resume_validation.aggregate_results import (
    paired_metric_summary,
    summarize_episode_rows,
)


def _row(scenario_id: str, height_mm: int, success: bool, margin: float, pitch: float) -> dict:
    return {
        "scenario_id": scenario_id,
        "height_mm": height_mm,
        "success": success,
        "min_longitudinal_support_margin_m": margin,
        "pitch_rate_rms_rad_s": pitch,
    }


def test_summary_reports_counts_intervals_and_equal_height_weighting() -> None:
    rows = [
        _row("h050-a", 50, True, 0.01, 0.4),
        _row("h050-b", 50, False, -0.01, 0.6),
        _row("h075-a", 75, True, 0.02, 0.3),
        _row("h100-a", 100, False, -0.02, 0.8),
    ]
    summary = summarize_episode_rows(rows)
    assert summary["aggregate"]["episode_count"] == 4
    assert summary["aggregate"]["success_count"] == 2
    assert summary["aggregate"]["equal_height_weighted_success_rate"] == pytest.approx(
        (0.5 + 1.0 + 0.0) / 3.0
    )
    assert len(summary["aggregate"]["success_wilson_95_ci"]) == 2
    assert (
        summary["aggregate"]["successful_episodes_only"]["minimum_margin_m"][
            "count"
        ]
        == 2
    )


def test_paired_summary_requires_exact_scenarios_and_uses_candidate_minus_baseline() -> None:
    baseline = [
        _row("one", 50, True, 0.01, 0.5),
        _row("two", 75, True, 0.02, 0.4),
    ]
    candidate = [
        _row("one", 50, True, 0.02, 0.3),
        _row("two", 75, True, 0.04, 0.2),
    ]
    summary = paired_metric_summary(
        baseline,
        candidate,
        metric="min_longitudinal_support_margin_m",
    )
    assert summary["pair_count"] == 2
    assert summary["candidate_minus_baseline"]["mean"] == pytest.approx(0.015)
    with pytest.raises(ValueError):
        paired_metric_summary(
            baseline,
            candidate[:1],
            metric="min_longitudinal_support_margin_m",
        )


def test_equal_height_continuous_aggregate_requires_every_height() -> None:
    rows = [
        _row("h050", 50, True, 0.01, 0.4),
        _row("h075", 75, True, 0.02, 0.3),
        _row("h100", 100, False, 0.03, 0.2),
    ]
    rows[-1]["min_longitudinal_support_margin_m"] = None
    rows[-1]["pitch_rate_rms_rad_s"] = None
    aggregate = summarize_episode_rows(rows)["aggregate"]
    assert aggregate["equal_height_weighted_mean_minimum_margin_m"] is None
    assert aggregate["equal_height_weighted_pitch_rate_rms_rad_s"] is None
