"""Paired batch evaluation for FSM or a frozen residual-PPO checkpoint."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import math
import random
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path("C:/robotics_sim/wlr_robot")
VALIDATION_ROOT = PROJECT_ROOT / "resume_validation_fsm_residual_ppo"
ISAACLAB_ROOT = Path("C:/robotics_sim/IsaacLab")
for extension in (ISAACLAB_ROOT / "source").iterdir():
    if extension.is_dir() and str(extension) not in sys.path:
        sys.path.append(str(extension))
for path in (ISAACLAB_ROOT, PROJECT_ROOT, VALIDATION_ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.append(str(path))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--controller", choices=("fsm", "B", "C"), required=True)
parser.add_argument("--checkpoint", type=Path)
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--height_mm", type=int, choices=(50, 75, 100), required=True)
parser.add_argument("--output_dir", type=Path, required=True)
parser.add_argument("--robot_usd", type=Path, default=VALIDATION_ROOT / "assets" / "converted" / "wlr_robot_validation.usd")
parser.add_argument("--max_episode_s", type=float, default=150.0)
parser.add_argument("--record_stride", type=int, default=3)
parser.add_argument("--initial_settle_physics_steps", type=int, default=120)
parser.add_argument("--limit", type=int, default=0, help="Diagnostic-only prefix limit; zero evaluates the full height split.")
parser.add_argument("--require_locked_hash", type=str, default="")
parser.add_argument("--scenario_id", type=str, default="", help="Exact single-scenario replay; used only for post-test video evidence.")
parser.add_argument("--video_path", type=Path)
parser.add_argument("--video_stride", type=int, default=3)
parser.add_argument("--video_fps", type=float, default=20.0)
parser.add_argument("--video_category", type=str, default="")
parser.add_argument("--video_outcome_label", choices=("", "success", "failure"), default="")
parser.add_argument("--video_width", type=int, default=1280)
parser.add_argument("--video_height", type=int, default=720)
parser.add_argument("--video_frames_dir", type=Path)
parser.add_argument("--video_seed", type=int, default=-1)
parser.add_argument("--video_checkpoint_label", type=str, default="")
parser.add_argument("--video_codec", choices=("libx264", "mjpeg"), default="libx264")
parser.add_argument(
    "--video_follow_camera",
    action=argparse.BooleanOptionalAction,
    default=False,
    help=(
        "Smoothly track the robot/obstacle midpoint for development replay video only. "
        "Disabled by default because repeated set_camera_view calls can invalidate the "
        "offscreen render product on this Isaac Sim installation."
    ),
)
parser.add_argument("--heartbeat_path", type=Path)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.video_path is not None and not args.enable_cameras:
    parser.error("--video_path requires --enable_cameras")
if args.video_path is not None and not args.scenario_id:
    parser.error("--video_path requires an exact --scenario_id")
if args.video_stride <= 0 or not math.isfinite(args.video_fps) or args.video_fps <= 0.0:
    parser.error("video stride and FPS must be positive")
if args.video_width <= 0 or args.video_height <= 0:
    parser.error("video width and height must be positive")
if args.video_frames_dir is not None and args.video_path is None:
    parser.error("--video_frames_dir requires --video_path")
app = AppLauncher(args).app

import gymnasium as gym
import numpy as np
import torch
from isaaclab.utils.math import quat_apply, quat_apply_inverse, quat_from_euler_xyz
from isaaclab_rl.skrl import SkrlVecEnvWrapper
from skrl.agents.torch.ppo import PPO
from skrl.memories.torch import RandomMemory
from skrl.resources.preprocessors.torch import RunningStandardScaler

from resume_validation.config_io import load_config
from resume_validation.load_balance import (
    formal_post_transfer_drive_speed,
    formal_post_transfer_support_geometry,
    formal_rear_transfer_wheel_speed,
    formal_support_unload_policy,
)
from resume_validation.ppo_models import ResidualPolicy, ResidualValue
from resume_validation.residual_rl_env import (
    ACTOR_OBS_DIM,
    CRITIC_STATE_DIM,
    WLRResidualRLEnv,
    make_residual_env_cfg,
)
from resume_validation.scenario_manifest import verify_manifest
from resume_validation.source_audit import sha256_file


def _load_scenarios(path: Path, height_mm: int) -> tuple[dict, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = [
        row for row in payload["scenarios"]
        if int(round(float(row["obstacle_height_m"]) * 1000)) == height_mm
    ]
    if not rows:
        raise ValueError(f"No {height_mm}mm scenarios in {path}")
    return payload.get("metadata", {}), rows


def _make_agent(env, checkpoint: Path):
    device = torch.device(env.device)
    models = {
        "policy": ResidualPolicy(env.observation_space, env.action_space, device),
        "value": ResidualValue(env.state_space, env.action_space, device),
    }
    cfg = {
        "rollouts": 1,
        "learning_epochs": 1,
        "mini_batches": 1,
        "random_timesteps": 0,
        "learning_starts": 0,
        "observation_preprocessor": RunningStandardScaler,
        "observation_preprocessor_kwargs": {"size": ACTOR_OBS_DIM, "device": device},
        "state_preprocessor": RunningStandardScaler,
        "state_preprocessor_kwargs": {"size": CRITIC_STATE_DIM, "device": device},
        "value_preprocessor": RunningStandardScaler,
        "value_preprocessor_kwargs": {"size": 1, "device": device},
        "experiment": {"checkpoint_interval": 0, "write_interval": 0},
    }
    memory = RandomMemory(memory_size=1, num_envs=env.num_envs, device=device)
    agent = PPO(
        models=models,
        memory=memory,
        cfg=cfg,
        observation_space=env.observation_space,
        state_space=env.state_space,
        action_space=env.action_space,
        device=device,
    )
    agent.load(str(checkpoint))
    agent.enable_training_mode(False, apply_to_models=True)
    return agent


def _configure_initial_state(raw_env: WLRResidualRLEnv, scenarios: list[dict]) -> None:
    num_envs = len(scenarios)
    noise = np.zeros((num_envs, 4), dtype=np.float32)
    for index, row in enumerate(scenarios):
        generator = random.Random(int(row["noise_seed"]))
        std = float(row["sensor_noise_std"])
        draws = [generator.gauss(0.0, std) for _ in range(4)]
        noise[index] = [draws[0] / 0.10, draws[1], draws[2] / 0.50, draws[3] / 0.20]
    raw_env.configure_scenarios(
        actuator_delay_steps=[int(row["actuator_delay_steps"]) for row in scenarios],
        obstacle_observation_noise=noise,
        friction=[float(row["friction"]) for row in scenarios],
    )
    current_distance = raw_env._distance_to_obstacle_front()
    desired_distance = torch.tensor(
        [float(row["initial_distance_m"]) for row in scenarios], dtype=torch.float32, device=raw_env.device
    )
    pitch = torch.tensor(
        [float(row["initial_pitch_rad"]) for row in scenarios], dtype=torch.float32, device=raw_env.device
    )
    root_pose = raw_env._robot.data.root_pose_w.clone()
    base_body_id = raw_env._robot.body_names.index("base_link")
    base_pos = raw_env._robot.data.body_pos_w[:, base_body_id]
    base_quat = raw_env._robot.data.body_quat_w[:, base_body_id]
    wheel_pos = raw_env._robot.data.body_pos_w[:, raw_env._wheel_body_ids]
    wheel_relative_b = quat_apply_inverse(
        base_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
        (wheel_pos - base_pos.unsqueeze(1)).reshape(-1, 3),
    ).reshape(num_envs, 4, 3)
    desired_quat = quat_from_euler_xyz(torch.zeros_like(pitch), pitch, torch.zeros_like(pitch))
    desired_wheel_relative = quat_apply(
        desired_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
        wheel_relative_b.reshape(-1, 3),
    ).reshape(num_envs, 4, 3)
    root_pose[:, 0] += current_distance - desired_distance
    # Place the lowest predicted wheel center just above its physical radius.
    # This avoids introducing a non-wheel ground penetration when applying the
    # pre-registered initial pitch variation.
    wheel_radius = raw_env._estimated_wheel_radius
    root_pose[:, 2] = wheel_radius - desired_wheel_relative[:, :, 2].amin(dim=1) + 0.002
    root_pose[:, 3:7] = desired_quat
    raw_env._robot.write_root_pose_to_sim(root_pose)
    raw_env._robot.write_root_velocity_to_sim(torch.zeros((num_envs, 6), device=raw_env.device))
    raw_env.scene.write_data_to_sim()


def _settle_nominal_standing(raw_env: WLRResidualRLEnv, physics_steps: int) -> None:
    """Physically settle the spawned articulation before scenario placement.

    These are initialization physics steps, not controller steps, and do not
    increment the episode or FSM clocks.
    """

    servo_target = raw_env._standing_servo_pos.expand(raw_env.num_envs, -1)
    wheel_target = torch.zeros((raw_env.num_envs, 4), device=raw_env.device)
    for _ in range(max(0, int(physics_steps))):
        raw_env._robot.set_joint_position_target(servo_target, joint_ids=raw_env._servo_joint_ids)
        raw_env._robot.set_joint_velocity_target(wheel_target, joint_ids=raw_env._wheel_joint_ids)
        raw_env.scene.write_data_to_sim()
        raw_env.sim.step(render=False)
        raw_env.scene.update(dt=raw_env.physics_dt)


def main() -> int:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    result_path = output_dir / "result.json"
    status_path = output_dir / "status.json"
    result: dict = {
        "schema": "resume_validation.controller_evaluation.v1",
        "started_unix": time.time(),
        "controller": args.controller,
        "height_mm": args.height_mm,
        "passed_execution": False,
        "failures": [],
    }
    raw_env = None
    env = None
    video_writer = None
    video_path = None
    video_frames_dir = None
    video_frame_count = 0
    encoded_frame_count = 0
    video_encoding_error = None
    consecutive_black_video_frames = 0
    heartbeat_path = args.heartbeat_path.resolve() if args.heartbeat_path else None

    def write_heartbeat(state: str, simulation_time_s: float = 0.0) -> None:
        if heartbeat_path is None:
            return
        heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = heartbeat_path.with_suffix(heartbeat_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "state": state,
                    "updated_unix": time.time(),
                    "simulation_time_s": float(simulation_time_s),
                    "frame_count": int(video_frame_count),
                    "encoded_frame_count": int(encoded_frame_count),
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        # On Windows the supervisor can momentarily hold the destination while
        # decoding it.  Heartbeat observability must never abort physics.
        for attempt in range(5):
            try:
                temporary.replace(heartbeat_path)
                break
            except PermissionError:
                if attempt == 4:
                    temporary.unlink(missing_ok=True)
                    break
                time.sleep(0.01)

    try:
        write_heartbeat("STARTING")
        manifest = args.manifest.resolve()
        if args.require_locked_hash:
            actual = sha256_file(manifest)
            if actual != args.require_locked_hash:
                raise RuntimeError(f"Locked manifest hash mismatch: {actual} != {args.require_locked_hash}")
            if not verify_manifest(manifest):
                raise RuntimeError("Locked manifest sidecar verification failed")
        metadata, scenarios = _load_scenarios(manifest, args.height_mm)
        if args.scenario_id:
            scenarios = [
                row
                for row in scenarios
                if str(row["scenario_id"]) == args.scenario_id
            ]
            if len(scenarios) != 1:
                raise ValueError(
                    f"Expected exactly one scenario_id={args.scenario_id!r} "
                    f"at {args.height_mm} mm, got {len(scenarios)}"
                )
            result["single_scenario_replay"] = True
        if args.limit > 0:
            if args.scenario_id:
                raise ValueError("--limit and --scenario_id are mutually exclusive")
            scenarios = scenarios[: args.limit]
            result["diagnostic_scenario_limit"] = args.limit
        checkpoint = args.checkpoint.resolve() if args.checkpoint else None
        if args.controller != "fsm" and checkpoint is None:
            raise ValueError("PPO evaluation requires --checkpoint")
        fsm_path = VALIDATION_ROOT / "configs" / "fsm.yaml"
        metrics_path = VALIDATION_ROOT / "configs" / "metrics.yaml"
        ppo_common_path = VALIDATION_ROOT / "configs" / "ppo_common.yaml"
        method_path = VALIDATION_ROOT / "configs" / (
            "ppo_with_com.yaml" if args.controller == "C" else "ppo_without_com.yaml"
        )
        fsm_cfg = load_config(fsm_path)
        ppo_common_cfg = load_config(ppo_common_path)
        method_cfg = load_config(method_path)
        common_reward_weights = {
            str(name): float(value)
            for name, value in ppo_common_cfg["reward"]["weights"].items()
        }
        residual_phase_window = tuple(
            int(value)
            for value in ppo_common_cfg["action"]["execution_phase_window"]
        )
        residual_phase_gains = tuple(
            float(value)
            for value in ppo_common_cfg["action"]["execution_phase_gains"]
        )
        residual_applied_action_hard_clip = float(
            ppo_common_cfg["action"]["applied_action_hard_clip"]
        )
        if (
            len(residual_phase_window) != 2
            or residual_phase_window[0] < 0
            or residual_phase_window[1] < residual_phase_window[0]
            or residual_phase_window[1] >= 13
        ):
            raise RuntimeError(
                f"Invalid common residual execution phase window: {residual_phase_window}"
            )
        if (
            len(residual_phase_gains)
            != residual_phase_window[1] - residual_phase_window[0] + 1
            or any(
                not math.isfinite(value) or value <= 0.0 or value > 4.0
                for value in residual_phase_gains
            )
        ):
            raise RuntimeError(
                f"Invalid common residual execution phase gains: {residual_phase_gains}"
            )
        projection_cfg = ppo_common_cfg["action"]["execution_projection"]
        residual_z_signs = tuple(
            int(value)
            for value in projection_cfg["wheel_center_z_signs"]
        )
        residual_executed_z_signs = tuple(
            int(value)
            for value in projection_cfg["executed_wheel_center_z_signs"]
        )
        residual_corrective_z_scales = tuple(
            float(value)
            for value in projection_cfg[
                "corrective_wheel_center_z_scales"
            ]
        )
        residual_corrective_minimum_shared_magnitude = float(
            projection_cfg["corrective_minimum_shared_magnitude"]
        )
        residual_corrective_wheel_speed_minimum_shared_magnitudes = tuple(
            float(value)
            for value in projection_cfg[
                "corrective_wheel_speed_minimum_shared_magnitudes"
            ]
        )
        residual_corrective_wheel_speed_signs = tuple(
            int(value)
            for value in projection_cfg["corrective_wheel_speed_signs"]
        )
        residual_corrective_wheel_speed_scales = tuple(
            float(value)
            for value in projection_cfg["corrective_wheel_speed_scales"]
        )
        residual_corrective_wheel_speed_phases = tuple(
            int(value)
            for value in projection_cfg["corrective_wheel_speed_phases"]
        )
        residual_action_mask = tuple(
            int(value) for value in projection_cfg["action_mask"]
        )
        residual_activation_threshold = 0.0
        state_gate_cfg = ppo_common_cfg["action"]["execution_state_gate"]
        residual_state_gate_type = str(state_gate_cfg["type"])
        residual_state_gate_min_pitch_rad = float(
            state_gate_cfg["minimum_pitch_rad"]
        )
        residual_state_gate_min_roll_rad = float(
            state_gate_cfg["minimum_roll_rad"]
        )
        residual_state_gate_early_roll_rad = float(
            state_gate_cfg["early_roll_rad"]
        )
        residual_state_gate_early_pitch_rate_rad_s = float(
            state_gate_cfg["early_pitch_rate_rad_s"]
        )
        residual_state_gate_corrective_latch = bool(
            state_gate_cfg["corrective_latch_until_phase_exit"]
        )
        if (
            projection_cfg["type"]
            != "wheel_center_z_deficient_diagonal_downward_support_phase9_counter_yaw_emergency_gate"
            or residual_z_signs != (-1, -1, 1, 1)
            or residual_executed_z_signs != (0, -1, -1, 0)
            or residual_corrective_z_scales
            != (0.0, 1.0, 1.0, 0.0)
            or not math.isfinite(
                residual_corrective_minimum_shared_magnitude
            )
            or residual_corrective_minimum_shared_magnitude != 0.1
            or residual_corrective_wheel_speed_minimum_shared_magnitudes
            != (0.25,)
            or residual_corrective_wheel_speed_signs
            != (-1, 1, -1, 1)
            or residual_corrective_wheel_speed_scales
            != (1.0, 1.0, 1.0, 1.0)
            or residual_corrective_wheel_speed_phases != (9,)
            or residual_action_mask
            != (0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1)
            or residual_phase_window != (8, 10)
            or residual_phase_gains != (3.0, 4.0, 3.0)
            or not math.isfinite(residual_applied_action_hard_clip)
            or residual_applied_action_hard_clip != 1.0
            or residual_state_gate_type
            != "phase_aware_roll_imu_emergency"
            or not math.isfinite(residual_state_gate_min_pitch_rad)
            or residual_state_gate_min_pitch_rad != 0.09
            or not math.isfinite(residual_state_gate_min_roll_rad)
            or residual_state_gate_min_roll_rad != 0.10
            or not math.isfinite(residual_state_gate_early_roll_rad)
            or residual_state_gate_early_roll_rad != 0.06
            or not math.isfinite(
                residual_state_gate_early_pitch_rate_rad_s
            )
            or residual_state_gate_early_pitch_rate_rad_s != 0.35
            or not residual_state_gate_corrective_latch
        ):
            raise RuntimeError(
                "Invalid common residual projection/state gate: "
                f"{projection_cfg}, {state_gate_cfg}"
            )
        com_margin_weight = (
            float(method_cfg["reward"]["com_margin_weight"])
            if args.controller in {"B", "C"}
            else 0.0
        )
        formal_offsets, formal_starts = formal_post_transfer_support_geometry(
            fsm_cfg,
            obstacle_height_m=args.height_mm / 1000.0,
        )
        formal_rear_transfer_speed = formal_rear_transfer_wheel_speed(
            fsm_cfg,
            obstacle_height_m=args.height_mm / 1000.0,
        )
        formal_post_transfer_speed = formal_post_transfer_drive_speed(
            fsm_cfg,
            obstacle_height_m=args.height_mm / 1000.0,
        )
        (
            formal_unload_low_force,
            formal_unload_high_force,
            formal_unload_rate,
            formal_unload_maximum,
        ) = formal_support_unload_policy(
            fsm_cfg,
            obstacle_height_m=args.height_mm / 1000.0,
        )
        if float(fsm_cfg["playback_profile"].get("speed_scale", 1.0)) != 1.0:
            raise RuntimeError("The wheel-distance-preserving FSM currently requires speed_scale == 1.0")
        result["provenance"] = {
            "manifest": str(manifest),
            "manifest_sha256": sha256_file(manifest),
            "manifest_metadata": metadata,
            "asset": str(args.robot_usd.resolve()),
            "asset_sha256": sha256_file(args.robot_usd),
            "checkpoint": str(checkpoint) if checkpoint else None,
            "checkpoint_sha256": sha256_file(checkpoint) if checkpoint else None,
            "fsm_config": str(fsm_path),
            "fsm_config_sha256": sha256_file(fsm_path),
            "effective_post_transfer_wheel_center_offsets_m": formal_offsets,
            "effective_post_transfer_offset_start_progress": formal_starts,
            "effective_rear_transfer_wheel_speed_rad_s": formal_rear_transfer_speed,
            "effective_post_transfer_forward_speed_rad_s": formal_post_transfer_speed,
            "effective_support_unload": {
                "low_force_n": formal_unload_low_force,
                "high_force_n": formal_unload_high_force,
                "rate_m_s": formal_unload_rate,
                "maximum_m": formal_unload_maximum,
            },
            "metrics_config": str(metrics_path),
            "metrics_config_sha256": sha256_file(metrics_path),
            "ppo_common_config": str(ppo_common_path),
            "ppo_common_config_sha256": sha256_file(ppo_common_path),
            "method_config": str(method_path),
            "method_config_sha256": sha256_file(method_path),
            "source_files": {
                name: {
                    "path": str(VALIDATION_ROOT / "src" / "resume_validation" / name),
                    "sha256": sha256_file(
                        VALIDATION_ROOT / "src" / "resume_validation" / name
                    ),
                }
                for name in (
                    "reward.py",
                    "residual_rl_env.py",
                    "residual_safety.py",
                    "training_randomization.py",
                    "ppo_models.py",
                    "evaluate_controller.py",
                )
            },
            "effective_reward_weights": {
                **common_reward_weights,
                "com_margin": com_margin_weight,
            },
            "effective_residual_execution_phase_window": list(
                residual_phase_window
            ),
            "effective_residual_execution_phase_gains": list(
                residual_phase_gains
            ),
            "effective_residual_applied_action_hard_clip": (
                residual_applied_action_hard_clip
            ),
            "effective_residual_wheel_center_z_signs": list(
                residual_z_signs
            ),
            "effective_residual_executed_wheel_center_z_signs": list(
                residual_executed_z_signs
            ),
            "effective_residual_corrective_wheel_center_z_scales": list(
                residual_corrective_z_scales
            ),
            "effective_residual_corrective_minimum_shared_magnitude": (
                residual_corrective_minimum_shared_magnitude
            ),
            "effective_residual_corrective_wheel_speed_minimum_shared_magnitudes": list(
                residual_corrective_wheel_speed_minimum_shared_magnitudes
            ),
            "effective_residual_corrective_wheel_speed_signs": list(
                residual_corrective_wheel_speed_signs
            ),
            "effective_residual_corrective_wheel_speed_scales": list(
                residual_corrective_wheel_speed_scales
            ),
            "effective_residual_corrective_wheel_speed_phases": list(
                residual_corrective_wheel_speed_phases
            ),
            "effective_residual_projection_type": str(
                projection_cfg["type"]
            ),
            "effective_residual_action_mask": list(residual_action_mask),
            "effective_residual_activation_threshold": (
                residual_activation_threshold
            ),
            "effective_residual_state_gate_type": residual_state_gate_type,
            "effective_residual_state_gate_min_pitch_rad": (
                residual_state_gate_min_pitch_rad
            ),
            "effective_residual_state_gate_min_roll_rad": (
                residual_state_gate_min_roll_rad
            ),
            "effective_residual_state_gate_early_roll_rad": (
                residual_state_gate_early_roll_rad
            ),
            "effective_residual_state_gate_early_pitch_rate_rad_s": (
                residual_state_gate_early_pitch_rate_rad_s
            ),
            "effective_residual_state_gate_corrective_latch": (
                residual_state_gate_corrective_latch
            ),
            "reward_occupancy_integration": ppo_common_cfg["reward"][
                "occupancy_integration"
            ],
            "reward_rate_integration": ppo_common_cfg["reward"][
                "rate_integration"
            ],
            "reward_terminal_safety": ppo_common_cfg["reward"][
                "terminal_safety"
            ],
            "reward_reset_initialization": ppo_common_cfg["reward"][
                "reset_initialization"
            ],
            "reward_baseline_regularization_timebase": ppo_common_cfg["reward"][
                "baseline_regularization_timebase"
            ],
            "evaluation_slip_metric": (
                "per control step, for wheels carrying at least the frozen "
                "minimum 2 N upward force, integrate the mean absolute "
                "difference between measured wheel surface speed "
                "(physical joint velocity times estimated radius) and "
                "measured body-frame base forward speed; slip ratio uses "
                "max(abs(wheel surface speed), 0.10 m/s) as denominator"
            ),
            "evaluation_command_variation_metric": (
                "mean per-active-step L2 change of the physically executed "
                "normalized residual action"
            ),
            "isaaclab": importlib.metadata.version("isaaclab"),
            "isaacsim": importlib.metadata.version("isaacsim"),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
        }
        cfg = make_residual_env_cfg(
            num_envs=len(scenarios),
            obstacle_height=args.height_mm / 1000.0,
            robot_usd_path=args.robot_usd,
            episode_length_s=args.max_episode_s,
            com_margin_weight=com_margin_weight,
            max_idle_gap_s=float(fsm_cfg["playback_profile"]["max_idle_gap_s"]),
            preserve_wheel_distance=bool(fsm_cfg["playback_profile"]["preserve_wheel_distance"]),
            fsm_contact_debounce_steps=int(fsm_cfg["contact_debounce_steps"]),
            phase_timeout_scale=float(fsm_cfg["phase_timeout_scale"]),
            fsm_post_transfer_wheel_center_offsets_m=formal_offsets,
            fsm_post_transfer_offset_start_progress=formal_starts,
            fsm_rear_transfer_wheel_speed_rad_s=formal_rear_transfer_speed,
            fsm_post_transfer_active_speed_rad_s=formal_post_transfer_speed,
            fsm_support_unload_low_force_n=formal_unload_low_force,
            fsm_support_unload_high_force_n=formal_unload_high_force,
            fsm_support_unload_rate_m_s=formal_unload_rate,
            fsm_support_unload_maximum_m=formal_unload_maximum,
            residual_reward_weights=common_reward_weights,
            residual_execution_phase_min=residual_phase_window[0],
            residual_execution_phase_max=residual_phase_window[1],
            residual_execution_phase_gains=residual_phase_gains,
            residual_applied_action_hard_clip=(
                residual_applied_action_hard_clip
            ),
            residual_projection_type=str(projection_cfg["type"]),
            residual_wheel_center_z_signs=residual_z_signs,
            residual_executed_wheel_center_z_signs=(
                residual_executed_z_signs
            ),
            residual_corrective_wheel_center_z_scales=(
                residual_corrective_z_scales
            ),
            residual_corrective_wheel_speed_signs=(
                residual_corrective_wheel_speed_signs
            ),
            residual_corrective_wheel_speed_scales=(
                residual_corrective_wheel_speed_scales
            ),
            residual_corrective_wheel_speed_phases=(
                residual_corrective_wheel_speed_phases
            ),
            residual_corrective_wheel_speed_minimum_shared_magnitudes=(
                residual_corrective_wheel_speed_minimum_shared_magnitudes
            ),
            residual_action_mask=residual_action_mask,
            residual_activation_threshold=residual_activation_threshold,
            residual_state_gate_type=residual_state_gate_type,
            residual_state_gate_min_pitch_rad=(
                residual_state_gate_min_pitch_rad
            ),
            residual_state_gate_early_pitch_rate_rad_s=(
                residual_state_gate_early_pitch_rate_rad_s
            ),
            residual_state_gate_min_roll_rad=(
                residual_state_gate_min_roll_rad
            ),
            residual_state_gate_early_roll_rad=(
                residual_state_gate_early_roll_rad
            ),
            residual_corrective_minimum_shared_magnitude=(
                residual_corrective_minimum_shared_magnitude
            ),
        )
        result["provenance"]["effective_residual_bounds"] = {
            str(name): float(value)
            for name, value in cfg.residual_bounds.items()
        }
        cfg.seed = int(metadata.get("seed", 0))
        if args.video_path is not None:
            cfg.viewer.resolution = (int(args.video_width), int(args.video_height))
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        raw_env = WLRResidualRLEnv(
            cfg,
            render_mode="rgb_array" if args.video_path is not None else None,
        )
        if args.video_path is not None:
            raw_env.sim.set_camera_view(
                eye=(-0.05, -2.30, 1.00),
                target=(0.60, 0.0, 0.24),
            )
            # Prime the offscreen render product before the first recorded
            # controller frame.  On Isaac Sim 5.1 the first RGB read after a
            # camera pose change can otherwise be an all-black initialization
            # frame even though subsequent reads are valid.
            for _ in range(3):
                raw_env.sim.render()
        env = SkrlVecEnvWrapper(raw_env, ml_framework="torch")
        observation, _ = env.reset()
        _settle_nominal_standing(raw_env, args.initial_settle_physics_steps)
        _configure_initial_state(raw_env, scenarios)
        # The wrapper observation returned by reset predates the paired initial
        # pose write above. Refresh it before the first deterministic action.
        observation = raw_env._get_observations()["policy"]
        result["initialization"] = {
            "settle_physics_steps": int(args.initial_settle_physics_steps),
            "settle_sim_time_s": int(args.initial_settle_physics_steps) * float(raw_env.physics_dt),
            "episode_clock_starts_after_settle": True,
        }
        video_path = args.video_path.resolve() if args.video_path else None
        camera_anchor_x = 0.60
        if video_path is not None:
            if video_path.parent != output_dir:
                raise ValueError(
                    "Video must be written directly inside the new evaluation output directory"
                )
            if video_path.exists():
                raise FileExistsError(f"Refusing to overwrite video: {video_path}")
            video_frames_dir = (
                args.video_frames_dir.resolve()
                if args.video_frames_dir is not None
                else None
            )
            if video_frames_dir is not None:
                if output_dir not in video_frames_dir.parents:
                    raise ValueError("Video frames directory must be inside the new evaluation output directory")
                video_frames_dir.mkdir(parents=True, exist_ok=False)
            import imageio.v2 as imageio

            try:
                video_writer = imageio.get_writer(
                    video_path,
                    fps=float(args.video_fps),
                    codec=args.video_codec,
                    quality=8,
                    macro_block_size=None,
                )
            except Exception as exc:
                video_encoding_error = f"{type(exc).__name__}: {exc}"
                video_writer = None
                if video_frames_dir is None:
                    video_frames_dir = output_dir / "frames_encode_failure"
                    video_frames_dir.mkdir(parents=True, exist_ok=True)
            result["video_replay"] = {
                "path": str(video_path),
                "scenario_id": args.scenario_id,
                "category": args.video_category,
                "locked_outcome_label": args.video_outcome_label,
                "frame_stride_control_steps": int(args.video_stride),
                "fps": float(args.video_fps),
                "resolution": [int(args.video_width), int(args.video_height)],
                "camera_eye_offset": [-0.65, -2.30, 0.76],
                "camera_target_initial_w": [0.60, 0.0, 0.24],
                "smooth_follow": bool(args.video_follow_camera),
                "overlay_is_diagnostic_only": True,
            }
        write_heartbeat("RUNNING", 0.0)
        agent = _make_agent(env, checkpoint) if checkpoint else None

        count = len(scenarios)
        active = torch.ones(count, dtype=torch.bool, device=raw_env.device)
        success = torch.zeros(count, dtype=torch.bool, device=raw_env.device)
        failure_reason = [""] * count
        terminal_nonwheel_contact_force_n: list[dict[str, float] | None] = [
            None
        ] * count
        terminal_wheel_contact_force_magnitude_n: list[
            list[float] | None
        ] = [None] * count
        terminal_wheel_contact_upward_force_n: list[list[float] | None] = [
            None
        ] * count
        terminal_wheel_on_top: list[list[bool] | None] = [None] * count
        terminal_full_wheel_on_top: list[list[bool] | None] = [None] * count
        terminal_all_wheels_on_top: list[bool | None] = [None] * count
        terminal_support_score: list[float | None] = [None] * count
        terminal_wheel_position_y_m: list[list[float] | None] = [None] * count
        terminal_front_load_trim_z_m: list[list[float] | None] = [None] * count
        terminal_support_unload_trim_m: list[list[float] | None] = [None] * count
        terminal_fsm_baseline_ik_invalid_count: list[int | None] = [None] * count
        terminal_fsm_baseline_ik_invalid_count_per_leg: list[
            list[int] | None
        ] = [None] * count
        terminal_fsm_diagnostic_front_support_clamp_count: list[
            int | None
        ] = [None] * count
        terminal_joint_limit_diagnostic: list[dict | None] = [None] * count
        min_margin = torch.full((count,), float("inf"), device=raw_env.device)
        valid_margin_count = torch.zeros(count, dtype=torch.long, device=raw_env.device)
        invalid_margin_count = torch.zeros_like(valid_margin_count)
        pitch_rate_sq_sum = torch.zeros(count, device=raw_env.device)
        pitch_rate_count = torch.zeros(count, dtype=torch.long, device=raw_env.device)
        pitch_sq_sum = torch.zeros(count, device=raw_env.device)
        episode_step_count = torch.zeros(count, dtype=torch.long, device=raw_env.device)
        max_abs_pitch = torch.zeros(count, device=raw_env.device)
        max_abs_pitch_rate = torch.zeros(count, device=raw_env.device)
        negative_margin_duration = torch.zeros(count, device=raw_env.device)
        wheel_slip_distance = torch.zeros(count, device=raw_env.device)
        wheel_slip_ratio_sum = torch.zeros(count, device=raw_env.device)
        wheel_slip_sample_count = torch.zeros(
            count, dtype=torch.long, device=raw_env.device
        )
        saturation_steps = torch.zeros(count, dtype=torch.long, device=raw_env.device)
        wheel_speed_saturation_steps = torch.zeros(
            count, dtype=torch.long, device=raw_env.device
        )
        executed_action_variation_sum = torch.zeros(
            count, device=raw_env.device
        )
        previous_executed_actions = torch.zeros(
            (count, 12), device=raw_env.device
        )
        initial_base_x = raw_env._root_pos_local()[:, 0].clone()
        final_base_x = initial_base_x.clone()
        rows: list[list[float]] = []
        max_steps = math.ceil(args.max_episode_s / float(raw_env.step_dt))

        for step in range(max_steps):
            if agent is None:
                actions = torch.zeros((count, 12), device=raw_env.device)
            else:
                with torch.no_grad():
                    _, outputs = agent.act(observation, env.state(), timestep=step, timesteps=max_steps)
                    actions = outputs["mean_actions"]
            observation, reward, terminated, truncated, _ = env.step(actions)
            terminated_flat = terminated.reshape(-1)
            truncated_flat = truncated.reshape(-1)
            done = active & (terminated_flat | truncated_flat)
            margin, margin_valid = raw_env._longitudinal_margin()
            roll, pitch, _ = raw_env._roll_pitch_yaw()
            pitch_rate = raw_env._robot.data.root_ang_vel_b[:, 1]
            root_x = raw_env._root_pos_local()[:, 0]
            phase = raw_env._fsm_phase
            raw_env._refresh_contact_state()
            contact_state = raw_env._wheel_contact_state.clone()
            wheel_on_top = raw_env._wheel_on_top.clone()
            full_wheel_on_top = raw_env._full_wheel_on_top.clone()
            all_wheels_on_top = raw_env._all_wheels_on_top.clone()
            support_score = raw_env.compute_com_support_metrics(
                update_cache=False
            )["score"]
            contact_force_vector_w, contact_force_n = (
                raw_env._wheel_contact_forces()
            )
            contact_upward_force_n = contact_force_vector_w[:, :, 2]
            base_forward_speed_m_s = raw_env._robot.data.root_lin_vel_b[:, 0]
            wheel_surface_speed_m_s = (
                raw_env._physical_wheel_velocities()
                * raw_env._estimated_wheel_radius.unsqueeze(1)
            )
            supported_wheel = contact_upward_force_n >= 2.0
            supported_wheel_count = supported_wheel.sum(dim=1)
            wheel_slip_speed_m_s = torch.abs(
                wheel_surface_speed_m_s - base_forward_speed_m_s.unsqueeze(1)
            )
            supported_slip_speed_m_s = (
                torch.where(
                    supported_wheel,
                    wheel_slip_speed_m_s,
                    torch.zeros_like(wheel_slip_speed_m_s),
                ).sum(dim=1)
                / torch.clamp(supported_wheel_count, min=1)
            )
            wheel_slip_ratio = wheel_slip_speed_m_s / torch.clamp(
                torch.abs(wheel_surface_speed_m_s),
                min=0.10,
            )
            supported_slip_ratio = (
                torch.where(
                    supported_wheel,
                    wheel_slip_ratio,
                    torch.zeros_like(wheel_slip_ratio),
                ).sum(dim=1)
                / torch.clamp(supported_wheel_count, min=1)
            )
            wheel_position_xz = raw_env._wheel_pos_local()[:, :, (0, 2)]
            wheel_position_y = raw_env._wheel_pos_local()[:, :, 1]
            com_x = raw_env._compute_com_xy()[0][:, 0]
            valid_support = (
                (contact_upward_force_n >= float(raw_env.cfg.contact_force_threshold_n))
                & (raw_env._wheel_on_ground | raw_env._wheel_on_top)
                & (~raw_env._wheel_on_front_face)
            )
            support_min_x = torch.min(
                torch.where(
                    valid_support,
                    wheel_position_xz[:, :, 0],
                    torch.full_like(wheel_position_xz[:, :, 0], float("inf")),
                ),
                dim=1,
            ).values
            support_max_x = torch.max(
                torch.where(
                    valid_support,
                    wheel_position_xz[:, :, 0],
                    torch.full_like(wheel_position_xz[:, :, 0], float("-inf")),
                ),
                dim=1,
            ).values
            reference_commands = raw_env._reference_commands.clone()
            executed_actions = raw_env._applied_actions.clone()
            scaled_wheel_center_residual_m = (
                raw_env._scaled_wheel_center_residual_m.clone()
            )
            scaled_wheel_speed_residual_rad_s = (
                raw_env._scaled_wheel_speed_residual_rad_s.clone()
            )
            requested_wheel_center_target_m = (
                raw_env._requested_wheel_center_target_m.clone()
            )
            final_wheel_center_target_m = (
                raw_env._final_wheel_center_target_m.clone()
            )
            final_servo_targets = raw_env._servo_targets.clone()
            final_wheel_targets_rad_s = (
                raw_env._physical_forward_wheel_cmds.clone()
            )
            front_load_trim_z_m = raw_env._fsm_front_load_trim_z_m.clone()
            support_unload_trim_m = raw_env._fsm_support_unload_trim_m.clone()
            # DirectRLEnv resets terminal environments inside step(). Replace
            # reset-state values with snapshots captured in _get_dones.
            margin = torch.where(done, raw_env._last_done_margin, margin)
            margin_valid = torch.where(done, raw_env._last_done_margin_valid, margin_valid)
            pitch = torch.where(done, raw_env._last_done_pitch, pitch)
            roll = torch.where(done, raw_env._last_done_roll, roll)
            pitch_rate = torch.where(done, raw_env._last_done_pitch_rate, pitch_rate)
            root_x = torch.where(done, raw_env._last_done_root_x, root_x)
            phase = torch.where(done, raw_env._last_done_fsm_phase, phase)
            contact_state = torch.where(
                done.unsqueeze(1), raw_env._last_done_wheel_contact_state, contact_state
            )
            contact_force_n = torch.where(
                done.unsqueeze(1), raw_env._last_done_wheel_contact_force_n, contact_force_n
            )
            contact_upward_force_n = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_wheel_contact_upward_force_n,
                contact_upward_force_n,
            )
            wheel_on_top = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_wheel_on_top,
                wheel_on_top,
            )
            full_wheel_on_top = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_full_wheel_on_top,
                full_wheel_on_top,
            )
            all_wheels_on_top = torch.where(
                done,
                raw_env._last_done_all_wheels_on_top,
                all_wheels_on_top,
            )
            support_score = torch.where(
                done,
                raw_env._last_done_support_score,
                support_score,
            )
            wheel_position_xz = torch.where(
                done[:, None, None], raw_env._last_done_wheel_position_xz, wheel_position_xz
            )
            wheel_position_y = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_wheel_position_y,
                wheel_position_y,
            )
            reference_commands = torch.where(
                done.unsqueeze(1), raw_env._last_done_reference_commands, reference_commands
            )
            executed_actions = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_applied_residual_action,
                executed_actions,
            )
            scaled_wheel_center_residual_m = torch.where(
                done[:, None, None],
                raw_env._last_done_scaled_wheel_center_residual_m,
                scaled_wheel_center_residual_m,
            )
            scaled_wheel_speed_residual_rad_s = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_scaled_wheel_speed_residual_rad_s,
                scaled_wheel_speed_residual_rad_s,
            )
            requested_wheel_center_target_m = torch.where(
                done[:, None, None],
                raw_env._last_done_requested_wheel_center_target_m,
                requested_wheel_center_target_m,
            )
            final_wheel_center_target_m = torch.where(
                done[:, None, None],
                raw_env._last_done_final_wheel_center_target_m,
                final_wheel_center_target_m,
            )
            final_servo_targets = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_servo_targets,
                final_servo_targets,
            )
            final_wheel_targets_rad_s = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_wheel_targets_rad_s,
                final_wheel_targets_rad_s,
            )
            front_load_trim_z_m = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_fsm_front_load_trim_z_m,
                front_load_trim_z_m,
            )
            support_unload_trim_m = torch.where(
                done.unsqueeze(1),
                raw_env._last_done_fsm_support_unload_trim_m,
                support_unload_trim_m,
            )
            support_transfer = active & (phase >= 4) & (phase <= 8)
            valid_active = support_transfer & margin_valid
            min_margin = torch.where(valid_active, torch.minimum(min_margin, margin), min_margin)
            valid_margin_count += valid_active.to(torch.long)
            invalid_margin_count += (support_transfer & (~margin_valid)).to(torch.long)
            pitch_rate_sq_sum += torch.where(
                support_transfer, pitch_rate.square(), torch.zeros_like(pitch_rate)
            )
            pitch_rate_count += support_transfer.to(torch.long)
            episode_step_count += active.to(torch.long)
            pitch_sq_sum += torch.where(
                active, pitch.square(), torch.zeros_like(pitch)
            )
            max_abs_pitch = torch.where(active, torch.maximum(max_abs_pitch, torch.abs(pitch)), max_abs_pitch)
            max_abs_pitch_rate = torch.where(
                active, torch.maximum(max_abs_pitch_rate, torch.abs(pitch_rate)), max_abs_pitch_rate
            )
            negative_margin_duration += (
                support_transfer & margin_valid & (margin < 0)
            ).to(torch.float32) * float(raw_env.step_dt)
            # DirectRLEnv resets terminal environments inside step(). Terminal
            # physical velocities are therefore not mixed with pre-reset
            # contact snapshots; the final control step is excluded from this
            # secondary integral.
            valid_slip_sample = active & (~done) & (supported_wheel_count > 0)
            wheel_slip_distance += torch.where(
                valid_slip_sample,
                supported_slip_speed_m_s * float(raw_env.step_dt),
                torch.zeros_like(supported_slip_speed_m_s),
            )
            wheel_slip_ratio_sum += torch.where(
                valid_slip_sample,
                supported_slip_ratio,
                torch.zeros_like(supported_slip_ratio),
            )
            wheel_slip_sample_count += valid_slip_sample.to(torch.long)
            saturation_steps += (
                active & torch.any(torch.abs(actions) >= 0.999, dim=1)
            ).to(torch.long)
            wheel_speed_saturation_steps += (
                active
                & torch.any(
                    torch.abs(final_wheel_targets_rad_s)
                    >= float(raw_env.cfg.wheel_max_speed_rad_s) - 1.0e-6,
                    dim=1,
                )
            ).to(torch.long)
            executed_action_variation_sum += torch.where(
                active,
                torch.linalg.vector_norm(
                    executed_actions - previous_executed_actions,
                    dim=1,
                ),
                torch.zeros(count, device=raw_env.device),
            )
            previous_executed_actions = torch.where(
                active.unsqueeze(1),
                executed_actions,
                previous_executed_actions,
            )
            final_base_x = torch.where(active, root_x, final_base_x)
            if (
                video_path is not None
                and step % int(args.video_stride) == 0
                and bool(active[0].item())
                and not bool(done[0].item())
            ):
                if args.video_follow_camera:
                    desired_anchor_x = (
                        0.55 * float(root_x[0].item())
                        + 0.45 * float(scenarios[0]["obstacle_front_x_m"])
                    )
                    camera_anchor_x = 0.88 * camera_anchor_x + 0.12 * desired_anchor_x
                    raw_env.sim.set_camera_view(
                        eye=(camera_anchor_x - 0.65, -2.30, 1.00),
                        target=(camera_anchor_x, 0.0, 0.24),
                    )
                import cv2

                # The Isaac Lab rgb_array annotator on this Isaac Sim 5.1 build
                # can alternate an empty buffer and a valid buffer. Re-render at
                # the same physics state up to three times and only record a valid
                # scene. This changes neither simulation time nor controller steps.
                for render_attempt in range(3):
                    frame = raw_env.render()
                    if frame is None or frame.size == 0:
                        render_mean = 0.0
                        render_std = 0.0
                    else:
                        frame = np.ascontiguousarray(frame)
                        render_mean = float(np.mean(frame))
                        render_std = float(np.std(frame))
                    if render_mean >= 2.0 and render_std >= 2.0:
                        consecutive_black_video_frames = 0
                        break
                    consecutive_black_video_frames += 1
                else:
                    raise RuntimeError(
                        "RGB renderer returned three blank retry frames at one physics state "
                        f"(mean={render_mean:.4f}, std={render_std:.4f})"
                    )
                controller_label = {
                    "fsm": "Frozen FSM",
                    "B": "Method B",
                    "C": "Method C",
                }[args.controller]
                checkpoint_label = args.video_checkpoint_label or (
                    checkpoint.name if checkpoint is not None else "none"
                )
                overlay = [
                    (
                        f"Controller: {controller_label}  Seed: "
                        f"{'n/a' if args.video_seed < 0 else args.video_seed}  Height: {args.height_mm} mm"
                    ),
                    (
                        f"Checkpoint: {checkpoint_label}  Scenario: {args.scenario_id}"
                    ),
                    (
                        f"Simulation time: {step * float(raw_env.step_dt):7.2f} s  "
                        f"FSM phase: {int(phase[0].item())}  Outcome: RUNNING"
                    ),
                    (
                        f"pitch={float(pitch[0].item()):+.4f}rad "
                        f"pitch_rate={float(pitch_rate[0].item()):+.4f}rad/s"
                    ),
                    (
                        f"CoM_x={float(com_x[0].item()):+.4f}m "
                        f"support=[{float(support_min_x[0].item()):+.4f},"
                        f"{float(support_max_x[0].item()):+.4f}]m "
                        f"margin={'invalid' if not bool(margin_valid[0].item()) else f'{float(margin[0].item()):+.4f}m'}"
                    ),
                    (
                        "contacts="
                        + ",".join(
                            str(int(value))
                            for value in contact_state[0].detach().cpu().tolist()
                        )
                        + f" residual_L2={float(torch.linalg.vector_norm(executed_actions[0]).item()):.4f}"
                    ),
                ]
                for line_index, text_value in enumerate(overlay):
                    cv2.putText(
                        frame,
                        text_value,
                        (18, 30 + 28 * line_index),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.58,
                        (245, 245, 245),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        frame,
                        text_value,
                        (18, 30 + 28 * line_index),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.58,
                        (20, 20, 20),
                        1,
                        cv2.LINE_AA,
                    )
                if video_frames_dir is not None:
                    frame_path = video_frames_dir / f"frame_{video_frame_count:06d}.png"
                    if not cv2.imwrite(str(frame_path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)):
                        raise RuntimeError(f"Failed to save raw PNG frame: {frame_path}")
                if video_writer is not None:
                    try:
                        video_writer.append_data(frame)
                        encoded_frame_count += 1
                    except Exception as exc:
                        video_encoding_error = f"{type(exc).__name__}: {exc}"
                        try:
                            video_writer.close()
                        except Exception:
                            pass
                        video_writer = None
                        if video_frames_dir is None:
                            video_frames_dir = output_dir / "frames_encode_failure"
                            video_frames_dir.mkdir(parents=True, exist_ok=True)
                            frame_path = video_frames_dir / f"frame_{video_frame_count:06d}.png"
                            cv2.imwrite(str(frame_path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                video_frame_count += 1
                write_heartbeat("RUNNING", step * float(raw_env.step_dt))
            if step % max(1, args.record_stride) == 0:
                for env_id in active.nonzero(as_tuple=False).flatten().detach().cpu().tolist():
                    rows.append(
                        [
                            step * float(raw_env.step_dt),
                            env_id,
                            float(root_x[env_id].item()),
                            float(pitch[env_id].item()),
                            float(pitch_rate[env_id].item()),
                            float(margin[env_id].item()) if bool(margin_valid[env_id].item()) else float("nan"),
                            float(phase[env_id].item()),
                            float(torch.linalg.vector_norm(actions[env_id]).item()),
                            float(reward[env_id].item()),
                            float(roll[env_id].item()),
                            *contact_state[env_id].detach().cpu().tolist(),
                            *contact_force_n[env_id].detach().cpu().tolist(),
                            *contact_upward_force_n[env_id]
                            .detach()
                            .cpu()
                            .tolist(),
                            *full_wheel_on_top[env_id]
                            .to(torch.long)
                            .detach()
                            .cpu()
                            .tolist(),
                            int(all_wheels_on_top[env_id].item()),
                            float(support_score[env_id].item()),
                            float(base_forward_speed_m_s[env_id].item()),
                            *wheel_surface_speed_m_s[env_id]
                            .detach()
                            .cpu()
                            .tolist(),
                            float(supported_slip_speed_m_s[env_id].item()),
                            float(supported_slip_ratio[env_id].item()),
                            int(supported_wheel_count[env_id].item()),
                            *wheel_position_y[env_id].detach().cpu().tolist(),
                            *wheel_position_xz[env_id].reshape(-1).detach().cpu().tolist(),
                            *front_load_trim_z_m[env_id].detach().cpu().tolist(),
                            *support_unload_trim_m[env_id].detach().cpu().tolist(),
                            *actions[env_id].detach().cpu().tolist(),
                            *executed_actions[env_id].detach().cpu().tolist(),
                            *scaled_wheel_center_residual_m[env_id]
                            .reshape(-1)
                            .detach()
                            .cpu()
                            .tolist(),
                            *scaled_wheel_speed_residual_rad_s[env_id]
                            .detach()
                            .cpu()
                            .tolist(),
                            *requested_wheel_center_target_m[env_id]
                            .reshape(-1)
                            .detach()
                            .cpu()
                            .tolist(),
                            *final_wheel_center_target_m[env_id]
                            .reshape(-1)
                            .detach()
                            .cpu()
                            .tolist(),
                            *final_servo_targets[env_id].detach().cpu().tolist(),
                            *final_wheel_targets_rad_s[env_id]
                            .detach()
                            .cpu()
                            .tolist(),
                            *reference_commands[env_id].detach().cpu().tolist(),
                        ]
                    )
            for env_id in done.nonzero(as_tuple=False).flatten().detach().cpu().tolist():
                is_success = bool(raw_env._last_done_success[env_id].item())
                success[env_id] = is_success
                if is_success:
                    failure_reason[env_id] = ""
                elif bool(raw_env._last_done_numerical[env_id].item()):
                    failure_reason[env_id] = "NUMERICAL_ERROR"
                elif bool(raw_env._last_done_collision[env_id].item()):
                    failure_reason[env_id] = "BODY_OR_LINK_COLLISION"
                elif bool(raw_env._last_done_fall[env_id].item()):
                    failure_reason[env_id] = "FALL"
                elif bool(raw_env._last_done_joint_limit[env_id].item()):
                    failure_reason[env_id] = "JOINT_LIMIT"
                elif bool(raw_env._last_done_phase_timeout[env_id].item()):
                    failure_reason[env_id] = "FSM_PHASE_TIMEOUT"
                elif bool(truncated_flat[env_id].item()):
                    failure_reason[env_id] = "TIMEOUT"
                else:
                    failure_reason[env_id] = "UNKNOWN_TERMINATION"
                terminal_nonwheel_contact_force_n[env_id] = {
                    name: float(force)
                    for name, force in zip(
                        raw_env._contact_nonwheel_names,
                        raw_env._last_done_nonwheel_contact_force_n[env_id]
                        .detach()
                        .cpu()
                        .tolist(),
                        strict=True,
                    )
                    if force > 0.0
                }
                terminal_wheel_contact_force_magnitude_n[env_id] = (
                    raw_env._last_done_wheel_contact_force_n[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_wheel_contact_upward_force_n[env_id] = (
                    raw_env._last_done_wheel_contact_upward_force_n[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_wheel_on_top[env_id] = (
                    raw_env._last_done_wheel_on_top[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_full_wheel_on_top[env_id] = (
                    raw_env._last_done_full_wheel_on_top[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_all_wheels_on_top[env_id] = bool(
                    raw_env._last_done_all_wheels_on_top[env_id].item()
                )
                terminal_support_score[env_id] = float(
                    raw_env._last_done_support_score[env_id].item()
                )
                terminal_wheel_position_y_m[env_id] = (
                    raw_env._last_done_wheel_position_y[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_front_load_trim_z_m[env_id] = (
                    raw_env._last_done_fsm_front_load_trim_z_m[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_support_unload_trim_m[env_id] = (
                    raw_env._last_done_fsm_support_unload_trim_m[env_id]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_fsm_baseline_ik_invalid_count[env_id] = int(
                    raw_env._last_done_fsm_baseline_ik_invalid_count[
                        env_id
                    ].item()
                )
                terminal_fsm_baseline_ik_invalid_count_per_leg[env_id] = (
                    raw_env._last_done_fsm_baseline_ik_invalid_count_per_leg[
                        env_id
                    ]
                    .detach()
                    .cpu()
                    .tolist()
                )
                terminal_fsm_diagnostic_front_support_clamp_count[env_id] = int(
                    raw_env._last_done_fsm_diagnostic_front_support_clamp_count[
                        env_id
                    ].item()
                )
                terminal_joint_limit_diagnostic[env_id] = (
                    {
                        "joint_position_raw_rad": raw_env._last_done_joint_position[
                            env_id
                        ]
                        .detach()
                        .cpu()
                        .tolist(),
                        "lower_limit_raw_rad": raw_env._raw_servo_lower_limits[
                            env_id
                        ]
                        .detach()
                        .cpu()
                        .tolist(),
                        "upper_limit_raw_rad": raw_env._raw_servo_upper_limits[
                            env_id
                        ]
                        .detach()
                        .cpu()
                        .tolist(),
                        "tracking_tolerance_rad": float(
                            raw_env.cfg.joint_limit_violation_tolerance_rad
                        ),
                        "violating_joint_names": [
                            name
                            for name, violated in zip(
                                raw_env._resolved_servo_joint_names,
                                raw_env._last_done_joint_limit_violation[env_id]
                                .detach()
                                .cpu()
                                .tolist(),
                                strict=True,
                            )
                            if violated
                        ],
                    }
                    if bool(raw_env._last_done_joint_limit[env_id].item())
                    else {}
                )
            active &= ~done
            if step % 300 == 0 or torch.any(done):
                phase_counts = (
                    torch.bincount(phase[active], minlength=13).detach().cpu().tolist()
                    if torch.any(active)
                    else [0] * 13
                )
                status_path.write_text(
                    json.dumps(
                        {
                            "schema": "resume_validation.controller_status.v1",
                            "updated_unix": time.time(),
                            "control_step": step,
                            "sim_time_s": step * float(raw_env.step_dt),
                            "active_count": int(active.sum().item()),
                            "completed_count": int((~active).sum().item()),
                            "success_count": int(success.sum().item()),
                            "phase_counts": phase_counts,
                            "env0": {
                                "base_x_m": float(root_x[0].item()),
                                "phase": int(phase[0].item()),
                                "contact_state": contact_state[0].detach().cpu().tolist(),
                                "contact_force_n": contact_force_n[0].detach().cpu().tolist(),
                                "contact_force_magnitude_n": contact_force_n[0]
                                .detach()
                                .cpu()
                                .tolist(),
                                "contact_upward_force_n": contact_upward_force_n[
                                    0
                                ]
                                .detach()
                                .cpu()
                                .tolist(),
                                "wheel_on_top": wheel_on_top[0]
                                .detach()
                                .cpu()
                                .tolist(),
                                "full_wheel_on_top": full_wheel_on_top[0]
                                .detach()
                                .cpu()
                                .tolist(),
                                "all_wheels_on_top": bool(
                                    all_wheels_on_top[0].item()
                                ),
                                "support_score": float(
                                    support_score[0].item()
                                ),
                                "wheel_position_y_m": wheel_position_y[0]
                                .detach()
                                .cpu()
                                .tolist(),
                                "wheel_position_xz_m": wheel_position_xz[0].detach().cpu().tolist(),
                                "fsm_front_load_trim_z_m": front_load_trim_z_m[0]
                                .detach()
                                .cpu()
                                .tolist(),
                                "fsm_support_unload_trim_m": support_unload_trim_m[0]
                                .detach()
                                .cpu()
                                .tolist(),
                                "terminal_nonwheel_contact_force_n": (
                                    {
                                        name: float(force)
                                        for name, force in zip(
                                            raw_env._contact_nonwheel_names,
                                            raw_env._last_done_nonwheel_contact_force_n[0]
                                            .detach()
                                            .cpu()
                                            .tolist(),
                                            strict=True,
                                        )
                                        if force > 0.0
                                    }
                                    if bool(done[0].item())
                                    else {}
                                ),
                                "terminal_joint_limit_diagnostic": (
                                    {
                                        "joint_position_raw_rad": raw_env._last_done_joint_position[0]
                                        .detach()
                                        .cpu()
                                        .tolist(),
                                        "lower_limit_raw_rad": raw_env._raw_servo_lower_limits[0]
                                        .detach()
                                        .cpu()
                                        .tolist(),
                                        "upper_limit_raw_rad": raw_env._raw_servo_upper_limits[0]
                                        .detach()
                                        .cpu()
                                        .tolist(),
                                        "tracking_tolerance_rad": float(
                                            raw_env.cfg.joint_limit_violation_tolerance_rad
                                        ),
                                        "violating_joint_names": [
                                            name
                                            for name, violated in zip(
                                                raw_env._resolved_servo_joint_names,
                                                raw_env._last_done_joint_limit_violation[0]
                                                .detach()
                                                .cpu()
                                                .tolist(),
                                                strict=True,
                                            )
                                            if violated
                                        ],
                                    }
                                    if bool(raw_env._last_done_joint_limit[0].item())
                                    else {}
                                ),
                            },
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            if not torch.any(active):
                break

        for env_id in active.nonzero(as_tuple=False).flatten().detach().cpu().tolist():
            failure_reason[env_id] = "TIMEOUT"
        episode_rows = []
        for index, scenario in enumerate(scenarios):
            margin_value = float(min_margin[index].item())
            episode_rows.append(
                {
                    **scenario,
                    "controller": args.controller,
                    "success": bool(success[index].item()),
                    "failure_reason": failure_reason[index],
                    "min_longitudinal_support_margin_m": margin_value if math.isfinite(margin_value) else None,
                    "valid_margin_samples": int(valid_margin_count[index].item()),
                    "invalid_margin_samples": int(invalid_margin_count[index].item()),
                    "pitch_rate_rms_rad_s": (
                        math.sqrt(
                            float(pitch_rate_sq_sum[index].item())
                            / int(pitch_rate_count[index].item())
                        )
                        if int(pitch_rate_count[index].item()) > 0
                        else None
                    ),
                    "pitch_rms_rad": (
                        math.sqrt(
                            float(pitch_sq_sum[index].item())
                            / int(episode_step_count[index].item())
                        )
                        if int(episode_step_count[index].item()) > 0
                        else None
                    ),
                    "support_transfer_samples": int(pitch_rate_count[index].item()),
                    "max_abs_pitch_rad": float(max_abs_pitch[index].item()),
                    "peak_abs_pitch_rate_rad_s": float(max_abs_pitch_rate[index].item()),
                    "negative_margin_duration_s": float(negative_margin_duration[index].item()),
                    "wheel_slip_distance_m": float(
                        wheel_slip_distance[index].item()
                    ),
                    "wheel_slip_ratio": (
                        float(wheel_slip_ratio_sum[index].item())
                        / int(wheel_slip_sample_count[index].item())
                        if int(wheel_slip_sample_count[index].item()) > 0
                        else None
                    ),
                    "wheel_slip_valid_samples": int(
                        wheel_slip_sample_count[index].item()
                    ),
                    "residual_saturation_rate": float(saturation_steps[index].item())
                    / max(1, int(episode_step_count[index].item())),
                    "wheel_speed_saturation_rate": float(
                        wheel_speed_saturation_steps[index].item()
                    )
                    / max(1, int(episode_step_count[index].item())),
                    "executed_residual_command_variation_l2": float(
                        executed_action_variation_sum[index].item()
                    )
                    / max(1, int(episode_step_count[index].item())),
                    "traversal_time_s": float(
                        episode_step_count[index].item()
                    )
                    * float(raw_env.step_dt),
                    "forward_progress_m": float((final_base_x[index] - initial_base_x[index]).item()),
                    "terminal_nonwheel_contact_force_n": (
                        terminal_nonwheel_contact_force_n[index] or {}
                    ),
                    "terminal_wheel_contact_force_magnitude_n": (
                        terminal_wheel_contact_force_magnitude_n[index]
                        or [0.0, 0.0, 0.0, 0.0]
                    ),
                    "terminal_wheel_contact_upward_force_n": (
                        terminal_wheel_contact_upward_force_n[index]
                        or [0.0, 0.0, 0.0, 0.0]
                    ),
                    "terminal_wheel_on_top": (
                        terminal_wheel_on_top[index]
                        or [False, False, False, False]
                    ),
                    "terminal_full_wheel_on_top": (
                        terminal_full_wheel_on_top[index]
                        or [False, False, False, False]
                    ),
                    "terminal_all_wheels_on_top": bool(
                        terminal_all_wheels_on_top[index] or False
                    ),
                    "terminal_support_score": (
                        terminal_support_score[index]
                        if terminal_support_score[index] is not None
                        else 0.0
                    ),
                    "terminal_wheel_position_y_m": (
                        terminal_wheel_position_y_m[index]
                        or [0.0, 0.0, 0.0, 0.0]
                    ),
                    "terminal_fsm_front_load_trim_z_m": (
                        terminal_front_load_trim_z_m[index] or [0.0, 0.0]
                    ),
                    "terminal_fsm_support_unload_trim_m": (
                        terminal_support_unload_trim_m[index]
                        or [0.0, 0.0, 0.0, 0.0]
                    ),
                    "terminal_fsm_baseline_ik_invalid_count": (
                        terminal_fsm_baseline_ik_invalid_count[index] or 0
                    ),
                    "terminal_fsm_baseline_ik_invalid_count_per_leg": (
                        terminal_fsm_baseline_ik_invalid_count_per_leg[index]
                        or [0, 0, 0, 0]
                    ),
                    "terminal_fsm_diagnostic_front_support_clamp_count": (
                        terminal_fsm_diagnostic_front_support_clamp_count[index]
                        or 0
                    ),
                    "terminal_joint_limit_diagnostic": (
                        terminal_joint_limit_diagnostic[index] or {}
                    ),
                }
            )
        episodes_path = output_dir / "episodes.jsonl"
        episodes_path.write_text(
            "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in episode_rows),
            encoding="utf-8",
        )
        telemetry_path = output_dir / "telemetry.csv"
        with telemetry_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "time_s", "env_id", "base_x_m", "pitch_rad",
                    "pitch_rate_rad_s", "margin_m", "fsm_phase", "action_l2",
                    "reward", "roll_rad",
                    "fl_contact_state", "fr_contact_state", "rl_contact_state", "rr_contact_state",
                    "fl_contact_force_n", "fr_contact_force_n", "rl_contact_force_n", "rr_contact_force_n",
                    "fl_contact_upward_force_n", "fr_contact_upward_force_n",
                    "rl_contact_upward_force_n", "rr_contact_upward_force_n",
                    "fl_full_wheel_on_top", "fr_full_wheel_on_top",
                    "rl_full_wheel_on_top", "rr_full_wheel_on_top",
                    "all_wheels_on_top", "support_score",
                    "base_forward_speed_m_s",
                    "fl_wheel_surface_speed_m_s", "fr_wheel_surface_speed_m_s",
                    "rl_wheel_surface_speed_m_s", "rr_wheel_surface_speed_m_s",
                    "supported_slip_speed_m_s", "supported_slip_ratio",
                    "supported_wheel_count",
                    "fl_wheel_y_m", "fr_wheel_y_m", "rl_wheel_y_m", "rr_wheel_y_m",
                    "fl_wheel_x_m", "fl_wheel_z_m", "fr_wheel_x_m", "fr_wheel_z_m",
                    "rl_wheel_x_m", "rl_wheel_z_m", "rr_wheel_x_m", "rr_wheel_z_m",
                    "fl_load_trim_z_m", "fr_load_trim_z_m",
                    "fl_unload_trim_m", "fr_unload_trim_m", "rl_unload_trim_m", "rr_unload_trim_m",
                    *[f"policy_action_{index:02d}" for index in range(12)],
                    *[f"executed_action_{index:02d}" for index in range(12)],
                    *[
                        f"scaled_wheel_center_residual_m_{index:02d}"
                        for index in range(8)
                    ],
                    *[
                        f"scaled_wheel_speed_residual_rad_s_{index:02d}"
                        for index in range(4)
                    ],
                    *[
                        f"requested_wheel_center_target_m_{index:02d}"
                        for index in range(8)
                    ],
                    *[
                        f"final_wheel_center_target_m_{index:02d}"
                        for index in range(8)
                    ],
                    *[f"final_servo_target_rad_{index:02d}" for index in range(8)],
                    *[
                        f"final_wheel_target_rad_s_{index:02d}"
                        for index in range(4)
                    ],
                    *[f"reference_{index:02d}" for index in range(12)],
                ]
            )
            writer.writerows(rows)
        valid_episode_margins = [
            row["min_longitudinal_support_margin_m"]
            for row in episode_rows
            if row["min_longitudinal_support_margin_m"] is not None
        ]
        result["aggregate"] = {
            "episode_count": count,
            "success_count": int(success.sum().item()),
            "success_rate": float(success.to(torch.float32).mean().item()),
            "mean_episode_min_margin_m": (
                sum(valid_episode_margins) / len(valid_episode_margins) if valid_episode_margins else None
            ),
            "mean_pitch_rate_rms_rad_s": (
                sum(
                    row["pitch_rate_rms_rad_s"]
                    for row in episode_rows
                    if row["pitch_rate_rms_rad_s"] is not None
                )
                / sum(row["pitch_rate_rms_rad_s"] is not None for row in episode_rows)
                if any(row["pitch_rate_rms_rad_s"] is not None for row in episode_rows)
                else None
            ),
            "failure_counts": {
                reason: sum(row["failure_reason"] == reason for row in episode_rows)
                for reason in sorted({row["failure_reason"] for row in episode_rows if row["failure_reason"]})
            },
        }
        result["artifacts"] = {
            "episodes": str(episodes_path),
            "episodes_sha256": sha256_file(episodes_path),
            "telemetry": str(telemetry_path),
            "telemetry_sha256": sha256_file(telemetry_path),
            "status": str(status_path),
            "status_sha256": sha256_file(status_path),
        }
        if video_writer is not None:
            video_writer.close()
            video_writer = None
        if video_path is not None:
            if video_frame_count <= 0:
                raise RuntimeError("Video replay produced no captured frames")
            result["video_replay"]["frame_count"] = video_frame_count
            result["video_replay"]["encoded_frame_count"] = encoded_frame_count
            result["video_replay"]["duration_s"] = (
                video_frame_count / float(args.video_fps)
            )
            result["video_replay"]["encoding_error"] = video_encoding_error
            if video_frames_dir is not None:
                result["artifacts"]["video_frames"] = str(video_frames_dir)
            if video_path.is_file() and video_path.stat().st_size > 0 and video_encoding_error is None:
                result["video_replay"]["sha256"] = sha256_file(video_path)
                result["artifacts"]["video"] = str(video_path)
                result["artifacts"]["video_sha256"] = sha256_file(video_path)
        result["passed_execution"] = True
    except Exception as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
        result["traceback"] = traceback.format_exc()
    finally:
        if video_writer is not None:
            video_writer.close()
        result["finished_unix"] = time.time()
        write_heartbeat("FINISHED", float(result.get("video_replay", {}).get("duration_s", 0.0)))
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        if env is not None:
            env.close()
        elif raw_env is not None:
            raw_env.close()
        # Isaac Sim 5.1 can wait indefinitely for a Replicator workflow during
        # graceful shutdown even though this evaluator uses an independent
        # imageio writer.  Do not wait for Replicator; all capture artifacts are
        # closed above before application teardown.
        app.close(wait_for_replicator=False)
    print(json.dumps({"result": str(result_path), "passed_execution": result["passed_execution"], "failures": result["failures"]}, indent=2))
    return 0 if result["passed_execution"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
