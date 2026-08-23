from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EpisodeMetrics:
    episode_id: str
    success: bool
    min_margin_m: float | None
    pitch_rate_rms_rad_s: float
    negative_margin_duration_s: float
    max_abs_pitch_rad: float
    peak_abs_pitch_rate_rad_s: float
    valid_margin_samples: int
    invalid_margin_samples: int


def compute_episode_metrics(
    episode_id: str,
    samples: Iterable[dict],
    *,
    success: bool,
    support_transfer_only: bool = True,
) -> EpisodeMetrics:
    rows = [
        row for row in samples
        if not support_transfer_only or bool(row.get("support_transfer_window", False))
    ]
    if not rows:
        raise ValueError("Episode metric window has no samples")
    margins = [float(row["margin_m"]) for row in rows if bool(row.get("margin_valid")) and row.get("margin_m") is not None]
    rates = [float(row["pitch_rate"]) for row in rows]
    pitches = [float(row["pitch"]) for row in rows]
    negative_duration = sum(
        float(row.get("control_dt", 0.0))
        for row in rows
        if bool(row.get("margin_valid")) and row.get("margin_m") is not None and float(row["margin_m"]) < 0.0
    )
    return EpisodeMetrics(
        episode_id=episode_id,
        success=bool(success),
        min_margin_m=min(margins) if margins else None,
        pitch_rate_rms_rad_s=math.sqrt(sum(value * value for value in rates) / len(rates)),
        negative_margin_duration_s=negative_duration,
        max_abs_pitch_rad=max(abs(value) for value in pitches),
        peak_abs_pitch_rate_rad_s=max(abs(value) for value in rates),
        valid_margin_samples=len(margins),
        invalid_margin_samples=len(rows) - len(margins),
    )
