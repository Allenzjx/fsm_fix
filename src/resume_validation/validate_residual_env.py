"""Fresh Isaac validation for the residual DirectRLEnv."""

from __future__ import annotations

import argparse
import json
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
parser.add_argument("--robot_usd", type=Path, default=VALIDATION_ROOT / "assets" / "converted" / "wlr_robot_validation.usd")
parser.add_argument("--num_envs", type=int, default=16)
parser.add_argument("--obstacle_height", type=float, default=0.05)
parser.add_argument("--settle_steps", type=int, default=180)
parser.add_argument("--zero_steps", type=int, default=300)
parser.add_argument("--random_steps", type=int, default=40)
parser.add_argument(
    "--training_randomization_level",
    choices=("nominal", "light", "full"),
    default="",
)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import importlib.metadata
import torch

from resume_validation.residual_rl_env import (
    ACTOR_OBS_DIM,
    CRITIC_STATE_DIM,
    WLRResidualRLEnv,
    make_residual_env_cfg,
)
from resume_validation.config_io import load_config
from resume_validation.source_audit import sha256_file


def tensor_stats(value: torch.Tensor) -> dict[str, float | int | bool]:
    return {
        "shape": list(value.shape),
        "finite": bool(torch.isfinite(value).all().item()),
        "min": float(value.min().item()),
        "max": float(value.max().item()),
        "mean": float(value.mean().item()),
        "std": float(value.std(unbiased=False).item()),
    }


