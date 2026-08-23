"""Replay the accepted 50/100 mm commands in the sensor-stable DirectRLEnv."""

from __future__ import annotations

import argparse
import csv
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
parser.add_argument("--height_mm", type=int, choices=(50, 100), required=True)
parser.add_argument("--seed", type=int, default=20260727)
parser.add_argument("--profile", choices=("raw", "fast"), default="raw")
parser.add_argument(
    "--max_idle_gap_s",
    type=float,
    default=0.0,
    help="Fast-profile inter-event gap cap; zero preserves every shifted inter-event gap.",
)
parser.add_argument("--output_dir", type=Path, required=True)
parser.add_argument("--robot_usd", type=Path, default=VALIDATION_ROOT / "assets" / "converted" / "wlr_robot_validation.usd")
parser.add_argument("--settle_s", type=float, default=2.0)
parser.add_argument(
    "--post_dwell_s",
    type=float,
    default=3.0,
    help="Observation-only tail after the final event; must exceed the frozen 1.5 s stable dwell.",
)
parser.add_argument("--obstacle_x", type=float, default=1.55)
parser.add_argument("--obstacle_length", type=float, default=2.0573755975573045)
parser.add_argument("--obstacle_width", type=float, default=0.882200685486094)
parser.add_argument(
    "--record_every",
    type=int,
    default=1,
    help="Deprecated compatibility option. Formal safety telemetry is captured every control step.",
)
parser.add_argument("--max_replay_s", type=float, default=0.0, help="Diagnostic truncation only; a truncated run cannot pass.")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import importlib.metadata
import torch

from resume_validation.actuator_mapping import SERVO_JOINT_NAMES, WHEEL_JOINT_NAMES
from resume_validation.replay_loader import flatten_events, load_replay
from resume_validation.residual_rl_env import WLRResidualRLEnv, make_residual_env_cfg
from resume_validation.source_audit import sha256_file


def _json(value) -> str:
    return json.dumps(value, separators=(",", ":"), allow_nan=False)


def _finite_tensor(value: torch.Tensor) -> bool:
    return bool(torch.isfinite(value).all().item())


