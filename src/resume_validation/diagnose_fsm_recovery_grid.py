"""Vectorized development-only grid search for phase-9 support geometry."""

from __future__ import annotations

import argparse
import json
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
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--output_dir", type=Path, required=True)
parser.add_argument("--max_episode_s", type=float, default=150.0)
parser.add_argument("--height_mm", type=int, choices=(50, 75, 100), default=100)
parser.add_argument(
    "--grid_kind",
    choices=(
        "front_right",
        "common_right_z",
        "front_support_fr",
        "front_support_unloaded_diagonal_z",
        "rear_recovery_blend",
        "rear_right_support_extension",
        "front_right_rear_left_support_extension",
        "front_right_rear_left_support_extension_wide",
        "post_transfer_offset_activation_start",
        "rear_left_extension_relief",
        "rear_left_extension_boundary",
        "rear_left_activation_start",
        "rear_right_extension_boundary",
        "front_right_extension_balance",
        "front_right_extension_upper_boundary",
        "front_right_extension_reach_boundary",
        "front_right_extension_diagnostic_limit",
        "post_transfer_geometry_height_scale_75",
        "front_right_extension_75_with_half_rear_support",
        "front_right_early_activation_75",
        "rear_transfer_front_wheel_speed_75",
        "front_right_extension_zero_transfer_front_speed_75",
        "post_transfer_forward_speed_zero_transfer_front_speed_75",
        "support_activation_zero_post_speed_75",
        "support_unload_zero_post_speed_75",
        "support_unload_rate_zero_post_speed_75",
        "post_transfer_speed_with_support_unload_75",
        "selected_combined_repeat_75",
    ),
    default="front_right",
)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import numpy as np
import torch
from isaaclab.utils.math import quat_apply, quat_apply_inverse, quat_from_euler_xyz
from isaaclab_rl.skrl import SkrlVecEnvWrapper

from resume_validation.config_io import load_config
from resume_validation.fsm_recovery_grid import recovery_grid_candidates
from resume_validation.residual_rl_env import WLRResidualRLEnv, make_residual_env_cfg
from resume_validation.source_audit import sha256_file


def _configure_initial_state(raw_env: WLRResidualRLEnv, scenario: dict, count: int) -> None:
    noise = np.zeros((count, 4), dtype=np.float32)
    for index in range(count):
        generator = random.Random(int(scenario["noise_seed"]))
        std = float(scenario["sensor_noise_std"])
        draws = [generator.gauss(0.0, std) for _ in range(4)]
        noise[index] = [draws[0] / 0.10, draws[1], draws[2] / 0.50, draws[3] / 0.20]
    raw_env.configure_scenarios(
        actuator_delay_steps=[int(scenario["actuator_delay_steps"])] * count,
        obstacle_observation_noise=noise,
        friction=[float(scenario["friction"])] * count,
    )
    current_distance = raw_env._distance_to_obstacle_front()
    desired_distance = torch.full(
        (count,), float(scenario["initial_distance_m"]), device=raw_env.device
    )
    pitch = torch.full(
        (count,), float(scenario["initial_pitch_rad"]), device=raw_env.device
    )
    root_pose = raw_env._robot.data.root_pose_w.clone()
    base_body_id = raw_env._robot.body_names.index("base_link")
    base_pos = raw_env._robot.data.body_pos_w[:, base_body_id]
    base_quat = raw_env._robot.data.body_quat_w[:, base_body_id]
    wheel_pos = raw_env._robot.data.body_pos_w[:, raw_env._wheel_body_ids]
    wheel_relative_b = quat_apply_inverse(
        base_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
        (wheel_pos - base_pos.unsqueeze(1)).reshape(-1, 3),
    ).reshape(count, 4, 3)
    desired_quat = quat_from_euler_xyz(
        torch.zeros_like(pitch), pitch, torch.zeros_like(pitch)
    )
    desired_wheel_relative = quat_apply(
        desired_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
        wheel_relative_b.reshape(-1, 3),
    ).reshape(count, 4, 3)
    root_pose[:, 0] += current_distance - desired_distance
    root_pose[:, 2] = (
        raw_env._estimated_wheel_radius
        - desired_wheel_relative[:, :, 2].amin(dim=1)
        + 0.002
    )
    root_pose[:, 3:7] = desired_quat
    raw_env._robot.write_root_pose_to_sim(root_pose)
    raw_env._robot.write_root_velocity_to_sim(
        torch.zeros((count, 6), device=raw_env.device)
    )
    raw_env.scene.write_data_to_sim()


