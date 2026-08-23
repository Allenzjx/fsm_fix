"""Fresh Isaac Sim integration validation for the isolated project."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path("C:/robotics_sim/wlr_robot")
VALIDATION_ROOT = PROJECT_ROOT / "resume_validation_fsm_residual_ppo"
ISAACLAB_ROOT = Path("C:/robotics_sim/IsaacLab")

# Logical command-space envelope observed in the two accepted replay logs.
# Commands outside this envelope are deliberately not a motion requirement for
# the derived validation asset: the authored PhysX limits are meant to stop
# unvalidated directions instead of silently expanding the robot workspace.
RECORDED_SAFE_COMMAND_DEG = {
    "front_left_hip": (-32.5, 63.0),
    "front_left_knee": (-42.0, 23.1),
    "front_right_hip": (0.0, 39.5),
    "front_right_knee": (-15.7, 31.4),
    "rear_left_hip": (-11.8, 24.2),
    "rear_left_knee": (0.0, 45.2),
    "rear_right_hip": (-35.3, 29.8),
    "rear_right_knee": (-60.0, 0.0),
}


def add_paths() -> None:
    for extension in (ISAACLAB_ROOT / "source").iterdir():
        if extension.is_dir() and str(extension) not in sys.path:
            sys.path.append(str(extension))
    for path in (ISAACLAB_ROOT, PROJECT_ROOT, VALIDATION_ROOT / "src"):
        if str(path) not in sys.path:
            sys.path.append(str(path))


add_paths()
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=VALIDATION_ROOT / "assets" / "validation" / "isaac_integration.json")
parser.add_argument("--robot_usd", type=Path, default=PROJECT_ROOT / "usd" / "wlr_robot_drive_test.usd")
parser.add_argument("--settle_steps", type=int, default=600)
parser.add_argument("--motion_steps", type=int, default=120)
parser.add_argument("--knee_negative_limit_deg", type=float, default=-35.0)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
simulation_app = launcher.app

import importlib.metadata
import torch

import wlr_obstacle_rl_env as legacy_env
legacy_env.KNEE_COMMAND_LIMIT_DEG = (float(args.knee_negative_limit_deg), legacy_env.KNEE_COMMAND_LIMIT_DEG[1])
from wlr_obstacle_rl_env import (
    SERVO_JOINT_NAMES,
    WHEEL_FORWARD_SIGN,
    WHEEL_JOINT_NAMES,
    WLRObstacleRLEnv,
    file_sha256,
    make_wlr_obstacle_env_cfg,
)


def finite_tree(value: Any) -> bool:
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all().item())
    if isinstance(value, dict):
        return all(finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def settle(env: WLRObstacleRLEnv, count: int) -> list[dict[str, Any]]:
    env.reset()
    action = torch.zeros((env.num_envs, 12), device=env.device)
    snapshots: list[dict[str, Any]] = []
    for index in range(count):
        result = env.step(action)
        if not finite_tree(result):
            raise RuntimeError(f"Non-finite environment result at settle step {index}")
        if index % 20 == 0 or index == count - 1:
            snapshots.append(env.get_diagnostics(0))
    return snapshots


def one_wheel(env: WLRObstacleRLEnv, name: str, count: int) -> dict[str, Any]:
    settle(env, 40)
    action = torch.zeros((1, 12), device=env.device)
    action[:, 8 + WHEEL_JOINT_NAMES.index(name)] = 0.60
    start = env.get_diagnostics(0)
    values = []
    for _ in range(count):
        env.step(action)
        values.append(float(env.get_diagnostics(0)["actual_wheel_velocities_physical"][name]))
    end = env.get_diagnostics(0)
    return {
        "joint": name,
        "configured_forward_sign": WHEEL_FORWARD_SIGN[name],
        "mean_physical_velocity_rad_s": sum(values[-30:]) / min(30, len(values)),
        "base_dx_m": float(end["base_pose"]["x"]) - float(start["base_pose"]["x"]),
        "raw_target_rad_s": float(end["wheel_commands_raw"][name]),
    }


def all_wheels(env: WLRObstacleRLEnv, count: int, direction: float) -> dict[str, Any]:
    settle(env, 40)
    action = torch.zeros((1, 12), device=env.device)
    action[:, 8:] = direction * 0.60
    start = env.get_diagnostics(0)
    for _ in range(count):
        env.step(action)
    end = env.get_diagnostics(0)
    return {
        "direction": direction,
        "base_dx_m": float(end["base_pose"]["x"]) - float(start["base_pose"]["x"]),
        "base_dy_m": float(end["base_pose"]["y"]) - float(start["base_pose"]["y"]),
        "yaw_delta_rad": float(end["yaw"]) - float(start["yaw"]),
        "actual_physical_velocity_rad_s": end["actual_wheel_velocities_physical"],
        "raw_targets_rad_s": end["wheel_commands_raw"],
    }


def one_joint(env: WLRObstacleRLEnv, name: str, action_value: float, count: int) -> dict[str, Any]:
    # Joint direction is tested airborne so ground contact cannot make a valid
    # downward knee command look like a joint-limit failure.
    settle(env, 20)
    root_pose = env._robot.data.root_pose_w.clone()
    root_pose[:, 2] += 0.25
    env._robot.write_root_pose_to_sim(root_pose)
    env._robot.write_root_velocity_to_sim(torch.zeros((env.num_envs, 6), device=env.device))
    env.scene.write_data_to_sim()
    action = torch.zeros((1, 12), device=env.device)
    local = SERVO_JOINT_NAMES.index(name)
    before = env._robot.data.joint_pos[0, env._servo_joint_ids[local]].item()
    action[:, local] = action_value
    for _ in range(count):
        env.step(action)
    after = env._robot.data.joint_pos[0, env._servo_joint_ids[local]].item()
    diag = env.get_diagnostics(0)
    return {
        "joint": name,
        "normalized_action": action_value,
        "measured_before_rad": before,
        "measured_after_rad": after,
        "measured_delta_rad": after - before,
        "command_deg": diag["servo_command_deg"][name],
        "target": diag["servo_command_diagnostics"][name],
    }


def main() -> int:
    output: dict[str, Any] = {
        "timestamp_unix": time.time(),
        "script": str(Path(__file__).resolve()),
        "passed": False,
        "failures": [],
        "warnings": [],
        "versions": {
            "isaaclab": importlib.metadata.version("isaaclab"),
            "isaacsim": importlib.metadata.version("isaacsim"),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
    }
    env = None
    try:
        asset = args.robot_usd.expanduser().resolve()
        output["robot_usd"] = str(asset)
        output["robot_usd_sha256"] = file_sha256(asset)
        cfg = make_wlr_obstacle_env_cfg(num_envs=1, robot_usd_path=asset, obstacle_height=0.05)
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        env = WLRObstacleRLEnv(cfg)
        output["setup_report"] = env.make_setup_report()
        snapshots = settle(env, args.settle_steps)
        output["static_stand"] = {
            "duration_sim_s": args.settle_steps * cfg.sim.dt * cfg.decimation,
            "first": snapshots[0],
            "last": snapshots[-1],
            "finite": finite_tree(snapshots),
            "sample_count": len(snapshots),
        }
        output["one_wheel_forward"] = [one_wheel(env, name, args.motion_steps) for name in WHEEL_JOINT_NAMES]
        output["all_wheels_forward"] = all_wheels(env, args.motion_steps, 1.0)
        output["all_wheels_reverse"] = all_wheels(env, args.motion_steps, -1.0)
        output["one_joint_motion"] = []
        for name in SERVO_JOINT_NAMES:
            output["one_joint_motion"].append(one_joint(env, name, 0.05, 20))
            output["one_joint_motion"].append(one_joint(env, name, -0.05, 20))
        if not output["static_stand"]["finite"]:
            output["failures"].append("static telemetry contains non-finite values")
        if output["all_wheels_forward"]["base_dx_m"] <= 0.02:
            output["failures"].append("all-wheel positive command did not move along +X")
        if output["all_wheels_reverse"]["base_dx_m"] >= -0.02:
            output["failures"].append("all-wheel negative command did not move along -X")
        for row in output["one_wheel_forward"]:
            if row["mean_physical_velocity_rad_s"] <= 0.05:
                output["failures"].append(f"{row['joint']} forward sign failed")
        for row in output["one_joint_motion"]:
            safe_low, safe_high = RECORDED_SAFE_COMMAND_DEG[row["joint"]]
            command_deg = float(row["command_deg"])
            within_recorded_envelope = safe_low - 1.0e-9 <= command_deg <= safe_high + 1.0e-9
            moved = abs(row["measured_delta_rad"]) >= 1e-4
            row["recorded_safe_command_range_deg"] = [safe_low, safe_high]
            row["within_recorded_safe_envelope"] = within_recorded_envelope
            row["motion_required"] = within_recorded_envelope
            row["moved"] = moved
            if within_recorded_envelope and not moved:
                output["failures"].append(f"{row['joint']} failed to move for {row['normalized_action']}")
            elif not within_recorded_envelope and not moved:
                row["classification"] = "expected_safe_limit_block"
            elif not within_recorded_envelope and moved:
                row["classification"] = "outside_recorded_envelope_not_scored"
                output["warnings"].append(
                    f"{row['joint']} moved for a diagnostic command outside its recorded safe envelope"
                )
            else:
                row["classification"] = "required_motion_pass"
        output["passed"] = not output["failures"]
    except Exception as exc:
        output["failures"].append(f"{type(exc).__name__}: {exc}")
        output["traceback"] = __import__("traceback").format_exc()
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        if env is not None:
            env.close()
        simulation_app.close()
    print(json.dumps({"output": str(args.output), "passed": output["passed"], "failures": output["failures"]}, indent=2))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
