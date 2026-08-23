"""Isaac Lab DirectRLEnv for FSM + bounded wheel-center residual PPO.

The scene/model plumbing is intentionally adapted from the project's proven
``WLRObstacleRLEnv``.  The action semantics, observations, sensor use, rewards,
success debounce, and control targets are implemented here and do not modify
the reference environment.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path("C:/robotics_sim/wlr_robot")
VALIDATION_ROOT = PROJECT_ROOT / "resume_validation_fsm_residual_ppo"
ISAACLAB_ROOT = Path("C:/robotics_sim/IsaacLab")
for extension in (ISAACLAB_ROOT / "source").iterdir():
    if extension.is_dir() and str(extension) not in sys.path:
        sys.path.append(str(extension))
for path in (ISAACLAB_ROOT, PROJECT_ROOT, VALIDATION_ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.append(str(path))

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaaclab.utils.math import quat_apply, quat_apply_inverse, quat_from_euler_xyz

import wlr_obstacle_rl_env as legacy

from .actuator_mapping import (
    FSM_REFERENCE_MARGIN_DEG,
    JOINT_COMMAND_SIGN,
    RECORDED_SAFE_COMMAND_DEG,
    SERVO_JOINT_NAMES,
    WHEEL_JOINT_NAMES,
)
from .fsm_phase_schedule import HIGH_PHASE_BOUNDARIES, LOW_PHASE_BOUNDARIES
from .load_balance import (
    front_support_offset_scale,
    post_transfer_capture_ready,
    post_transfer_forward_speed,
    post_transfer_offset_scale,
    rear_transfer_wheel_speed,
    update_unload_trim,
)
from .reference_tensor import ReferenceSources, TorchReferenceBank
from .reward import (
    integrate_boolean_occupancy,
    integrate_rate,
    monotonic_phase_progress_delta,
)
from .residual_safety import (
    apply_phase_action_gain,
    phase_aware_imu_emergency_masks,
    phase_aware_roll_imu_emergency_masks,
    positive_pitch_hazard_mask,
    project_balanced_z_signed_magnitude,
    project_confidence_balanced_z_gate,
    project_phase_aware_emergency_balanced_z_gate,
    project_phase_aware_emergency_support_counter_yaw_gate,
    project_pitch_corrective_balanced_z_gate,
    project_zero_preserving_balanced_z_gate,
    residual_phase_mask,
    update_phase8_corrective_latch,
)
from .scenario_manifest import REFERENCE_OBSTACLE_CENTER_X_M, REFERENCE_OBSTACLE_LENGTH_M
from .training_randomization import (
    cache_independent_reset_root_xz,
    sample_training_scenario,
)

ACTOR_OBS_DIM = 96
CRITIC_STATE_DIM = 146
ACTION_DIM = 12
PHASE_COUNT = 13

REWARD_WEIGHTS = {
    "progress": 8.0,
    "phase_progress": 2.0,
    "success": 200.0,
    "top_contact": 1.0,
    "recovery": 2.0,
    "com_margin": 0.0,
    "pitch_rate_sq": -0.25,
    "excessive_tilt": -1.0,
    "slip": -0.2,
    "fall": -200.0,
    "body_collision": -200.0,
    "numerical": -200.0,
    "phase_timeout": -200.0,
    "contact_impact": -0.01,
    "residual_magnitude": -120.0,
    "residual_left_right_asymmetry": -180.0,
    "action_rate": -0.1,
    "joint_acceleration": -1.0e-4,
    "wheel_speed_saturation": -0.1,
    "joint_limit": -200.0,
    "time": -0.005,
    "stuck": -6.0,
}


def make_residual_env_cfg(
    *,
    num_envs: int,
    obstacle_height: float,
    robot_usd_path: str | Path = VALIDATION_ROOT / "assets" / "converted" / "wlr_robot_validation.usd",
    episode_length_s: float = 120.0,
    com_margin_weight: float = 0.0,
    max_idle_gap_s: float = 1.0,
    preserve_wheel_distance: bool = True,
    fsm_contact_debounce_steps: int = 3,
    phase_timeout_scale: float = 1.25,
    fsm_post_transfer_wheel_center_offsets_m: Sequence[Sequence[float]] | None = None,
    fsm_post_transfer_offset_start_progress: Sequence[float] | None = None,
    fsm_rear_transfer_wheel_speed_rad_s: Sequence[float] | None = None,
    fsm_post_transfer_active_speed_rad_s: float | None = None,
    fsm_support_unload_low_force_n: float = 4.0,
    fsm_support_unload_high_force_n: float = 8.0,
    fsm_support_unload_rate_m_s: float = 0.0015,
    fsm_support_unload_maximum_m: float = 0.0,
    residual_reward_weights: dict[str, float] | None = None,
    residual_execution_phase_min: int = 8,
    residual_execution_phase_max: int = 10,
    residual_execution_phase_gains: Sequence[float] = (3.0, 4.0, 3.0),
    residual_applied_action_hard_clip: float = 1.0,
    residual_projection_type: str = "wheel_center_z_deficient_diagonal_downward_support_phase9_counter_yaw_emergency_gate",
    residual_wheel_center_z_signs: Sequence[int] = (-1, -1, 1, 1),
    residual_executed_wheel_center_z_signs: Sequence[int] = (0, -1, -1, 0),
    residual_corrective_wheel_center_z_scales: Sequence[float] = (
        0.0,
        1.0,
        1.0,
        0.0,
    ),
    residual_corrective_wheel_speed_signs: Sequence[int] = (-1, 1, -1, 1),
    residual_corrective_wheel_speed_scales: Sequence[float] = (
        1.0,
        1.0,
        1.0,
        1.0,
    ),
    residual_corrective_wheel_speed_phases: Sequence[int] = (9,),
    residual_corrective_wheel_speed_minimum_shared_magnitudes: Sequence[
        float
    ] = (0.25,),
    residual_action_mask: Sequence[int] = (0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1),
    residual_activation_threshold: float = 0.0,
    residual_state_gate_type: str = "phase_aware_roll_imu_emergency",
    residual_state_gate_min_pitch_rad: float = 0.09,
    residual_state_gate_early_pitch_rad: float = 0.04,
    residual_state_gate_early_pitch_rate_rad_s: float = 0.35,
    residual_state_gate_min_roll_rad: float = 0.10,
    residual_state_gate_early_roll_rad: float = 0.06,
    residual_corrective_minimum_shared_magnitude: float = 0.1,
    obstacle_x: float | None = REFERENCE_OBSTACLE_CENTER_X_M,
    obstacle_length: float | None = REFERENCE_OBSTACLE_LENGTH_M,
    obstacle_width: float | None = 0.882200685486094,
) -> legacy.WLRObstacleEnvCfg:
    cfg = legacy.make_wlr_obstacle_env_cfg(
        num_envs=num_envs,
        robot_usd_path=robot_usd_path,
        obstacle_height=obstacle_height,
        obstacle_x=obstacle_x,
        obstacle_length=obstacle_length,
        obstacle_width=obstacle_width,
        episode_length_s=episode_length_s,
    )
    cfg.action_space = ACTION_DIM
    cfg.observation_space = ACTOR_OBS_DIM
    cfg.state_space = CRITIC_STATE_DIM
    cfg.robot.spawn.activate_contact_sensors = True
    cfg.contact_sensor = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/.*",
        history_length=3,
        update_period=cfg.sim.dt,
        track_air_time=True,
    )
    cfg.residual_bounds = {
        "wheel_center_x_m": 0.0075,
        "wheel_center_z_m": 0.010,
        "wheel_speed_rad_s": 0.10,
    }
    phase_min = int(residual_execution_phase_min)
    phase_max = int(residual_execution_phase_max)
    if phase_min < 0 or phase_max >= PHASE_COUNT or phase_min > phase_max:
        raise ValueError(
            f"invalid residual execution phase window [{phase_min}, {phase_max}]"
        )
    cfg.residual_execution_phase_min = phase_min
    cfg.residual_execution_phase_max = phase_max
    phase_gains = tuple(float(value) for value in residual_execution_phase_gains)
    if len(phase_gains) != phase_max - phase_min + 1:
        raise ValueError(
            "residual execution phase gains must align one-to-one with the "
            f"phase window [{phase_min}, {phase_max}]"
        )
    if any(
        not math.isfinite(value) or value <= 0.0 or value > 4.0
        for value in phase_gains
    ):
        raise ValueError(
            "residual execution phase gains must be finite and in (0, 4]"
        )
    full_phase_gains = [1.0] * PHASE_COUNT
    full_phase_gains[phase_min : phase_max + 1] = phase_gains
    cfg.residual_execution_phase_gains = tuple(full_phase_gains)
    applied_action_hard_clip = float(residual_applied_action_hard_clip)
    if (
        not math.isfinite(applied_action_hard_clip)
        or applied_action_hard_clip != 1.0
    ):
        raise ValueError(
            "residual applied-action hard clip must be exactly 1.0"
        )
    cfg.residual_applied_action_hard_clip = applied_action_hard_clip
    projection_type = str(residual_projection_type)
    supported_projection_types = {
        "wheel_center_z_four_wheel_balanced_signed_magnitude",
        "wheel_center_z_four_wheel_balanced_zero_preserving_gate",
        "wheel_center_z_four_wheel_balanced_confidence_gate",
        "wheel_center_z_four_wheel_balanced_pitch_corrective_gate",
        "wheel_center_z_four_wheel_phase_aware_emergency_gate",
        "wheel_center_z_four_wheel_phase_aware_roll_emergency_gate",
        "wheel_center_z_front_right_rear_left_diagonal_emergency_gate",
        "wheel_center_z_front_right_only_ik_feasible_emergency_gate",
        "wheel_center_z_asymmetric_diagonal_ik_margin_emergency_gate",
        "wheel_center_z_deficient_diagonal_downward_support_emergency_gate",
        "wheel_center_z_deficient_diagonal_downward_support_phase9_counter_yaw_emergency_gate",
    }
    if projection_type not in supported_projection_types:
        raise ValueError(
            f"unsupported residual projection type: {projection_type}"
        )
    cfg.residual_projection_type = projection_type
    activation_threshold = float(residual_activation_threshold)
    if (
        not math.isfinite(activation_threshold)
        or activation_threshold < 0.0
        or activation_threshold >= 1.0
    ):
        raise ValueError(
            "residual activation threshold must be finite and in [0, 1)"
        )
    cfg.residual_activation_threshold = activation_threshold
    state_gate_type = str(residual_state_gate_type)
    if state_gate_type not in {
        "positive_pitch_imu_threshold",
        "phase_aware_pitch_rate_imu_emergency",
        "phase_aware_roll_imu_emergency",
    }:
        raise ValueError(
            f"unsupported residual state gate type: {state_gate_type}"
        )
    cfg.residual_state_gate_type = state_gate_type
    state_gate_min_pitch_rad = float(residual_state_gate_min_pitch_rad)
    if (
        not math.isfinite(state_gate_min_pitch_rad)
        or state_gate_min_pitch_rad <= 0.0
        or state_gate_min_pitch_rad >= math.pi / 2.0
    ):
        raise ValueError(
            "residual positive-pitch hazard threshold must be finite and in "
            "(0, pi/2)"
        )
    cfg.residual_state_gate_min_pitch_rad = state_gate_min_pitch_rad
    state_gate_early_pitch_rad = float(
        residual_state_gate_early_pitch_rad
    )
    state_gate_early_pitch_rate_rad_s = float(
        residual_state_gate_early_pitch_rate_rad_s
    )
    if (
        not math.isfinite(state_gate_early_pitch_rad)
        or state_gate_early_pitch_rad <= 0.0
        or state_gate_early_pitch_rad >= state_gate_min_pitch_rad
        or not math.isfinite(state_gate_early_pitch_rate_rad_s)
        or state_gate_early_pitch_rate_rad_s <= 0.0
    ):
        raise ValueError(
            "residual early IMU thresholds must satisfy "
            "0 < early pitch < high pitch and early pitch rate > 0"
        )
    cfg.residual_state_gate_early_pitch_rad = (
        state_gate_early_pitch_rad
    )
    cfg.residual_state_gate_early_pitch_rate_rad_s = (
        state_gate_early_pitch_rate_rad_s
    )
    state_gate_min_roll_rad = float(residual_state_gate_min_roll_rad)
    state_gate_early_roll_rad = float(residual_state_gate_early_roll_rad)
    if (
        not math.isfinite(state_gate_min_roll_rad)
        or not math.isfinite(state_gate_early_roll_rad)
        or state_gate_early_roll_rad <= 0.0
        or state_gate_min_roll_rad <= state_gate_early_roll_rad
        or state_gate_min_roll_rad >= math.pi / 2.0
    ):
        raise ValueError(
            "residual roll IMU thresholds must satisfy "
            "0 < early roll < high roll < pi/2"
        )
    cfg.residual_state_gate_min_roll_rad = state_gate_min_roll_rad
    cfg.residual_state_gate_early_roll_rad = state_gate_early_roll_rad
    corrective_minimum_shared_magnitude = float(
        residual_corrective_minimum_shared_magnitude
    )
    if (
        not math.isfinite(corrective_minimum_shared_magnitude)
        or corrective_minimum_shared_magnitude < 0.0
        or corrective_minimum_shared_magnitude >= 1.0
    ):
        raise ValueError(
            "residual corrective minimum shared magnitude must be finite "
            "and in [0, 1)"
        )
    cfg.residual_corrective_minimum_shared_magnitude = (
        corrective_minimum_shared_magnitude
    )
    z_signs = tuple(int(value) for value in residual_wheel_center_z_signs)
    if len(z_signs) != 4 or any(value not in {-1, 1} for value in z_signs):
        raise ValueError(
            "residual wheel-center z signs must contain four values in {-1, 1}"
        )
    cfg.residual_wheel_center_z_signs = z_signs
    executed_z_signs = tuple(
        int(value) for value in residual_executed_wheel_center_z_signs
    )
    if (
        len(executed_z_signs) != 4
        or any(value not in {-1, 0, 1} for value in executed_z_signs)
    ):
        raise ValueError(
            "executed wheel-center z signs must contain four values in "
            "{-1, 0, 1}"
        )
    cfg.residual_executed_wheel_center_z_signs = executed_z_signs
    corrective_z_scales = tuple(
        float(value)
        for value in residual_corrective_wheel_center_z_scales
    )
    if (
        len(corrective_z_scales) != 4
        or any(
            not math.isfinite(value)
            or value < 0.0
            or value > 1.0
            for value in corrective_z_scales
        )
        or any(
            (sign == 0 and scale != 0.0)
            or (sign != 0 and scale <= 0.0)
            for sign, scale in zip(
                executed_z_signs,
                corrective_z_scales,
                strict=True,
            )
        )
    ):
        raise ValueError(
            "corrective wheel-center z scales must align with executed "
            "signs and remain in [0, 1]"
        )
    cfg.residual_corrective_wheel_center_z_scales = (
        corrective_z_scales
    )
    corrective_speed_signs = tuple(
        int(value) for value in residual_corrective_wheel_speed_signs
    )
    if corrective_speed_signs != (-1, 1, -1, 1):
        raise ValueError(
            "corrective physical-forward wheel-speed signs must be "
            "(-1, 1, -1, 1)"
        )
    cfg.residual_corrective_wheel_speed_signs = corrective_speed_signs
    corrective_speed_scales = tuple(
        float(value) for value in residual_corrective_wheel_speed_scales
    )
    if (
        len(corrective_speed_scales) != 4
        or any(
            not math.isfinite(value) or value <= 0.0 or value > 1.0
            for value in corrective_speed_scales
        )
    ):
        raise ValueError(
            "corrective wheel-speed scales must contain four finite "
            "values in (0, 1]"
        )
    cfg.residual_corrective_wheel_speed_scales = (
        corrective_speed_scales
    )
    corrective_speed_floors = tuple(
        float(value)
        for value in (
            residual_corrective_wheel_speed_minimum_shared_magnitudes
        )
    )
    if (
        len(corrective_speed_floors) != 1
        or any(
            not math.isfinite(value) or value < 0.0 or value >= 1.0
            for value in corrective_speed_floors
        )
    ):
        raise ValueError(
            "residual corrective wheel-speed minimum shared magnitudes "
            "must contain one finite value in [0, 1)"
        )
    cfg.residual_corrective_wheel_speed_minimum_shared_magnitudes = (
        corrective_speed_floors
    )
    corrective_speed_phases = tuple(
        int(value) for value in residual_corrective_wheel_speed_phases
    )
    if corrective_speed_phases != (9,):
        raise ValueError(
            "corrective counter-yaw wheel-speed phases must be (9,)"
        )
    cfg.residual_corrective_wheel_speed_phases = corrective_speed_phases
    action_mask = tuple(int(value) for value in residual_action_mask)
    expected_action_mask = (0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1)
    if action_mask != expected_action_mask:
        raise ValueError(
            "counter-yaw residual action mask must be "
            f"{expected_action_mask}"
        )
    cfg.residual_action_mask = action_mask
    cfg.reference_sources = {
        "replay_50mm": str(
            PROJECT_ROOT / "height_based_obstacle_replay" / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        ),
        "replay_100mm": str(
            PROJECT_ROOT / "height_based_obstacle_replay" / "saved_height_steps" / "height_10cm" / "accepted_steps.jsonl"
        ),
        "max_idle_gap_s": float(max_idle_gap_s),
        "preserve_wheel_distance": bool(preserve_wheel_distance),
    }
    configured_reward_weights = (
        dict(REWARD_WEIGHTS)
        if residual_reward_weights is None
        else {str(name): float(value) for name, value in residual_reward_weights.items()}
    )
    if set(configured_reward_weights) != set(REWARD_WEIGHTS):
        missing = sorted(set(REWARD_WEIGHTS) - set(configured_reward_weights))
        extra = sorted(set(configured_reward_weights) - set(REWARD_WEIGHTS))
        raise ValueError(
            f"residual reward weights mismatch: missing={missing}, extra={extra}"
        )
    if not all(math.isfinite(value) for value in configured_reward_weights.values()):
        raise ValueError("residual reward weights must be finite")
    cfg.residual_reward_weights = configured_reward_weights
    cfg.residual_reward_weights["com_margin"] = float(com_margin_weight)
    cfg.stable_dwell_s = 1.5
    cfg.max_stable_angular_velocity_rad_s = 0.50
    cfg.contact_force_threshold_n = 2.0
    cfg.residual_servo_velocity_limit_rad_s = 5.0
    cfg.residual_wheel_acceleration_limit_rad_s2 = 6.0
    cfg.terminate_on_residual_success = True
    cfg.disable_episode_termination = False
    cfg.joint_limit_violation_tolerance_rad = math.radians(2.0)
    cfg.fsm_contact_debounce_steps = int(fsm_contact_debounce_steps)
    cfg.phase_timeout_scale = float(phase_timeout_scale)
    formal_offsets = (
        tuple(tuple(float(value) for value in row) for row in fsm_post_transfer_wheel_center_offsets_m)
        if fsm_post_transfer_wheel_center_offsets_m is not None
        else ((0.0, 0.0),) * 4
    )
    formal_starts = (
        tuple(float(value) for value in fsm_post_transfer_offset_start_progress)
        if fsm_post_transfer_offset_start_progress is not None
        else (0.0,) * 4
    )
    if len(formal_offsets) != 4 or any(len(row) != 2 for row in formal_offsets):
        raise ValueError("formal post-transfer wheel-center offsets must have shape 4x2")
    if len(formal_starts) != 4:
        raise ValueError("formal post-transfer offset starts must contain four values")
    if any(
        (not math.isfinite(value)) or abs(value) > 0.020
        for row in formal_offsets
        for value in row
    ):
        raise ValueError("formal post-transfer wheel-center offsets exceed +/-0.020 m")
    if any(
        (not math.isfinite(value)) or value < 0.0 or value >= 1.0
        for value in formal_starts
    ):
        raise ValueError("formal post-transfer offset starts must be in [0, 1)")
    cfg.fsm_post_transfer_wheel_center_offsets_m = formal_offsets
    cfg.fsm_post_transfer_offset_start_progress = formal_starts
    rear_transfer_speed = (
        tuple(float(value) for value in fsm_rear_transfer_wheel_speed_rad_s)
        if fsm_rear_transfer_wheel_speed_rad_s is not None
        else (0.3, 0.3, 0.3, 0.3)
    )
    if len(rear_transfer_speed) != 4:
        raise ValueError("formal rear-transfer wheel speeds must contain four values")
    if any(
        (not math.isfinite(value)) or abs(value) > 0.3
        for value in rear_transfer_speed
    ):
        raise ValueError("formal rear-transfer wheel speeds must be within +/-0.3 rad/s")
    if fsm_post_transfer_active_speed_rad_s is not None:
        post_transfer_speed = float(fsm_post_transfer_active_speed_rad_s)
        if (
            not math.isfinite(post_transfer_speed)
            or post_transfer_speed < 0.0
            or post_transfer_speed > 0.3
        ):
            raise ValueError(
                "formal post-transfer speed must be within [0, 0.3] rad/s"
            )
    else:
        post_transfer_speed = None
    low_force = float(fsm_support_unload_low_force_n)
    high_force = float(fsm_support_unload_high_force_n)
    unload_rate = float(fsm_support_unload_rate_m_s)
    unload_maximum = float(fsm_support_unload_maximum_m)
    if not all(
        math.isfinite(value)
        for value in (low_force, high_force, unload_rate, unload_maximum)
    ):
        raise ValueError("formal support-unload parameters must be finite")
    if low_force < 0.0 or high_force <= low_force:
        raise ValueError("formal support-unload force thresholds are invalid")
    if unload_rate < 0.0 or unload_rate > 0.005:
        raise ValueError("formal support-unload rate must be in [0, 0.005] m/s")
    if unload_maximum < 0.0 or unload_maximum > 0.005:
        raise ValueError("formal support-unload maximum must be in [0, 0.005] m")
    cfg.fsm_rear_transfer_wheel_speed_rad_s = rear_transfer_speed
    cfg.fsm_post_transfer_forward_speed_rad_s = 0.3
    cfg.fsm_post_transfer_active_speed_rad_s = post_transfer_speed
    cfg.fsm_support_unload_low_force_n = low_force
    cfg.fsm_support_unload_high_force_n = high_force
    cfg.fsm_support_unload_rate_m_s = unload_rate
    cfg.fsm_support_unload_maximum_m = unload_maximum
    return cfg


class WLRResidualRLEnv(legacy.WLRObstacleRLEnv):
    """Residual controller with an asymmetric, deployment-conscious actor."""

    def __init__(self, cfg: legacy.WLRObstacleEnvCfg, render_mode: str | None = None, **kwargs: Any):
        self._residual_ready = False
        super().__init__(cfg, render_mode, **kwargs)
        self._applied_actions = torch.zeros_like(self._raw_actions)
        self._residual_execution_phase_gains = torch.as_tensor(
            cfg.residual_execution_phase_gains,
            dtype=self._raw_actions.dtype,
            device=self.device,
        )

        self._reference_bank = TorchReferenceBank(
            ReferenceSources(
                Path(cfg.reference_sources["replay_50mm"]),
                Path(cfg.reference_sources["replay_100mm"]),
                float(cfg.reference_sources["max_idle_gap_s"]),
                bool(cfg.reference_sources["preserve_wheel_distance"]),
            ),
            device=str(self.device),
        )
        self._obstacle_height_env = torch.full(
            (self.num_envs,), float(cfg.obstacle_height), dtype=torch.float32, device=self.device
        )
        self._reference_commands = torch.zeros((self.num_envs, 12), dtype=torch.float32, device=self.device)
        self._reference_wheel_centers = torch.zeros((self.num_envs, 4, 2), dtype=torch.float32, device=self.device)
        self._fsm_front_load_trim_z_m = torch.zeros(
            (self.num_envs, 2), dtype=torch.float32, device=self.device
        )
        self._fsm_support_unload_trim_m = torch.zeros(
            (self.num_envs, 4), dtype=torch.float32, device=self.device
        )
        self._fsm_diagnostic_wheel_center_offset_m = torch.zeros(
            (self.num_envs, 4, 2), dtype=torch.float32, device=self.device
        )
        self._fsm_post_transfer_wheel_center_offset_m = torch.as_tensor(
            cfg.fsm_post_transfer_wheel_center_offsets_m,
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0).expand(self.num_envs, -1, -1).clone()
        self._fsm_post_transfer_offset_start_progress = torch.as_tensor(
            cfg.fsm_post_transfer_offset_start_progress,
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0).expand(self.num_envs, -1).clone()
        self._fsm_diagnostic_post_transfer_offset_start_progress = torch.zeros(
            (self.num_envs, 4), dtype=torch.float32, device=self.device
        )
        self._fsm_diagnostic_post_transfer_offset_start_phase = torch.full(
            (self.num_envs, 4), 9, dtype=torch.long, device=self.device
        )
        self._fsm_diagnostic_rear_transfer_wheel_speed_rad_s = torch.full(
            (self.num_envs, 4),
            float("nan"),
            dtype=torch.float32,
            device=self.device,
        )
        self._fsm_diagnostic_post_transfer_forward_speed_rad_s = torch.full(
            (self.num_envs,),
            float("nan"),
            dtype=torch.float32,
            device=self.device,
        )
        self._fsm_diagnostic_support_unload_maximum_m = torch.full(
            (self.num_envs,),
            float("nan"),
            dtype=torch.float32,
            device=self.device,
        )
        self._fsm_diagnostic_support_unload_rate_m_s = torch.full(
            (self.num_envs,),
            float("nan"),
            dtype=torch.float32,
            device=self.device,
        )
        self._fsm_diagnostic_front_support_offset_deg = torch.zeros(
            (self.num_envs, 8), dtype=torch.float32, device=self.device
        )
        self._fsm_diagnostic_rear_recovery_max_blend: torch.Tensor | None = None
        self._fsm_diagnostic_front_support_clamp_count = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device
        )
        self._fsm_phase = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._fsm_phase_progress = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
        self._reference_progress = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
        self._phase_elapsed_counter = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._phase_exit_debounce_counter = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device
        )
        self._phase_exit_latched = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device
        )
        self._phase_gate_waiting = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device
        )
        self._residual_phase8_corrective_latched = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device
        )
        self._last_fsm_progress = torch.zeros_like(self._fsm_phase_progress)
        self._stable_dwell_counter = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._ik_invalid_count = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._fsm_baseline_ik_invalid_count = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device
        )
        self._fsm_baseline_ik_invalid_count_per_leg = torch.zeros(
            (self.num_envs, 4), dtype=torch.long, device=self.device
        )
        self._residual_saturation_count = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._last_root_lin_vel_b = self._robot.data.root_lin_vel_b.clone()
        self._last_joint_vel = self._robot.data.joint_vel[:, self._servo_joint_ids].clone()
        self._last_contact_force = torch.zeros((self.num_envs, 4), dtype=torch.float32, device=self.device)
        self._last_done_success = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self._last_done_fall = torch.zeros_like(self._last_done_success)
        self._last_done_collision = torch.zeros_like(self._last_done_success)
        self._last_done_numerical = torch.zeros_like(self._last_done_success)
        self._last_done_joint_limit = torch.zeros_like(self._last_done_success)
        self._joint_limit_violation_latched = torch.zeros_like(self._last_done_success)
        self._joint_limit_first_position = torch.full(
            (self.num_envs, len(SERVO_JOINT_NAMES)),
            float("nan"),
            dtype=torch.float32,
            device=self.device,
        )
        self._joint_limit_first_violation = torch.zeros(
            (self.num_envs, len(SERVO_JOINT_NAMES)),
            dtype=torch.bool,
            device=self.device,
        )
        self._last_done_joint_position = torch.full_like(
            self._joint_limit_first_position,
            float("nan"),
        )
        self._last_done_joint_limit_violation = torch.zeros_like(
            self._joint_limit_first_violation
        )
        self._last_done_root_x = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
        self._last_done_margin = torch.full(
            (self.num_envs,), float("nan"), dtype=torch.float32, device=self.device
        )
        self._last_done_margin_valid = torch.zeros_like(self._last_done_success)
        self._last_done_pitch = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
        self._last_done_roll = torch.zeros_like(self._last_done_pitch)
        self._last_done_pitch_rate = torch.zeros_like(self._last_done_pitch)
        self._last_done_fsm_phase = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._phase_timeout_buf = torch.zeros_like(self._last_done_success)
        self._last_done_phase_timeout = torch.zeros_like(self._last_done_success)
        self._last_done_wheel_contact_state = torch.zeros(
            (self.num_envs, 4), dtype=torch.long, device=self.device
        )
        self._last_done_wheel_contact_force_n = torch.zeros(
            (self.num_envs, 4), dtype=torch.float32, device=self.device
        )
        self._last_done_wheel_contact_upward_force_n = torch.zeros_like(
            self._last_done_wheel_contact_force_n
        )
        self._last_done_wheel_on_top = torch.zeros(
            (self.num_envs, 4), dtype=torch.bool, device=self.device
        )
        self._last_done_full_wheel_on_top = torch.zeros_like(
            self._last_done_wheel_on_top
        )
        self._last_done_all_wheels_on_top = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device
        )
        self._last_done_support_score = torch.zeros(
            self.num_envs, dtype=torch.float32, device=self.device
        )
        self._last_done_wheel_position_xz = torch.zeros(
            (self.num_envs, 4, 2), dtype=torch.float32, device=self.device
        )
        self._last_done_wheel_position_y = torch.zeros(
            (self.num_envs, 4), dtype=torch.float32, device=self.device
        )
        self._last_done_reference_commands = torch.zeros(
            (self.num_envs, 12), dtype=torch.float32, device=self.device
        )
        self._scaled_wheel_center_residual_m = torch.zeros(
            (self.num_envs, 4, 2), dtype=torch.float32, device=self.device
        )
        self._scaled_wheel_speed_residual_rad_s = torch.zeros(
            (self.num_envs, 4), dtype=torch.float32, device=self.device
        )
        self._requested_wheel_center_target_m = torch.zeros_like(
            self._scaled_wheel_center_residual_m
        )
        self._final_wheel_center_target_m = torch.zeros_like(
            self._scaled_wheel_center_residual_m
        )
        self._last_done_residual_action = torch.zeros_like(self._raw_actions)
        self._last_done_applied_residual_action = torch.zeros_like(
            self._raw_actions
        )
        self._last_done_scaled_wheel_center_residual_m = torch.zeros_like(
            self._scaled_wheel_center_residual_m
        )
        self._last_done_scaled_wheel_speed_residual_rad_s = torch.zeros_like(
            self._scaled_wheel_speed_residual_rad_s
        )
        self._last_done_requested_wheel_center_target_m = torch.zeros_like(
            self._requested_wheel_center_target_m
        )
        self._last_done_final_wheel_center_target_m = torch.zeros_like(
            self._final_wheel_center_target_m
        )
        self._last_done_servo_targets = torch.zeros_like(self._servo_targets)
        self._last_done_wheel_targets_rad_s = torch.zeros_like(
            self._physical_forward_wheel_cmds
        )
        self._last_done_fsm_front_load_trim_z_m = torch.zeros_like(
            self._fsm_front_load_trim_z_m
        )
        self._last_done_fsm_support_unload_trim_m = torch.zeros_like(
            self._fsm_support_unload_trim_m
        )
        self._last_done_fsm_baseline_ik_invalid_count = torch.zeros_like(
            self._fsm_baseline_ik_invalid_count
        )
        self._last_done_fsm_baseline_ik_invalid_count_per_leg = (
            torch.zeros_like(self._fsm_baseline_ik_invalid_count_per_leg)
        )
        self._last_done_fsm_diagnostic_front_support_clamp_count = (
            torch.zeros_like(self._fsm_diagnostic_front_support_clamp_count)
        )
        self._last_raw_reward_terms: dict[str, torch.Tensor] = {}
        self._last_weighted_reward_terms: dict[str, torch.Tensor] = {}
        self._residual_episode_sums = {
            name: torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
            for name in cfg.residual_reward_weights
        }
        self._reward_episode_raw_sums = {
            name: torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
            for name in cfg.residual_reward_weights
        }
        self._external_reference_commands: torch.Tensor | None = None
        self._action_delay_steps = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._action_history = torch.zeros((3, self.num_envs, ACTION_DIM), dtype=torch.float32, device=self.device)
        self._obstacle_observation_noise = torch.zeros((self.num_envs, 4), dtype=torch.float32, device=self.device)
        self._scenario_friction = torch.ones(self.num_envs, dtype=torch.float32, device=self.device)
        self._training_randomization_level_cfg: dict[str, Any] | None = None
        self._training_randomization_seed = 0
        self._training_nominal_distance_m = 0.2681075872973213
        self._training_episode_index = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device
        )
        self._training_initial_distance_m = torch.full(
            (self.num_envs,),
            self._training_nominal_distance_m,
            dtype=torch.float32,
            device=self.device,
        )
        self._training_initial_pitch_rad = torch.zeros(
            self.num_envs, dtype=torch.float32, device=self.device
        )

        self._joint_command_sign = torch.tensor(
            [JOINT_COMMAND_SIGN[name] for name in SERVO_JOINT_NAMES],
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)
        self._wheel_forward_sign = torch.tensor(
            [legacy.WHEEL_FORWARD_SIGN[name] for name in WHEEL_JOINT_NAMES],
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)
        self._leg_l1 = torch.tensor(
            [0.14786, 0.1478, 0.1478, 0.14779], dtype=torch.float32, device=self.device
        ).unsqueeze(0)
        self._leg_l2 = torch.tensor(
            [math.hypot(0.1559, 0.02)] * 4, dtype=torch.float32, device=self.device
        ).unsqueeze(0)
        self._leg_hip_zero = torch.tensor(
            [
                math.atan2(-0.0002124, 0.14786),
                0.0,
                0.0,
                0.0,
            ],
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)
        self._leg_knee_zero = torch.tensor(
            [
                -1.5098 + math.atan2(-0.02, 0.1559) - math.atan2(-0.0002124, 0.14786),
                -1.4988 + math.atan2(-0.02, 0.1559),
                1.55 + math.atan2(0.02, 0.1559),
                1.5269 + math.atan2(0.02, 0.1559),
            ],
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)
        self._phase_bounds_low = torch.tensor(
            LOW_PHASE_BOUNDARIES,
            dtype=torch.float32,
            device=self.device,
        )
        self._phase_bounds_high = torch.tensor(
            HIGH_PHASE_BOUNDARIES,
            dtype=torch.float32,
            device=self.device,
        )
        self._contact_wheel_ids, _ = self._contact_sensor.find_bodies(
            "front_left_wheel|front_right_wheel|rear_left_wheel|rear_right_wheel",
            preserve_order=True,
        )
        self._contact_nonwheel_ids = [
            index for index, name in enumerate(self._contact_sensor.body_names) if "wheel" not in name
        ]
        self._contact_nonwheel_names = [
            self._contact_sensor.body_names[index] for index in self._contact_nonwheel_ids
        ]
        root_quat = self._robot.data.root_quat_w
        root_pos = self._robot.data.root_pos_w
        wheel_pos = self._robot.data.body_pos_w[:, self._wheel_body_ids]
        self._training_standing_wheel_relative_b = quat_apply_inverse(
            root_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
            (wheel_pos - root_pos.unsqueeze(1)).reshape(-1, 3),
        ).reshape(self.num_envs, 4, 3).clone()
        self._check_finite_tensor(
            "residual.training_standing_wheel_relative_b",
            self._training_standing_wheel_relative_b,
        )
        self._last_done_nonwheel_contact_force_n = torch.zeros(
            (self.num_envs, len(self._contact_nonwheel_ids)),
            dtype=torch.float32,
            device=self.device,
        )
        self._residual_ready = True

    def _refresh_contact_state(self) -> None:
        """Refresh geometry while keeping the formal success predicate sensor-based."""
        super()._refresh_contact_state()
        if not self._residual_ready:
            return

        # The legacy environment folds a link-center bounding-box heuristic
        # (_nonwheel_obstacle_contact_count) into _all_wheels_on_top.  Formal
        # validation instead rejects non-wheel contact from the ContactSensor
        # at the configured 5 N threshold in _get_dones().  Recompute this
        # geometry-only prerequisite here so the heuristic cannot silently
        # veto an otherwise valid full-wheel-on-top state.
        support = self.compute_com_support_metrics(update_cache=False)
        self._all_wheels_on_top = (
            torch.all(self._full_wheel_on_top, dim=1)
            & self._stable_tilt()
            & (support["score"] >= 0.45)
        )

    def _phase_bounds_by_height(self) -> torch.Tensor:
        alpha = torch.clamp(
            (self._obstacle_height_env - 0.05) / 0.05,
            0.0,
            1.0,
        ).unsqueeze(1)
        return self._phase_bounds_low.unsqueeze(0) + alpha * (
            self._phase_bounds_high - self._phase_bounds_low
        ).unsqueeze(0)

    @staticmethod
    def _phase_from_progress(progress: torch.Tensor, bounds: torch.Tensor) -> torch.Tensor:
        # Equivalent to torch.bucketize(..., right=False), but supports one
        # boundary vector per environment.
        return torch.sum(progress.unsqueeze(1) > bounds, dim=1).to(torch.long)

    def _setup_scene(self) -> None:
        self._robot = Articulation(self.cfg.robot)
        self.scene.articulations["robot"] = self._robot
        self._obstacle = RigidObject(self.cfg.obstacle)
        self.scene.rigid_objects["obstacle"] = self._obstacle
        self._contact_sensor = ContactSensor(self.cfg.contact_sensor)
        self.scene.sensors["contact_sensor"] = self._contact_sensor
        self.cfg.terrain.num_envs = self.scene.cfg.num_envs
        self.cfg.terrain.env_spacing = self.scene.cfg.env_spacing
        self._terrain = self.cfg.terrain.class_type(self.cfg.terrain)
        self.scene.clone_environments(copy_from_source=False)
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[self.cfg.terrain.prim_path])
        sim_utils.DomeLightCfg(intensity=2500.0, color=(0.85, 0.88, 0.95)).func(
            "/World/Light", sim_utils.DomeLightCfg(intensity=2500.0, color=(0.85, 0.88, 0.95))
        )

    def _compute_raw_servo_limit_tensors(self) -> tuple[torch.Tensor, torch.Tensor]:
        lower = torch.zeros(self.num_envs, len(SERVO_JOINT_NAMES), dtype=torch.float32, device=self.device)
        upper = torch.zeros_like(lower)
        for index, name in enumerate(SERVO_JOINT_NAMES):
            sign = float(JOINT_COMMAND_SIGN[name])
            command_low, command_high = RECORDED_SAFE_COMMAND_DEG[name]
            raw_a = self._standing_servo_pos[:, index] + sign * math.radians(command_low)
            raw_b = self._standing_servo_pos[:, index] + sign * math.radians(command_high)
            lower[:, index] = torch.minimum(raw_a, raw_b)
            upper[:, index] = torch.maximum(raw_a, raw_b)
        return lower, upper

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        if not torch.is_tensor(actions):
            actions = torch.as_tensor(actions, dtype=torch.float32, device=self.device)
        actions = actions.to(self.device, dtype=torch.float32)
        if actions.shape != (self.num_envs, ACTION_DIM):
            raise RuntimeError(f"Expected residual actions {(self.num_envs, ACTION_DIM)}, got {tuple(actions.shape)}")
        if not torch.isfinite(actions).all():
            raise RuntimeError("Non-finite residual action")
        self._action_history[1:] = self._action_history[:-1].clone()
        self._action_history[0] = torch.clamp(actions, -1.0, 1.0)
        env_index = torch.arange(self.num_envs, device=self.device)
        delayed_actions = self._action_history[self._action_delay_steps, env_index]
        self._previous_actions[:] = self._raw_actions
        self._raw_actions[:] = delayed_actions
        self._residual_saturation_count += torch.any(torch.abs(actions) > 1.0, dim=1).to(torch.long)
        self._update_fsm_reference()
        self._process_residual_actions()

    def _update_fsm_reference(self) -> None:
        elapsed = self.episode_length_buf.to(torch.float32) * float(self.step_dt)
        duration = self._reference_bank.duration_s(self._obstacle_height_env)
        time_normalized = torch.clamp(elapsed / torch.clamp(duration, min=1.0e-6), 0.0, 1.0)
        if self._external_reference_commands is not None:
            normalized = time_normalized
        else:
            self._refresh_contact_state()
            previous_phase = self._fsm_phase.clone()
            candidate = torch.clamp(
                self._reference_progress + float(self.step_dt) / torch.clamp(duration, min=1.0e-6),
                0.0,
                1.0,
            )
            front_contact = torch.any(
                self._wheel_on_front_face[:, :2] | self._wheel_on_top[:, :2], dim=1
            )
            any_front_top = torch.any(self._wheel_on_top[:, :2], dim=1)
            both_front_top = torch.all(self._wheel_on_top[:, :2], dim=1)
            any_rear_top = torch.any(self._wheel_on_top[:, 2:], dim=1)
            both_rear_top = torch.all(self._wheel_on_top[:, 2:], dim=1)
            all_top = torch.all(self._wheel_on_top, dim=1)
            roll, pitch, _ = self._roll_pitch_yaw()
            stable_top = (
                all_top
                & (torch.abs(roll) <= float(self.cfg.max_stable_tilt_rad))
                & (torch.abs(pitch) <= float(self.cfg.max_stable_tilt_rad))
                & (
                    torch.linalg.vector_norm(self._robot.data.root_ang_vel_b, dim=1)
                    <= float(self.cfg.max_stable_angular_velocity_rad_s)
                )
            )
            phase = self._fsm_phase
            exit_condition = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
            exit_condition = torch.where(phase == 2, front_contact, exit_condition)
            exit_condition = torch.where(phase == 3, front_contact, exit_condition)
            exit_condition = torch.where(phase == 4, any_front_top, exit_condition)
            exit_condition = torch.where(phase == 5, both_front_top, exit_condition)
            exit_condition = torch.where(phase == 6, both_front_top, exit_condition)
            exit_condition = torch.where(phase == 7, any_rear_top, exit_condition)
            exit_condition = torch.where(phase == 8, both_rear_top, exit_condition)
            exit_condition = torch.where(phase == 9, all_top, exit_condition)
            exit_condition = torch.where(phase == 10, stable_top, exit_condition)
            self._phase_exit_debounce_counter = torch.where(
                exit_condition,
                self._phase_exit_debounce_counter + 1,
                torch.zeros_like(self._phase_exit_debounce_counter),
            )
            debounced_exit = (
                self._phase_exit_debounce_counter
                >= int(self.cfg.fsm_contact_debounce_steps)
            )
            # A contact milestone may legitimately occur before the end of its
            # planned command window (for example both front wheels can touch
            # the top before a subsequent posture adjustment lifts one).
            # Latch the debounced milestone for the remainder of the phase.
            self._phase_exit_latched |= debounced_exit
            exit_ready = self._phase_exit_latched
            phase_bounds = self._phase_bounds_by_height()
            upper_by_phase = torch.cat(
                (
                    phase_bounds,
                    torch.ones((self.num_envs, 2), dtype=torch.float32, device=self.device),
                ),
                dim=1,
            )
            upper = torch.gather(upper_by_phase, 1, phase.unsqueeze(1)).squeeze(1)
            normalized = torch.where(
                (candidate >= upper) & (~exit_ready),
                torch.clamp(upper - 1.0e-6, min=0.0),
                candidate,
            )
            self._phase_gate_waiting = (candidate >= upper) & (~exit_ready)
            self._reference_progress[:] = normalized
            new_phase = self._phase_from_progress(normalized, phase_bounds)
            phase_changed = new_phase != previous_phase
            self._phase_elapsed_counter = torch.where(
                phase_changed,
                torch.zeros_like(self._phase_elapsed_counter),
                self._phase_elapsed_counter + 1,
            )
            self._phase_exit_debounce_counter = torch.where(
                phase_changed,
                torch.zeros_like(self._phase_exit_debounce_counter),
                self._phase_exit_debounce_counter,
            )
            self._phase_exit_latched = torch.where(
                phase_changed,
                torch.zeros_like(self._phase_exit_latched),
                self._phase_exit_latched,
            )
        if self._external_reference_commands is None:
            self._reference_commands[:] = self._reference_bank.sample_fsm(
                normalized,
                self._obstacle_height_env,
                self._fsm_diagnostic_rear_recovery_max_blend,
            )
            approach_contact = torch.any(
                self._wheel_on_front_face[:, :2] | self._wheel_on_top[:, :2],
                dim=1,
            )
            approach_fallback = (self._fsm_phase == 2) & (~approach_contact)
            # The accepted 100 mm source ends with both rear wheels at the
            # riser. During the contact-gated rear-transfer phases, continue a
            # conservative physical-forward roll until the required top
            # contacts are observed. This extends the partial source reference;
            # it does not bypass or weaken the phase gate.
            rear_transfer = ((self._fsm_phase == 7) | (self._fsm_phase == 8)) & (
                ~torch.all(self._wheel_on_top[:, 2:], dim=1)
            )
            # A phase gate must never create unbounded travel by holding a
            # non-zero source wheel command. Stop at the gate unless an
            # explicitly configured contact-recovery command applies below.
            self._reference_commands[:, 8:] = torch.where(
                (self._phase_gate_waiting | (self._fsm_phase == 6)).unsqueeze(1),
                torch.zeros_like(self._reference_commands[:, 8:]),
                self._reference_commands[:, 8:],
            )
            self._reference_commands[:, 8:] = torch.where(
                approach_fallback.unsqueeze(1),
                torch.full_like(self._reference_commands[:, 8:], 0.3),
                self._reference_commands[:, 8:],
            )
            transfer_wheel_speed = rear_transfer_wheel_speed(
                self._fsm_diagnostic_rear_transfer_wheel_speed_rad_s,
                default_physical_forward_rad_s=(
                    self.cfg.fsm_rear_transfer_wheel_speed_rad_s
                ),
            )
            self._reference_commands[:, 8:] = torch.where(
                rear_transfer.unsqueeze(1),
                transfer_wheel_speed,
                self._reference_commands[:, 8:],
            )
            post_transfer_speed = post_transfer_forward_speed(
                self._fsm_phase,
                self._obstacle_height_env,
                post_transfer_capture_ready(
                    self._all_wheels_on_top,
                    self._wheel_contact_forces()[0][:, :, 2],
                    force_threshold_n=float(
                        self.cfg.contact_force_threshold_n
                    ),
                ),
                maximum_rad_s=float(
                    self.cfg.fsm_post_transfer_forward_speed_rad_s
                ),
                formal_active_speed_rad_s=(
                    self.cfg.fsm_post_transfer_active_speed_rad_s
                ),
                diagnostic_active_speed_rad_s=(
                    self._fsm_diagnostic_post_transfer_forward_speed_rad_s
                ),
            )
            post_transfer_active = (
                (self._fsm_phase >= 9)
                & (self._fsm_phase <= 10)
                & (self._obstacle_height_env > 0.05 + 1.0e-6)
            )
            self._reference_commands[:, 8:] = torch.where(
                post_transfer_active.unsqueeze(1),
                post_transfer_speed.unsqueeze(1).expand_as(
                    self._reference_commands[:, 8:]
                ),
                self._reference_commands[:, 8:],
            )
        else:
            self._reference_commands[:] = self._external_reference_commands
        phase_bounds = self._phase_bounds_by_height()
        self._fsm_phase[:] = self._phase_from_progress(normalized, phase_bounds)
        lower_table = torch.cat(
            (
                torch.zeros((self.num_envs, 1), dtype=torch.float32, device=self.device),
                phase_bounds,
                torch.ones((self.num_envs, 1), dtype=torch.float32, device=self.device),
            ),
            dim=1,
        )
        upper_table = torch.cat(
            (
                phase_bounds,
                torch.ones((self.num_envs, 2), dtype=torch.float32, device=self.device),
            ),
            dim=1,
        )
        lower = torch.gather(lower_table, 1, self._fsm_phase.unsqueeze(1)).squeeze(1)
        upper = torch.gather(upper_table, 1, self._fsm_phase.unsqueeze(1)).squeeze(1)
        self._fsm_phase_progress[:] = torch.clamp((normalized - lower) / torch.clamp(upper - lower, min=1e-6), 0, 1)
        support_offset_scale = front_support_offset_scale(
            self._fsm_phase,
            self._fsm_phase_progress,
        )
        support_unclamped = self._reference_commands[:, :8] + (
            support_offset_scale.unsqueeze(1)
            * self._fsm_diagnostic_front_support_offset_deg
        )
        support_lower = torch.tensor(
            [
                RECORDED_SAFE_COMMAND_DEG[name][0]
                + FSM_REFERENCE_MARGIN_DEG
                for name in SERVO_JOINT_NAMES
            ],
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)
        support_upper = torch.tensor(
            [
                RECORDED_SAFE_COMMAND_DEG[name][1]
                - FSM_REFERENCE_MARGIN_DEG
                for name in SERVO_JOINT_NAMES
            ],
            dtype=torch.float32,
            device=self.device,
        ).unsqueeze(0)
        support_clamped = torch.maximum(
            torch.minimum(support_unclamped, support_upper),
            support_lower,
        )
        support_offset_active = torch.any(
            torch.abs(
                support_offset_scale.unsqueeze(1)
                * self._fsm_diagnostic_front_support_offset_deg
            )
            > 1.0e-8,
            dim=1,
        )
        self._fsm_diagnostic_front_support_clamp_count += (
            support_offset_active
            & torch.any(torch.abs(support_clamped - support_unclamped) > 1.0e-7, dim=1)
        ).to(torch.long)
        self._reference_commands[:, :8] = support_clamped
        if self._external_reference_commands is None:
            wheel_forces, _ = self._wheel_contact_forces()
            load_balance_active = (self._fsm_phase >= 9) & (self._fsm_phase <= 10)
            self._fsm_front_load_trim_z_m.zero_()
            unload_rate_m_s = torch.where(
                torch.isfinite(
                    self._fsm_diagnostic_support_unload_rate_m_s
                ),
                self._fsm_diagnostic_support_unload_rate_m_s,
                torch.full_like(
                    self._fsm_diagnostic_support_unload_rate_m_s,
                    float(self.cfg.fsm_support_unload_rate_m_s),
                ),
            )
            unload_maximum_m = torch.where(
                torch.isfinite(
                    self._fsm_diagnostic_support_unload_maximum_m
                ),
                self._fsm_diagnostic_support_unload_maximum_m,
                torch.full_like(
                    self._fsm_diagnostic_support_unload_maximum_m,
                    float(self.cfg.fsm_support_unload_maximum_m),
                ),
            )
            self._fsm_support_unload_trim_m[:] = update_unload_trim(
                self._fsm_support_unload_trim_m,
                wheel_forces[:, :, 2],
                load_balance_active,
                dt_s=float(self.step_dt),
                low_force_n=float(self.cfg.fsm_support_unload_low_force_n),
                high_force_n=float(self.cfg.fsm_support_unload_high_force_n),
                rate_m_s=unload_rate_m_s,
                maximum_m=unload_maximum_m,
            )
        else:
            self._fsm_front_load_trim_z_m.zero_()
            self._fsm_support_unload_trim_m.zero_()

    def set_external_reference(self, commands: torch.Tensor | None) -> None:
        """Select exact replay commands instead of the compressed FSM bank."""
        if commands is None:
            self._external_reference_commands = None
            return
        value = torch.as_tensor(commands, dtype=torch.float32, device=self.device)
        if value.shape == (12,):
            value = value.unsqueeze(0).expand(self.num_envs, -1)
        if value.shape != (self.num_envs, 12):
            raise ValueError(f"Expected external reference shape {(self.num_envs, 12)}, got {tuple(value.shape)}")
        if not torch.isfinite(value).all():
            raise ValueError("External replay reference contains non-finite values")
        self._external_reference_commands = value.clone()

    def _fk(self, servo_raw: torch.Tensor) -> torch.Tensor:
        q1 = servo_raw[:, 0::2] + self._leg_hip_zero
        q2 = servo_raw[:, 1::2] + self._leg_knee_zero
        return torch.stack(
            (
                self._leg_l1 * torch.cos(q1) + self._leg_l2 * torch.cos(q1 + q2),
                self._leg_l1 * torch.sin(q1) + self._leg_l2 * torch.sin(q1 + q2),
            ),
            dim=2,
        )

    def _solve_ik(
        self,
        target_center: torch.Tensor,
        reference_raw: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Solve all four planar legs and select the branch nearest reference."""

        x, z = target_center[:, :, 0], target_center[:, :, 1]
        cosine = (x.square() + z.square() - self._leg_l1.square() - self._leg_l2.square()) / (
            2.0 * self._leg_l1 * self._leg_l2
        )
        workspace_valid = (cosine >= -1.0) & (cosine <= 1.0)
        magnitude = torch.acos(torch.clamp(cosine, -1.0, 1.0))
        candidates: list[torch.Tensor] = []
        costs: list[torch.Tensor] = []
        ref_q1, ref_q2 = reference_raw[:, 0::2], reference_raw[:, 1::2]
        for q2_effective in (magnitude, -magnitude):
            q1_effective = torch.atan2(z, x) - torch.atan2(
                self._leg_l2 * torch.sin(q2_effective),
                self._leg_l1 + self._leg_l2 * torch.cos(q2_effective),
            )
            q1 = q1_effective - self._leg_hip_zero
            q2 = q2_effective - self._leg_knee_zero
            candidate = torch.stack((q1, q2), dim=2)
            candidate_flat = candidate.reshape(self.num_envs, 8)
            within = (
                (candidate_flat >= self._raw_servo_lower_limits)
                & (candidate_flat <= self._raw_servo_upper_limits)
            ).reshape(self.num_envs, 4, 2).all(dim=2)
            valid = workspace_valid & within
            cost = (q1 - ref_q1).square() + (q2 - ref_q2).square()
            costs.append(torch.where(valid, cost, torch.full_like(cost, 1.0e9)))
            candidates.append(candidate)
        choose_second = costs[1] < costs[0]
        chosen = torch.where(choose_second.unsqueeze(2), candidates[1], candidates[0])
        ik_valid = torch.minimum(costs[0], costs[1]) < 1.0e8
        return chosen.reshape(self.num_envs, 8), ik_valid

    def _process_residual_actions(self) -> None:
        reference_servo_deg = self._reference_commands[:, :8]
        reference_wheels = self._reference_commands[:, 8:]
        reference_raw = self._standing_servo_pos + self._joint_command_sign * torch.deg2rad(reference_servo_deg)
        nominal_centers = self._fk(reference_raw)
        nominal_radius = torch.linalg.vector_norm(nominal_centers, dim=2)
        shortened_radius = torch.clamp(
            nominal_radius - self._fsm_support_unload_trim_m,
            min=1.0e-6,
        )
        baseline_centers = nominal_centers * (
            shortened_radius / torch.clamp(nominal_radius, min=1.0e-6)
        ).unsqueeze(2)
        diagnostic_smooth = post_transfer_offset_scale(
            self._fsm_phase.unsqueeze(1),
            self._fsm_phase_progress.unsqueeze(1),
            self._fsm_diagnostic_post_transfer_offset_start_progress,
            self._fsm_diagnostic_post_transfer_offset_start_phase,
        )
        formal_smooth = post_transfer_offset_scale(
            self._fsm_phase.unsqueeze(1),
            self._fsm_phase_progress.unsqueeze(1),
            self._fsm_post_transfer_offset_start_progress,
        )
        formal_delta = (
            formal_smooth.unsqueeze(2)
            * self._fsm_post_transfer_wheel_center_offset_m
        )
        diagnostic_delta = (
            diagnostic_smooth.unsqueeze(2)
            * self._fsm_diagnostic_wheel_center_offset_m
        )
        baseline_centers += formal_delta + diagnostic_delta
        baseline_solution, baseline_valid = self._solve_ik(baseline_centers, reference_raw)
        diagnostic_leg_active = torch.any(
            torch.abs(diagnostic_delta) > 1.0e-8,
            dim=2,
        )
        formal_leg_active = torch.any(
            torch.abs(formal_delta) > 1.0e-8,
            dim=2,
        )
        trim_leg_active = (
            (self._fsm_support_unload_trim_m > 1.0e-8)
            | diagnostic_leg_active
            | formal_leg_active
        )
        baseline_invalid = trim_leg_active & (~baseline_valid)
        self._fsm_baseline_ik_invalid_count += torch.any(
            baseline_invalid,
            dim=1,
        ).to(torch.long)
        self._fsm_baseline_ik_invalid_count_per_leg += baseline_invalid.to(
            torch.long
        )
        baseline_use = trim_leg_active & baseline_valid
        baseline_raw = torch.where(
            baseline_use.unsqueeze(2),
            baseline_solution.reshape(self.num_envs, 4, 2),
            reference_raw.reshape(self.num_envs, 4, 2),
        ).reshape(self.num_envs, 8)
        self._reference_wheel_centers[:] = self._fk(baseline_raw)
        self._reference_commands[:, :8] = torch.rad2deg(
            (baseline_raw - self._standing_servo_pos) / self._joint_command_sign
        )
        residual_enabled = residual_phase_mask(
            self._fsm_phase,
            phase_min=int(self.cfg.residual_execution_phase_min),
            phase_max=int(self.cfg.residual_execution_phase_max),
        )
        corrective_output = torch.zeros_like(
            residual_enabled,
            dtype=torch.bool,
        )
        roll_rad, pitch_rad, _ = self._roll_pitch_yaw()
        if self.cfg.residual_state_gate_type == "positive_pitch_imu_threshold":
            residual_enabled &= positive_pitch_hazard_mask(
                pitch_rad,
                minimum_pitch_rad=float(
                    self.cfg.residual_state_gate_min_pitch_rad
                ),
            )
            corrective_output = residual_enabled.clone()
        elif (
            self.cfg.residual_state_gate_type
            == "phase_aware_pitch_rate_imu_emergency"
        ):
            residual_enabled, corrective_output = (
                phase_aware_imu_emergency_masks(
                    self._fsm_phase,
                    pitch_rad,
                    self._robot.data.root_ang_vel_b[:, 1],
                    rear_transfer_phase=int(
                        self.cfg.residual_execution_phase_min
                    ),
                    post_transfer_phase_min=int(
                        self.cfg.residual_execution_phase_min
                    )
                    + 1,
                    post_transfer_phase_max=int(
                        self.cfg.residual_execution_phase_max
                    ),
                    minimum_pitch_rad=float(
                        self.cfg.residual_state_gate_min_pitch_rad
                    ),
                    early_pitch_rad=float(
                        self.cfg.residual_state_gate_early_pitch_rad
                    ),
                    early_pitch_rate_rad_s=float(
                        self.cfg.residual_state_gate_early_pitch_rate_rad_s
                    ),
                )
            )
            rear_transfer = self._fsm_phase == int(
                self.cfg.residual_execution_phase_min
            )
            self._residual_phase8_corrective_latched[:] = (
                update_phase8_corrective_latch(
                    self._fsm_phase,
                    rear_transfer & corrective_output,
                    self._residual_phase8_corrective_latched,
                    rear_transfer_phase=int(
                        self.cfg.residual_execution_phase_min
                    ),
                )
            )
            residual_enabled |= (
                rear_transfer
                & self._residual_phase8_corrective_latched
            )
            corrective_output |= (
                rear_transfer
                & self._residual_phase8_corrective_latched
            )
        elif (
            self.cfg.residual_state_gate_type
            == "phase_aware_roll_imu_emergency"
        ):
            residual_enabled, corrective_output = (
                phase_aware_roll_imu_emergency_masks(
                    self._fsm_phase,
                    roll_rad,
                    pitch_rad,
                    self._robot.data.root_ang_vel_b[:, 1],
                    rear_transfer_phase=int(
                        self.cfg.residual_execution_phase_min
                    ),
                    post_transfer_phase_min=int(
                        self.cfg.residual_execution_phase_min
                    )
                    + 1,
                    post_transfer_phase_max=int(
                        self.cfg.residual_execution_phase_max
                    ),
                    minimum_pitch_rad=float(
                        self.cfg.residual_state_gate_min_pitch_rad
                    ),
                    minimum_roll_rad=float(
                        self.cfg.residual_state_gate_min_roll_rad
                    ),
                    early_roll_rad=float(
                        self.cfg.residual_state_gate_early_roll_rad
                    ),
                    early_pitch_rate_rad_s=float(
                        self.cfg.residual_state_gate_early_pitch_rate_rad_s
                    ),
                )
            )
            rear_transfer = self._fsm_phase == int(
                self.cfg.residual_execution_phase_min
            )
            self._residual_phase8_corrective_latched[:] = (
                update_phase8_corrective_latch(
                    self._fsm_phase,
                    rear_transfer & corrective_output,
                    self._residual_phase8_corrective_latched,
                    rear_transfer_phase=int(
                        self.cfg.residual_execution_phase_min
                    ),
                )
            )
            residual_enabled |= (
                rear_transfer
                & self._residual_phase8_corrective_latched
            )
            corrective_output |= (
                rear_transfer
                & self._residual_phase8_corrective_latched
            )
        else:
            raise RuntimeError(
                "unsupported residual state gate type at runtime: "
                f"{self.cfg.residual_state_gate_type}"
            )
        phase_gated_actions = self._raw_actions * residual_enabled.to(
            self._raw_actions.dtype
        ).unsqueeze(1)
        projection_kwargs = {
            "wheel_center_z_signs": tuple(
                int(value)
                for value in self.cfg.residual_wheel_center_z_signs
            ),
            "action_mask": tuple(
                int(value) for value in self.cfg.residual_action_mask
            ),
        }
        if (
            self.cfg.residual_projection_type
            == "wheel_center_z_four_wheel_balanced_confidence_gate"
        ):
            projected_actions = project_confidence_balanced_z_gate(
                phase_gated_actions,
                activation_threshold=float(
                    self.cfg.residual_activation_threshold
                ),
                **projection_kwargs,
            )
        elif (
            self.cfg.residual_projection_type
            == "wheel_center_z_four_wheel_balanced_zero_preserving_gate"
        ):
            projected_actions = project_zero_preserving_balanced_z_gate(
                phase_gated_actions,
                **projection_kwargs,
            )
        elif (
            self.cfg.residual_projection_type
            == "wheel_center_z_four_wheel_balanced_pitch_corrective_gate"
        ):
            projected_actions = project_pitch_corrective_balanced_z_gate(
                phase_gated_actions,
                executed_wheel_center_z_signs=tuple(
                    int(value)
                    for value in self.cfg.residual_executed_wheel_center_z_signs
                ),
                **projection_kwargs,
            )
        elif (
            self.cfg.residual_projection_type
            in {
                "wheel_center_z_four_wheel_phase_aware_emergency_gate",
                "wheel_center_z_four_wheel_phase_aware_roll_emergency_gate",
                "wheel_center_z_front_right_rear_left_diagonal_emergency_gate",
                "wheel_center_z_front_right_only_ik_feasible_emergency_gate",
                "wheel_center_z_asymmetric_diagonal_ik_margin_emergency_gate",
                "wheel_center_z_deficient_diagonal_downward_support_emergency_gate",
            }
        ):
            projected_actions = (
                project_phase_aware_emergency_balanced_z_gate(
                    phase_gated_actions,
                    corrective_output,
                    executed_wheel_center_z_signs=tuple(
                        int(value)
                        for value in (
                            self.cfg
                            .residual_executed_wheel_center_z_signs
                        )
                    ),
                    corrective_wheel_center_z_scales=tuple(
                        float(value)
                        for value in (
                            self.cfg
                            .residual_corrective_wheel_center_z_scales
                        )
                    ),
                    corrective_minimum_shared_magnitude=float(
                        self.cfg
                        .residual_corrective_minimum_shared_magnitude
                    ),
                    **projection_kwargs,
                )
            )
        elif (
            self.cfg.residual_projection_type
            == "wheel_center_z_deficient_diagonal_downward_support_phase9_counter_yaw_emergency_gate"
        ):
            projected_actions = (
                project_phase_aware_emergency_support_counter_yaw_gate(
                    phase_gated_actions,
                    corrective_output,
                    self._fsm_phase,
                    wheel_center_z_signs=tuple(
                        int(value)
                        for value in self.cfg.residual_wheel_center_z_signs
                    ),
                    executed_wheel_center_z_signs=tuple(
                        int(value)
                        for value in (
                            self.cfg
                            .residual_executed_wheel_center_z_signs
                        )
                    ),
                    corrective_wheel_center_z_scales=tuple(
                        float(value)
                        for value in (
                            self.cfg
                            .residual_corrective_wheel_center_z_scales
                        )
                    ),
                    corrective_minimum_shared_magnitude=float(
                        self.cfg
                        .residual_corrective_minimum_shared_magnitude
                    ),
                    corrective_wheel_speed_minimum_shared_magnitudes=tuple(
                        float(value)
                        for value in (
                            self.cfg
                            .residual_corrective_wheel_speed_minimum_shared_magnitudes
                        )
                    ),
                    corrective_wheel_speed_signs=tuple(
                        int(value)
                        for value in (
                            self.cfg
                            .residual_corrective_wheel_speed_signs
                        )
                    ),
                    corrective_wheel_speed_scales=tuple(
                        float(value)
                        for value in (
                            self.cfg
                            .residual_corrective_wheel_speed_scales
                        )
                    ),
                    corrective_wheel_speed_phases=tuple(
                        int(value)
                        for value in (
                            self.cfg
                            .residual_corrective_wheel_speed_phases
                        )
                    ),
                    action_mask=tuple(
                        int(value)
                        for value in self.cfg.residual_action_mask
                    ),
                )
            )
        elif (
            self.cfg.residual_projection_type
            == "wheel_center_z_four_wheel_balanced_signed_magnitude"
        ):
            projected_actions = project_balanced_z_signed_magnitude(
                phase_gated_actions,
                **projection_kwargs,
            )
        else:
            raise RuntimeError(
                "unsupported residual projection type at runtime: "
                f"{self.cfg.residual_projection_type}"
            )
        self._applied_actions[:] = projected_actions
        self._applied_actions[:] = apply_phase_action_gain(
            self._applied_actions,
            self._fsm_phase,
            phase_gains=self._residual_execution_phase_gains,
            hard_clip=float(self.cfg.residual_applied_action_hard_clip),
        )
        zero_action = torch.all(self._applied_actions == 0.0, dim=1)

        bounds_x = float(self.cfg.residual_bounds["wheel_center_x_m"])
        bounds_z = float(self.cfg.residual_bounds["wheel_center_z_m"])
        residual = self._applied_actions[:, :8].reshape(
            self.num_envs, 4, 2
        ).clone()
        residual[:, :, 0] *= bounds_x
        residual[:, :, 1] *= bounds_z
        target_center = self._reference_wheel_centers + residual
        self._scaled_wheel_center_residual_m[:] = residual
        self._requested_wheel_center_target_m[:] = target_center
        chosen, ik_valid = self._solve_ik(target_center, baseline_raw)
        all_legs_valid = ik_valid.all(dim=1)
        self._ik_invalid_count += ((~all_legs_valid) & (~zero_action)).to(torch.long)
        chosen = torch.where(all_legs_valid.unsqueeze(1), chosen, baseline_raw)

        max_step = float(self.cfg.residual_servo_velocity_limit_rad_s) * float(self.step_dt)
        limited = torch.clamp(chosen, self._servo_targets - max_step, self._servo_targets + max_step)
        final_servo = torch.where(zero_action.unsqueeze(1), baseline_raw, limited)
        final_servo = torch.maximum(torch.minimum(final_servo, self._raw_servo_upper_limits), self._raw_servo_lower_limits)
        self._servo_targets[:] = final_servo
        self._final_wheel_center_target_m[:] = self._fk(final_servo)
        self._servo_command_deg[:] = torch.rad2deg((final_servo - self._standing_servo_pos) / self._joint_command_sign)

        self._scaled_wheel_speed_residual_rad_s[:] = (
            self._applied_actions[:, 8:]
            * float(self.cfg.residual_bounds["wheel_speed_rad_s"])
        )
        wheel_desired = torch.clamp(
            reference_wheels
            + self._scaled_wheel_speed_residual_rad_s,
            -float(self.cfg.wheel_max_speed_rad_s),
            float(self.cfg.wheel_max_speed_rad_s),
        )
        max_wheel_step = float(self.cfg.residual_wheel_acceleration_limit_rad_s2) * float(self.step_dt)
        wheel_limited = torch.clamp(
            wheel_desired,
            self._physical_forward_wheel_cmds - max_wheel_step,
            self._physical_forward_wheel_cmds + max_wheel_step,
        )
        self._physical_forward_wheel_cmds[:] = torch.where(zero_action.unsqueeze(1), reference_wheels, wheel_limited)
        self._raw_joint_wheel_velocity_targets[:] = self._physical_forward_wheel_cmds * self._wheel_forward_sign
        self._check_finite_tensor("residual.servo_targets", self._servo_targets)
        self._check_finite_tensor("residual.wheel_targets", self._raw_joint_wheel_velocity_targets)

    def _wheel_contact_forces(self) -> tuple[torch.Tensor, torch.Tensor]:
        forces = self._contact_sensor.data.net_forces_w[:, self._contact_wheel_ids, :]
        return forces, torch.linalg.vector_norm(forces, dim=2)

    def _longitudinal_margin(self) -> tuple[torch.Tensor, torch.Tensor]:
        self._refresh_contact_state()
        forces, _ = self._wheel_contact_forces()
        upward = forces[:, :, 2]
        valid_support = (
            (upward >= float(self.cfg.contact_force_threshold_n))
            & (self._wheel_on_ground | self._wheel_on_top)
            & (~self._wheel_on_front_face)
        )
        wheel_x = self._wheel_pos_local()[:, :, 0]
        positive_inf = torch.full_like(wheel_x, float("inf"))
        negative_inf = torch.full_like(wheel_x, float("-inf"))
        support_min = torch.min(torch.where(valid_support, wheel_x, positive_inf), dim=1).values
        support_max = torch.max(torch.where(valid_support, wheel_x, negative_inf), dim=1).values
        count = valid_support.sum(dim=1)
        total_force = torch.sum(torch.where(valid_support, upward, torch.zeros_like(upward)), dim=1)
        valid = (count >= 2) & ((support_max - support_min) >= 0.03) & (
            total_force >= float(self.cfg.contact_force_threshold_n)
        )
        com_x = self._compute_com_xy()[0][:, 0]
        margin = torch.minimum(com_x - support_min, support_max - com_x)
        margin = torch.where(valid, margin, torch.zeros_like(margin))
        return margin, valid

    def _get_observations(self) -> dict[str, torch.Tensor]:
        if not self._residual_ready:
            return super()._get_observations()
        self._refresh_contact_state()
        root = self._root_pos_local()
        roll, pitch, _ = self._roll_pitch_yaw()
        front_relative = self._obstacle_front_x() - root[:, 0]
        top_relative = float(self.cfg.obstacle_height) - root[:, 2]
        detection_valid = torch.ones((self.num_envs, 1), dtype=torch.float32, device=self.device)
        detection_age = torch.zeros_like(detection_valid)
        obstacle_obs = torch.cat(
            (
                (self._obstacle_height_env / 0.10).unsqueeze(1),
                front_relative.unsqueeze(1),
                (-root[:, 1] / 0.5).unsqueeze(1),
                (top_relative / 0.20).unsqueeze(1),
                detection_valid,
                detection_age,
            ),
            dim=1,
        )
        obstacle_obs[:, :4] += self._obstacle_observation_noise
        phase_one_hot = torch.nn.functional.one_hot(self._fsm_phase, num_classes=PHASE_COUNT).to(torch.float32)
        elapsed_norm = torch.clamp(
            self.episode_length_buf.to(torch.float32) * float(self.step_dt)
            / torch.clamp(self._reference_bank.duration_s(self._obstacle_height_env), min=1.0e-6),
            0,
            1,
        ).unsqueeze(1)
        fsm_obs = torch.cat(
            (
                phase_one_hot,
                self._fsm_phase_progress.unsqueeze(1),
                elapsed_norm,
                self._reference_wheel_centers.reshape(self.num_envs, 8) / 0.35,
                self._reference_commands[:, 8:] / float(self.cfg.wheel_max_speed_rad_s),
            ),
            dim=1,
        )
        projected_gravity = self._robot.data.projected_gravity_b
        imu_acc = (self._robot.data.root_lin_vel_b - self._last_root_lin_vel_b) / float(self.step_dt)
        base_obs = torch.cat(
            (
                projected_gravity,
                torch.stack((roll, pitch), dim=1),
                self._robot.data.root_ang_vel_b / 5.0,
                self._robot.data.root_lin_vel_b / 2.0,
                torch.clamp(imu_acc / 20.0, -5.0, 5.0),
                (root[:, 2] / 0.5).unsqueeze(1),
            ),
            dim=1,
        )
        servo_pos = self._robot.data.joint_pos[:, self._servo_joint_ids]
        servo_vel = self._robot.data.joint_vel[:, self._servo_joint_ids]
        half = torch.clamp((self._raw_servo_upper_limits - self._raw_servo_lower_limits) * 0.5, min=1.0e-5)
        center = (self._raw_servo_upper_limits + self._raw_servo_lower_limits) * 0.5
        joint_norm = (servo_pos - center) / half
        limit_distance = torch.minimum(
            servo_pos - self._raw_servo_lower_limits,
            self._raw_servo_upper_limits - servo_pos,
        ) / half
        tracking = (self._servo_targets - servo_pos) / half
        proprio = torch.cat(
            (
                joint_norm,
                servo_vel / 5.0,
                self._physical_wheel_velocities() / float(self.cfg.wheel_max_speed_rad_s),
                self._previous_actions,
                tracking,
                limit_distance,
            ),
            dim=1,
        )
        actor = torch.cat((obstacle_obs, fsm_obs, base_obs, proprio), dim=1)
        if actor.shape[1] != ACTOR_OBS_DIM:
            raise RuntimeError(f"Actor observation dimension mismatch: {actor.shape[1]} != {ACTOR_OBS_DIM}")

        forces, force_magnitude = self._wheel_contact_forces()
        margin, margin_valid = self._longitudinal_margin()
        contact_one_hot = torch.nn.functional.one_hot(self._wheel_contact_state, num_classes=4).to(torch.float32)
        com_xy = self._compute_com_xy()[0]
        critic_extra = torch.cat(
            (
                self._obstacle_height_env.unsqueeze(1),
                contact_one_hot.reshape(self.num_envs, 16),
                force_magnitude / 50.0,
                (self._wheel_pos_local() - root.unsqueeze(1)).reshape(self.num_envs, 12),
                torch.cat((com_xy - root[:, :2], (root[:, 2:3] * 0.0)), dim=1),
                margin.unsqueeze(1),
                margin_valid.to(torch.float32).unsqueeze(1),
                self._robot.data.root_vel_w / 5.0,
                self._scenario_friction.unsqueeze(1),
                (self._action_delay_steps.to(torch.float32) / 2.0).unsqueeze(1),
                torch.ones((self.num_envs, 1), device=self.device),
                torch.stack(
                    (
                        torch.full_like(self._obstacle_height_env, self._obstacle_front_x()),
                        torch.zeros_like(self._obstacle_height_env),
                        self._obstacle_height_env,
                    ),
                    dim=1,
                ),
            ),
            dim=1,
        )
        critic = torch.cat((actor, critic_extra), dim=1)
        if critic.shape[1] != CRITIC_STATE_DIM:
            raise RuntimeError(f"Critic state dimension mismatch: {critic.shape[1]} != {CRITIC_STATE_DIM}")
        self._check_finite_tensor("residual.observation.actor", actor)
        self._check_finite_tensor("residual.observation.critic", critic)
        self._last_root_lin_vel_b[:] = self._robot.data.root_lin_vel_b
        return {"policy": actor, "critic": critic}

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        if not self._residual_ready:
            return super()._get_dones()
        self._refresh_contact_state()
        root = self._root_pos_local()
        roll, pitch, _ = self._roll_pitch_yaw()
        forces, _ = self._wheel_contact_forces()
        all_force_supported = torch.all(forces[:, :, 2] >= float(self.cfg.contact_force_threshold_n), dim=1)
        stable = (
            self._all_wheels_on_top
            & all_force_supported
            & (torch.abs(roll) <= float(self.cfg.max_stable_tilt_rad))
            & (torch.abs(pitch) <= float(self.cfg.max_stable_tilt_rad))
            & (
                torch.linalg.vector_norm(self._robot.data.root_ang_vel_b, dim=1)
                <= float(self.cfg.max_stable_angular_velocity_rad_s)
            )
        )
        self._fall_buf[:] = self._compute_fall(roll, pitch, root)
        nonwheel_forces = self._contact_sensor.data.net_forces_w[:, self._contact_nonwheel_ids, :]
        nonwheel_contact = torch.any(torch.linalg.vector_norm(nonwheel_forces, dim=2) > 5.0, dim=1)
        body_collision = nonwheel_contact
        numerical = ~torch.isfinite(self._robot.data.root_state_w).all(dim=1)
        position = self._robot.data.joint_pos[:, self._servo_joint_ids]
        tolerance = float(self.cfg.joint_limit_violation_tolerance_rad)
        joint_limit = torch.any(
            (position < self._raw_servo_lower_limits - tolerance)
            | (position > self._raw_servo_upper_limits + tolerance),
            dim=1,
        )
        joint_limit_per_joint = (
            (position < self._raw_servo_lower_limits - tolerance)
            | (position > self._raw_servo_upper_limits + tolerance)
        )
        first_joint_limit = joint_limit & (~self._joint_limit_violation_latched)
        self._joint_limit_first_position = torch.where(
            first_joint_limit.unsqueeze(1),
            position,
            self._joint_limit_first_position,
        )
        self._joint_limit_first_violation = torch.where(
            first_joint_limit.unsqueeze(1),
            joint_limit_per_joint,
            self._joint_limit_first_violation,
        )
        self._joint_limit_violation_latched |= joint_limit
        phase_bounds = self._phase_bounds_by_height()
        phase_lower = torch.cat(
            (
                torch.zeros((self.num_envs, 1), dtype=torch.float32, device=self.device),
                phase_bounds,
                torch.ones((self.num_envs, 1), dtype=torch.float32, device=self.device),
            ),
            dim=1,
        )
        phase_upper = torch.cat(
            (
                phase_bounds,
                torch.ones((self.num_envs, 2), dtype=torch.float32, device=self.device),
            ),
            dim=1,
        )
        env_index = torch.arange(self.num_envs, device=self.device)
        phase_width = phase_upper[env_index, self._fsm_phase] - phase_lower[
            env_index, self._fsm_phase
        ]
        phase_timeout_steps = torch.ceil(
            phase_width
            * self._reference_bank.duration_s(self._obstacle_height_env)
            * float(self.cfg.phase_timeout_scale)
            / float(self.step_dt)
        ).to(torch.long)
        self._phase_timeout_buf[:] = (
            (self._phase_elapsed_counter > torch.clamp(phase_timeout_steps, min=3))
            & (self._external_reference_commands is None)
            & (self._fsm_phase >= 2)
            & (self._fsm_phase <= 10)
        )
        unsafe = (
            self._fall_buf
            | body_collision
            | numerical
            | self._joint_limit_violation_latched
            | self._phase_timeout_buf
        )
        stable &= ~unsafe
        self._stable_dwell_counter = torch.where(
            stable, self._stable_dwell_counter + 1, torch.zeros_like(self._stable_dwell_counter)
        )
        required = math.ceil(float(self.cfg.stable_dwell_s) / float(self.step_dt))
        self._success_buf[:] = (self._stable_dwell_counter >= required) & (~unsafe)
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        success_termination = (
            self._success_buf
            if bool(self.cfg.terminate_on_residual_success)
            else torch.zeros_like(self._success_buf)
        )
        terminated = (
            success_termination
            | self._fall_buf
            | body_collision
            | numerical
            | self._joint_limit_violation_latched
            | self._phase_timeout_buf
        )
        if bool(self.cfg.disable_episode_termination):
            # Exact command replays must dispatch their entire immutable event
            # sequence.  The runner records failure predicates separately.
            terminated = torch.zeros_like(terminated)
        done = terminated | time_out
        self._last_done_success = torch.where(done, self._success_buf, self._last_done_success)
        self._last_done_fall = torch.where(done, self._fall_buf, self._last_done_fall)
        self._last_done_collision = torch.where(done, body_collision, self._last_done_collision)
        self._last_done_numerical = torch.where(done, numerical, self._last_done_numerical)
        self._last_done_joint_limit = torch.where(
            done, self._joint_limit_violation_latched, self._last_done_joint_limit
        )
        self._last_done_joint_position = torch.where(
            done.unsqueeze(1),
            self._joint_limit_first_position,
            self._last_done_joint_position,
        )
        self._last_done_joint_limit_violation = torch.where(
            done.unsqueeze(1),
            self._joint_limit_first_violation,
            self._last_done_joint_limit_violation,
        )
        margin, margin_valid = self._longitudinal_margin()
        self._last_done_root_x = torch.where(done, root[:, 0], self._last_done_root_x)
        self._last_done_margin = torch.where(done, margin, self._last_done_margin)
        self._last_done_margin_valid = torch.where(done, margin_valid, self._last_done_margin_valid)
        self._last_done_pitch = torch.where(done, pitch, self._last_done_pitch)
        self._last_done_roll = torch.where(done, roll, self._last_done_roll)
        self._last_done_pitch_rate = torch.where(
            done, self._robot.data.root_ang_vel_b[:, 1], self._last_done_pitch_rate
        )
        self._last_done_fsm_phase = torch.where(done, self._fsm_phase, self._last_done_fsm_phase)
        self._last_done_phase_timeout = torch.where(
            done, self._phase_timeout_buf, self._last_done_phase_timeout
        )
        wheel_force_magnitude = torch.linalg.vector_norm(forces, dim=2)
        wheel_position = self._wheel_pos_local()
        wheel_position_xz = wheel_position[:, :, (0, 2)]
        support_score = self.compute_com_support_metrics(
            update_cache=False
        )["score"]
        self._last_done_wheel_contact_state = torch.where(
            done.unsqueeze(1),
            self._wheel_contact_state,
            self._last_done_wheel_contact_state,
        )
        self._last_done_wheel_contact_force_n = torch.where(
            done.unsqueeze(1),
            wheel_force_magnitude,
            self._last_done_wheel_contact_force_n,
        )
        self._last_done_wheel_contact_upward_force_n = torch.where(
            done.unsqueeze(1),
            forces[:, :, 2],
            self._last_done_wheel_contact_upward_force_n,
        )
        self._last_done_wheel_on_top = torch.where(
            done.unsqueeze(1),
            self._wheel_on_top,
            self._last_done_wheel_on_top,
        )
        self._last_done_full_wheel_on_top = torch.where(
            done.unsqueeze(1),
            self._full_wheel_on_top,
            self._last_done_full_wheel_on_top,
        )
        self._last_done_all_wheels_on_top = torch.where(
            done,
            self._all_wheels_on_top,
            self._last_done_all_wheels_on_top,
        )
        self._last_done_support_score = torch.where(
            done,
            support_score,
            self._last_done_support_score,
        )
        self._last_done_wheel_position_xz = torch.where(
            done[:, None, None],
            wheel_position_xz,
            self._last_done_wheel_position_xz,
        )
        self._last_done_wheel_position_y = torch.where(
            done.unsqueeze(1),
            wheel_position[:, :, 1],
            self._last_done_wheel_position_y,
        )
        self._last_done_reference_commands = torch.where(
            done.unsqueeze(1),
            self._reference_commands,
            self._last_done_reference_commands,
        )
        self._last_done_residual_action = torch.where(
            done.unsqueeze(1),
            self._raw_actions,
            self._last_done_residual_action,
        )
        self._last_done_applied_residual_action = torch.where(
            done.unsqueeze(1),
            self._applied_actions,
            self._last_done_applied_residual_action,
        )
        self._last_done_scaled_wheel_center_residual_m = torch.where(
            done[:, None, None],
            self._scaled_wheel_center_residual_m,
            self._last_done_scaled_wheel_center_residual_m,
        )
        self._last_done_scaled_wheel_speed_residual_rad_s = torch.where(
            done.unsqueeze(1),
            self._scaled_wheel_speed_residual_rad_s,
            self._last_done_scaled_wheel_speed_residual_rad_s,
        )
        self._last_done_requested_wheel_center_target_m = torch.where(
            done[:, None, None],
            self._requested_wheel_center_target_m,
            self._last_done_requested_wheel_center_target_m,
        )
        self._last_done_final_wheel_center_target_m = torch.where(
            done[:, None, None],
            self._final_wheel_center_target_m,
            self._last_done_final_wheel_center_target_m,
        )
        self._last_done_servo_targets = torch.where(
            done.unsqueeze(1),
            self._servo_targets,
            self._last_done_servo_targets,
        )
        self._last_done_wheel_targets_rad_s = torch.where(
            done.unsqueeze(1),
            self._physical_forward_wheel_cmds,
            self._last_done_wheel_targets_rad_s,
        )
        self._last_done_fsm_front_load_trim_z_m = torch.where(
            done.unsqueeze(1),
            self._fsm_front_load_trim_z_m,
            self._last_done_fsm_front_load_trim_z_m,
        )
        self._last_done_fsm_support_unload_trim_m = torch.where(
            done.unsqueeze(1),
            self._fsm_support_unload_trim_m,
            self._last_done_fsm_support_unload_trim_m,
        )
        self._last_done_fsm_baseline_ik_invalid_count = torch.where(
            done,
            self._fsm_baseline_ik_invalid_count,
            self._last_done_fsm_baseline_ik_invalid_count,
        )
        self._last_done_fsm_baseline_ik_invalid_count_per_leg = torch.where(
            done.unsqueeze(1),
            self._fsm_baseline_ik_invalid_count_per_leg,
            self._last_done_fsm_baseline_ik_invalid_count_per_leg,
        )
        self._last_done_fsm_diagnostic_front_support_clamp_count = torch.where(
            done,
            self._fsm_diagnostic_front_support_clamp_count,
            self._last_done_fsm_diagnostic_front_support_clamp_count,
        )
        nonwheel_force_magnitude = torch.linalg.vector_norm(nonwheel_forces, dim=2)
        self._last_done_nonwheel_contact_force_n = torch.where(
            done.unsqueeze(1),
            nonwheel_force_magnitude,
            self._last_done_nonwheel_contact_force_n,
        )
        return terminated, time_out

    def _get_rewards(self) -> torch.Tensor:
        if not self._residual_ready:
            return super()._get_rewards()
        self._refresh_contact_state()
        root_x = self._root_pos_local()[:, 0]
        progress = torch.clamp(root_x - self._last_base_x, -0.05, 0.05)
        phase_delta, phase_coordinate = monotonic_phase_progress_delta(
            self._fsm_phase,
            self._fsm_phase_progress,
            self._last_fsm_progress,
        )
        margin, margin_valid = self._longitudinal_margin()
        transfer = (self._fsm_phase >= 4) & (self._fsm_phase <= 8) & (progress > 0.0)
        com_raw = torch.where(margin >= 0, torch.clamp(margin, max=0.03), 3.0 * margin)
        com_raw = torch.where(margin_valid & transfer, com_raw, torch.zeros_like(com_raw))
        roll, pitch, _ = self._roll_pitch_yaw()
        wheel_surface_speed = self._physical_wheel_velocities() * self._estimated_wheel_radius.unsqueeze(1)
        slip = torch.mean(
            torch.abs(wheel_surface_speed - self._robot.data.root_lin_vel_b[:, 0:1])
            / torch.clamp(torch.abs(wheel_surface_speed), min=0.10),
            dim=1,
        )
        forces, force_magnitude = self._wheel_contact_forces()
        impact = torch.relu(force_magnitude - self._last_contact_force - 5.0).mean(dim=1)
        servo_vel = self._robot.data.joint_vel[:, self._servo_joint_ids]
        joint_accel = torch.mean(torch.square((servo_vel - self._last_joint_vel) / float(self.step_dt)), dim=1)
        position = self._robot.data.joint_pos[:, self._servo_joint_ids]
        joint_limit = torch.any(
            (position < self._raw_servo_lower_limits - float(self.cfg.joint_limit_violation_tolerance_rad))
            | (position > self._raw_servo_upper_limits + float(self.cfg.joint_limit_violation_tolerance_rad)),
            dim=1,
        ).to(torch.float32)
        body_collision = torch.any(
            torch.linalg.vector_norm(
                self._contact_sensor.data.net_forces_w[
                    :, self._contact_nonwheel_ids, :
                ],
                dim=2,
            )
            > 5.0,
            dim=1,
        ).to(torch.float32)
        numerical = (
            ~torch.isfinite(self._robot.data.root_state_w).all(dim=1)
        ).to(torch.float32)
        step_dt = float(self.step_dt)
        raw = {
            "progress": progress,
            "phase_progress": phase_delta,
            "success": self._success_buf.to(torch.float32),
            "top_contact": (
                self._full_wheel_on_top.to(torch.float32).mean(dim=1)
                * float(self.step_dt)
            ),
            "recovery": (
                ((self._fsm_phase >= 9) & (torch.abs(pitch) < 0.15)).to(
                    torch.float32
                )
                * float(self.step_dt)
            ),
            "com_margin": com_raw,
            "pitch_rate_sq": integrate_rate(
                torch.square(self._robot.data.root_ang_vel_b[:, 1]),
                step_dt,
            ),
            "excessive_tilt": integrate_rate(
                (torch.abs(roll) + torch.abs(pitch)).square(),
                step_dt,
            ),
            "slip": integrate_rate(
                torch.clamp(slip, 0.0, 5.0),
                step_dt,
            ),
            "fall": self._fall_buf.to(torch.float32),
            "body_collision": body_collision,
            "numerical": numerical,
            "phase_timeout": self._phase_timeout_buf.to(torch.float32),
            "contact_impact": impact,
            "residual_magnitude": integrate_rate(
                torch.mean(torch.square(self._raw_actions), dim=1),
                step_dt,
            ),
            "residual_left_right_asymmetry": integrate_rate(
                torch.mean(
                    torch.square(
                        torch.cat(
                            (
                                self._raw_actions[:, 0:2]
                                - self._raw_actions[:, 2:4],
                                self._raw_actions[:, 4:6]
                                - self._raw_actions[:, 6:8],
                                (
                                    self._raw_actions[:, 8]
                                    - self._raw_actions[:, 9]
                                ).unsqueeze(1),
                                (
                                    self._raw_actions[:, 10]
                                    - self._raw_actions[:, 11]
                                ).unsqueeze(1),
                            ),
                            dim=1,
                        )
                    ),
                    dim=1,
                ),
                step_dt,
            ),
            "action_rate": torch.mean(torch.square(self._raw_actions - self._previous_actions), dim=1),
            "joint_acceleration": integrate_rate(
                torch.clamp(joint_accel, 0.0, 1.0e5),
                step_dt,
            ),
            "wheel_speed_saturation": integrate_rate(
                torch.any(
                    torch.abs(self._physical_forward_wheel_cmds)
                    >= float(self.cfg.wheel_max_speed_rad_s) - 1.0e-4,
                    dim=1,
                ).to(torch.float32),
                step_dt,
            ),
            "joint_limit": joint_limit,
            "time": torch.ones(self.num_envs, dtype=torch.float32, device=self.device),
            "stuck": integrate_boolean_occupancy(
                self._stuck_buf,
                float(self.step_dt),
            ),
        }
        total = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
        for name, value in raw.items():
            weight = float(self.cfg.residual_reward_weights[name])
            weighted = value * weight
            self._reward_episode_raw_sums[name] += value
            self._residual_episode_sums[name] += weighted
            self._last_raw_reward_terms[name] = value
            self._last_weighted_reward_terms[name] = weighted
            total += weighted
        self._last_base_x[:] = root_x
        self._last_fsm_progress[:] = phase_coordinate
        self._last_contact_force[:] = force_magnitude
        self._last_joint_vel[:] = servo_vel
        self.extras["reward_terms_raw"] = {name: value.detach() for name, value in raw.items()}
        self.extras["reward_terms_weighted"] = {
            name: value.detach() for name, value in self._last_weighted_reward_terms.items()
        }
        return total

    def _reset_idx(self, env_ids: Sequence[int] | torch.Tensor | None) -> None:
        if env_ids is None:
            env_ids = self._robot._ALL_INDICES
        if not isinstance(env_ids, torch.Tensor):
            env_ids = torch.as_tensor(env_ids, dtype=torch.long, device=self.device)
        super()._reset_idx(env_ids)
        if not self._residual_ready:
            return
        if self._training_randomization_level_cfg is not None:
            self._apply_training_randomization(env_ids)
        self._stable_dwell_counter[env_ids] = 0
        self._joint_limit_violation_latched[env_ids] = False
        self._joint_limit_first_position[env_ids] = float("nan")
        self._joint_limit_first_violation[env_ids] = False
        self._ik_invalid_count[env_ids] = 0
        self._fsm_baseline_ik_invalid_count[env_ids] = 0
        self._fsm_baseline_ik_invalid_count_per_leg[env_ids] = 0
        self._fsm_diagnostic_front_support_clamp_count[env_ids] = 0
        self._residual_saturation_count[env_ids] = 0
        self._fsm_phase[env_ids] = 0
        self._fsm_phase_progress[env_ids] = 0
        self._reference_progress[env_ids] = 0
        self._phase_elapsed_counter[env_ids] = 0
        self._phase_exit_debounce_counter[env_ids] = 0
        self._phase_exit_latched[env_ids] = False
        self._phase_gate_waiting[env_ids] = False
        self._residual_phase8_corrective_latched[env_ids] = False
        self._fsm_front_load_trim_z_m[env_ids] = 0
        self._fsm_support_unload_trim_m[env_ids] = 0
        self._phase_timeout_buf[env_ids] = False
        self._last_fsm_progress[env_ids] = 0
        self._last_root_lin_vel_b[env_ids] = 0
        self._last_joint_vel[env_ids] = 0
        self._last_contact_force[env_ids] = 0
        self._action_history[:, env_ids] = 0
        self._applied_actions[env_ids] = 0
        for value in self._reward_episode_raw_sums.values():
            value[env_ids] = 0
        for value in self._residual_episode_sums.values():
            value[env_ids] = 0

    def residual_diagnostics(self, env_id: int = 0) -> dict[str, Any]:
        index = int(env_id)
        return {
            "fsm_phase": int(self._fsm_phase[index].item()),
            "fsm_phase_progress": float(self._fsm_phase_progress[index].item()),
            "reference_commands": self._reference_commands[index].detach().cpu().tolist(),
            "reference_wheel_centers_m": self._reference_wheel_centers[index].detach().cpu().tolist(),
            "residual_action": self._raw_actions[index].detach().cpu().tolist(),
            "applied_residual_action": self._applied_actions[
                index
            ].detach().cpu().tolist(),
            "servo_target_raw_rad": self._servo_targets[index].detach().cpu().tolist(),
            "wheel_target_physical_rad_s": self._physical_forward_wheel_cmds[index].detach().cpu().tolist(),
            "ik_invalid_count": int(self._ik_invalid_count[index].item()),
            "fsm_baseline_ik_invalid_count": int(
                self._fsm_baseline_ik_invalid_count[index].item()
            ),
            "fsm_diagnostic_front_support_clamp_count": int(
                self._fsm_diagnostic_front_support_clamp_count[index].item()
            ),
            "residual_saturation_count": int(self._residual_saturation_count[index].item()),
            "success_dwell_steps": int(self._stable_dwell_counter[index].item()),
            "reward_terms_raw": {
                name: float(value[index].item()) for name, value in self._last_raw_reward_terms.items()
            },
            "reward_terms_weighted": {
                name: float(value[index].item()) for name, value in self._last_weighted_reward_terms.items()
            },
        }

    def configure_scenarios(
        self,
        *,
        actuator_delay_steps: Sequence[int] | torch.Tensor,
        obstacle_observation_noise: Sequence[Sequence[float]] | torch.Tensor,
        friction: Sequence[float] | torch.Tensor | None = None,
    ) -> None:
        """Apply paired per-environment scenario parameters before evaluation."""
        delay = torch.as_tensor(actuator_delay_steps, dtype=torch.long, device=self.device)
        noise = torch.as_tensor(obstacle_observation_noise, dtype=torch.float32, device=self.device)
        if delay.shape != (self.num_envs,) or torch.any((delay < 0) | (delay > 2)):
            raise ValueError("actuator_delay_steps must have shape [num_envs] and values in [0, 2]")
        if noise.shape != (self.num_envs, 4) or not torch.isfinite(noise).all():
            raise ValueError("obstacle_observation_noise must have finite shape [num_envs, 4]")
        self._action_delay_steps[:] = delay
        self._obstacle_observation_noise[:] = noise
        self._action_history.zero_()
        if friction is None:
            return
        values = torch.as_tensor(friction, dtype=torch.float32, device="cpu")
        if values.shape != (self.num_envs,) or not torch.isfinite(values).all() or torch.any(values <= 0):
            raise ValueError("friction must have finite positive shape [num_envs]")
        env_ids = torch.arange(self.num_envs, dtype=torch.long, device="cpu")
        self._scenario_friction[:] = values.to(self.device)
        self._write_scenario_friction()

    def _write_scenario_friction(self) -> None:
        """Write the complete per-environment friction tensor to both assets."""

        values = self._scenario_friction.detach().cpu()
        env_ids = torch.arange(self.num_envs, dtype=torch.long, device="cpu")
        for asset in (self._robot, self._obstacle):
            materials = asset.root_physx_view.get_material_properties()
            for env_index in range(self.num_envs):
                materials[env_index, :, 0] = values[env_index]
                materials[env_index, :, 1] = values[env_index]
                materials[env_index, :, 2] = 0.0
            asset.root_physx_view.set_material_properties(materials, env_ids)

    def configure_training_randomization(
        self,
        *,
        level_cfg: dict[str, Any],
        seed: int,
        nominal_distance_m: float,
    ) -> None:
        """Enable deterministic bounded randomization on each subsequent reset."""

        # Validate the registered bounds before enabling the reset hook.
        sample_training_scenario(
            seed=seed,
            env_id=0,
            episode_index=0,
            nominal_distance_m=nominal_distance_m,
            level_cfg=level_cfg,
        )
        self._training_randomization_level_cfg = dict(level_cfg)
        self._training_randomization_seed = int(seed)
        self._training_nominal_distance_m = float(nominal_distance_m)
        self._training_episode_index.zero_()
        self._training_initial_distance_m.fill_(self._training_nominal_distance_m)
        self._training_initial_pitch_rad.zero_()

    def _apply_training_randomization(self, env_ids: torch.Tensor) -> None:
        rows = [
            sample_training_scenario(
                seed=self._training_randomization_seed,
                env_id=int(env_id),
                episode_index=int(self._training_episode_index[env_id].item()),
                nominal_distance_m=self._training_nominal_distance_m,
                level_cfg=self._training_randomization_level_cfg,
            )
            for env_id in env_ids.detach().cpu().tolist()
        ]
        self._training_episode_index[env_ids] += 1
        delay = torch.tensor(
            [row["actuator_delay_steps"] for row in rows],
            dtype=torch.long,
            device=self.device,
        )
        noise = torch.tensor(
            [row["obstacle_observation_noise"] for row in rows],
            dtype=torch.float32,
            device=self.device,
        )
        friction = torch.tensor(
            [row["friction"] for row in rows],
            dtype=torch.float32,
            device=self.device,
        )
        self._action_delay_steps[env_ids] = delay
        self._obstacle_observation_noise[env_ids] = noise
        self._action_history[:, env_ids] = 0
        self._scenario_friction[env_ids] = friction
        self._write_scenario_friction()

        desired_distance = torch.tensor(
            [row["initial_distance_m"] for row in rows],
            dtype=torch.float32,
            device=self.device,
        )
        pitch = torch.tensor(
            [row["initial_pitch_rad"] for row in rows],
            dtype=torch.float32,
            device=self.device,
        )
        self._training_initial_distance_m[env_ids] = desired_distance
        self._training_initial_pitch_rad[env_ids] = pitch
        root_pose = self._robot.data.default_root_state[env_ids, :7].clone()
        root_pose[:, :3] += self.scene.env_origins[env_ids]
        wheel_relative_b = self._training_standing_wheel_relative_b[env_ids]
        desired_quat = quat_from_euler_xyz(
            torch.zeros_like(pitch),
            pitch,
            torch.zeros_like(pitch),
        )
        desired_wheel_relative = quat_apply(
            desired_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
            wheel_relative_b.reshape(-1, 3),
        ).reshape(len(rows), 4, 3)
        root_xz_local = cache_independent_reset_root_xz(
            obstacle_front_x_m=self._obstacle_front_x(),
            desired_distance_m=desired_distance,
            desired_wheel_relative_m=desired_wheel_relative,
            wheel_radius_m=self._estimated_wheel_radius[env_ids],
        )
        root_pose[:, 0] = self.scene.env_origins[env_ids, 0] + root_xz_local[:, 0]
        root_pose[:, 2] = self.scene.env_origins[env_ids, 2] + root_xz_local[:, 1]
        root_pose[:, 3:7] = desired_quat
        self._robot.write_root_pose_to_sim(root_pose, env_ids)
        self._robot.write_root_velocity_to_sim(
            torch.zeros((len(rows), 6), dtype=torch.float32, device=self.device),
            env_ids,
        )
        root_x_local = root_pose[:, 0] - self.scene.env_origins[env_ids, 0]
        self._last_base_x[env_ids] = root_x_local
        self._episode_max_base_x[env_ids] = root_x_local
        self._last_distance_to_obstacle_front[env_ids] = desired_distance
        self._episode_min_distance_to_obstacle_front[env_ids] = desired_distance

    def configure_diagnostic_wheel_center_offsets(
        self,
        offsets_m: Sequence[Sequence[Sequence[float]]] | torch.Tensor,
    ) -> None:
        """Set phase-9/10-only offsets for explicit development grid searches."""

        offsets = torch.as_tensor(offsets_m, dtype=torch.float32, device=self.device)
        expected = (self.num_envs, 4, 2)
        if offsets.shape != expected:
            raise ValueError(
                f"diagnostic offsets must have shape {expected}, got {tuple(offsets.shape)}"
            )
        if not torch.isfinite(offsets).all() or torch.any(torch.abs(offsets) > 0.020):
            raise ValueError("diagnostic offsets must be finite and within +/-0.020 m")
        self._fsm_diagnostic_wheel_center_offset_m[:] = offsets

    def configure_diagnostic_post_transfer_offset_start_progress(
        self,
        start_progress: Sequence[float] | torch.Tensor,
    ) -> None:
        """Set the per-environment phase-9 progress where offset ramping starts."""

        values = torch.as_tensor(
            start_progress,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs,)
        if values.shape != expected:
            raise ValueError(
                f"diagnostic offset start progress must have shape {expected}"
            )
        if (
            not torch.isfinite(values).all()
            or torch.any(values < 0.0)
            or torch.any(values >= 1.0)
        ):
            raise ValueError(
                "diagnostic offset start progress must be within [0, 1)"
            )
        self._fsm_diagnostic_post_transfer_offset_start_progress[:] = (
            values.unsqueeze(1)
        )

    def configure_diagnostic_post_transfer_leg_offset_start_progress(
        self,
        start_progress: Sequence[Sequence[float]] | torch.Tensor,
    ) -> None:
        """Set phase-9 offset-ramp start independently for all four legs."""

        values = torch.as_tensor(
            start_progress,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs, 4)
        if values.shape != expected:
            raise ValueError(
                f"diagnostic per-leg offset start must have shape {expected}"
            )
        if (
            not torch.isfinite(values).all()
            or torch.any(values < 0.0)
            or torch.any(values >= 1.0)
        ):
            raise ValueError(
                "diagnostic per-leg offset start must be within [0, 1)"
            )
        self._fsm_diagnostic_post_transfer_offset_start_progress[:] = values

    def configure_diagnostic_post_transfer_leg_offset_start_phase(
        self,
        start_phase: Sequence[Sequence[int]] | torch.Tensor,
    ) -> None:
        """Set offset-ramp activation phase independently for all four legs."""

        values = torch.as_tensor(
            start_phase,
            dtype=torch.long,
            device=self.device,
        )
        expected = (self.num_envs, 4)
        if values.shape != expected:
            raise ValueError(
                f"diagnostic per-leg offset phase must have shape {expected}"
            )
        if torch.any(values < 6) or torch.any(values > 9):
            raise ValueError(
                "diagnostic per-leg offset phase must be within [6, 9]"
            )
        self._fsm_diagnostic_post_transfer_offset_start_phase[:] = values

    def configure_diagnostic_rear_transfer_wheel_speed(
        self,
        speed_rad_s: Sequence[Sequence[float]] | torch.Tensor,
    ) -> None:
        """Set per-wheel physical-forward speeds for phase-7/8 diagnostics."""

        values = torch.as_tensor(
            speed_rad_s,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs, 4)
        if values.shape != expected:
            raise ValueError(
                f"diagnostic rear-transfer speed must have shape {expected}"
            )
        if not torch.isfinite(values).all() or torch.any(torch.abs(values) > 0.3):
            raise ValueError(
                "diagnostic rear-transfer speeds must be finite within +/-0.3 rad/s"
            )
        self._fsm_diagnostic_rear_transfer_wheel_speed_rad_s[:] = values

    def configure_diagnostic_post_transfer_forward_speed(
        self,
        speed_rad_s: Sequence[float] | torch.Tensor,
    ) -> None:
        """Set per-environment physical-forward speeds for phase-9/10 diagnostics."""

        values = torch.as_tensor(
            speed_rad_s,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs,)
        if values.shape != expected:
            raise ValueError(
                f"diagnostic post-transfer speed must have shape {expected}"
            )
        if not torch.isfinite(values).all() or torch.any(
            (values < 0.0) | (values > 0.3)
        ):
            raise ValueError(
                "diagnostic post-transfer speeds must be finite within [0, 0.3] rad/s"
            )
        self._fsm_diagnostic_post_transfer_forward_speed_rad_s[:] = values

    def configure_diagnostic_support_unload(
        self,
        maximum_m: Sequence[float] | torch.Tensor,
        rate_m_s: Sequence[float] | torch.Tensor,
    ) -> None:
        """Set bounded high-load radial shortening for diagnostic environments."""

        maximum = torch.as_tensor(
            maximum_m,
            dtype=torch.float32,
            device=self.device,
        )
        rate = torch.as_tensor(
            rate_m_s,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs,)
        if maximum.shape != expected or rate.shape != expected:
            raise ValueError(
                "diagnostic support unload maximum and rate must both have "
                f"shape {expected}"
            )
        if (
            (not torch.isfinite(maximum).all())
            or torch.any((maximum < 0.0) | (maximum > 0.005))
        ):
            raise ValueError(
                "diagnostic support unload maximum must be finite within [0, 0.005] m"
            )
        if (
            (not torch.isfinite(rate).all())
            or torch.any((rate <= 0.0) | (rate > 0.005))
        ):
            raise ValueError(
                "diagnostic support unload rate must be finite within (0, 0.005] m/s"
            )
        self._fsm_diagnostic_support_unload_maximum_m[:] = maximum
        self._fsm_diagnostic_support_unload_rate_m_s[:] = rate

    def configure_diagnostic_front_support_command_offsets(
        self,
        offsets_deg: Sequence[Sequence[float]] | torch.Tensor,
    ) -> None:
        """Set phase-6-to-10 front-support command offsets for grid searches."""

        offsets = torch.as_tensor(
            offsets_deg,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs, 8)
        if offsets.shape != expected:
            raise ValueError(
                f"diagnostic front-support offsets must have shape {expected}"
            )
        if not torch.isfinite(offsets).all():
            raise ValueError("diagnostic front-support offsets must be finite")
        self._fsm_diagnostic_front_support_offset_deg[:] = offsets

    def configure_diagnostic_rear_recovery_max_blend(
        self,
        maximum_blend: Sequence[float] | torch.Tensor,
    ) -> None:
        """Set per-environment rear recovery fractions for development grids."""

        values = torch.as_tensor(
            maximum_blend,
            dtype=torch.float32,
            device=self.device,
        )
        expected = (self.num_envs,)
        if values.shape != expected:
            raise ValueError(
                f"diagnostic rear recovery blend must have shape {expected}"
            )
        if (
            not torch.isfinite(values).all()
            or torch.any(values < 0.0)
            or torch.any(values > 1.0)
        ):
            raise ValueError("diagnostic rear recovery blend must be within [0, 1]")
        self._fsm_diagnostic_rear_recovery_max_blend = values.clone()
