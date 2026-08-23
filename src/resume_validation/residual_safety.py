from __future__ import annotations

import math

import torch


ACTION_DIM = 12
WHEEL_CENTER_Z_ACTION_INDICES = (1, 3, 5, 7)
Z_ONLY_ACTION_MASK = (0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0)
COUNTER_YAW_ACTION_MASK = (
    0,
    1,
    0,
    1,
    0,
    1,
    0,
    1,
    1,
    1,
    1,
    1,
)


def residual_phase_mask(
    fsm_phase: torch.Tensor,
    *,
    phase_min: int,
    phase_max: int,
) -> torch.Tensor:
    """Return the common physical-residual enable mask for each environment."""

    if phase_min < 0 or phase_max < phase_min:
        raise ValueError(f"invalid residual phase window [{phase_min}, {phase_max}]")
    return (fsm_phase >= int(phase_min)) & (fsm_phase <= int(phase_max))


def positive_pitch_hazard_mask(
    pitch_rad: torch.Tensor,
    *,
    minimum_pitch_rad: float,
) -> torch.Tensor:
    """Enable residual recovery only above a finite positive IMU pitch."""

    threshold = float(minimum_pitch_rad)
    if (
        not math.isfinite(threshold)
        or threshold <= 0.0
        or threshold >= math.pi / 2.0
    ):
        raise ValueError(
            "positive-pitch hazard threshold must be finite and in (0, pi/2)"
        )
    if not torch.is_tensor(pitch_rad):
        raise ValueError("pitch_rad must be a torch tensor")
    if not torch.isfinite(pitch_rad).all():
        raise ValueError("pitch_rad must be finite")
    return pitch_rad >= threshold