def _settle(raw_env: WLRResidualRLEnv, physics_steps: int = 120) -> None:
    servo = raw_env._standing_servo_pos.expand(raw_env.num_envs, -1)
    wheels = torch.zeros((raw_env.num_envs, 4), device=raw_env.device)
    for _ in range(physics_steps):
        raw_env._robot.set_joint_position_target(servo, joint_ids=raw_env._servo_joint_ids)
        raw_env._robot.set_joint_velocity_target(wheels, joint_ids=raw_env._wheel_joint_ids)
        raw_env.scene.write_data_to_sim()
        raw_env.sim.step(render=False)
        raw_env.scene.update(dt=raw_env.physics_dt)


def _park_inactive(raw_env: WLRResidualRLEnv, inactive_ids: torch.Tensor) -> None:
    """Keep completed candidates out of contact without touching active ones."""

    if inactive_ids.numel() == 0:
        return
    origins = raw_env.scene.env_origins[inactive_ids]
    root_pose = raw_env._robot.data.root_pose_w[inactive_ids].clone()
    root_pose[:, 0] = origins[:, 0] - 5.0
    root_pose[:, 1] = origins[:, 1]
    root_pose[:, 2] = origins[:, 2] + 1.0
    root_pose[:, 3:7] = torch.tensor(
        [1.0, 0.0, 0.0, 0.0],
        dtype=root_pose.dtype,
        device=root_pose.device,
    )
    raw_env._robot.write_root_pose_to_sim(root_pose, inactive_ids)
    raw_env._robot.write_root_velocity_to_sim(
        torch.zeros((inactive_ids.numel(), 6), device=raw_env.device),
        inactive_ids,
    )


