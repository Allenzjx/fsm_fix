"""Episode-window metric regressions."""

from __future__ import annotations

import math

import pytest

from resume_validation.metrics import compute_episode_metrics


def test_support_transfer_metrics_preserve_negative_margin_and_invalid_counts() -> None:
    samples = [
        {
            "support_transfer_window": True,
            "margin_valid": True,
            "margin_m": 0.01,
            "pitch_rate": 0.2,
            "pitch": 0.1,
            "control_dt": 0.02,
        },
        {
            "support_transfer_window": True,
            "margin_valid": True,
            "margin_m": -0.02,
            "pitch_rate": -0.4,
            "pitch": -0.15,
            "control_dt": 0.02,
        },
        {
            "support_transfer_window": True,
            "margin_valid": False,
            "margin_m": None,
            "pitch_rate": 0.0,
            "pitch": 0.0,
            "control_dt": 0.02,
        },
        {
            "support_transfer_window": False,
            "margin_valid": True,
            "margin_m": -9.0,
            "pitch_rate": 9.0,
            "pitch": 9.0,
            "control_dt": 1.0,
        },
    ]
    metrics = compute_episode_metrics("episode", samples, success=False)
    assert metrics.min_margin_m == -0.02
    assert metrics.pitch_rate_rms_rad_s == pytest.approx(
        math.sqrt((0.2**2 + 0.4**2) / 3.0)
    )
    assert metrics.negative_margin_duration_s == 0.02
    assert metrics.valid_margin_samples == 2
    assert metrics.invalid_margin_samples == 1
    assert metrics.max_abs_pitch_rad == 0.15


def test_empty_metric_window_is_rejected() -> None:
    with pytest.raises(ValueError):
        compute_episode_metrics(
            "empty",
            [{"support_transfer_window": False}],
            success=False,
        )