def main() -> int:
    result: dict = {
        "schema": "resume_validation.residual_env_validation.v1",
        "started_unix": time.time(),
        "passed": False,
        "failures": [],
        "versions": {
            "isaaclab": importlib.metadata.version("isaaclab"),
            "isaacsim": importlib.metadata.version("isaacsim"),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
        },
        "asset": {
            "path": str(args.robot_usd.resolve()),
            "sha256": sha256_file(args.robot_usd),
        },
    }
    env = None
    try:
        torch.manual_seed(20260727)
        cfg = make_residual_env_cfg(
            num_envs=args.num_envs,
            obstacle_height=args.obstacle_height,
            robot_usd_path=args.robot_usd,
        )
        # This validator compares the command produced in a control step with
        # the reference from that same step.  Automatic terminal resets replace
        # the public reference tensor before the post-step assertion and would
        # therefore compare different episodes.  Safety predicates remain
        # active and are inspected; only automatic termination is disabled.
        cfg.disable_episode_termination = True
        if getattr(args, "device", None):
            cfg.sim.device = args.device
        cfg.seed = 20260727
        env = WLRResidualRLEnv(cfg)
        if args.training_randomization_level:
            training_cfg = load_config(VALIDATION_ROOT / "configs" / "obstacle_train.yaml")
            env.configure_training_randomization(
                level_cfg=training_cfg["randomization_levels"][
                    args.training_randomization_level
                ],
                seed=cfg.seed,
                nominal_distance_m=float(
                    training_cfg["initial_distance"]["nominal_m"]
                ),
            )
        zeros = torch.zeros((env.num_envs, 12), dtype=torch.float32, device=env.device)
        obs, _ = env.reset()
        # Hold the actual standing command during the contact settling check;
        # otherwise the FSM begins its approach while the "static" sensor
        # baseline is being measured.
        env.set_external_reference(zeros)
        for _ in range(args.settle_steps):
            obs, _, _, _, _ = env.step(zeros)
        forces = env._contact_sensor.data.net_forces_w
        result["contact_sensor"] = {
            "body_names": list(env._contact_sensor.body_names),
            "net_forces": tensor_stats(forces),
            "active_body_count_per_env": (
                torch.linalg.vector_norm(forces, dim=2) > float(cfg.contact_force_threshold_n)
            ).sum(dim=1).detach().cpu().tolist(),
        }
        if not torch.isfinite(forces).all():
            result["failures"].append("ContactSensor net_forces_w contains non-finite values")
        if not torch.all(
            (torch.linalg.vector_norm(forces[:, env._contact_wheel_ids, :], dim=2) > cfg.contact_force_threshold_n)
            .sum(dim=1)
            >= 2
        ):
            result["failures"].append("fewer than two force-supported wheels after static settling")

        env.set_external_reference(None)
        obs, _ = env.reset()
        max_servo_error = 0.0
        max_wheel_error = 0.0
        obs_min = torch.full((ACTOR_OBS_DIM,), float("inf"), device=env.device)
        obs_max = torch.full((ACTOR_OBS_DIM,), float("-inf"), device=env.device)
        for _ in range(args.zero_steps):
            obs, reward, terminated, truncated, _ = env.step(zeros)
            reference_servo_raw = env._standing_servo_pos + env._joint_command_sign * torch.deg2rad(
                env._reference_commands[:, :8]
            )
            max_servo_error = max(
                max_servo_error, float(torch.max(torch.abs(env._servo_targets - reference_servo_raw)).item())
            )
            max_wheel_error = max(
                max_wheel_error,
                float(
                    torch.max(
                        torch.abs(env._physical_forward_wheel_cmds - env._reference_commands[:, 8:])
                    ).item()
                ),
            )
            obs_min = torch.minimum(obs_min, obs["policy"].amin(dim=0))
            obs_max = torch.maximum(obs_max, obs["policy"].amax(dim=0))
            if not torch.isfinite(reward).all():
                result["failures"].append("non-finite reward during zero-residual rollout")
                break
            if torch.any(terminated | truncated):
                obs, _ = env.reset()
        result["zero_residual"] = {
            "steps": args.zero_steps,
            "max_servo_target_error_rad": max_servo_error,
            "max_wheel_target_error_rad_s": max_wheel_error,
            "bitwise_or_exact_float_equal": max_servo_error == 0.0 and max_wheel_error == 0.0,
        }
        if max_servo_error != 0.0 or max_wheel_error != 0.0:
            result["failures"].append("zero residual is not exactly equivalent to FSM targets")

        reset_obs, _ = env.reset()
        result["episode_reset"] = {
            "actor_observation_finite": bool(torch.isfinite(reset_obs["policy"]).all().item()),
            "critic_state_finite": bool(torch.isfinite(reset_obs["critic"]).all().item()),
            "episode_length_zero": bool(torch.all(env.episode_length_buf == 0).item()),
            "fsm_phase_zero": bool(torch.all(env._fsm_phase == 0).item()),
        }
        if not all(result["episode_reset"].values()):
            result["failures"].append("explicit vectorized episode reset did not restore finite zero-phase state")
        if args.training_randomization_level:
            training_cfg = load_config(VALIDATION_ROOT / "configs" / "obstacle_train.yaml")
            level_cfg = training_cfg["randomization_levels"][
                args.training_randomization_level
            ]
            distance_half = float(level_cfg["initial_distance_half_range_m"])
            pitch_half = float(level_cfg["initial_pitch_half_range_rad"])
            friction_low, friction_high = map(float, level_cfg["friction_range"])
            delay_low, delay_high = map(int, level_cfg["actuator_delay_steps"])
            nominal_distance = float(training_cfg["initial_distance"]["nominal_m"])
            randomization_checks = {
                "episode_index_advanced": bool(torch.all(env._training_episode_index > 0).item()),
                "distance_within_bounds": bool(
                    torch.all(
                        torch.abs(env._training_initial_distance_m - nominal_distance)
                        <= distance_half + 1.0e-7
                    ).item()
                ),
                "pitch_within_bounds": bool(
                    torch.all(
                        torch.abs(env._training_initial_pitch_rad)
                        <= pitch_half + 1.0e-7
                    ).item()
                ),
                "friction_within_bounds": bool(
                    torch.all(
                        (env._scenario_friction >= friction_low)
                        & (env._scenario_friction <= friction_high)
                    ).item()
                ),
                "delay_within_bounds": bool(
                    torch.all(
                        (env._action_delay_steps >= delay_low)
                        & (env._action_delay_steps <= delay_high)
                    ).item()
                ),
                "noise_finite": bool(
                    torch.isfinite(env._obstacle_observation_noise).all().item()
                ),
            }
            result["training_randomization"] = {
                "level": args.training_randomization_level,
                "checks": randomization_checks,
                "initial_distance_m": env._training_initial_distance_m.detach().cpu().tolist(),
                "initial_pitch_rad": env._training_initial_pitch_rad.detach().cpu().tolist(),
                "friction": env._scenario_friction.detach().cpu().tolist(),
                "actuator_delay_steps": env._action_delay_steps.detach().cpu().tolist(),
                "obstacle_observation_noise": env._obstacle_observation_noise.detach().cpu().tolist(),
            }
            if not all(randomization_checks.values()):
                result["failures"].append("training randomization integration checks failed")

        generator = torch.Generator(device=env.device).manual_seed(991)
        for _ in range(args.random_steps):
            actions = torch.empty_like(zeros).uniform_(-0.25, 0.25, generator=generator)
            obs, reward, _, _, _ = env.step(actions)
            if not torch.isfinite(reward).all() or not torch.isfinite(obs["policy"]).all() or not torch.isfinite(obs["critic"]).all():
                result["failures"].append("non-finite value during bounded random residual rollout")
                break
        result["observation"] = {
            "actor": tensor_stats(obs["policy"]),
            "critic": tensor_stats(obs["critic"]),
            "actor_feature_min": obs_min.detach().cpu().tolist(),
            "actor_feature_max": obs_max.detach().cpu().tolist(),
            "expected_actor_dim": ACTOR_OBS_DIM,
            "expected_critic_dim": CRITIC_STATE_DIM,
        }
        result["diagnostic_env0"] = env.residual_diagnostics(0)
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
