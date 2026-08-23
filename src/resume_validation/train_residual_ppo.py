"""Train one auditable residual-PPO method/seed/stage with skrl 2.0."""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import math
import os
import random
import sys
import time
from datetime import datetime
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
parser.add_argument("--method", choices=("B", "C"), required=True)
parser.add_argument("--seed", type=int, choices=(11, 29, 47), required=True)
parser.add_argument("--height_mm", type=int, choices=(50, 75, 100), required=True)
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--iterations", type=int, default=300)
parser.add_argument("--rollouts", type=int, default=64)
parser.add_argument("--learning_epochs", type=int, default=5)
parser.add_argument("--mini_batches", type=int, default=8)
parser.add_argument("--checkpoint_every_iterations", type=int, default=25)
parser.add_argument("--resume", type=Path)
parser.add_argument(
    "--resume_offset_timesteps",
    type=int,
    default=0,
    help="Completed timesteps represented by a recovery checkpoint in the same stage",
)
parser.add_argument("--run_name", type=str, default="")
parser.add_argument("--output_root", type=Path, default=VALIDATION_ROOT / "runs" / "training")
parser.add_argument("--robot_usd", type=Path, default=VALIDATION_ROOT / "assets" / "converted" / "wlr_robot_validation.usd")
parser.add_argument(
    "--randomization_level",
    choices=("nominal", "light", "full"),
    default="nominal",
)
parser.add_argument("--smoke_only", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import gymnasium as gym
import numpy as np
import torch
from torch import nn

import skrl
from isaaclab_rl.skrl import SkrlVecEnvWrapper
from skrl.agents.torch.ppo import PPO
from skrl.agents.torch.ppo.ppo import PPO_CFG
from skrl.memories.torch import RandomMemory
from skrl.resources.preprocessors.torch import RunningStandardScaler
from skrl.resources.schedulers.torch import KLAdaptiveLR
from skrl.trainers.torch import SequentialTrainer

from resume_validation.config_io import config_sha256, differing_leaf_paths, load_config
from resume_validation.episode_tracking import advance_episode_accumulators
from resume_validation.load_balance import (
    formal_post_transfer_drive_speed,
    formal_post_transfer_support_geometry,
    formal_rear_transfer_wheel_speed,
    formal_support_unload_policy,
)
from resume_validation.ppo_models import (
    ACTOR_HIDDEN,
    CRITIC_HIDDEN,
    INITIAL_LOG_STD,
    MAX_LOG_STD,
    MIN_LOG_STD,
    ResidualPolicy,
    ResidualValue,
    flat_dim,
)
from resume_validation.residual_rl_env import (
    ACTION_DIM,
    ACTOR_OBS_DIM,
    CRITIC_STATE_DIM,
    REWARD_WEIGHTS,
    WLRResidualRLEnv,
    make_residual_env_cfg,
)
from resume_validation.source_audit import sha256_file


class AuditablePPO(PPO):
    """PPO with a local display-accumulator repair for skrl 2.0.

    ``PPO.record_transition`` still performs the unmodified memory write and
    learning data path. Only the two display accumulators are restored from
    their pre-call values using correct first-axis done indexing.
    """

    def record_transition(self, **kwargs) -> None:
        if self.write_interval > 0:
            previous_rewards = (
                None
                if self._cumulative_rewards is None
                else self._cumulative_rewards.clone()
            )
            previous_timesteps = (
                None
                if self._cumulative_timesteps is None
                else self._cumulative_timesteps.clone()
            )
        else:
            previous_rewards = None
            previous_timesteps = None

        super().record_transition(**kwargs)

        if self.write_interval > 0:
            (
                self._cumulative_rewards,
                self._cumulative_timesteps,
            ) = advance_episode_accumulators(
                previous_rewards,
                previous_timesteps,
                kwargs["rewards"],
                kwargs["terminated"],
                kwargs["truncated"],
            )


def ppo_config(run_dir: Path, device: torch.device, common_cfg: dict) -> dict:
    ppo = common_cfg["ppo"]
    cfg: dict = {}
    cfg.update(
        {
            "rollouts": args.rollouts,
            "learning_epochs": args.learning_epochs,
            "mini_batches": args.mini_batches,
            "discount_factor": float(ppo["discount_factor"]),
            "gae_lambda": float(ppo["lambda"]),
            "learning_rate": float(ppo["learning_rate"]),
            "learning_rate_scheduler": KLAdaptiveLR,
            "learning_rate_scheduler_kwargs": {"kl_threshold": float(ppo["kl_threshold"])},
            "random_timesteps": 0,
            "learning_starts": 0,
            "grad_norm_clip": float(ppo["grad_norm_clip"]),
            "ratio_clip": float(ppo["ratio_clip"]),
            "value_clip": float(ppo["value_clip"]),
            "entropy_loss_scale": float(ppo["entropy_loss_scale"]),
            "value_loss_scale": 1.0,
            "kl_threshold": float(ppo["kl_threshold"]),
            "observation_preprocessor": RunningStandardScaler,
            "observation_preprocessor_kwargs": {"size": ACTOR_OBS_DIM, "device": device},
            "state_preprocessor": RunningStandardScaler,
            "state_preprocessor_kwargs": {"size": CRITIC_STATE_DIM, "device": device},
            "value_preprocessor": RunningStandardScaler,
            "value_preprocessor_kwargs": {"size": 1, "device": device},
            "time_limit_bootstrap": False,
            "experiment": {
                "directory": str(run_dir.parent),
                "experiment_name": run_dir.name,
                "write_interval": args.rollouts,
                "checkpoint_interval": max(1, args.checkpoint_every_iterations) * args.rollouts,
                "store_separately": False,
                "wandb": False,
            },
        }
    )
    try:
        signature = inspect.signature(PPO.__init__)
        if "cfg" not in signature.parameters:
            raise RuntimeError("Installed skrl PPO does not expose cfg")
    except (TypeError, ValueError):
        pass
    unknown = set(cfg) - set(inspect.signature(PPO_CFG).parameters)
    if unknown:
        raise RuntimeError(
            f"Installed skrl PPO_CFG does not support keys: {sorted(unknown)}"
        )
    return cfg


def finite_models(models: dict[str, nn.Module]) -> bool:
    return all(torch.isfinite(value).all().item() for model in models.values() for value in model.state_dict().values())


def main() -> int:
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    method_name = "without_com" if args.method == "B" else "with_com"
    run_name = args.run_name.strip() or (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_method-{args.method}_{method_name}"
        f"_seed-{args.seed}_height-{args.height_mm}mm"
    )
    run_dir = args.output_root.resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=False)
    result_path = run_dir / "training_result.json"
    result: dict = {
        "schema": "resume_validation.residual_ppo_training.v1",
        "started_unix": time.time(),
        "method": args.method,
        "method_name": method_name,
        "seed": args.seed,
        "height_mm": args.height_mm,
        "run_dir": str(run_dir),
        "status": "RUNNING",
        "failures": [],
        "training_budget": {
            "local_timesteps_requested": args.iterations * args.rollouts,
            "resume_offset_timesteps": args.resume_offset_timesteps,
            "cumulative_timesteps_requested": (
                args.resume_offset_timesteps + args.iterations * args.rollouts
            ),
            "parallel_environments": args.num_envs,
            "local_transitions_requested": (
                args.iterations * args.rollouts * args.num_envs
            ),
            "cumulative_transitions_requested": (
                (args.resume_offset_timesteps + args.iterations * args.rollouts)
                * args.num_envs
            ),
        },
    }
    raw_env = None
    env = None
    try:
        if args.resume_offset_timesteps < 0:
            raise RuntimeError("resume_offset_timesteps must be nonnegative")
        if args.resume_offset_timesteps % args.rollouts != 0:
            raise RuntimeError("resume_offset_timesteps must align to a rollout boundary")
        if args.resume_offset_timesteps and args.resume is None:
            raise RuntimeError("resume_offset_timesteps requires --resume")
        config_paths = [
            VALIDATION_ROOT / "configs" / "ppo_common.yaml",
            VALIDATION_ROOT / "configs" / ("ppo_without_com.yaml" if args.method == "B" else "ppo_with_com.yaml"),
            VALIDATION_ROOT / "configs" / "metrics.yaml",
            VALIDATION_ROOT / "configs" / "fsm.yaml",
            VALIDATION_ROOT / "configs" / "obstacle_train.yaml",
        ]
        metrics_cfg = load_config(config_paths[2])
        fsm_cfg = load_config(config_paths[3])
        obstacle_train_cfg = load_config(config_paths[4])
        if not metrics_cfg.get("frozen", False):
            raise RuntimeError("metrics.yaml is not frozen")
        if not fsm_cfg.get("frozen", False):
            raise RuntimeError("fsm.yaml is not frozen")
        common_cfg = load_config(config_paths[0])
        common_reward_weights = {
            str(name): float(value)
            for name, value in common_cfg["reward"]["weights"].items()
        }
        residual_phase_window = tuple(
            int(value)
            for value in common_cfg["action"]["execution_phase_window"]
        )
        residual_phase_gains = tuple(
            float(value)
            for value in common_cfg["action"]["execution_phase_gains"]
        )
        residual_applied_action_hard_clip = float(
            common_cfg["action"]["applied_action_hard_clip"]
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
                not np.isfinite(value) or value <= 0.0 or value > 4.0
                for value in residual_phase_gains
            )
        ):
            raise RuntimeError(
                f"Invalid common residual execution phase gains: {residual_phase_gains}"
            )
        projection_cfg = common_cfg["action"]["execution_projection"]
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
        state_gate_cfg = common_cfg["action"]["execution_state_gate"]
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
            or not np.isfinite(
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
            or not np.isfinite(residual_applied_action_hard_clip)
            or residual_applied_action_hard_clip != 1.0
            or residual_state_gate_type
            != "phase_aware_roll_imu_emergency"
            or not np.isfinite(residual_state_gate_min_pitch_rad)
            or residual_state_gate_min_pitch_rad != 0.09
            or not np.isfinite(residual_state_gate_min_roll_rad)
            or residual_state_gate_min_roll_rad != 0.10
            or not np.isfinite(residual_state_gate_early_roll_rad)
            or residual_state_gate_early_roll_rad != 0.06
            or not np.isfinite(
                residual_state_gate_early_pitch_rate_rad_s
            )
            or residual_state_gate_early_pitch_rate_rad_s != 0.35
            or not residual_state_gate_corrective_latch
        ):
            raise RuntimeError(
                "Invalid common residual projection/state gate: "
                f"{projection_cfg}, {state_gate_cfg}"
            )
        registered_local_timesteps = int(
            common_cfg["training_budget"]["local_timesteps_by_stage"][
                str(args.height_mm)
            ]
        )
        requested_cumulative_timesteps = (
            args.resume_offset_timesteps + args.iterations * args.rollouts
        )
        if (
            not args.smoke_only
            and requested_cumulative_timesteps
            != registered_local_timesteps
        ):
            raise RuntimeError(
                "Requested cumulative timesteps "
                f"{requested_cumulative_timesteps} != registered full-development "
                f"budget {registered_local_timesteps}"
            )
        network_cfg = common_cfg["network"]
        if tuple(network_cfg["actor_hidden"]) != ACTOR_HIDDEN:
            raise RuntimeError("Actor architecture differs from the recorded common config")
        if tuple(network_cfg["critic_hidden"]) != CRITIC_HIDDEN:
            raise RuntimeError("Critic architecture differs from the recorded common config")
        if str(network_cfg["activation"]).lower() != "elu":
            raise RuntimeError("Only the recorded ELU architecture is implemented")
        if str(network_cfg["initial_actor_mean"]).lower() != "zero":
            raise RuntimeError("Initial actor mean must be recorded as zero")
        if float(network_cfg["initial_log_std"]) != INITIAL_LOG_STD:
            raise RuntimeError("Initial actor log standard deviation differs from the model")
        if float(network_cfg["min_log_std"]) != MIN_LOG_STD:
            raise RuntimeError("Minimum actor log standard deviation differs from the model")
        if float(network_cfg["max_log_std"]) != MAX_LOG_STD:
            raise RuntimeError("Maximum actor log standard deviation differs from the model")
        if not (
            MIN_LOG_STD <= INITIAL_LOG_STD <= MAX_LOG_STD
        ):
            raise RuntimeError(
                "Actor log standard deviation initialization is outside its bounds"
            )
        without_com_cfg = load_config(VALIDATION_ROOT / "configs" / "ppo_without_com.yaml")
        with_com_cfg = load_config(VALIDATION_ROOT / "configs" / "ppo_with_com.yaml")
        actual_ablation_differences = differing_leaf_paths(without_com_cfg, with_com_cfg)
        expected_ablation_differences = {"method", "reward.com_margin_weight"}
        if actual_ablation_differences != expected_ablation_differences:
            raise RuntimeError(
                "B/C configuration drift: expected only method label and CoM reward weight "
                f"to differ, got {sorted(actual_ablation_differences)}"
            )
        method_cfg = without_com_cfg if args.method == "B" else with_com_cfg
        com_weight = float(method_cfg["reward"]["com_margin_weight"])
        expected_com_weight = 0.0 if args.method == "B" else 8.0
        if com_weight != expected_com_weight:
            raise RuntimeError(
                f"Method {args.method} CoM reward weight {com_weight} != frozen intended {expected_com_weight}"
            )
        max_idle_gap_s = float(fsm_cfg["playback_profile"]["max_idle_gap_s"])
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
        cfg = make_residual_env_cfg(
            num_envs=args.num_envs,
            obstacle_height=args.height_mm / 1000.0,
            robot_usd_path=args.robot_usd,
            episode_length_s=150.0,
            com_margin_weight=com_weight,
            max_idle_gap_s=max_idle_gap_s,
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
        cfg.seed = args.seed
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        result["provenance"] = {
            "asset_path": str(args.robot_usd.resolve()),
            "asset_sha256": sha256_file(args.robot_usd),
            "configs": {
                path.name: {"path": str(path), "sha256": sha256_file(path), "canonical_config_sha256": config_sha256(path)}
                for path in config_paths
            },
            "source_files": {
                name: {
                    "path": str(VALIDATION_ROOT / "src" / "resume_validation" / name),
                    "sha256": sha256_file(
                        VALIDATION_ROOT / "src" / "resume_validation" / name
                    ),
                }
                for name in (
                    "episode_tracking.py",
                    "reward.py",
                    "residual_rl_env.py",
                    "residual_safety.py",
                    "training_randomization.py",
                    "ppo_models.py",
                    "train_residual_ppo.py",
                )
            },
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
            "effective_reward_weights": cfg.residual_reward_weights,
            "effective_training_randomization": {
                str(name): value
                for name, value in obstacle_train_cfg["randomization_levels"][
                    args.randomization_level
                ].items()
            },
            "effective_residual_bounds": {
                str(name): float(value)
                for name, value in cfg.residual_bounds.items()
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
            "registered_local_training_timesteps": (
                registered_local_timesteps
            ),
            "reward_occupancy_integration": common_cfg["reward"][
                "occupancy_integration"
            ],
            "reward_rate_integration": common_cfg["reward"][
                "rate_integration"
            ],
            "reward_terminal_safety": common_cfg["reward"][
                "terminal_safety"
            ],
            "reward_reset_initialization": common_cfg["reward"][
                "reset_initialization"
            ],
            "reward_baseline_regularization_timebase": common_cfg["reward"][
                "baseline_regularization_timebase"
            ],
            "episode_tracker_policy": (
                "local AuditablePPO repairs only skrl 2.0 display accumulators; "
                "rollout memory, GAE, losses, and parameter updates are unchanged"
            ),
            "isaaclab": importlib.metadata.version("isaaclab"),
            "isaacsim": importlib.metadata.version("isaacsim"),
            "skrl": skrl.__version__,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "pid": os.getpid(),
        }
        result["arguments"] = vars(args).copy()
        for key, value in list(result["arguments"].items()):
            if isinstance(value, Path):
                result["arguments"][key] = str(value)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        raw_env = WLRResidualRLEnv(cfg)
        raw_env.configure_training_randomization(
            level_cfg=obstacle_train_cfg["randomization_levels"][
                args.randomization_level
            ],
            seed=args.seed,
            nominal_distance_m=float(
                obstacle_train_cfg["initial_distance"]["nominal_m"]
            ),
        )
        env = SkrlVecEnvWrapper(raw_env, ml_framework="torch")
        device = torch.device(env.device)
        skrl.config.torch.device = device
        observation_space = env.observation_space
        state_space = env.state_space
        action_space = env.action_space
        if flat_dim(observation_space) != ACTOR_OBS_DIM or flat_dim(state_space) != CRITIC_STATE_DIM:
            raise RuntimeError("Actor/critic space dimensions do not match the frozen schema")
        models = {
            "policy": ResidualPolicy(observation_space, action_space, device),
            "value": ResidualValue(state_space, action_space, device),
        }
        memory = RandomMemory(memory_size=args.rollouts, num_envs=env.num_envs, device=device)
        agent = AuditablePPO(
            models=models,
            memory=memory,
            cfg=ppo_config(run_dir, device, common_cfg),
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=device,
        )
        if args.resume:
            agent.load(str(args.resume.resolve()))
            result["resume_checkpoint"] = {
                "path": str(args.resume.resolve()),
                "sha256": sha256_file(args.resume),
            }

        trainer = SequentialTrainer(
            cfg={
                "timesteps": args.iterations * args.rollouts,
                "headless": True,
                "disable_progressbar": False,
                "close_environment_at_exit": False,
                "environment_info": "log",
            },
            env=env,
            agents=agent,
        )
        observation, _ = env.reset()
        states = env.state()
        if not torch.isfinite(observation).all() or states is None or not torch.isfinite(states).all():
            raise RuntimeError("Non-finite actor observation or critic state before training")
        agent.enable_training_mode(True)
        with torch.no_grad():
            preflight_action, _ = agent.act(
                observation,
                states,
                timestep=0,
                timesteps=max(1, args.iterations * args.rollouts),
            )
        if (
            preflight_action.shape != (env.num_envs, ACTION_DIM)
            or not torch.isfinite(preflight_action).all()
            or agent._current_values is None
            or not torch.isfinite(agent._current_values).all()
        ):
            raise RuntimeError("PPO preflight action/value has invalid shape or values")
        for _ in range(8):
            action = torch.zeros((env.num_envs, ACTION_DIM), device=device)
            observation, reward, terminated, truncated, _ = env.step(action)
            if not all(torch.isfinite(value).all() for value in (observation, reward, env.state())):
                raise RuntimeError("Non-finite zero-residual smoke rollout")
        reward_terms = raw_env._last_raw_reward_terms
        if set(reward_terms) != set(REWARD_WEIGHTS):
            raise RuntimeError(
                "Runtime reward terms differ from the registered reward keys"
            )
        if not all(torch.isfinite(value).all() for value in reward_terms.values()):
            raise RuntimeError("Non-finite runtime raw reward term")
        terminal_safety_names = (
            "fall",
            "body_collision",
            "numerical",
            "phase_timeout",
            "joint_limit",
        )
        result["preflight"] = {
            "actor_observation_shape": list(observation.shape),
            "critic_state_shape": list(env.state().shape),
            "contact_force_finite": bool(torch.isfinite(raw_env._contact_sensor.data.net_forces_w).all().item()),
            "policy_action_shape": list(preflight_action.shape),
            "policy_action_finite": True,
            "policy_action_max_abs": float(torch.abs(preflight_action).max().item()),
            "critic_value_shape": list(agent._current_values.shape),
            "critic_value_finite": True,
            "zero_residual_exact": True,
            "reward_term_count": len(reward_terms),
            "reward_term_names": sorted(reward_terms),
            "reward_terms_finite": True,
            "reward_control_step_dt_s": float(raw_env.step_dt),
            "terminal_safety_raw_max_abs": {
                name: float(torch.abs(reward_terms[name]).max().item())
                for name in terminal_safety_names
            },
            "episode_tracker_class": type(agent).__name__,
            "episode_tracker_env0_preserved_when_other_envs_done": bool(
                advance_episode_accumulators(
                    torch.arange(8, dtype=torch.float32, device=device).reshape(
                        8, 1
                    ),
                    torch.arange(
                        10, 18, dtype=torch.int32, device=device
                    ).reshape(8, 1),
                    torch.ones((8, 1), dtype=torch.float32, device=device),
                    torch.tensor(
                        [[False], [False], [False], [False], [False], [True], [False], [False]],
                        dtype=torch.bool,
                        device=device,
                    ),
                    torch.tensor(
                        [[False], [False], [False], [False], [False], [False], [False], [True]],
                        dtype=torch.bool,
                        device=device,
                    ),
                )[0][0].item()
                == 1.0
            ),
        }
        if args.smoke_only:
            probe_env_ids = torch.tensor(
                [0],
                dtype=torch.long,
                device=device,
            )
            original_probe_root_pose = raw_env._robot.data.root_pose_w[
                probe_env_ids
            ].clone()
            original_probe_root_velocity = (
                raw_env._robot.data.root_vel_w[probe_env_ids].clone()
            )
            projection_probe = torch.tensor(
                [
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.8,
                    0.9,
                    -1.0,
                    0.2,
                    -0.3,
                ],
                dtype=raw_env._raw_actions.dtype,
                device=raw_env._raw_actions.device,
            )
            raw_env._raw_actions[0] = projection_probe
            raw_env._fsm_phase[0] = residual_phase_window[0]
            raw_env._process_residual_actions()
            below_hazard_roll_rad, below_hazard_pitch_rad, _ = (
                raw_env._roll_pitch_yaw()
            )
            below_hazard_roll_rad = float(below_hazard_roll_rad[0].item())
            below_hazard_pitch_rad = float(below_hazard_pitch_rad[0].item())
            below_hazard_exact_zero = bool(
                below_hazard_pitch_rad < residual_state_gate_min_pitch_rad
                and below_hazard_roll_rad
                < residual_state_gate_early_roll_rad
                and torch.all(raw_env._applied_actions[0] == 0.0).item()
                and torch.all(
                    raw_env._scaled_wheel_center_residual_m[0] == 0.0
                ).item()
            )
            result["preflight"][
                "residual_state_gate_below_pitch_rad"
            ] = below_hazard_pitch_rad
            result["preflight"][
                "residual_state_gate_below_roll_rad"
            ] = below_hazard_roll_rad
            result["preflight"][
                "residual_state_gate_below_exact_zero"
            ] = below_hazard_exact_zero
            if not below_hazard_exact_zero:
                raise RuntimeError(
                    "Registered roll/pitch state gate did not preserve "
                    "exact zero below threshold"
                )
            hazard_probe_root_pose = original_probe_root_pose.clone()
            hazard_probe_root_pose[:, 3:7] = torch.tensor(
                [
                    math.cos(0.055),
                    math.sin(0.055),
                    0.0,
                    0.0,
                ],
                dtype=hazard_probe_root_pose.dtype,
                device=device,
            )
            raw_env._robot.write_root_pose_to_sim(
                hazard_probe_root_pose,
                probe_env_ids,
            )
            raw_env._robot.write_root_velocity_to_sim(
                torch.zeros((1, 6), dtype=torch.float32, device=device),
                probe_env_ids,
            )
            raw_env.scene.write_data_to_sim()
            above_hazard_roll_rad = float(
                raw_env._roll_pitch_yaw()[0][0].item()
            )
            result["preflight"][
                "residual_state_gate_above_roll_rad"
            ] = above_hazard_roll_rad
            if above_hazard_roll_rad < residual_state_gate_min_roll_rad:
                raise RuntimeError(
                    "Positive-roll hazard probe did not cross the registered "
                    "state-gate threshold"
                )
            realization_phase_bounds = (
                raw_env._phase_bounds_by_height()
            )
            realization_upper_progress = realization_phase_bounds[
                0,
                residual_phase_window[0],
            ]
            realization_progress_increment = (
                float(raw_env.step_dt)
                / raw_env._reference_bank.duration_s(
                    raw_env._obstacle_height_env
                )[0]
            )
            realization_target_progress = torch.clamp(
                realization_upper_progress - 1.0e-6,
                min=0.0,
                max=1.0,
            )
            raw_env._reference_progress[0] = torch.clamp(
                realization_target_progress
                - realization_progress_increment,
                min=0.0,
                max=1.0,
            )
            raw_env._fsm_phase[0] = residual_phase_window[0]
            raw_env._phase_exit_debounce_counter[0] = 0
            raw_env._phase_exit_latched[0] = False
            raw_env._residual_phase8_corrective_latched[0] = False
            raw_env._update_fsm_reference()
            realization_actual_phase = int(
                raw_env._fsm_phase[0].item()
            )
            realization_actual_progress = float(
                raw_env._reference_progress[0].item()
            )
            if realization_actual_phase != residual_phase_window[0]:
                raise RuntimeError(
                    "Physical-realization probe did not sample the held "
                    "phase-8 FSM reference"
                )
            small_positive_probe = projection_probe * 0.25
            raw_env._raw_actions[0].zero_()
            raw_env._process_residual_actions()
            raw_env._raw_actions[0] = small_positive_probe
            residual_ik_invalid_before = int(
                raw_env._ik_invalid_count[0].item()
            )
            raw_env._process_residual_actions()
            residual_ik_invalid_after = int(
                raw_env._ik_invalid_count[0].item()
            )
            realization_reference_center = (
                raw_env._reference_wheel_centers[0].detach().clone()
            )
            realization_requested_center = (
                raw_env._requested_wheel_center_target_m[0]
                .detach()
                .clone()
            )
            realization_final_center = (
                raw_env._final_wheel_center_target_m[0]
                .detach()
                .clone()
            )
            realization_baseline_raw = (
                raw_env._standing_servo_pos[0]
                + raw_env._joint_command_sign[0]
                * torch.deg2rad(raw_env._reference_commands[0, :8])
            )
            realization_baseline_raw_all = (
                raw_env._standing_servo_pos
                + raw_env._joint_command_sign
                * torch.deg2rad(raw_env._reference_commands[:, :8])
            )
            _, realization_ik_valid_all = raw_env._solve_ik(
                raw_env._requested_wheel_center_target_m,
                realization_baseline_raw_all,
            )
            realization_ik_valid = (
                realization_ik_valid_all[0].detach().clone()
            )
            realization_final_servo = (
                raw_env._servo_targets[0].detach().clone()
            )
            realization_requested_delta = (
                realization_requested_center
                - realization_reference_center
            )
            realization_final_delta = (
                realization_final_center
                - realization_reference_center
            )
            realization_floor_m = (
                residual_corrective_minimum_shared_magnitude
                * residual_phase_gains[0]
                * float(
                    raw_env.cfg.residual_bounds["wheel_center_z_m"]
                )
            )
            front_right_requested_error_m = float(
                torch.abs(
                    realization_requested_delta[1, 1]
                    + realization_floor_m
                ).item()
            )
            rear_left_requested_error_m = float(
                torch.abs(
                    realization_requested_delta[2, 1]
                    - (
                        realization_floor_m
                        * residual_executed_z_signs[2]
                        * residual_corrective_z_scales[2]
                    )
                ).item()
            )
            front_right_final_target_improved = bool(
                realization_final_delta[1, 1].item() < -1.0e-7
                and torch.abs(
                    realization_final_center[1, 1]
                    - realization_requested_center[1, 1]
                ).item()
                < torch.abs(
                    realization_reference_center[1, 1]
                    - realization_requested_center[1, 1]
                ).item()
            )
            rear_left_final_target_improved = bool(
                (
                    realization_final_delta[2, 1].item()
                    * residual_executed_z_signs[2]
                )
                > 1.0e-7
                and torch.abs(
                    realization_final_center[2, 1]
                    - realization_requested_center[2, 1]
                ).item()
                < torch.abs(
                    realization_reference_center[2, 1]
                    - realization_requested_center[2, 1]
                ).item()
            )
            inactive_requested_exact = bool(
                torch.equal(
                    realization_requested_delta[:, 0],
                    torch.zeros(
                        4,
                        dtype=realization_requested_delta.dtype,
                        device=device,
                    ),
                )
                and realization_requested_delta[0, 1].item() == 0.0
                and realization_requested_delta[3, 1].item() == 0.0
            )
            front_right_servo_delta_max_abs_rad = float(
                torch.abs(
                    realization_final_servo[2:4]
                    - realization_baseline_raw[2:4]
                ).max().item()
            )
            rear_left_servo_delta_max_abs_rad = float(
                torch.abs(
                    realization_final_servo[4:6]
                    - realization_baseline_raw[4:6]
                ).max().item()
            )
            residual_final_target_realization_passed = bool(
                residual_ik_invalid_after == residual_ik_invalid_before
                and torch.all(realization_ik_valid).item()
                and front_right_requested_error_m <= 1.0e-8
                and rear_left_requested_error_m <= 1.0e-8
                and front_right_final_target_improved
                and rear_left_final_target_improved
                and inactive_requested_exact
                and front_right_servo_delta_max_abs_rad > 1.0e-7
                and rear_left_servo_delta_max_abs_rad > 1.0e-7
            )
            result["preflight"][
                "residual_realization_requested_delta_z_m"
            ] = realization_requested_delta[:, 1].cpu().tolist()
            result["preflight"][
                "residual_realization_reference_phase"
            ] = realization_actual_phase
            result["preflight"][
                "residual_realization_reference_progress"
            ] = realization_actual_progress
            result["preflight"][
                "residual_realization_ik_valid_fl_fr_rl_rr"
            ] = realization_ik_valid.cpu().tolist()
            result["preflight"][
                "residual_realization_final_delta_z_m"
            ] = realization_final_delta[:, 1].cpu().tolist()
            result["preflight"][
                "residual_realization_ik_invalid_count_delta"
            ] = residual_ik_invalid_after - residual_ik_invalid_before
            result["preflight"][
                "residual_realization_front_right_requested_error_m"
            ] = front_right_requested_error_m
            result["preflight"][
                "residual_realization_rear_left_requested_error_m"
            ] = rear_left_requested_error_m
            result["preflight"][
                "residual_realization_front_right_servo_delta_max_abs_rad"
            ] = front_right_servo_delta_max_abs_rad
            result["preflight"][
                "residual_realization_rear_left_servo_delta_max_abs_rad"
            ] = rear_left_servo_delta_max_abs_rad
            result["preflight"][
                "residual_realization_inactive_coordinates_requested_exact"
            ] = inactive_requested_exact
            result["preflight"][
                "residual_final_target_realization_passed"
            ] = residual_final_target_realization_passed
            raw_env._raw_actions[0] = projection_probe
            phase_gate_scaled_max: dict[str, float] = {}
            phase_gate_expected_enabled: dict[str, bool] = {}
            phase_applied_actions: dict[int, torch.Tensor] = {}
            phase_gate_probe_phases = sorted(
                {
                    max(0, residual_phase_window[0] - 1),
                    *range(
                        residual_phase_window[0],
                        residual_phase_window[1] + 1,
                    ),
                    min(12, residual_phase_window[1] + 1),
                }
            )
            for phase in phase_gate_probe_phases:
                raw_env._fsm_phase[0] = phase
                raw_env._process_residual_actions()
                phase_gate_scaled_max[str(phase)] = float(
                    max(
                        torch.abs(
                            raw_env._scaled_wheel_center_residual_m[0]
                        ).max().item(),
                        torch.abs(
                            raw_env._scaled_wheel_speed_residual_rad_s[0]
                        ).max().item(),
                    )
                )
                phase_gate_expected_enabled[str(phase)] = bool(
                    residual_phase_window[0]
                    <= phase
                    <= residual_phase_window[1]
                )
                phase_applied_actions[phase] = (
                    raw_env._applied_actions[0].detach().clone()
                )
            result["preflight"]["residual_phase_gate_scaled_max"] = (
                phase_gate_scaled_max
            )
            result["preflight"]["residual_phase_gate_expected_enabled"] = (
                phase_gate_expected_enabled
            )
            result["preflight"]["residual_phase_gate_passed"] = bool(
                all(
                    value > 0.0 if phase_gate_expected_enabled[phase] else value == 0.0
                    for phase, value in phase_gate_scaled_max.items()
                )
            )
            result["preflight"][
                "residual_direction_projection_applied_z"
            ] = {
                str(phase): action[[1, 3, 5, 7]].cpu().tolist()
                for phase, action in phase_applied_actions.items()
            }
            result["preflight"][
                "residual_projection_applied_action"
            ] = {
                str(phase): action.cpu().tolist()
                for phase, action in phase_applied_actions.items()
            }
            expected_applied_action_tensor = torch.zeros_like(
                projection_probe
            )
            projection_sign_tensor = torch.as_tensor(
                residual_z_signs,
                dtype=projection_probe.dtype,
                device=projection_probe.device,
            )
            expected_shared_magnitude = torch.clamp_min(
                torch.mean(
                    projection_probe[[1, 3, 5, 7]]
                    * projection_sign_tensor
                ),
                0.0,
            )
            expected_climb_action_tensor = (
                expected_applied_action_tensor.clone()
            )
            expected_climb_action_tensor[[1, 3, 5, 7]] = (
                expected_shared_magnitude
                * torch.as_tensor(
                    residual_z_signs,
                    dtype=projection_probe.dtype,
                    device=projection_probe.device,
                )
                * residual_phase_gains[0]
            )
            expected_corrective_action_tensors: dict[int, torch.Tensor] = {}
            for phase_offset, phase_gain in enumerate(
                residual_phase_gains
            ):
                phase = residual_phase_window[0] + phase_offset
                expected_corrective = expected_applied_action_tensor.clone()
                expected_corrective[[1, 3, 5, 7]] = (
                    expected_shared_magnitude
                    * torch.as_tensor(
                        residual_executed_z_signs,
                        dtype=projection_probe.dtype,
                        device=projection_probe.device,
                    )
                    * torch.as_tensor(
                        residual_corrective_z_scales,
                        dtype=projection_probe.dtype,
                        device=projection_probe.device,
                    )
                    * phase_gain
                )
                if phase in residual_corrective_wheel_speed_phases:
                    expected_corrective[8:12] = (
                        torch.clamp_min(
                            expected_shared_magnitude,
                            residual_corrective_wheel_speed_minimum_shared_magnitudes[
                                residual_corrective_wheel_speed_phases.index(
                                    phase
                                )
                            ],
                        )
                        * torch.as_tensor(
                            residual_corrective_wheel_speed_signs,
                            dtype=projection_probe.dtype,
                            device=projection_probe.device,
                        )
                        * torch.as_tensor(
                            residual_corrective_wheel_speed_scales,
                            dtype=projection_probe.dtype,
                            device=projection_probe.device,
                        )
                        * phase_gain
                    )
                expected_corrective.clamp_(
                    -residual_applied_action_hard_clip,
                    residual_applied_action_hard_clip,
                )
                expected_corrective_action_tensors[phase] = (
                    expected_corrective
                )
            expected_corrective_action_tensor = (
                expected_corrective_action_tensors[
                    residual_phase_window[0]
                ]
            )
            expected_floor_action_tensors: dict[int, torch.Tensor] = {}
            phase_floor_applied_actions: dict[int, torch.Tensor] = {}
            phase_floor_requested_delta_z_m: dict[int, torch.Tensor] = {}
            phase_floor_final_delta_z_m: dict[int, torch.Tensor] = {}
            phase_floor_wheel_speed_residual_rad_s: dict[
                int, torch.Tensor
            ] = {}
            phase_floor_wheel_command_delta_rad_s: dict[
                int, torch.Tensor
            ] = {}
            phase_floor_raw_wheel_target_delta_rad_s: dict[
                int, torch.Tensor
            ] = {}
            phase_floor_ik_valid: dict[int, torch.Tensor] = {}
            phase_floor_ik_invalid_delta: dict[int, int] = {}
            raw_env._raw_actions[0] = small_positive_probe
            for phase_offset, phase_gain in enumerate(
                residual_phase_gains
            ):
                phase = residual_phase_window[0] + phase_offset
                expected_floor = expected_applied_action_tensor.clone()
                expected_floor[[1, 3, 5, 7]] = (
                    residual_corrective_minimum_shared_magnitude
                    * torch.as_tensor(
                        residual_executed_z_signs,
                        dtype=projection_probe.dtype,
                        device=projection_probe.device,
                    )
                    * torch.as_tensor(
                        residual_corrective_z_scales,
                        dtype=projection_probe.dtype,
                        device=projection_probe.device,
                    )
                    * phase_gain
                )
                if phase in residual_corrective_wheel_speed_phases:
                    expected_floor[8:12] = (
                        residual_corrective_wheel_speed_minimum_shared_magnitudes[
                            residual_corrective_wheel_speed_phases.index(phase)
                        ]
                        * torch.as_tensor(
                            residual_corrective_wheel_speed_signs,
                            dtype=projection_probe.dtype,
                            device=projection_probe.device,
                        )
                        * torch.as_tensor(
                            residual_corrective_wheel_speed_scales,
                            dtype=projection_probe.dtype,
                            device=projection_probe.device,
                        )
                        * phase_gain
                    )
                expected_floor.clamp_(
                    -residual_applied_action_hard_clip,
                    residual_applied_action_hard_clip,
                )
                expected_floor_action_tensors[phase] = expected_floor
                raw_env._residual_phase8_corrective_latched[0] = False
                raw_env._fsm_phase[0] = phase
                invalid_before = int(
                    raw_env._ik_invalid_count[0].item()
                )
                raw_env._process_residual_actions()
                invalid_after = int(
                    raw_env._ik_invalid_count[0].item()
                )
                phase_floor_applied_actions[phase] = (
                    raw_env._applied_actions[0].detach().clone()
                )
                phase_floor_requested_delta_z_m[phase] = (
                    raw_env._requested_wheel_center_target_m[0, :, 1]
                    - raw_env._reference_wheel_centers[0, :, 1]
                ).detach().clone()
                phase_floor_final_delta_z_m[phase] = (
                    raw_env._final_wheel_center_target_m[0, :, 1]
                    - raw_env._reference_wheel_centers[0, :, 1]
                ).detach().clone()
                phase_floor_wheel_speed_residual_rad_s[phase] = (
                    raw_env._scaled_wheel_speed_residual_rad_s[0]
                    .detach()
                    .clone()
                )
                phase_floor_wheel_command_delta_rad_s[phase] = (
                    raw_env._physical_forward_wheel_cmds[0]
                    - raw_env._reference_commands[0, 8:]
                ).detach().clone()
                phase_floor_raw_wheel_target_delta_rad_s[phase] = (
                    raw_env._raw_joint_wheel_velocity_targets[0]
                    - raw_env._reference_commands[0, 8:]
                    * raw_env._wheel_forward_sign[0]
                ).detach().clone()
                phase_baseline_raw = (
                    raw_env._standing_servo_pos
                    + raw_env._joint_command_sign
                    * torch.deg2rad(raw_env._reference_commands[:, :8])
                )
                _, phase_valid_all = raw_env._solve_ik(
                    raw_env._requested_wheel_center_target_m,
                    phase_baseline_raw,
                )
                phase_floor_ik_valid[phase] = (
                    phase_valid_all[0].detach().clone()
                )
                phase_floor_ik_invalid_delta[phase] = (
                    invalid_after - invalid_before
                )
            result["preflight"][
                "residual_phase_selective_floor_applied_z"
            ] = {
                str(phase): action[[1, 3, 5, 7]].cpu().tolist()
                for phase, action in phase_floor_applied_actions.items()
            }
            result["preflight"][
                "residual_phase_selective_floor_requested_delta_z_m"
            ] = {
                str(phase): delta.cpu().tolist()
                for phase, delta in phase_floor_requested_delta_z_m.items()
            }
            result["preflight"][
                "residual_phase_selective_floor_final_delta_z_m"
            ] = {
                str(phase): delta.cpu().tolist()
                for phase, delta in phase_floor_final_delta_z_m.items()
            }
            result["preflight"][
                "residual_phase_selective_floor_wheel_speed_residual_rad_s"
            ] = {
                str(phase): delta.cpu().tolist()
                for phase, delta in (
                    phase_floor_wheel_speed_residual_rad_s.items()
                )
            }
            result["preflight"][
                "residual_phase_selective_floor_wheel_command_delta_rad_s"
            ] = {
                str(phase): delta.cpu().tolist()
                for phase, delta in (
                    phase_floor_wheel_command_delta_rad_s.items()
                )
            }
            result["preflight"][
                "residual_phase_selective_floor_raw_wheel_target_delta_rad_s"
            ] = {
                str(phase): delta.cpu().tolist()
                for phase, delta in (
                    phase_floor_raw_wheel_target_delta_rad_s.items()
                )
            }
            result["preflight"][
                "residual_phase_selective_floor_ik_valid_fl_fr_rl_rr"
            ] = {
                str(phase): valid.cpu().tolist()
                for phase, valid in phase_floor_ik_valid.items()
            }
            result["preflight"][
                "residual_phase_selective_floor_ik_invalid_delta"
            ] = {
                str(phase): delta
                for phase, delta in phase_floor_ik_invalid_delta.items()
            }
            residual_phase_selective_floor_realization_passed = bool(
                all(
                    torch.equal(
                        phase_floor_applied_actions[phase],
                        expected_floor_action_tensors[phase],
                    )
                    and torch.allclose(
                        phase_floor_requested_delta_z_m[phase],
                        expected_floor_action_tensors[phase][
                            [1, 3, 5, 7]
                        ]
                        * float(
                            raw_env.cfg.residual_bounds[
                                "wheel_center_z_m"
                            ]
                        ),
                        rtol=0.0,
                        atol=1.0e-7,
                    )
                    and torch.allclose(
                        phase_floor_final_delta_z_m[phase],
                        phase_floor_requested_delta_z_m[phase],
                        rtol=0.0,
                        atol=1.0e-7,
                    )
                    and torch.allclose(
                        phase_floor_wheel_speed_residual_rad_s[phase],
                        expected_floor_action_tensors[phase][8:12]
                        * float(
                            raw_env.cfg.residual_bounds[
                                "wheel_speed_rad_s"
                            ]
                        ),
                        rtol=0.0,
                        atol=1.0e-7,
                    )
                    and torch.allclose(
                        phase_floor_wheel_command_delta_rad_s[phase],
                        phase_floor_wheel_speed_residual_rad_s[phase],
                        rtol=0.0,
                        atol=1.0e-7,
                    )
                    and torch.allclose(
                        phase_floor_raw_wheel_target_delta_rad_s[phase],
                        phase_floor_wheel_speed_residual_rad_s[phase]
                        * raw_env._wheel_forward_sign[0],
                        rtol=0.0,
                        atol=1.0e-7,
                    )
                    and torch.all(
                        phase_floor_ik_valid[phase]
                    ).item()
                    and phase_floor_ik_invalid_delta[phase] == 0
                    for phase in range(
                        residual_phase_window[0],
                        residual_phase_window[1] + 1,
                    )
                )
            )
            result["preflight"][
                "residual_phase_selective_floor_realization_passed"
            ] = residual_phase_selective_floor_realization_passed
            raw_env._raw_actions[0] = projection_probe
            result["preflight"][
                "residual_direction_projection_passed"
            ] = bool(
                all(
                    torch.equal(
                        phase_applied_actions[phase],
                        expected_corrective_action_tensors[phase],
                    )
                    for phase in range(
                        residual_phase_window[0],
                        residual_phase_window[1] + 1,
                    )
                )
            )
            enabled_phase_applied_action = phase_applied_actions[
                residual_phase_window[0]
            ].cpu().tolist()
            result["preflight"]["residual_action_mask_passed"] = bool(
                enabled_phase_applied_action is not None
                and all(
                    value == 0.0
                    for value, enabled in zip(
                        enabled_phase_applied_action,
                        residual_action_mask,
                        strict=True,
                    )
                    if not enabled
                )
            )
            result["preflight"][
                "residual_deficient_diagonal_downward_structure_passed"
            ] = bool(
                enabled_phase_applied_action is not None
                and enabled_phase_applied_action[1] == 0.0
                and enabled_phase_applied_action[3] < 0.0
                and enabled_phase_applied_action[5] < 0.0
                and enabled_phase_applied_action[7] == 0.0
                and math.isclose(
                    enabled_phase_applied_action[5],
                    (
                        residual_corrective_z_scales[2]
                        * enabled_phase_applied_action[3]
                    ),
                    rel_tol=0.0,
                    abs_tol=1.0e-7,
                )
            )
            slow_pitch_probe_root_pose = original_probe_root_pose.clone()
            slow_pitch_probe_root_pose[:, 3:7] = torch.tensor(
                [
                    math.cos(0.05),
                    0.0,
                    math.sin(0.05),
                    0.0,
                ],
                dtype=slow_pitch_probe_root_pose.dtype,
                device=device,
            )
            raw_env._robot.write_root_pose_to_sim(
                slow_pitch_probe_root_pose,
                probe_env_ids,
            )
            raw_env._robot.write_root_velocity_to_sim(
                torch.zeros((1, 6), dtype=torch.float32, device=device),
                probe_env_ids,
            )
            raw_env.scene.write_data_to_sim()
            raw_env._raw_actions[0] = projection_probe
            raw_env._fsm_phase[0] = residual_phase_window[0]
            raw_env._process_residual_actions()
            slow_pitch_phase8_action = (
                raw_env._applied_actions[0].detach().clone()
            )
            raw_env._fsm_phase[0] = residual_phase_window[0] + 1
            raw_env._process_residual_actions()
            slow_pitch_phase9_action = (
                raw_env._applied_actions[0].detach().clone()
            )
            result["preflight"][
                "residual_slow_pitch_phase8_climb_applied_z"
            ] = slow_pitch_phase8_action[[1, 3, 5, 7]].cpu().tolist()
            result["preflight"][
                "residual_slow_pitch_phase9_exact_zero"
            ] = bool(torch.all(slow_pitch_phase9_action == 0.0).item())
            result["preflight"][
                "residual_slow_pitch_climb_preserved"
            ] = bool(
                torch.equal(
                    slow_pitch_phase8_action,
                    expected_climb_action_tensor,
                )
                and torch.all(slow_pitch_phase9_action == 0.0).item()
            )
            early_hazard_probe_root_pose = original_probe_root_pose.clone()
            early_hazard_probe_root_pose[:, 3:7] = torch.tensor(
                [
                    math.cos(0.035),
                    math.sin(0.035),
                    0.0,
                    0.0,
                ],
                dtype=early_hazard_probe_root_pose.dtype,
                device=device,
            )
            early_hazard_probe_velocity = torch.tensor(
                [[0.0, 0.0, 0.0, 0.0, 0.4, 0.0]],
                dtype=torch.float32,
                device=device,
            )
            raw_env._robot.write_root_pose_to_sim(
                early_hazard_probe_root_pose,
                probe_env_ids,
            )
            raw_env._robot.write_root_velocity_to_sim(
                early_hazard_probe_velocity,
                probe_env_ids,
            )
            raw_env.scene.write_data_to_sim()
            raw_env._raw_actions[0] = projection_probe
            raw_env._fsm_phase[0] = residual_phase_window[0]
            raw_env._process_residual_actions()
            early_phase8_action = (
                raw_env._applied_actions[0].detach().clone()
            )
            early_roll_rad = float(
                raw_env._roll_pitch_yaw()[0][0].item()
            )
            early_pitch_rate_rad_s = float(
                raw_env._robot.data.root_ang_vel_b[0, 1].item()
            )
            early_hazard_probe_velocity[:, 4] = 0.0
            raw_env._robot.write_root_velocity_to_sim(
                early_hazard_probe_velocity,
                probe_env_ids,
            )
            raw_env.scene.write_data_to_sim()
            raw_env._raw_actions[0] = small_positive_probe
            raw_env._fsm_phase[0] = residual_phase_window[0]
            raw_env._process_residual_actions()
            latched_phase8_floor_action = (
                raw_env._applied_actions[0].detach().clone()
            )
            expected_floor_action_tensor = torch.zeros_like(
                projection_probe
            )
            expected_floor_action_tensor[[1, 3, 5, 7]] = (
                residual_corrective_minimum_shared_magnitude
                * residual_phase_gains[0]
                * torch.as_tensor(
                    residual_executed_z_signs,
                    dtype=projection_probe.dtype,
                    device=projection_probe.device,
                )
                * torch.as_tensor(
                    residual_corrective_z_scales,
                    dtype=projection_probe.dtype,
                    device=projection_probe.device,
                )
            )
            if residual_phase_window[0] in (
                residual_corrective_wheel_speed_phases
            ):
                expected_floor_action_tensor[8:12] = (
                    residual_corrective_wheel_speed_minimum_shared_magnitudes[
                        residual_corrective_wheel_speed_phases.index(
                            residual_phase_window[0]
                        )
                    ]
                    * residual_phase_gains[0]
                    * torch.as_tensor(
                        residual_corrective_wheel_speed_signs,
                        dtype=projection_probe.dtype,
                        device=projection_probe.device,
                    )
                    * torch.as_tensor(
                        residual_corrective_wheel_speed_scales,
                        dtype=projection_probe.dtype,
                        device=projection_probe.device,
                    )
                )
            expected_floor_action_tensor.clamp_(
                -residual_applied_action_hard_clip,
                residual_applied_action_hard_clip,
            )
            raw_env._fsm_phase[0] = residual_phase_window[0] + 1
            raw_env._process_residual_actions()
            early_phase9_action = (
                raw_env._applied_actions[0].detach().clone()
            )
            result["preflight"]["residual_early_hazard_roll_rad"] = (
                early_roll_rad
            )
            result["preflight"][
                "residual_early_hazard_pitch_rate_rad_s"
            ] = early_pitch_rate_rad_s
            result["preflight"][
                "residual_early_hazard_phase8_applied_z"
            ] = early_phase8_action[[1, 3, 5, 7]].cpu().tolist()
            result["preflight"][
                "residual_early_hazard_phase9_applied_z"
            ] = early_phase9_action[[1, 3, 5, 7]].cpu().tolist()
            result["preflight"][
                "residual_latched_phase8_floor_applied_z"
            ] = latched_phase8_floor_action[
                [1, 3, 5, 7]
            ].cpu().tolist()
            result["preflight"][
                "residual_early_hazard_direction_passed"
            ] = bool(
                early_roll_rad
                >= residual_state_gate_early_roll_rad
                and early_roll_rad
                < residual_state_gate_min_roll_rad
                and early_pitch_rate_rad_s
                >= residual_state_gate_early_pitch_rate_rad_s
                and torch.equal(
                    early_phase8_action,
                    expected_corrective_action_tensor,
                )
                and torch.equal(
                    latched_phase8_floor_action,
                    expected_floor_action_tensor,
                )
                and torch.all(early_phase9_action == 0.0).item()
            )
            raw_env._raw_actions[0] = -projection_probe
            raw_env._fsm_phase[0] = residual_phase_window[0]
            raw_env._process_residual_actions()
            result["preflight"][
                "residual_zero_preserving_gate_passed"
            ] = bool(
                torch.all(raw_env._applied_actions[0] == 0.0).item()
                and torch.all(
                    raw_env._scaled_wheel_center_residual_m[0] == 0.0
                ).item()
                and torch.all(
                    raw_env._scaled_wheel_speed_residual_rad_s[0] == 0.0
                ).item()
            )
            raw_env._robot.write_root_pose_to_sim(
                original_probe_root_pose,
                probe_env_ids,
            )
            raw_env._robot.write_root_velocity_to_sim(
                original_probe_root_velocity,
                probe_env_ids,
            )
            raw_env.scene.write_data_to_sim()
            if not result["preflight"]["residual_phase_gate_passed"]:
                raise RuntimeError(
                    "Residual physical-execution phase gate failed runtime audit"
                )
            if not result["preflight"][
                "residual_direction_projection_passed"
            ]:
                raise RuntimeError(
                    "Residual physical direction projection failed runtime audit"
                )
            if not result["preflight"][
                "residual_early_hazard_direction_passed"
            ]:
                raise RuntimeError(
                    "Residual early rapid-rise direction failed runtime audit"
                )
            if not result["preflight"][
                "residual_slow_pitch_climb_preserved"
            ]:
                raise RuntimeError(
                    "Residual phase-8 slow-pitch climb preservation failed "
                    "runtime audit"
                )
            if not result["preflight"]["residual_action_mask_passed"]:
                raise RuntimeError(
                    "Residual physical action mask failed runtime audit"
                )
            if not result["preflight"][
                "residual_deficient_diagonal_downward_structure_passed"
            ]:
                raise RuntimeError(
                    "Residual deficient-diagonal downward corrective structure failed "
                    "runtime audit"
                )
            if not result["preflight"][
                "residual_final_target_realization_passed"
            ]:
                raise RuntimeError(
                    "Residual front-right/rear-left final-target realization failed "
                    "runtime audit"
                )
            if not result["preflight"][
                "residual_phase_selective_floor_realization_passed"
            ]:
                raise RuntimeError(
                    "Residual phase-selective floor realization failed "
                    "runtime audit"
                )
            if not result["preflight"][
                "residual_zero_preserving_gate_passed"
            ]:
                raise RuntimeError(
                    "Residual zero-preserving physical gate failed runtime audit"
                )
            partial_reset_ids = torch.tensor(
                [0, env.num_envs - 1],
                dtype=torch.long,
                device=device,
            ).unique()
            raw_env._reset_idx(partial_reset_ids)
            if not torch.isfinite(
                raw_env._robot.data.root_pose_w[partial_reset_ids]
            ).all():
                raise RuntimeError("Non-finite root pose after partial-reset preflight")
            result["preflight"]["partial_reset_env_count"] = int(
                partial_reset_ids.numel()
            )
            result["preflight"]["partial_reset_finite"] = True
            forced_fall_ids = torch.tensor(
                [0],
                dtype=torch.long,
                device=device,
            )
            forced_fall_pose = raw_env._robot.data.root_pose_w[
                forced_fall_ids
            ].clone()
            forced_fall_pose[:, 2] += 0.25
            forced_fall_pose[:, 0] = (
                raw_env.scene.env_origins[forced_fall_ids, 0]
                + float(raw_env.cfg.obstacle_x)
            )
            forced_fall_pose[:, 3:7] = torch.tensor(
                [0.7648422, 0.6442177, 0.0, 0.0],
                dtype=forced_fall_pose.dtype,
                device=device,
            )
            raw_env._robot.write_root_pose_to_sim(
                forced_fall_pose,
                forced_fall_ids,
            )
            raw_env._robot.write_root_velocity_to_sim(
                torch.zeros((1, 6), dtype=torch.float32, device=device),
                forced_fall_ids,
            )
            raw_env.scene.write_data_to_sim()
            forced_action = torch.zeros(
                (env.num_envs, ACTION_DIM),
                dtype=torch.float32,
                device=device,
            )
            (
                _,
                forced_reward,
                forced_terminated,
                _,
                _,
            ) = env.step(forced_action)
            forced_fall_weighted = float(
                raw_env._last_weighted_reward_terms["fall"][0].item()
            )
            forced_fall_reward = float(forced_reward[0].reshape(-1)[0].item())
            forced_fall_terminated = bool(
                forced_terminated[0].reshape(-1)[0].item()
            )
            forced_fall_reward_finite = bool(
                torch.isfinite(forced_reward).all().item()
            )
            result["preflight"]["forced_fall_terminated"] = (
                forced_fall_terminated
            )
            result["preflight"]["forced_fall_raw_term"] = float(
                raw_env._last_raw_reward_terms["fall"][0].item()
            )
            result["preflight"]["forced_fall_weighted_term"] = (
                forced_fall_weighted
            )
            result["preflight"]["forced_fall_total_reward"] = (
                forced_fall_reward
            )
            result["preflight"]["forced_fall_reward_finite"] = (
                forced_fall_reward_finite
            )
            result["preflight"]["forced_fall_terminal_snapshot"] = bool(
                raw_env._last_done_fall[0].item()
            )
            if (
                not forced_fall_terminated
                or forced_fall_weighted != -200.0
                or not forced_fall_reward_finite
            ):
                raise RuntimeError(
                    "Forced-fall terminal reward preflight did not produce "
                    "a finite termination with the exact -200 fall term"
                )
            (
                _,
                post_reset_reward,
                post_reset_terminated,
                post_reset_truncated,
                _,
            ) = env.step(forced_action)
            post_reset_distance = float(
                raw_env._distance_to_obstacle_front()[0].item()
            )
            post_reset_expected_distance = float(
                raw_env._training_initial_distance_m[0].item()
            )
            post_reset_distance_error = abs(
                post_reset_distance - post_reset_expected_distance
            )
            post_reset_success = bool(raw_env._success_buf[0].item())
            post_reset_done = bool(
                (
                    post_reset_terminated[0].reshape(-1)[0]
                    | post_reset_truncated[0].reshape(-1)[0]
                ).item()
            )
            result["preflight"]["post_terminal_reset_distance_m"] = (
                post_reset_distance
            )
            result["preflight"]["post_terminal_reset_expected_distance_m"] = (
                post_reset_expected_distance
            )
            result["preflight"]["post_terminal_reset_distance_error_m"] = (
                post_reset_distance_error
            )
            result["preflight"]["post_terminal_reset_success"] = (
                post_reset_success
            )
            result["preflight"]["post_terminal_reset_done"] = post_reset_done
            result["preflight"]["post_terminal_reset_reward_finite"] = bool(
                torch.isfinite(post_reset_reward).all().item()
            )
            if (
                post_reset_distance_error > 0.01
                or post_reset_success
                or post_reset_done
                or not torch.isfinite(post_reset_reward).all()
            ):
                raise RuntimeError(
                    "Post-terminal randomized reset did not recover the "
                    "registered pre-obstacle initial distribution"
                )
            result["status"] = "SMOKE_PASS"
        else:
            trainer.train()
            if not finite_models(models):
                raise RuntimeError("Model contains non-finite parameters after training")
            result["training_budget"]["local_timesteps_completed"] = (
                args.iterations * args.rollouts
            )
            result["training_budget"]["cumulative_timesteps_completed"] = (
                args.resume_offset_timesteps + args.iterations * args.rollouts
            )
            result["training_budget"]["local_transitions_completed"] = (
                args.iterations * args.rollouts * args.num_envs
            )
            result["training_budget"]["cumulative_transitions_completed"] = (
                (args.resume_offset_timesteps + args.iterations * args.rollouts)
                * args.num_envs
            )
            checkpoint_dir = run_dir / "checkpoints"
            checkpoint_dir.mkdir(exist_ok=True)
            final_checkpoint = checkpoint_dir / "final_agent.pt"
            agent.save(str(final_checkpoint))
            result["final_checkpoint"] = {
                "path": str(final_checkpoint),
                "sha256": sha256_file(final_checkpoint),
            }
            result["status"] = "COMPLETED"
        result["finished_unix"] = time.time()
    except Exception as exc:
        result["status"] = "FAILED"
        result["failures"].append(f"{type(exc).__name__}: {exc}")
        result["traceback"] = __import__("traceback").format_exc()
        result["finished_unix"] = time.time()
    finally:
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        if env is not None:
            env.close()
        elif raw_env is not None:
            raw_env.close()
        app.close()
    print(json.dumps({"result": str(result_path), "status": result["status"], "failures": result["failures"]}, indent=2))
    return 0 if result["status"] in {"SMOKE_PASS", "COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