def phase_aware_imu_emergency_masks(
    fsm_phase: torch.Tensor,
    pitch_rad: torch.Tensor,
    pitch_rate_rad_s: torch.Tensor,
    *,
    rear_transfer_phase: int,
    post_transfer_phase_min: int,
    post_transfer_phase_max: int,
    minimum_pitch_rad: float,
    early_pitch_rad: float,
    early_pitch_rate_rad_s: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return physical-enable and corrective-direction masks.

    Rear transfer keeps the historical climb direction for a slow
    high-pitch branch, but switches to pitch correction when the real IMU
    observes the registered early rapid-rise precursor. Post-transfer
    high-pitch branches always use correction. All other rows remain off.
    """

    if (
        int(rear_transfer_phase) < 0
        or int(post_transfer_phase_min) != int(rear_transfer_phase) + 1
        or int(post_transfer_phase_max) < int(post_transfer_phase_min)
    ):
        raise ValueError("invalid phase-aware emergency phase ordering")
    high_pitch = float(minimum_pitch_rad)
    early_pitch = float(early_pitch_rad)
    early_rate = float(early_pitch_rate_rad_s)
    if (
        not math.isfinite(high_pitch)
        or not math.isfinite(early_pitch)
        or not math.isfinite(early_rate)
        or early_pitch <= 0.0
        or high_pitch <= early_pitch
        or high_pitch >= math.pi / 2.0
        or early_rate <= 0.0
    ):
        raise ValueError("invalid phase-aware IMU emergency thresholds")
    if (
        not torch.is_tensor(fsm_phase)
        or not torch.is_tensor(pitch_rad)
        or not torch.is_tensor(pitch_rate_rad_s)
        or fsm_phase.shape != pitch_rad.shape
        or pitch_rad.shape != pitch_rate_rad_s.shape
    ):
        raise ValueError("phase, pitch, and pitch-rate tensors must align")
    if (
        not torch.isfinite(pitch_rad).all()
        or not torch.isfinite(pitch_rate_rad_s).all()
    ):
        raise ValueError("pitch and pitch rate must be finite")

    rear_transfer = fsm_phase == int(rear_transfer_phase)
    post_transfer = (
        (fsm_phase >= int(post_transfer_phase_min))
        & (fsm_phase <= int(post_transfer_phase_max))
    )
    high_pitch_hazard = pitch_rad >= high_pitch
    rapid_rise_hazard = (
        (pitch_rad >= early_pitch)
        & (pitch_rate_rad_s >= early_rate)
    )
    corrective = (rear_transfer & rapid_rise_hazard) | (
        post_transfer & high_pitch_hazard
    )
    enabled = (rear_transfer & (high_pitch_hazard | rapid_rise_hazard)) | (
        post_transfer & high_pitch_hazard
    )
    return enabled, corrective


def phase_aware_roll_imu_emergency_masks(
    fsm_phase: torch.Tensor,
    roll_rad: torch.Tensor,
    pitch_rad: torch.Tensor,
    pitch_rate_rad_s: torch.Tensor,
    *,
    rear_transfer_phase: int,
    post_transfer_phase_min: int,
    post_transfer_phase_max: int,
    minimum_pitch_rad: float,
    minimum_roll_rad: float,
    early_roll_rad: float,
    early_pitch_rate_rad_s: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return v23 enable and pure-roll-correction masks.

    Rear transfer retains the historical high-pitch climb branch. A positive
    high-roll hazard in phases 8--10, or the registered phase-8 rapid-roll
    precursor, selects the pure-roll correction. Post-transfer pitch alone
    has no authority because the bilaterally tied v20--v22 pitch correction
    did not add a development rescue.
    """

    if (
        int(rear_transfer_phase) < 0
        or int(post_transfer_phase_min) != int(rear_transfer_phase) + 1
        or int(post_transfer_phase_max) < int(post_transfer_phase_min)
    ):
        raise ValueError("invalid phase-aware roll emergency phase ordering")
    high_pitch = float(minimum_pitch_rad)
    high_roll = float(minimum_roll_rad)
    early_roll = float(early_roll_rad)
    early_rate = float(early_pitch_rate_rad_s)
    if (
        not math.isfinite(high_pitch)
        or not math.isfinite(high_roll)
        or not math.isfinite(early_roll)
        or not math.isfinite(early_rate)
        or high_pitch <= 0.0
        or high_pitch >= math.pi / 2.0
        or early_roll <= 0.0
        or high_roll <= early_roll
        or high_roll >= math.pi / 2.0
        or early_rate <= 0.0
    ):
        raise ValueError("invalid phase-aware roll IMU emergency thresholds")
    if (
        not torch.is_tensor(fsm_phase)
        or not torch.is_tensor(roll_rad)
        or not torch.is_tensor(pitch_rad)
        or not torch.is_tensor(pitch_rate_rad_s)
        or fsm_phase.shape != roll_rad.shape
        or roll_rad.shape != pitch_rad.shape
        or pitch_rad.shape != pitch_rate_rad_s.shape
    ):
        raise ValueError(
            "phase, roll, pitch, and pitch-rate tensors must align"
        )
    if (
        not torch.isfinite(roll_rad).all()
        or not torch.isfinite(pitch_rad).all()
        or not torch.isfinite(pitch_rate_rad_s).all()
    ):
        raise ValueError("roll, pitch, and pitch rate must be finite")

    rear_transfer = fsm_phase == int(rear_transfer_phase)
    registered_window = (
        (fsm_phase >= int(rear_transfer_phase))
        & (fsm_phase <= int(post_transfer_phase_max))
    )
    high_pitch_climb = pitch_rad >= high_pitch
    high_roll_hazard = roll_rad >= high_roll
    rapid_roll_hazard = (
        (roll_rad >= early_roll)
        & (pitch_rate_rad_s >= early_rate)
    )
    corrective = registered_window & (
        high_roll_hazard | (rear_transfer & rapid_roll_hazard)
    )
    enabled = corrective | (rear_transfer & high_pitch_climb)
    return enabled, corrective


def update_phase8_corrective_latch(
    fsm_phase: torch.Tensor,
    rapid_rise_corrective: torch.Tensor,
    previous_latch: torch.Tensor,
    *,
    rear_transfer_phase: int,
) -> torch.Tensor:
    """Latch a rapid-rise correction through phase 8 and clear on exit."""

    if (
        not torch.is_tensor(fsm_phase)
        or not torch.is_tensor(rapid_rise_corrective)
        or not torch.is_tensor(previous_latch)
        or fsm_phase.shape != rapid_rise_corrective.shape
        or fsm_phase.shape != previous_latch.shape
        or rapid_rise_corrective.dtype != torch.bool
        or previous_latch.dtype != torch.bool
    ):
        raise ValueError(
            "phase-8 latch inputs must be aligned phase/bool tensors"
        )
    rear_transfer = fsm_phase == int(rear_transfer_phase)
    return torch.where(
        rear_transfer,
        previous_latch | (rear_transfer & rapid_rise_corrective),
        torch.zeros_like(previous_latch),
    )


def apply_phase_action_gain(
    actions: torch.Tensor,
    fsm_phase: torch.Tensor,
    *,
    phase_gains: torch.Tensor,
    hard_clip: float = 1.0,
) -> torch.Tensor:
    """Apply prevalidated per-phase gains under normalized action bounds."""

    if actions.ndim < 1 or actions.shape[-1] != ACTION_DIM:
        raise ValueError(
            f"residual actions must have trailing dimension {ACTION_DIM}"
        )
    if fsm_phase.shape != actions.shape[:-1]:
        raise ValueError(
            "FSM phase shape must match residual action batch dimensions"
        )
    if phase_gains.ndim != 1:
        raise ValueError("residual phase gains must be one-dimensional")
    clip = float(hard_clip)
    if not math.isfinite(clip) or clip != 1.0:
        raise ValueError("normalized residual hard clip must be exactly 1.0")
    gains = phase_gains[fsm_phase.to(torch.long)].unsqueeze(-1)
    return torch.clamp(actions * gains, min=-clip, max=clip)


def project_balanced_z_signed_magnitude(
    actions: torch.Tensor,
    *,
    wheel_center_z_signs: tuple[int, int, int, int],
    action_mask: tuple[int, ...] = Z_ONLY_ACTION_MASK,
) -> torch.Tensor:
    """Map raw actions into one balanced, z-only physical residual magnitude.

    All four wheel-center z channels contribute to one mean absolute
    magnitude. Front-left/right use its negative value and rear-left/right
    use its positive value. Disabled x and wheel-speed dimensions are exactly
    zero. Raw policy actions are not modified.
    """

    if actions.ndim < 1 or actions.shape[-1] != ACTION_DIM:
        raise ValueError(
            f"residual actions must have trailing dimension {ACTION_DIM}"
        )
    signs = tuple(int(value) for value in wheel_center_z_signs)
    if len(signs) != 4 or any(value not in {-1, 1} for value in signs):
        raise ValueError(
            "wheel-center z direction signs must contain four values in {-1, 1}"
        )
    if signs != (-1, -1, 1, 1):
        raise ValueError(
            "balanced z projection requires signs (-1, -1, 1, 1)"
        )
    mask = tuple(int(value) for value in action_mask)
    if len(mask) != ACTION_DIM or any(value not in {0, 1} for value in mask):
        raise ValueError(
            f"residual action mask must contain {ACTION_DIM} values in {{0, 1}}"
        )
    if mask != Z_ONLY_ACTION_MASK:
        raise ValueError(
            f"z-only physical authority requires action mask {Z_ONLY_ACTION_MASK}"
        )
    masked = actions * torch.as_tensor(
        mask,
        dtype=actions.dtype,
        device=actions.device,
    )
    projected = torch.zeros_like(masked)
    shared_magnitude = torch.mean(
        torch.abs(masked[..., [1, 3, 5, 7]]),
        dim=-1,
    )
    projected[..., 1] = -shared_magnitude
    projected[..., 3] = -shared_magnitude
    projected[..., 5] = shared_magnitude
    projected[..., 7] = shared_magnitude
    return projected


def project_zero_preserving_balanced_z_gate(
    actions: torch.Tensor,
    *,
    wheel_center_z_signs: tuple[int, int, int, int],
    action_mask: tuple[int, ...] = Z_ONLY_ACTION_MASK,
) -> torch.Tensor:
    """Project the signed z drive onto one safe, zero-preserving direction.

    Unlike the historical mean-absolute projection, this map preserves an
    exact off action. The four enabled raw channels are first aligned with
    the registered front-negative/rear-positive direction and averaged. A
    non-positive shared drive executes zero; a positive drive executes one
    balanced magnitude on all four wheel centers.
    """

    if actions.ndim < 1 or actions.shape[-1] != ACTION_DIM:
        raise ValueError(
            f"residual actions must have trailing dimension {ACTION_DIM}"
        )
    signs = tuple(int(value) for value in wheel_center_z_signs)
    if len(signs) != 4 or any(value not in {-1, 1} for value in signs):
        raise ValueError(
            "wheel-center z direction signs must contain four values in {-1, 1}"
        )
    if signs != (-1, -1, 1, 1):
        raise ValueError(
            "balanced z projection requires signs (-1, -1, 1, 1)"
        )
    mask = tuple(int(value) for value in action_mask)
    if len(mask) != ACTION_DIM or any(value not in {0, 1} for value in mask):
        raise ValueError(
            f"residual action mask must contain {ACTION_DIM} values in {{0, 1}}"
        )
    if mask != Z_ONLY_ACTION_MASK:
        raise ValueError(
            f"z-only physical authority requires action mask {Z_ONLY_ACTION_MASK}"
        )
    masked = actions * torch.as_tensor(
        mask,
        dtype=actions.dtype,
        device=actions.device,
    )
    z_signs = torch.as_tensor(
        signs,
        dtype=actions.dtype,
        device=actions.device,
    )
    shared_drive = torch.mean(
        masked[..., list(WHEEL_CENTER_Z_ACTION_INDICES)] * z_signs,
        dim=-1,
    )
    shared_magnitude = torch.clamp_min(shared_drive, 0.0)
    projected = torch.zeros_like(masked)
    projected[..., list(WHEEL_CENTER_Z_ACTION_INDICES)] = (
        shared_magnitude.unsqueeze(-1) * z_signs
    )
    return projected


def project_pitch_corrective_balanced_z_gate(
    actions: torch.Tensor,
    *,
    wheel_center_z_signs: tuple[int, int, int, int],
    executed_wheel_center_z_signs: tuple[int, int, int, int],
    action_mask: tuple[int, ...] = Z_ONLY_ACTION_MASK,
) -> torch.Tensor:
    """Preserve the learned shared drive but execute its pitch correction.

    The input half-space remains aligned with the historical
    front-negative/rear-positive actor channels so an already-frozen policy
    can be evaluated counterfactually. A positive shared drive is executed
    in the opposite, front-positive/rear-negative wheel-center-z direction
    to oppose an excessive positive body pitch. Zero and the opposite input
    half-space remain exactly off.
    """

    if actions.ndim < 1 or actions.shape[-1] != ACTION_DIM:
        raise ValueError(
            f"residual actions must have trailing dimension {ACTION_DIM}"
        )
    drive_signs = tuple(int(value) for value in wheel_center_z_signs)
    if drive_signs != (-1, -1, 1, 1):
        raise ValueError(
            "pitch-corrective shared-drive alignment requires signs "
            "(-1, -1, 1, 1)"
        )
    output_signs = tuple(
        int(value) for value in executed_wheel_center_z_signs
    )
    if output_signs != (1, 1, -1, -1):
        raise ValueError(
            "pitch-corrective executed direction requires signs "
            "(1, 1, -1, -1)"
        )
    mask = tuple(int(value) for value in action_mask)
    if mask != Z_ONLY_ACTION_MASK:
        raise ValueError(
            f"z-only physical authority requires action mask {Z_ONLY_ACTION_MASK}"
        )
    masked = actions * torch.as_tensor(
        mask,
        dtype=actions.dtype,
        device=actions.device,
    )
    drive_sign_tensor = torch.as_tensor(
        drive_signs,
        dtype=actions.dtype,
        device=actions.device,
    )
    shared_drive = torch.mean(
        masked[..., list(WHEEL_CENTER_Z_ACTION_INDICES)]
        * drive_sign_tensor,
        dim=-1,
    )
    shared_magnitude = torch.clamp_min(shared_drive, 0.0)
    projected = torch.zeros_like(masked)
    projected[..., list(WHEEL_CENTER_Z_ACTION_INDICES)] = (
        shared_magnitude.unsqueeze(-1)
        * torch.as_tensor(
            output_signs,
            dtype=actions.dtype,
            device=actions.device,
        )
    )
    return projected


def project_phase_aware_emergency_balanced_z_gate(
    actions: torch.Tensor,
    corrective_mask: torch.Tensor,
    *,
    wheel_center_z_signs: tuple[int, int, int, int],
    executed_wheel_center_z_signs: tuple[int, int, int, int],
    corrective_wheel_center_z_scales: (
        tuple[float, float, float, float] | None
    ) = None,
    corrective_minimum_shared_magnitude: float = 0.0,
    action_mask: tuple[int, ...] = Z_ONLY_ACTION_MASK,
) -> torch.Tensor:
    """Execute one shared drive in climb or corrective direction per row.

    The actor half-space remains aligned with the historical climb direction
    for checkpoint compatibility. A true ``corrective_mask`` reverses only
    the executed z signs. Exact zero and the opposite actor half-space remain
    off in either mode.
    """

    if actions.ndim < 1 or actions.shape[-1] != ACTION_DIM:
        raise ValueError(
            f"residual actions must have trailing dimension {ACTION_DIM}"
        )
    if (
        not torch.is_tensor(corrective_mask)
        or corrective_mask.shape != actions.shape[:-1]
        or corrective_mask.dtype != torch.bool
    ):
        raise ValueError(
            "corrective mask must be a boolean tensor aligned to action batches"
        )
    drive_signs = tuple(int(value) for value in wheel_center_z_signs)
    if drive_signs != (-1, -1, 1, 1):
        raise ValueError(
            "phase-aware shared-drive alignment requires signs "
            "(-1, -1, 1, 1)"
        )
    corrective_signs = tuple(
        int(value) for value in executed_wheel_center_z_signs
    )
    if corrective_signs not in {
        (1, 1, -1, -1),
        (1, -1, 1, -1),
        (0, -1, 1, 0),
        (0, -1, 0, 0),
        (0, -1, -1, 0),
    }:
        raise ValueError(
            "phase-aware corrective direction requires registered pitch "
            "(1, 1, -1, -1), roll (1, -1, 1, -1), or diagonal "
            "(0, -1, 1, 0), or IK-feasible front-right-only "
            "(0, -1, 0, 0), or deficient-diagonal downward-support "
            "(0, -1, -1, 0) signs"
        )
    if corrective_wheel_center_z_scales is None:
        corrective_scales = (1.0, 1.0, 1.0, 1.0)
    else:
        corrective_scales = tuple(
            float(value)
            for value in corrective_wheel_center_z_scales
        )
        if (
            len(corrective_scales) != 4
            or any(
                not math.isfinite(value)
                or value < 0.0
                or value > 1.0
                for value in corrective_scales
            )
            or any(
                (sign == 0 and scale != 0.0)
                or (sign != 0 and scale <= 0.0)
                for sign, scale in zip(
                    corrective_signs,
                    corrective_scales,
                    strict=True,
                )
            )
        ):
            raise ValueError(
                "explicit corrective wheel-center z scales must contain "
                "four finite values in [0, 1], use zero exactly on "
                "zero-sign channels, and be positive on active channels"
            )
    corrective_floor = float(corrective_minimum_shared_magnitude)
    if (
        not math.isfinite(corrective_floor)
        or corrective_floor < 0.0
        or corrective_floor >= 1.0
    ):
        raise ValueError(
            "corrective minimum shared magnitude must be finite and in [0, 1)"
        )
    mask = tuple(int(value) for value in action_mask)
    if mask != Z_ONLY_ACTION_MASK:
        raise ValueError(
            f"z-only physical authority requires action mask {Z_ONLY_ACTION_MASK}"
        )
    masked = actions * torch.as_tensor(
        mask,
        dtype=actions.dtype,
        device=actions.device,
    )
    drive_sign_tensor = torch.as_tensor(
        drive_signs,
        dtype=actions.dtype,
        device=actions.device,
    )
    shared_drive = torch.mean(
        masked[..., list(WHEEL_CENTER_Z_ACTION_INDICES)]
        * drive_sign_tensor,
        dim=-1,
    )
    shared_magnitude = torch.clamp_min(shared_drive, 0.0)
    shared_magnitude = torch.where(
        corrective_mask & (shared_drive > 0.0),
        torch.clamp_min(shared_magnitude, corrective_floor),
        shared_magnitude,
    )
    corrective_sign_tensor = torch.as_tensor(
        corrective_signs,
        dtype=actions.dtype,
        device=actions.device,
    )
    corrective_scale_tensor = torch.as_tensor(
        corrective_scales,
        dtype=actions.dtype,
        device=actions.device,
    )
    output_signs = torch.where(
        corrective_mask.unsqueeze(-1),
        corrective_sign_tensor * corrective_scale_tensor,
        drive_sign_tensor,
    )
    projected = torch.zeros_like(masked)
    projected[..., list(WHEEL_CENTER_Z_ACTION_INDICES)] = (
        shared_magnitude.unsqueeze(-1) * output_signs
    )
    return projected


def project_phase_aware_emergency_support_counter_yaw_gate(
    actions: torch.Tensor,
    corrective_mask: torch.Tensor,
    fsm_phase: torch.Tensor,
    *,
    wheel_center_z_signs: tuple[int, int, int, int],
    executed_wheel_center_z_signs: tuple[int, int, int, int],
    corrective_wheel_center_z_scales: tuple[float, float, float, float],
    corrective_minimum_shared_magnitude: float,
    corrective_wheel_speed_minimum_shared_magnitudes: tuple[float, ...],
    corrective_wheel_speed_signs: tuple[int, int, int, int],
    corrective_wheel_speed_scales: tuple[float, float, float, float],
    corrective_wheel_speed_phases: tuple[int, ...],
    action_mask: tuple[int, ...] = COUNTER_YAW_ACTION_MASK,
) -> torch.Tensor:
    """Add phase-selective skid-steer yaw authority to corrective z support.

    The checkpoint-compatible shared drive is still computed exclusively
    from the historical wheel-center-z actor half-space. Wheel-speed output
    is derived from that same magnitude and exists only on corrective rows
    in the explicitly registered phase.
    """

    mask = tuple(int(value) for value in action_mask)
    if mask != COUNTER_YAW_ACTION_MASK:
        raise ValueError(
            "counter-yaw physical authority requires action mask "
            f"{COUNTER_YAW_ACTION_MASK}"
        )
    if (
        not torch.is_tensor(fsm_phase)
        or fsm_phase.shape != actions.shape[:-1]
    ):
        raise ValueError(
            "FSM phase must be a tensor aligned to action batches"
        )
    speed_signs = tuple(int(value) for value in corrective_wheel_speed_signs)
    if speed_signs != (-1, 1, -1, 1):
        raise ValueError(
            "counter-yaw physical-forward wheel-speed signs must be "
            "(-1, 1, -1, 1)"
        )
    speed_scales = tuple(
        float(value) for value in corrective_wheel_speed_scales
    )
    if (
        len(speed_scales) != 4
        or any(
            not math.isfinite(value) or value <= 0.0 or value > 1.0
            for value in speed_scales
        )
    ):
        raise ValueError(
            "counter-yaw wheel-speed scales must contain four finite "
            "values in (0, 1]"
        )
    speed_phases = tuple(
        int(value) for value in corrective_wheel_speed_phases
    )
    if (
        not speed_phases
        or tuple(sorted(set(speed_phases))) != speed_phases
        or any(value < 0 for value in speed_phases)
    ):
        raise ValueError(
            "counter-yaw wheel-speed phases must be a non-empty, sorted, "
            "unique tuple of non-negative integers"
        )
    speed_floors = tuple(
        float(value)
        for value in corrective_wheel_speed_minimum_shared_magnitudes
    )
    if (
        len(speed_floors) != len(speed_phases)
        or any(
            not math.isfinite(value) or value < 0.0 or value >= 1.0
            for value in speed_floors
        )
    ):
        raise ValueError(
            "counter-yaw wheel-speed minimum shared magnitudes must align "
            "with phases and contain finite values in [0, 1)"
        )

    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        corrective_mask,
        wheel_center_z_signs=wheel_center_z_signs,
        executed_wheel_center_z_signs=executed_wheel_center_z_signs,
        corrective_wheel_center_z_scales=(
            corrective_wheel_center_z_scales
        ),
        corrective_minimum_shared_magnitude=(
            corrective_minimum_shared_magnitude
        ),
        action_mask=Z_ONLY_ACTION_MASK,
    )
    counter_yaw = corrective_mask & torch.isin(
        fsm_phase.to(torch.long),
        torch.as_tensor(
            speed_phases,
            dtype=torch.long,
            device=fsm_phase.device,
        ),
    )
    shared_magnitude = torch.abs(projected[..., 3])
    selected_speed_floor = torch.zeros_like(shared_magnitude)
    for phase, speed_floor in zip(
        speed_phases,
        speed_floors,
        strict=True,
    ):
        selected_speed_floor = torch.where(
            fsm_phase == phase,
            torch.full_like(selected_speed_floor, speed_floor),
            selected_speed_floor,
        )
    shared_magnitude = torch.where(
        shared_magnitude > 0.0,
        torch.maximum(shared_magnitude, selected_speed_floor),
        shared_magnitude,
    )
    projected[..., 8:12] = torch.where(
        counter_yaw.unsqueeze(-1),
        shared_magnitude.unsqueeze(-1)
        * torch.as_tensor(
            speed_signs,
            dtype=actions.dtype,
            device=actions.device,
        )
        * torch.as_tensor(
            speed_scales,
            dtype=actions.dtype,
            device=actions.device,
        ),
        torch.zeros_like(projected[..., 8:12]),
    )
    return projected