def main() -> int:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    result_path = output_dir / "result.json"
    result: dict = {
        "schema": "resume_validation.fsm_recovery_grid.v1",
        "started_unix": time.time(),
        "passed_execution": False,
        "failures": [],
    }
    raw_env = None
    env = None
    try:
        manifest = args.manifest.resolve()
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        scenario = next(
            row
            for row in payload["scenarios"]
            if int(round(float(row["obstacle_height_m"]) * 1000))
            == args.height_mm
        )
        candidates = recovery_grid_candidates(args.grid_kind)
        count = len(candidates)
        fsm_cfg = load_config(VALIDATION_ROOT / "configs" / "fsm.yaml")
        cfg = make_residual_env_cfg(
            num_envs=count,
            obstacle_height=args.height_mm / 1000.0,
            episode_length_s=args.max_episode_s,
            max_idle_gap_s=float(fsm_cfg["playback_profile"]["max_idle_gap_s"]),
            preserve_wheel_distance=bool(
                fsm_cfg["playback_profile"]["preserve_wheel_distance"]
            ),
            fsm_contact_debounce_steps=int(fsm_cfg["contact_debounce_steps"]),
            phase_timeout_scale=float(fsm_cfg["phase_timeout_scale"]),
        )
        cfg.seed = int(payload.get("metadata", {}).get("seed", 0))
        cfg.fsm_support_unload_maximum_m = 0.0
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        raw_env = WLRResidualRLEnv(cfg)
        env = SkrlVecEnvWrapper(raw_env, ml_framework="torch")
        env.reset()
        _settle(raw_env)
        _configure_initial_state(raw_env, scenario, count)
        offsets = torch.zeros((count, 4, 2), device=raw_env.device)
        command_offsets = torch.zeros((count, 8), device=raw_env.device)
        for index, candidate in enumerate(candidates):
            offsets[index] = torch.tensor(
                candidate["wheel_center_offsets_m"],
                device=raw_env.device,
            )
            command_offsets[index] = torch.tensor(
                candidate.get("front_support_command_offsets_deg", [0.0] * 8),
                device=raw_env.device,
            )
        raw_env.configure_diagnostic_wheel_center_offsets(offsets)
        raw_env.configure_diagnostic_front_support_command_offsets(
            command_offsets
        )
        if args.grid_kind == "rear_recovery_blend":
            raw_env.configure_diagnostic_rear_recovery_max_blend(
                [
                    float(candidate["rear_recovery_max_blend"])
                    for candidate in candidates
                ]
            )
        if all(
            "post_transfer_leg_offset_start_progress" in candidate
            for candidate in candidates
        ):
            raw_env.configure_diagnostic_post_transfer_leg_offset_start_progress(
                [
                    candidate["post_transfer_leg_offset_start_progress"]
                    for candidate in candidates
                ]
            )
        elif all(
            "post_transfer_offset_start_progress" in candidate
            for candidate in candidates
        ):
            raw_env.configure_diagnostic_post_transfer_offset_start_progress(
                [
                    float(candidate["post_transfer_offset_start_progress"])
                    for candidate in candidates
                ]
            )
        if all(
            "post_transfer_leg_offset_start_phase" in candidate
            for candidate in candidates
        ):
            raw_env.configure_diagnostic_post_transfer_leg_offset_start_phase(
                [
                    candidate["post_transfer_leg_offset_start_phase"]
                    for candidate in candidates
                ]
            )
        if all(
            "diagnostic_rear_transfer_wheel_speed_rad_s" in candidate
            for candidate in candidates
        ):
            raw_env.configure_diagnostic_rear_transfer_wheel_speed(
                [
                    candidate["diagnostic_rear_transfer_wheel_speed_rad_s"]
                    for candidate in candidates
                ]
            )
        if all(
            "diagnostic_post_transfer_forward_speed_rad_s" in candidate
            for candidate in candidates
        ):
            raw_env.configure_diagnostic_post_transfer_forward_speed(
                [
                    float(
                        candidate[
                            "diagnostic_post_transfer_forward_speed_rad_s"
                        ]
                    )
                    for candidate in candidates
                ]
            )
        if all(
            "diagnostic_support_unload_maximum_m" in candidate
            and "diagnostic_support_unload_rate_m_s" in candidate
            for candidate in candidates
        ):
            raw_env.configure_diagnostic_support_unload(
                [
                    float(candidate["diagnostic_support_unload_maximum_m"])
                    for candidate in candidates
                ],
                [
                    float(candidate["diagnostic_support_unload_rate_m_s"])
                    for candidate in candidates
                ],
            )

        active = torch.ones(count, dtype=torch.bool, device=raw_env.device)
        succeeded = torch.zeros_like(active)
        post_transfer_top_maximum_minimum_upward_force_n = torch.full(
            (count,),
            float("-inf"),
            dtype=torch.float32,
            device=raw_env.device,
        )
        post_transfer_top_eligible_sample_count = torch.zeros(
            count,
            dtype=torch.long,
            device=raw_env.device,
        )
        post_transfer_top_maximum_wheel_upward_force_n = torch.full(
            (count, 4),
            float("-inf"),
            dtype=torch.float32,
            device=raw_env.device,
        )
        best_minimum_snapshot_upward_force_n = torch.full(
            (count, 4),
            float("nan"),
            dtype=torch.float32,
            device=raw_env.device,
        )
        best_minimum_snapshot_time_s = torch.full(
            (count,),
            float("nan"),
            dtype=torch.float32,
            device=raw_env.device,
        )
        best_minimum_snapshot_roll_rad = torch.full_like(
            best_minimum_snapshot_time_s,
            float("nan"),
        )
        best_minimum_snapshot_pitch_rad = torch.full_like(
            best_minimum_snapshot_time_s,
            float("nan"),
        )
        success_condition_dwell_steps = torch.zeros(
            count,
            dtype=torch.long,
            device=raw_env.device,
        )
        maximum_success_condition_dwell_steps = torch.zeros_like(
            success_condition_dwell_steps
        )
        failure_reason = [""] * count
        terminal_snapshot: list[dict | None] = [None] * count
        max_steps = int(np.ceil(args.max_episode_s / float(raw_env.step_dt)))
        status_path = output_dir / "status.json"
        for step in range(max_steps):
            actions = torch.zeros((count, 12), device=raw_env.device)
            _, _, terminated, truncated, _ = env.step(actions)
            truncated_flat = truncated.reshape(-1)
            done = active & (terminated.reshape(-1) | truncated_flat)
            for index in done.nonzero(as_tuple=False).flatten().cpu().tolist():
                if bool(raw_env._last_done_success[index].item()):
                    succeeded[index] = True
                    failure_reason[index] = ""
                elif bool(raw_env._last_done_collision[index].item()):
                    failure_reason[index] = "BODY_OR_LINK_COLLISION"
                elif bool(raw_env._last_done_joint_limit[index].item()):
                    failure_reason[index] = "JOINT_LIMIT"
                elif bool(raw_env._last_done_phase_timeout[index].item()):
                    failure_reason[index] = "FSM_PHASE_TIMEOUT"
                elif bool(raw_env._last_done_fall[index].item()):
                    failure_reason[index] = "FALL"
                elif bool(truncated_flat[index].item()):
                    failure_reason[index] = "TIMEOUT"
                else:
                    failure_reason[index] = "OTHER"
                nonwheel = {
                    name: float(force)
                    for name, force in zip(
                        raw_env._contact_nonwheel_names,
                        raw_env._last_done_nonwheel_contact_force_n[index]
                        .detach()
                        .cpu()
                        .tolist(),
                        strict=True,
                    )
                    if force > 0.0
                }
                terminal_snapshot[index] = {
                    "terminal_control_step": step,
                    "terminal_sim_time_s": step * float(raw_env.step_dt),
                    "terminal_phase": int(
                        raw_env._last_done_fsm_phase[index].item()
                    ),
                    "terminal_root_x_m": float(
                        raw_env._last_done_root_x[index].item()
                    ),
                    "terminal_margin_m": (
                        float(raw_env._last_done_margin[index].item())
                        if bool(raw_env._last_done_margin_valid[index].item())
                        else None
                    ),
                    "terminal_pitch_rad": float(
                        raw_env._last_done_pitch[index].item()
                    ),
                    "terminal_roll_rad": float(
                        raw_env._last_done_roll[index].item()
                    ),
                    "terminal_wheel_contact_force_n": (
                        raw_env._last_done_wheel_contact_force_n[index]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_wheel_contact_upward_force_n": (
                        raw_env._last_done_wheel_contact_upward_force_n[index]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_wheel_position_xz_m": (
                        raw_env._last_done_wheel_position_xz[index]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_reference_commands": (
                        raw_env._last_done_reference_commands[index]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_fsm_baseline_ik_invalid_count": int(
                        raw_env._last_done_fsm_baseline_ik_invalid_count[
                            index
                        ].item()
                    ),
                    "terminal_fsm_baseline_ik_invalid_count_per_leg": (
                        raw_env._last_done_fsm_baseline_ik_invalid_count_per_leg[
                            index
                        ]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_fsm_diagnostic_front_support_clamp_count": int(
                        raw_env._last_done_fsm_diagnostic_front_support_clamp_count[
                            index
                        ].item()
                    ),
                    "terminal_fsm_support_unload_trim_m": (
                        raw_env._last_done_fsm_support_unload_trim_m[index]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_nonwheel_contact_force_n": nonwheel,
                }
            still_active = active & (~done)
            current_upward = raw_env._wheel_contact_forces()[0][:, :, 2]
            current_minimum = torch.min(current_upward, dim=1).values
            roll, pitch, _ = raw_env._roll_pitch_yaw()
            eligible_without_force = (
                still_active
                & (raw_env._fsm_phase >= 9)
                & (raw_env._fsm_phase <= 10)
                & raw_env._all_wheels_on_top
                & (torch.abs(roll) <= float(raw_env.cfg.max_stable_tilt_rad))
                & (torch.abs(pitch) <= float(raw_env.cfg.max_stable_tilt_rad))
                & (
                    torch.linalg.vector_norm(
                        raw_env._robot.data.root_ang_vel_b,
                        dim=1,
                    )
                    <= float(raw_env.cfg.max_stable_angular_velocity_rad_s)
                )
            )
            improved_minimum = (
                eligible_without_force
                & (
                    current_minimum
                    > post_transfer_top_maximum_minimum_upward_force_n
                )
            )
            post_transfer_top_eligible_sample_count += (
                eligible_without_force.to(torch.long)
            )
            post_transfer_top_maximum_wheel_upward_force_n = torch.where(
                eligible_without_force.unsqueeze(1),
                torch.maximum(
                    post_transfer_top_maximum_wheel_upward_force_n,
                    current_upward,
                ),
                post_transfer_top_maximum_wheel_upward_force_n,
            )
            best_minimum_snapshot_upward_force_n = torch.where(
                improved_minimum.unsqueeze(1),
                current_upward,
                best_minimum_snapshot_upward_force_n,
            )
            best_minimum_snapshot_time_s = torch.where(
                improved_minimum,
                torch.full_like(
                    best_minimum_snapshot_time_s,
                    step * float(raw_env.step_dt),
                ),
                best_minimum_snapshot_time_s,
            )
            best_minimum_snapshot_roll_rad = torch.where(
                improved_minimum,
                roll,
                best_minimum_snapshot_roll_rad,
            )
            best_minimum_snapshot_pitch_rad = torch.where(
                improved_minimum,
                pitch,
                best_minimum_snapshot_pitch_rad,
            )
            post_transfer_top_maximum_minimum_upward_force_n = torch.where(
                eligible_without_force,
                torch.maximum(
                    post_transfer_top_maximum_minimum_upward_force_n,
                    current_minimum,
                ),
                post_transfer_top_maximum_minimum_upward_force_n,
            )
            all_upward = (
                torch.all(
                    current_upward
                    >= float(raw_env.cfg.contact_force_threshold_n),
                    dim=1,
                )
                & eligible_without_force
            )
            success_condition_dwell_steps = torch.where(
                all_upward,
                success_condition_dwell_steps + 1,
                torch.zeros_like(success_condition_dwell_steps),
            )
            maximum_success_condition_dwell_steps = torch.maximum(
                maximum_success_condition_dwell_steps,
                success_condition_dwell_steps,
            )
            active &= ~done
            _park_inactive(
                raw_env,
                (~active).nonzero(as_tuple=False).flatten(),
            )
            if step % 300 == 0 or torch.any(done):
                status_path.write_text(
                    json.dumps(
                        {
                            "control_step": step,
                            "sim_time_s": step * float(raw_env.step_dt),
                            "active_count": int(active.sum().item()),
                            "active_candidate_ids": active.nonzero(
                                as_tuple=False
                            )
                            .flatten()
                            .cpu()
                            .tolist(),
                            "success_count": int(succeeded.sum().item()),
                            "completed_failure_counts": {
                                reason: sum(
                                    value == reason for value in failure_reason
                                )
                                for reason in sorted(
                                    {
                                        value
                                        for value in failure_reason
                                        if value
                                    }
                                )
                            },
                            "phase_counts": (
                                torch.bincount(raw_env._fsm_phase[active], minlength=13)
                                .cpu()
                                .tolist()
                                if torch.any(active)
                                else [0] * 13
                            ),
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            if not torch.any(active):
                break
        for index in active.nonzero(as_tuple=False).flatten().cpu().tolist():
            failure_reason[index] = "TIMEOUT"

        rows = []
        for index, candidate in enumerate(candidates):
            snapshot = terminal_snapshot[index]
            if snapshot is None:
                snapshot = {
                    "terminal_control_step": max_steps,
                    "terminal_sim_time_s": args.max_episode_s,
                    "terminal_phase": int(raw_env._fsm_phase[index].item()),
                    "terminal_root_x_m": float(
                        raw_env._root_pos_local()[index, 0].item()
                    ),
                    "terminal_margin_m": None,
                    "terminal_pitch_rad": None,
                    "terminal_roll_rad": None,
                    "terminal_wheel_contact_force_n": [],
                    "terminal_wheel_contact_upward_force_n": (
                        raw_env._wheel_contact_forces()[0][index, :, 2]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    "terminal_wheel_position_xz_m": [],
                    "terminal_reference_commands": [],
                    "terminal_fsm_baseline_ik_invalid_count": int(
                        raw_env._fsm_baseline_ik_invalid_count[index].item()
                    ),
                    "terminal_fsm_diagnostic_front_support_clamp_count": int(
                        raw_env._fsm_diagnostic_front_support_clamp_count[
                            index
                        ].item()
                    ),
                    "terminal_nonwheel_contact_force_n": {},
                }
            rows.append(
                {
                    "candidate_id": index,
                    "parameters": candidate["parameters"],
                    "wheel_center_offsets_m": candidate[
                        "wheel_center_offsets_m"
                    ],
                    "front_support_command_offsets_deg": candidate.get(
                        "front_support_command_offsets_deg",
                        [0.0] * 8,
                    ),
                    "success": bool(succeeded[index].item()),
                    "failure_reason": failure_reason[index],
                    "diagnostic_post_transfer_top_maximum_minimum_wheel_upward_force_n": (
                        float(
                            post_transfer_top_maximum_minimum_upward_force_n[
                                index
                            ].item()
                        )
                        if bool(
                            torch.isfinite(
                                post_transfer_top_maximum_minimum_upward_force_n[
                                    index
                                ]
                            ).item()
                        )
                        else None
                    ),
                    "diagnostic_post_transfer_top_eligible_sample_count": int(
                        post_transfer_top_eligible_sample_count[index].item()
                    ),
                    "diagnostic_post_transfer_top_maximum_wheel_upward_force_n": (
                        post_transfer_top_maximum_wheel_upward_force_n[index]
                        .detach()
                        .cpu()
                        .tolist()
                        if int(
                            post_transfer_top_eligible_sample_count[index].item()
                        )
                        > 0
                        else None
                    ),
                    "diagnostic_best_minimum_upward_force_snapshot": (
                        {
                            "time_s": float(
                                best_minimum_snapshot_time_s[index].item()
                            ),
                            "wheel_upward_force_n": (
                                best_minimum_snapshot_upward_force_n[index]
                                .detach()
                                .cpu()
                                .tolist()
                            ),
                            "roll_rad": float(
                                best_minimum_snapshot_roll_rad[index].item()
                            ),
                            "pitch_rad": float(
                                best_minimum_snapshot_pitch_rad[index].item()
                            ),
                        }
                        if int(
                            post_transfer_top_eligible_sample_count[index].item()
                        )
                        > 0
                        else None
                    ),
                    "diagnostic_longest_success_condition_dwell_s": (
                        int(
                            maximum_success_condition_dwell_steps[index].item()
                        )
                        * float(raw_env.step_dt)
                    ),
                    **snapshot,
                }
            )
        result.update(
            {
                "passed_execution": True,
                "manifest": str(manifest),
                "manifest_sha256": sha256_file(manifest),
                "scenario_id": scenario["scenario_id"],
                "height_mm": args.height_mm,
                "grid_kind": args.grid_kind,
                "candidate_count": count,
                "success_count": sum(row["success"] for row in rows),
                "candidates": rows,
            }
        )
    except Exception as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
        result["traceback"] = traceback.format_exc()
    finally:
        result["finished_unix"] = time.time()
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        if env is not None:
            env.close()
        elif raw_env is not None:
            raw_env.close()
        app.close()
    return 0 if result["passed_execution"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
