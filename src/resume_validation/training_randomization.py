"""Deterministic, bounded per-reset training scenario sampling."""

from __future__ import annotations

import random
from typing import Any

import torch


def cache_independent_reset_root_xz(
    *,
    obstacle_front_x_m: float,
    desired_distance_m: torch.Tensor,
    desired_wheel_relative_m: torch.Tensor,
    wheel_radius_m: torch.Tensor,
    ground_clearance_m: float = 0.002,
) -> torch.Tensor:
    """Compute local reset root x/z without reading the terminal pose cache."""

    if desired_wheel_relative_m.ndim != 3 or desired_wheel_relative_m.shape[1:] != (4, 3):
        raise ValueError("desired_wheel_relative_m must have shape [N, 4, 3]")
    count = desired_wheel_relative_m.shape[0]
    if desired_distance_m.shape != (count,) or wheel_radius_m.shape != (count,):
        raise ValueError("distance and radius must have shape [N]")
    values = (
        desired_wheel_relative_m,
        desired_distance_m,
        wheel_radius_m,
    )
    if not all(torch.isfinite(value).all() for value in values):
        raise ValueError("reset geometry inputs must be finite")
    if ground_clearance_m < 0.0:
        raise ValueError("ground_clearance_m must be non-negative")
    root_x = (
        float(obstacle_front_x_m)
        - desired_distance_m
        - desired_wheel_relative_m[:, :, 0].amax(dim=1)
    )
    root_z = (
        wheel_radius_m
        - desired_wheel_relative_m[:, :, 2].amin(dim=1)
        + float(ground_clearance_m)
    )
    return torch.stack((root_x, root_z), dim=1)


def sample_training_scenario(
    *,
    seed: int,
    env_id: int,
    episode_index: int,
    nominal_distance_m: float,
    level_cfg: dict[str, Any],
) -> dict[str, Any]:
    """Sample one scenario without depending on reset batching or call order."""

    mixed_seed = (
        int(seed) * 1_000_003
        + int(env_id) * 97_409
        + int(episode_index) * 65_537
        + 0x5A17
    )
    generator = random.Random(mixed_seed)
    distance_half = float(level_cfg["initial_distance_half_range_m"])
    pitch_half = float(level_cfg["initial_pitch_half_range_rad"])
    friction_low, friction_high = map(float, level_cfg["friction_range"])
    delay_low, delay_high = map(int, level_cfg["actuator_delay_steps"])
    noise_low, noise_high = map(float, level_cfg["sensor_noise_std_range"])
    if distance_half < 0.0 or pitch_half < 0.0:
        raise ValueError("Initial-state half-ranges must be non-negative")
    if not (0.0 < friction_low <= friction_high):
        raise ValueError("Friction range must be positive and ordered")
    if not (0 <= delay_low <= delay_high <= 2):
        raise ValueError("Actuator delay range must be ordered within [0, 2]")
    if not (0.0 <= noise_low <= noise_high):
        raise ValueError("Sensor-noise range must be non-negative and ordered")
    noise_std = generator.uniform(noise_low, noise_high)
    raw_noise = [generator.gauss(0.0, noise_std) for _ in range(4)]
    return {
        "initial_distance_m": nominal_distance_m
        + generator.uniform(-distance_half, distance_half),
        "initial_pitch_rad": generator.uniform(-pitch_half, pitch_half),
        "friction": generator.uniform(friction_low, friction_high),
        "actuator_delay_steps": generator.randint(delay_low, delay_high),
        "sensor_noise_std": noise_std,
        "obstacle_observation_noise": [
            raw_noise[0] / 0.10,
            raw_noise[1],
            raw_noise[2] / 0.50,
            raw_noise[3] / 0.20,
        ],
    }
