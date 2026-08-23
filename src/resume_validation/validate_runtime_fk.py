"""Compare analytic planar FK with Isaac body poses for 1,024 safe samples."""

from __future__ import annotations

import argparse
import json
import math
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
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--num_envs", type=int, default=128)
parser.add_argument("--batches", type=int, default=8)
parser.add_argument("--tolerance_m", type=float, default=5.0e-4)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import torch
from isaaclab.utils.math import quat_apply_inverse, quat_from_euler_xyz

from resume_validation.actuator_mapping import JOINT_COMMAND_SIGN, SERVO_JOINT_NAMES
from resume_validation.residual_rl_env import (
    RECORDED_SAFE_COMMAND_DEG,
    WLRResidualRLEnv,
    make_residual_env_cfg,
)

HIP_ORIGIN_XYZ = [
    (0.125605412969816, 0.00130809302576086, 0.111477729785037),
    (0.125613921776569, -0.241332100772366, 0.111477729785037),
    (-0.170186078223461, 0.0, 0.110012233831204),
    (-0.17017756941671, -0.242991906974238, 0.110012233831204),
]
HIP_ORIGIN_RPY = [
    (math.pi / 2, 0.0608549307343607, 0.0),
    (math.pi / 2, 0.0554849314629031, 0.0),
    (-math.pi / 2, 0.00255307404240576, -math.pi),
    (-math.pi / 2, 0.00187729446256285, -math.pi),
]


