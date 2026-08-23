"""Small, vectorized contact-load trim used by the deployed FSM."""

from __future__ import annotations

import math
from collections.abc import Mapping


def _piecewise_height_anchor(
    anchors: Mapping,
    obstacle_height_m: float,
) -> float | tuple[float, ...]:
    """Interpolate scalar or vector values through the formal height anchors."""

    height = float(obstacle_height_m)
    if not math.isfinite(height):
        raise ValueError("obstacle height must be finite")
    anchor_items = (
        (0.05, anchors["50mm"]),
        (0.075, anchors["75mm"]),
        (0.10, anchors["100mm"]),
    )
    vector = isinstance(anchor_items[0][1], (list, tuple))
    normalized: list[tuple[float, tuple[float, ...]]] = []
    expected_width: int | None = None
    for anchor_height, raw_value in anchor_items:
        if vector != isinstance(raw_value, (list, tuple)):
            raise ValueError("formal height anchors must use consistent shapes")
        values = (
            tuple(float(value) for value in raw_value)
            if vector
            else (float(raw_value),)
        )
        if expected_width is None:
            expected_width = len(values)
        if len(values) != expected_width:
            raise ValueError("formal height-anchor vectors must have equal lengths")
        if not all(math.isfinite(value) for value in values):
            raise ValueError("formal height-anchor values must be finite")
        normalized.append((anchor_height, values))

    for anchor_height, values in normalized:
        if math.isclose(height, anchor_height, rel_tol=0.0, abs_tol=1.0e-12):
            return values if vector else values[0]
    if height <= normalized[0][0]:
        values = normalized[0][1]
    elif height >= normalized[-1][0]:
        values = normalized[-1][1]
    else:
        lower, upper = (
            (normalized[0], normalized[1])
            if height < normalized[1][0]
            else (normalized[1], normalized[2])
        )
        alpha = (height - lower[0]) / (upper[0] - lower[0])
        values = tuple(
            low + alpha * (high - low)
            for low, high in zip(lower[1], upper[1], strict=True)
        )
    return values if vector else values[0]


def formal_rear_transfer_wheel_speed(
    fsm_config: Mapping,
    obstacle_height_m: float,
) -> tuple[float, float, float, float]:
    """Validate and return the formal phase-7/8 physical-forward wheel speeds."""

    section = fsm_config["rear_transfer_reference"]["rear_transfer_drive"]
    wheel_order = tuple(section["wheel_order"])
    expected_order = ("front_left", "front_right", "rear_left", "rear_right")
    if wheel_order != expected_order:
        raise ValueError(f"formal rear-transfer wheel order must be {expected_order}")
    value = _piecewise_height_anchor(
        section["speed_anchors_rad_s"],
        obstacle_height_m,
    )
    if not isinstance(value, tuple) or len(value) != 4:
        raise ValueError("formal rear-transfer speed anchors must contain four values")
    if any(abs(speed) > 0.3 for speed in value):
        raise ValueError("formal rear-transfer speeds exceed +/-0.3 rad/s")
    return value


def formal_post_transfer_drive_speed(
    fsm_config: Mapping,
    obstacle_height_m: float,
) -> float:
    """Validate and return the formal phase-9/10 physical-forward speed."""

    section = fsm_config["rear_transfer_reference"]["post_transfer_drive"]
    maximum = float(section["maximum_physical_forward_speed_rad_s"])
    if not math.isfinite(maximum) or maximum < 0.0 or maximum > 0.3:
        raise ValueError("formal post-transfer maximum speed must be in [0, 0.3]")
    value = _piecewise_height_anchor(
        section["speed_anchors_rad_s"],
        obstacle_height_m,
    )
    if isinstance(value, tuple):
        raise ValueError("formal post-transfer speed anchors must be scalar")
    if value < 0.0 or value > maximum:
        raise ValueError(
            "formal post-transfer speed must be within the configured maximum"
        )
    return value


def formal_support_unload_policy(
    fsm_config: Mapping,
    obstacle_height_m: float,
) -> tuple[float, float, float, float]:
    """Validate and return low/high force, rate, and height-conditioned bound."""

    section = fsm_config["support_load_balance"]
    low_force = float(section["low_force_n"])
    high_force = float(section["high_force_n"])
    rate = float(section["shortening_rate_m_s"])
    maximum = _piecewise_height_anchor(
        section["maximum_radial_shortening_by_height_m"],
        obstacle_height_m,
    )
    if isinstance(maximum, tuple):
        raise ValueError("formal support-unload maximum anchors must be scalar")
    if not all(math.isfinite(value) for value in (low_force, high_force, rate)):
        raise ValueError("formal support-unload parameters must be finite")
    if low_force < 0.0 or high_force <= low_force:
        raise ValueError("formal support-unload force thresholds are invalid")
    if rate < 0.0 or rate > 0.005:
        raise ValueError("formal support-unload rate must be in [0, 0.005] m/s")
    if maximum < 0.0 or maximum > 0.005:
        raise ValueError("formal support-unload maximum must be in [0, 0.005] m")
    if not bool(section["enabled"]):
        maximum = 0.0
    return low_force, high_force, rate, maximum