def project_confidence_balanced_z_gate(
    actions: torch.Tensor,
    *,
    wheel_center_z_signs: tuple[int, int, int, int],
    activation_threshold: float,
    action_mask: tuple[int, ...] = Z_ONLY_ACTION_MASK,
) -> torch.Tensor:
    """Execute balanced z only above a registered positive confidence margin."""

    threshold = float(activation_threshold)
    if (
        not math.isfinite(threshold)
        or threshold < 0.0
        or threshold >= 1.0
    ):
        raise ValueError(
            "confidence activation threshold must be finite and in [0, 1)"
        )
    if actions.ndim < 1 or actions.shape[-1] != ACTION_DIM:
        raise ValueError(
            f"residual actions must have trailing dimension {ACTION_DIM}"
        )
    signs = tuple(int(value) for value in wheel_center_z_signs)
    if signs != (-1, -1, 1, 1):
        raise ValueError(
            "balanced z projection requires signs (-1, -1, 1, 1)"
        )
    mask = tuple(int(value) for value in action_mask)
    if mask != Z_ONLY_ACTION_MASK:
        raise ValueError(
            f"z-only physical authority requires action mask {Z_ONLY_ACTION_MASK}"
        )
    masked = actions * torch.as_tensor(
        mask,
        dtype=actions.dtype,
        device=actions.device,
    )
    z_signs = torch.as_tensor(
        signs,
        dtype=actions.dtype,
        device=actions.device,
    )
    shared_drive = torch.mean(
        masked[..., list(WHEEL_CENTER_Z_ACTION_INDICES)] * z_signs,
        dim=-1,
    )
    shared_magnitude = torch.clamp_min(shared_drive - threshold, 0.0)
    projected = torch.zeros_like(masked)
    projected[..., list(WHEEL_CENTER_Z_ACTION_INDICES)] = (
        shared_magnitude.unsqueeze(-1) * z_signs
    )
    return projected
