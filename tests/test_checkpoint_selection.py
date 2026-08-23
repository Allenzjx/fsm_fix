from __future__ import annotations

import pytest

from resume_validation.checkpoint_selection import (
    select_checkpoint,
    select_checkpoint_with_disclosed_fallback,
)


def _row(
    name: str,
    *,
    success: float,
    margin: float,
    pitch: float,
    safety: int = 0,
) -> dict:
    return {
        "checkpoint_sha256": name,
        "success_rate": success,
        "mean_min_margin_m": margin,
        "pitch_rate_rms_rad_s": pitch,
        "slip_distance_m": None,
        "saturation_rate": 0.1,
        "safety_violations": safety,
    }


def test_frozen_selection_uses_eligibility_then_stability() -> None:
    low_success_high_margin = _row(
        "a",
        success=0.4,
        margin=0.03,
        pitch=0.2,
    )
    eligible = _row("b", success=0.6, margin=0.01, pitch=0.3)
    chosen = select_checkpoint(
        [low_success_high_margin, eligible],
        minimum_success_rate=0.5,
    )
    assert chosen["checkpoint_sha256"] == "b"


def test_disclosed_fallback_prefers_success_and_reports_status() -> None:
    first = _row("a", success=0.4, margin=0.03, pitch=0.2)
    second = _row("b", success=0.45, margin=0.01, pitch=0.3)
    selected, status = select_checkpoint_with_disclosed_fallback(
        [first, second],
        minimum_success_rate=0.5,
    )
    assert selected["checkpoint_sha256"] == "b"
    assert status == "FALLBACK_BELOW_FSM_SUCCESS_FLOOR"


def test_strict_selection_rejects_no_eligible_candidate() -> None:
    with pytest.raises(ValueError):
        select_checkpoint(
            [_row("unsafe", success=1.0, margin=0.02, pitch=0.2, safety=1)],
            minimum_success_rate=0.5,
        )