def formal_post_transfer_support_geometry(
    fsm_config: Mapping,
    obstacle_height_m: float | None = None,
) -> tuple[tuple[tuple[float, float], ...], tuple[float, ...]]:
    """Validate and return the height-conditioned formal phase-9 geometry."""

    section = fsm_config["post_transfer_support_geometry"]
    if not bool(section["enabled"]):
        return (
            ((0.0, 0.0),) * 4,
            (0.0,) * 4,
        )
    offsets_raw = section["wheel_center_offsets_m"]
    starts_raw = section["offset_start_progress_per_leg"]
    if len(offsets_raw) != 4 or any(len(row) != 2 for row in offsets_raw):
        raise ValueError("formal wheel-center offsets must have shape 4x2")
    if len(starts_raw) != 4:
        raise ValueError("formal offset starts must contain four values")
    offsets = tuple(
        tuple(float(value) for value in row)
        for row in offsets_raw
    )
    starts = tuple(float(value) for value in starts_raw)
    if not all(math.isfinite(value) for row in offsets for value in row):
        raise ValueError("formal wheel-center offsets must be finite")
    if any(abs(value) > 0.020 for row in offsets for value in row):
        raise ValueError("formal wheel-center offsets exceed the 20 mm limit")
    if not all(math.isfinite(value) and 0.0 <= value < 1.0 for value in starts):
        raise ValueError("formal offset starts must be finite in [0, 1)")
    if obstacle_height_m is not None:
        height = float(obstacle_height_m)
        if not math.isfinite(height):
            raise ValueError("obstacle height must be finite")
        conditioning = section["height_conditioning"]
        low_height = float(conditioning["low_height_m"])
        high_height = float(conditioning["high_height_m"])
        low_scale = float(conditioning["low_scale"])
        high_scale = float(conditioning["high_scale"])
        if not all(
            math.isfinite(value)
            for value in (low_height, high_height, low_scale, high_scale)
        ):
            raise ValueError("formal geometry height conditioning must be finite")
        if high_height <= low_height:
            raise ValueError("formal geometry high height must exceed low height")
        if not (0.0 <= low_scale <= 1.0 and 0.0 <= high_scale <= 1.0):
            raise ValueError("formal geometry height scales must be in [0, 1]")
        height_fraction = min(
            max((height - low_height) / (high_height - low_height), 0.0),
            1.0,
        )
        scale = low_scale + height_fraction * (high_scale - low_scale)
        offsets = tuple(
            tuple(value * scale for value in row)
            for row in offsets
        )
    return offsets, starts


def post_transfer_offset_scale(
    fsm_phase,
    phase_progress,
    start_progress=0.0,
    start_phase=9,
):
    """Ramp an offset in a selected phase and hold through phase 10."""

    import torch

    progress = torch.clamp(phase_progress, 0.0, 1.0)
    start = torch.as_tensor(
        start_progress,
        dtype=progress.dtype,
        device=progress.device,
    )
    phase = torch.as_tensor(
        start_phase,
        dtype=fsm_phase.dtype,
        device=fsm_phase.device,
    )
    normalized = torch.clamp(
        (progress - start) / torch.clamp(1.0 - start, min=1.0e-6),
        0.0,
        1.0,
    )
    smooth = normalized.square() * (3.0 - 2.0 * normalized)
    hold = (fsm_phase > phase) & (fsm_phase <= 10)
    return torch.where(
        fsm_phase == phase,
        smooth,
        torch.where(hold, torch.ones_like(smooth), torch.zeros_like(smooth)),
    )


def front_support_offset_scale(fsm_phase, phase_progress):
    """Ramp a diagnostic support-posture offset in phase 6 and hold to phase 10."""

    import torch

    progress = torch.clamp(phase_progress, 0.0, 1.0)
    smooth = progress.square() * (3.0 - 2.0 * progress)
    hold = (fsm_phase >= 7) & (fsm_phase <= 10)
    return torch.where(
        fsm_phase == 6,
        smooth,
        torch.where(hold, torch.ones_like(smooth), torch.zeros_like(smooth)),
    )


def rear_transfer_wheel_speed(
    diagnostic_speed,
    default_physical_forward_rad_s=0.3,
):
    """Use finite diagnostic phase-7/8 wheel speeds, otherwise the default."""

    import torch

    values = torch.as_tensor(diagnostic_speed)
    default = torch.as_tensor(
        default_physical_forward_rad_s,
        dtype=values.dtype,
        device=values.device,
    )
    try:
        default = torch.broadcast_to(default, values.shape)
    except RuntimeError as exc:
        raise ValueError(
            "default rear-transfer wheel speed cannot broadcast to diagnostics"
        ) from exc
    return torch.where(
        torch.isfinite(values),
        values,
        default,
    )


