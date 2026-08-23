from __future__ import annotations

import math
from typing import Iterable


def _optional_minimization_value(row: dict, name: str) -> float:
    value = row.get(name)
    if value is None:
        return math.inf
    numeric = float(value)
    return numeric if math.isfinite(numeric) else math.inf


def _stability_key(row: dict) -> tuple[float, float, float, float, str]:
    margin = float(row["mean_min_margin_m"])
    pitch = float(row["pitch_rate_rms_rad_s"])
    if not math.isfinite(margin) or not math.isfinite(pitch):
        raise ValueError("Checkpoint selection metrics must be finite")
    # max() is used, hence minimized terms carry a negative sign. The final
    # checkpoint hash makes exact metric ties deterministic and auditable.
    return (
        margin,
        -pitch,
        -_optional_minimization_value(row, "slip_distance_m"),
        -_optional_minimization_value(row, "saturation_rate"),
        str(row.get("checkpoint_sha256", "")),
    )


def select_checkpoint(rows: Iterable[dict], *, minimum_success_rate: float) -> dict:
    records = list(rows)
    eligible = [
        row for row in records
        if float(row["success_rate"]) >= minimum_success_rate
        and int(row.get("safety_violations", 0)) == 0
    ]
    if not eligible:
        raise ValueError("No checkpoint satisfies the frozen eligibility rules")
    return max(eligible, key=_stability_key)


def select_checkpoint_with_disclosed_fallback(
    rows: Iterable[dict],
    *,
    minimum_success_rate: float,
) -> tuple[dict, str]:
    """Apply the frozen rule without making an incomplete experiment vanish.

    A candidate meeting the FSM-derived success floor and zero severe safety
    violations is selected by the registered stability ordering. If every
    candidate misses that success floor, the highest-success safety-clean
    checkpoint is selected for a *disclosed confirmatory fallback*. This keeps
    the required locked comparison executable but it is not evidence that the
    validation gate was passed. If every candidate has a serious violation,
    the least-violating candidate is retained for disclosure and likewise
    cannot support an improvement claim.
    """

    records = list(rows)
    if not records:
        raise ValueError("At least one checkpoint candidate is required")
    try:
        return (
            select_checkpoint(
                records,
                minimum_success_rate=minimum_success_rate,
            ),
            "ELIGIBLE",
        )
    except ValueError:
        safety_clean = [
            row
            for row in records
            if int(row.get("safety_violations", 0)) == 0
        ]
        if safety_clean:
            chosen = max(
                safety_clean,
                key=lambda row: (
                    float(row["success_rate"]),
                    *_stability_key(row),
                ),
            )
            return chosen, "FALLBACK_BELOW_FSM_SUCCESS_FLOOR"
        chosen = max(
            records,
            key=lambda row: (
                -int(row.get("safety_violations", 0)),
                float(row["success_rate"]),
                *_stability_key(row),
            ),
        )
        return chosen, "FALLBACK_SAFETY_VIOLATIONS_PRESENT"