def main() -> int:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    replay_path = (
        PROJECT_ROOT
        / "height_based_obstacle_replay"
        / "saved_height_steps"
        / ("height_05cm" if args.height_mm == 50 else "height_10cm")
        / "accepted_steps.jsonl"
    )
    steps = load_replay(replay_path)
    recorded_duration = sum(step.duration_s for step in steps)
    if args.profile == "raw":
        events = flatten_events(steps)
        total_duration = recorded_duration
    else:
        gap_cap = args.max_idle_gap_s if args.max_idle_gap_s > 0.0 else 1.0e12
        events = flatten_events(steps, max_idle_gap_s=gap_cap)
        total_duration = max((event.time_s for event in events), default=0.0) + 0.05
    result: dict = {
        "schema": "resume_validation.direct_replay.v1",
        "started_unix": time.time(),
        "passed": False,
        "failures": [],
        "height_mm": args.height_mm,
        "seed": args.seed,
        "telemetry_nominal_stride_control_steps": max(1, args.record_every),
        "telemetry_forced_on_safety_or_terminal_event": True,
        "source_replay": {
            "path": str(replay_path),
            "sha256": sha256_file(replay_path),
            "step_count": len(steps),
            "event_count": len(events),
            "dispatched_command_count": sum(len(event.playback_commands) for event in events),
            "raw_duration_s": recorded_duration,
            "playback_duration_s": total_duration,
            "profile": args.profile,
            "max_idle_gap_s": args.max_idle_gap_s if args.profile == "fast" else None,
            "playback_semantics": "dispatch expanded_commands when present, otherwise command; reconstruct post-event state",
            "reference_sequence_model_sha256": "af333f7c0db7ece943a919030b03bc294b1cd9ebc7dc2f10452b57975f399c68",
            "reference_playback_sha256": "b6b40d276dfb49e4dd181f65dbabab5e77a54cfb34b6e648b067d41433f2d836",
        },
        "asset": {"path": str(args.robot_usd.resolve()), "sha256": sha256_file(args.robot_usd)},
        "versions": {
            "isaaclab": importlib.metadata.version("isaaclab"),
            "isaacsim": importlib.metadata.version("isaacsim"),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
        },
        "implementation": {
            "runner_path": str(Path(__file__).resolve()),
            "runner_sha256": sha256_file(Path(__file__)),
            "metrics_config_sha256": sha256_file(VALIDATION_ROOT / "configs" / "metrics.yaml"),
            "actuator_config_sha256": sha256_file(
                VALIDATION_ROOT / "configs" / "actuator_limits.yaml"
            ),
            "telemetry_config_sha256": sha256_file(
                VALIDATION_ROOT / "configs" / "telemetry_contact.yaml"
            ),
        },
        "geometry": {
            "obstacle_height_m": args.height_mm / 1000.0,
            "obstacle_x_m": args.obstacle_x,
            "obstacle_length_m": args.obstacle_length,
            "obstacle_width_m": args.obstacle_width,
            "front_x_m": args.obstacle_x - args.obstacle_length / 2.0,
            "back_x_m": args.obstacle_x + args.obstacle_length / 2.0,
        },
    }
    env = None
    telemetry_file = output_dir / "telemetry.jsonl"
    contacts_file = output_dir / "contacts.jsonl"
    commands_file = output_dir / "commands.csv"
    try:
        cfg = make_residual_env_cfg(
            num_envs=1,
            obstacle_height=args.height_mm / 1000.0,
            robot_usd_path=args.robot_usd,
            obstacle_x=args.obstacle_x,
            obstacle_length=args.obstacle_length,
            obstacle_width=args.obstacle_width,
            episode_length_s=total_duration + args.settle_s + args.post_dwell_s + 10.0,
        )
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        cfg.seed = int(args.seed)
        cfg.terminate_on_residual_success = False
        cfg.disable_episode_termination = True
        env = WLRResidualRLEnv(cfg)
        zero = torch.zeros((1, 12), dtype=torch.float32, device=env.device)
        initial_reference = torch.zeros((1, 12), dtype=torch.float32, device=env.device)
        env.set_external_reference(initial_reference)
        env.reset()
        for _ in range(math.ceil(args.settle_s / float(env.step_dt))):
            env.step(zero)

        current_servo = {name: 0.0 for name in SERVO_JOINT_NAMES}
        current_wheels = {name: 0.0 for name in WHEEL_JOINT_NAMES}
        event_cursor = 0
        dispatched_command_count = 0
        sample_count = 0
        metric_sample_count = 0
        stable_success_seen = False
        fall_seen = False
        collision_seen = False
        numerical_seen = False
        joint_limit_seen = False
        command_limit_seen = False
        min_margin = float("inf")
        invalid_margin_samples = 0
        pitch_rate_sq_sum = 0.0
        max_abs_pitch = 0.0
        max_abs_roll = 0.0
        initial_base_x = float(env._root_pos_local()[0, 0].item())
        last_base_x = initial_base_x
        termination_step = None
        max_dispatch_jitter_s = 0.0

        telemetry_stream = telemetry_file.open("w", encoding="utf-8")
        contacts_stream = contacts_file.open("w", encoding="utf-8")
        command_stream = commands_file.open("w", encoding="utf-8", newline="")
        command_writer = csv.DictWriter(
            command_stream,
            fieldnames=[
                "time_s",
                "dispatch_time_s",
                "dispatch_jitter_s",
                "event_cursor",
                "step_index",
                "event_index",
                "command",
                "playback_commands",
                *SERVO_JOINT_NAMES,
                *WHEEL_JOINT_NAMES,
            ],
        )
        command_writer.writeheader()
        try:
            replay_duration = min(total_duration, args.max_replay_s) if args.max_replay_s > 0 else total_duration
            total_control_duration = replay_duration + args.post_dwell_s
            total_steps = math.ceil(total_control_duration / float(env.step_dt))
            for control_step in range(total_steps + 1):
                replay_time = min(control_step * float(env.step_dt), total_control_duration)
                while event_cursor < len(events) and events[event_cursor].time_s <= replay_time + 1.0e-9:
                    event = events[event_cursor]
                    current_servo.update(event.servo_targets_deg)
                    current_wheels.update(event.wheel_targets_rad_s)
                    dispatched_command_count += len(event.playback_commands)
                    dispatch_jitter_s = max(0.0, replay_time - event.time_s)
                    max_dispatch_jitter_s = max(max_dispatch_jitter_s, dispatch_jitter_s)
                    command_writer.writerow(
                        {
                            "time_s": event.time_s,
                            "dispatch_time_s": replay_time,
                            "dispatch_jitter_s": dispatch_jitter_s,
                            "event_cursor": event_cursor,
                            "step_index": event.step_index,
                            "event_index": event.event_index,
                            "command": event.command,
                            "playback_commands": " | ".join(event.playback_commands),
                            **current_servo,
                            **current_wheels,
                        }
                    )
                    event_cursor += 1
                reference = torch.tensor(
                    [[current_servo[name] for name in SERVO_JOINT_NAMES] + [current_wheels[name] for name in WHEEL_JOINT_NAMES]],
                    dtype=torch.float32,
                    device=env.device,
                )
                env.set_external_reference(reference)
                _, reward, terminated, truncated, _ = env.step(zero)
                root = env._root_pos_local()[0]
                roll, pitch, _ = env._roll_pitch_yaw()
                wheel_pos = env._wheel_pos_local()[0]
                force_vectors, force_magnitude = env._wheel_contact_forces()
                margin, margin_valid = env._longitudinal_margin()
                com_xy = env._compute_com_xy()[0][0]
                pitch_rate = float(env._robot.data.root_ang_vel_b[0, 1].item())
                finite = (
                    _finite_tensor(root)
                    and _finite_tensor(env._robot.data.root_state_w)
                    and _finite_tensor(force_vectors)
                    and bool(torch.isfinite(reward).all().item())
                )
                numerical_seen |= not finite
                stable_success_seen |= bool(env._success_buf[0].item())
                fall_seen |= bool(env._fall_buf[0].item())
                nonwheel_forces = env._contact_sensor.data.net_forces_w[0, env._contact_nonwheel_ids, :]
                actual_nonwheel_contact = bool(
                    torch.any(torch.linalg.vector_norm(nonwheel_forces, dim=1) > 5.0).item()
                )
                # ContactSensor net force excludes internal articulation forces;
                # any external non-wheel support/collision is invalid here.
                collision = actual_nonwheel_contact
                collision_seen |= collision
                position = env._robot.data.joint_pos[0, env._servo_joint_ids]
                targets = env._servo_targets[0]
                command_limit = bool(
                    torch.any(
                        (targets < env._raw_servo_lower_limits[0] - 1.0e-6)
                        | (targets > env._raw_servo_upper_limits[0] + 1.0e-6)
                    ).item()
                )
                command_limit_seen |= command_limit
                tolerance = float(env.cfg.joint_limit_violation_tolerance_rad)
                joint_limit = bool(
                    torch.any(
                        (position < env._raw_servo_lower_limits[0] - tolerance)
                        | (position > env._raw_servo_upper_limits[0] + tolerance)
                    ).item()
                )
                joint_limit_seen |= joint_limit
                if bool(margin_valid[0].item()):
                    min_margin = min(min_margin, float(margin[0].item()))
                else:
                    invalid_margin_samples += 1
                pitch_rate_sq_sum += pitch_rate * pitch_rate
                metric_sample_count += 1
                max_abs_pitch = max(max_abs_pitch, abs(float(pitch[0].item())))
                max_abs_roll = max(max_abs_roll, abs(float(roll[0].item())))
                last_base_x = float(root[0].item())
                done_now = bool((terminated | truncated)[0].item())
                record_this_step = (
                    control_step % max(1, args.record_every) == 0
                    or collision
                    or fall_seen
                    or joint_limit
                    or command_limit
                    or (not finite)
                    or bool(env._success_buf[0].item())
                    or done_now
                )
                if not record_this_step:
                    continue
                telemetry_stream.write(
                    _json(
                        {
                            "sample_index": sample_count,
                            "control_step": control_step,
                            "time_s": replay_time,
                            "event_cursor": event_cursor,
                            "base_position_m": root.detach().cpu().tolist(),
                            "base_roll_rad": float(roll[0].item()),
                            "base_pitch_rad": float(pitch[0].item()),
                            "base_linear_velocity_body_m_s": env._robot.data.root_lin_vel_b[0].detach().cpu().tolist(),
                            "base_angular_velocity_body_rad_s": env._robot.data.root_ang_vel_b[0].detach().cpu().tolist(),
                            "com_xy_m": com_xy.detach().cpu().tolist(),
                            "margin_m": float(margin[0].item()) if bool(margin_valid[0].item()) else None,
                            "margin_valid": bool(margin_valid[0].item()),
                            "wheel_position_m": wheel_pos.detach().cpu().tolist(),
                            "wheel_contact_state": env._wheel_contact_state[0].detach().cpu().tolist(),
                            "wheel_contact_force_w_n": force_vectors[0].detach().cpu().tolist(),
                            "wheel_contact_force_magnitude_n": force_magnitude[0].detach().cpu().tolist(),
                            "legacy_geometry_nonwheel_obstacle_contact_count": int(
                                env._nonwheel_obstacle_contact_count[0].item()
                            ),
                            "actual_nonwheel_contact": actual_nonwheel_contact,
                            "servo_position_raw_rad": position.detach().cpu().tolist(),
                            "servo_target_raw_rad": env._servo_targets[0].detach().cpu().tolist(),
                            "wheel_velocity_physical_rad_s": env._physical_wheel_velocities()[0].detach().cpu().tolist(),
                            "wheel_target_physical_rad_s": env._physical_forward_wheel_cmds[0].detach().cpu().tolist(),
                            "reference_command": reference[0].detach().cpu().tolist(),
                            "success_dwell_steps": int(env._stable_dwell_counter[0].item()),
                            "stable_success": bool(env._success_buf[0].item()),
                            "fall": bool(env._fall_buf[0].item()),
                            "collision": collision,
                            "joint_limit": joint_limit,
                            "command_limit": command_limit,
                            "joint_limit_tolerance_rad": tolerance,
                            "finite": finite,
                            "reward": float(reward[0].item()),
                        }
                    )
                    + "\n"
                )
                for body_index, body_name in enumerate(env._contact_sensor.body_names):
                    force = env._contact_sensor.data.net_forces_w[0, body_index]
                    magnitude_n = float(torch.linalg.vector_norm(force).item())
                    if magnitude_n < float(cfg.contact_force_threshold_n):
                        continue
                    contacts_stream.write(
                        _json(
                            {
                                "sample_index": sample_count,
                                "time_s": replay_time,
                                "body_name": body_name,
                                "force_w_n": force.detach().cpu().tolist(),
                                "magnitude_n": magnitude_n,
                                "wheel": "wheel" in body_name,
                                "source": "isaaclab.ContactSensor.net_forces_w",
                            }
                        )
                        + "\n"
                    )
                sample_count += 1
                if done_now:
                    stable_success_seen |= bool(env._last_done_success[0].item())
                    fall_seen |= bool(env._last_done_fall[0].item())
                    collision_seen |= bool(env._last_done_collision[0].item())
                    numerical_seen |= bool(env._last_done_numerical[0].item())
                    termination_step = control_step
                    break
        finally:
            telemetry_stream.close()
            contacts_stream.close()
            command_stream.close()

        checks = {
            "not_diagnostic_truncation": args.max_replay_s <= 0,
            "all_events_dispatched": event_cursor == len(events),
            "all_commands_dispatched": (
                dispatched_command_count
                == int(result["source_replay"]["dispatched_command_count"])
            ),
            "stable_success_dwell_observed": stable_success_seen,
            "no_fall": not fall_seen,
            "no_body_or_link_collision": not collision_seen,
            "no_joint_limit_violation": not joint_limit_seen,
            "no_command_limit_violation": not command_limit_seen,
            "no_numerical_error": not numerical_seen,
            "contact_sensor_rows_present": contacts_file.stat().st_size > 0,
        }
        result["checks"] = checks
        result["metrics"] = {
            "sample_count": sample_count,
            "control_metric_sample_count": metric_sample_count,
            "events_dispatched": event_cursor,
            "commands_dispatched": dispatched_command_count,
            "initial_base_x_m": initial_base_x,
            "final_base_x_m": last_base_x,
            "forward_progress_m": last_base_x - initial_base_x,
            "episode_min_longitudinal_support_margin_m": min_margin if math.isfinite(min_margin) else None,
            "invalid_margin_samples": invalid_margin_samples,
            "pitch_rate_rms_rad_s": math.sqrt(pitch_rate_sq_sum / max(1, metric_sample_count)),
            "max_abs_pitch_rad": max_abs_pitch,
            "max_abs_roll_rad": max_abs_roll,
            "termination_control_step": termination_step,
            "max_dispatch_jitter_s": max_dispatch_jitter_s,
            "control_dt_s": float(env.step_dt),
        }
        result["artifacts"] = {
            "telemetry_jsonl": str(telemetry_file),
            "telemetry_sha256": sha256_file(telemetry_file),
            "contacts_jsonl": str(contacts_file),
            "contacts_sha256": sha256_file(contacts_file),
            "commands_csv": str(commands_file),
            "commands_sha256": sha256_file(commands_file),
        }
        result["passed"] = all(checks.values())
        result["failures"] = [name for name, passed in checks.items() if not passed]
    except Exception as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
        result["traceback"] = traceback.format_exc()
    finally:
        result["finished_unix"] = time.time()
        result_path = output_dir / "result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        if env is not None:
            env.close()
        app.close()
    print(json.dumps({"result": str(output_dir / "result.json"), "passed": result["passed"], "failures": result["failures"]}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