def post_transfer_forward_speed(
    fsm_phase,
    obstacle_height_m,
    all_wheel_force_supported=None,
    *,
    maximum_rad_s: float,
    low_height_m: float = 0.05,
    high_height_m: float = 0.10,
    formal_active_speed_rad_s=None,
    diagnostic_active_speed_rad_s=None,
):
    """Return a height-conditioned all-wheel forward recovery command.

    The complete 50 mm source remains untouched.  At 75/100 mm, phases 9 and
    10 use 50/100 percent of ``maximum_rad_s`` so the partial 100 mm source
    cannot reverse only the front wheels after rear transfer.
    """

    import torch

    alpha = torch.clamp(
        (obstacle_height_m - float(low_height_m))
        / (float(high_height_m) - float(low_height_m)),
        0.0,
        1.0,
    )
    active = (fsm_phase >= 9) & (fsm_phase <= 10)
    selected_active_speed = alpha * float(maximum_rad_s)
    if formal_active_speed_rad_s is not None:
        formal = torch.as_tensor(
            formal_active_speed_rad_s,
            dtype=selected_active_speed.dtype,
            device=selected_active_speed.device,
        )
        selected_active_speed = torch.broadcast_to(
            formal,
            selected_active_speed.shape,
        )
    speed = torch.where(
        active,
        selected_active_speed,
        torch.zeros_like(selected_active_speed),
    )
    if diagnostic_active_speed_rad_s is not None:
        diagnostic = torch.as_tensor(
            diagnostic_active_speed_rad_s,
            dtype=speed.dtype,
            device=speed.device,
        )
        selected_active_speed = torch.where(
            torch.isfinite(diagnostic),
            diagnostic,
            selected_active_speed,
        )
        speed = torch.where(
            active,
            selected_active_speed,
            torch.zeros_like(speed),
        )
    if all_wheel_force_supported is not None:
        speed = torch.where(
            all_wheel_force_supported,
            torch.zeros_like(speed),
            speed,
        )
    return speed


def post_transfer_capture_ready(
    all_wheels_on_top,
    wheel_upward_force_n,
    *,
    force_threshold_n: float,
):
    """Stop post-transfer rolling once geometry or full support is captured."""

    import torch

    force_supported = torch.all(
        wheel_upward_force_n >= float(force_threshold_n),
        dim=1,
    )
    return all_wheels_on_top | force_supported


def update_load_trim(
    current,
    upward_force_n,
    active,
    *,
    dt_s: float,
    low_force_n: float,
    high_force_n: float,
    rate_m_s: float,
    maximum_m: float,
):
    """Apply a bounded hysteretic integrator to wheel-center extension.

    The function intentionally relies only on the tensor-like ``where`` and
    ``clamp`` operations supplied by PyTorch, keeping the policy deterministic
    and vectorized across environments.
    """

    import torch

    delta = float(rate_m_s) * float(dt_s)
    step = torch.where(
        upward_force_n < float(low_force_n),
        torch.full_like(current, delta),
        torch.where(
            upward_force_n > float(high_force_n),
            torch.full_like(current, -delta),
            torch.zeros_like(current),
        ),
    )
    updated = torch.clamp(current + step, 0.0, float(maximum_m))
    return torch.where(active.unsqueeze(1), updated, torch.zeros_like(updated))


def update_unload_trim(
    current,
    upward_force_n,
    active,
    *,
    dt_s: float,
    low_force_n: float,
    high_force_n: float,
    rate_m_s: float,
    maximum_m: float,
):
    """Shorten highly loaded legs and release trim once their load is low."""

    import torch

    rate = torch.as_tensor(
        rate_m_s,
        dtype=current.dtype,
        device=current.device,
    )
    maximum = torch.as_tensor(
        maximum_m,
        dtype=current.dtype,
        device=current.device,
    )
    while rate.ndim < current.ndim:
        rate = rate.unsqueeze(-1)
    while maximum.ndim < current.ndim:
        maximum = maximum.unsqueeze(-1)
    delta = rate * float(dt_s)
    step = torch.where(
        upward_force_n > float(high_force_n),
        torch.ones_like(current) * delta,
        torch.where(
            upward_force_n < float(low_force_n),
            -torch.ones_like(current) * delta,
            torch.zeros_like(current),
        ),
    )
    updated = torch.minimum(
        torch.maximum(current + step, torch.zeros_like(current)),
        maximum,
    )
    return torch.where(active.unsqueeze(1), updated, torch.zeros_like(updated))