def main() -> int:
    result: dict = {
        "schema": "resume_validation.runtime_fk_validation.v1",
        "started_unix": time.time(),
        "passed": False,
        "failures": [],
        "sampled_configurations": args.num_envs * args.batches,
        "per_leg_comparisons": args.num_envs * args.batches * 4,
        "tolerance_m": args.tolerance_m,
    }
    env = None
    try:
        cfg = make_residual_env_cfg(num_envs=args.num_envs, obstacle_height=0.05, episode_length_s=20.0)
        cfg.seed = 2026072701
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        env = WLRResidualRLEnv(cfg)
        generator = torch.Generator(device=env.device).manual_seed(2026072701)
        hip_xyz = torch.tensor(HIP_ORIGIN_XYZ, dtype=torch.float32, device=env.device)
        rpy = torch.tensor(HIP_ORIGIN_RPY, dtype=torch.float32, device=env.device)
        hip_quat = quat_from_euler_xyz(rpy[:, 0], rpy[:, 1], rpy[:, 2])
        base_body_id = env._robot.body_names.index("base_link")
        errors: list[torch.Tensor] = []
        jacobian_conditions: list[torch.Tensor] = []
        unexpected_contact_samples = 0
        max_contact_force_n = 0.0
        limit_violations = 0
        max_commanded_actual_servo_delta_rad = 0.0
        branch_rows = []
        for batch in range(args.batches):
            command_deg = torch.zeros((args.num_envs, 8), dtype=torch.float32, device=env.device)
            for index, name in enumerate(SERVO_JOINT_NAMES):
                low, high = RECORDED_SAFE_COMMAND_DEG[name]
                margin = 0.02 * (high - low)
                command_deg[:, index].uniform_(low + margin, high - margin, generator=generator)
            raw = env._standing_servo_pos + env._joint_command_sign * torch.deg2rad(command_deg)
            joint_pos = env._robot.data.joint_pos.clone()
            joint_vel = torch.zeros_like(env._robot.data.joint_vel)
            joint_pos[:, env._servo_joint_ids] = raw
            joint_pos[:, env._wheel_joint_ids] = 0.0
            root_pose = env._robot.data.root_pose_w.clone()
            root_pose[:, 2] += 0.8
            env._robot.write_root_pose_to_sim(root_pose)
            env._robot.write_root_velocity_to_sim(torch.zeros((args.num_envs, 6), device=env.device))
            env._robot.write_joint_state_to_sim(joint_pos, joint_vel)
            env._robot.set_joint_position_target(raw, joint_ids=env._servo_joint_ids)
            env._robot.set_joint_velocity_target(
                torch.zeros((args.num_envs, 4), device=env.device), joint_ids=env._wheel_joint_ids
            )
            env.scene.write_data_to_sim()
            env.sim.step(render=False)
            env.scene.update(dt=env.physics_dt)
            contact_magnitude = torch.linalg.vector_norm(
                env._contact_sensor.data.net_forces_w, dim=2
            )
            max_contact_force_n = max(max_contact_force_n, float(contact_magnitude.max().item()))
            unexpected_contact_samples += int(
                torch.any(contact_magnitude > 5.0, dim=1).sum().item()
            )
            limit_violations += int(
                torch.any(
                    (raw < env._raw_servo_lower_limits - 1.0e-6)
                    | (raw > env._raw_servo_upper_limits + 1.0e-6),
                    dim=1,
                ).sum().item()
            )

            base_pos = env._robot.data.body_pos_w[:, base_body_id]
            base_quat = env._robot.data.body_quat_w[:, base_body_id]
            wheel_pos = env._robot.data.body_pos_w[:, env._wheel_body_ids]
            base_relative = quat_apply_inverse(
                base_quat.unsqueeze(1).expand(-1, 4, -1).reshape(-1, 4),
                (wheel_pos - base_pos.unsqueeze(1)).reshape(-1, 3),
            ).reshape(args.num_envs, 4, 3)
            hip_relative = base_relative - hip_xyz.unsqueeze(0)
            plane = quat_apply_inverse(
                hip_quat.unsqueeze(0).expand(args.num_envs, -1, -1).reshape(-1, 4),
                hip_relative.reshape(-1, 3),
            ).reshape(args.num_envs, 4, 3)
            # Compare poses against the actual post-step joint state.  The
            # articulation is dynamic and can move slightly between the state
            # write and the body-pose read; comparing body poses against the
            # pre-step command creates sparse millimetre-scale false outliers.
            actual_servo_raw = env._robot.data.joint_pos[:, env._servo_joint_ids]
            max_commanded_actual_servo_delta_rad = max(
                max_commanded_actual_servo_delta_rad,
                float(torch.max(torch.abs(actual_servo_raw - raw)).item()),
            )
            predicted = env._fk(actual_servo_raw)
            actual = plane[:, :, :2]
            batch_error = torch.linalg.vector_norm(predicted - actual, dim=2)
            errors.append(batch_error.detach().cpu())
            q1_effective = raw[:, 0::2] + env._leg_hip_zero
            q2_effective = raw[:, 1::2] + env._leg_knee_zero
            j11 = -env._leg_l1 * torch.sin(q1_effective) - env._leg_l2 * torch.sin(
                q1_effective + q2_effective
            )
            j12 = -env._leg_l2 * torch.sin(q1_effective + q2_effective)
            j21 = env._leg_l1 * torch.cos(q1_effective) + env._leg_l2 * torch.cos(
                q1_effective + q2_effective
            )
            j22 = env._leg_l2 * torch.cos(q1_effective + q2_effective)
            jacobian = torch.stack((j11, j12, j21, j22), dim=2).reshape(-1, 2, 2)
            singular_values = torch.linalg.svdvals(jacobian)
            condition = singular_values[:, 0] / torch.clamp(singular_values[:, 1], min=1.0e-9)
            jacobian_conditions.append(condition.detach().cpu())
            branch_rows.append(
                {
                    "batch": batch,
                    "max_error_m": float(batch_error.max().item()),
                    "rms_error_m": float(torch.sqrt(torch.mean(batch_error.square())).item()),
                }
            )
        values = torch.cat([item.reshape(-1) for item in errors])
        condition_values = torch.cat(jacobian_conditions)
        sorted_values = torch.sort(values).values
        p95 = float(sorted_values[min(len(sorted_values) - 1, math.floor(0.95 * len(sorted_values)))].item())
        result["metrics"] = {
            "max_error_m": float(values.max().item()),
            "mean_error_m": float(values.mean().item()),
            "rms_error_m": float(torch.sqrt(torch.mean(values.square())).item()),
            "p95_error_m": p95,
            "batch_metrics": branch_rows,
            "jacobian_condition_max": float(condition_values.max().item()),
            "jacobian_condition_p95": float(
                torch.quantile(condition_values, torch.tensor(0.95)).item()
            ),
            "unexpected_external_contact_sample_count": unexpected_contact_samples,
            "max_contact_force_n": max_contact_force_n,
            "safe_limit_violation_sample_count": limit_violations,
            "max_commanded_actual_servo_delta_rad": max_commanded_actual_servo_delta_rad,
        }
        if result["metrics"]["max_error_m"] > args.tolerance_m:
            result["failures"].append(
                f"max FK error {result['metrics']['max_error_m']:.9f}m exceeds {args.tolerance_m:.9f}m"
            )
        if unexpected_contact_samples:
            result["failures"].append(
                f"{unexpected_contact_samples} airborne workspace samples had unexpected external contact above 5 N"
            )
        if limit_violations:
            result["failures"].append(
                f"{limit_violations} sampled configurations exceeded the recorded safe command envelope"
            )
        result["passed"] = not result["failures"]
    except Exception as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
        result["traceback"] = traceback.format_exc()
    finally:
        result["finished_unix"] = time.time()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        if env is not None:
            env.close()
        app.close()
    print(json.dumps({"output": str(args.output), "passed": result["passed"], "failures": result["failures"]}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
