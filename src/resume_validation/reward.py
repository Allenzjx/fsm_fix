from __future__ import annotations

import math
from typing import Mapping

import torch


def monotonic_phase_progress_delta(
    fsm_phase: torch.Tensor,
    phase_progress: torch.Tensor,
    previous_coordinate: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return a non-negative delta on the global ``phase + progress`` axis."""

    coordinate = fsm_phase.to(dtype=phase_progress.dtype) + torch.clamp(
        phase_progress, 0.0, 1.0
    )
    delta = torch.clamp(coordinate - previous_coordinate, 0.0, 1.0)
    return delta, coordinate


def integrate_boolean_occupancy(
    active: torch.Tensor,
    step_dt: float,
) -> torch.Tensor:
    """Convert a per-step Boolean state into occupied seconds."""

    if not math.isfinite(step_dt) or step_dt <= 0.0:
        raise ValueError("step_dt must be finite and positive")
    return active.to(dtype=torch.float32) * float(step_dt)


def integrate_rate(
    value_per_second: torch.Tensor,
    step_dt: float,
) -> torch.Tensor:
    """Integrate a continuous state/rate cost over one control interval."""

    if not math.isfinite(step_dt) or step_dt <= 0.0:
        raise ValueError("step_dt must be finite and positive")
    if not torch.is_floating_point(value_per_second):
        value_per_second = value_per_second.to(dtype=torch.float32)
    return value_per_second * float(step_dt)


def reward_terms(
    state: Mapping[str, float],
    *,
    com_weight: float,
    step_dt: float = 1.0 / 60.0,
) -> dict[str, float]:
    if not math.isfinite(step_dt) or step_dt <= 0.0:
        raise ValueError("step_dt must be finite and positive")
    progress = float(state.get("progress_delta", 0.0))
    phase_progress = float(state.get("phase_progress_delta", 0.0))
    success = float(state.get("success", 0.0))
    pitch_rate = float(state.get("pitch_rate", 0.0))
    action_rate = float(state.get("action_rate_sq", 0.0))
    residual = float(state.get("residual_sq", 0.0))
    margin = float(state.get("margin_m", 0.0))
    margin_valid = bool(state.get("margin_valid", 0.0))
    transfer = bool(state.get("support_transfer_window", 0.0))
    advancing = progress > 0.0
    com_raw = min(0.03, margin) if margin >= 0 else 3.0 * margin
    com_term = com_weight * com_raw if margin_valid and transfer and advancing else 0.0
    return {
        "progress": 8.0 * progress,
        "phase_progress": 2.0 * phase_progress,
        "success": 200.0 * success,
        "com_margin": com_term,
        "pitch_rate": -0.25 * pitch_rate * pitch_rate * step_dt,
        "action_rate": -0.1 * action_rate,
        "residual_magnitude": -120.0 * residual * step_dt,
        "time": -0.005,
    }


def total_reward(
    state: Mapping[str, float],
    *,
    com_weight: float,
    step_dt: float = 1.0 / 60.0,
) -> float:
    return sum(
        reward_terms(
            state,
            com_weight=com_weight,
            step_dt=step_dt,
        ).values()
    )
