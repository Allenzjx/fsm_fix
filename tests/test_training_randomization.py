"""Determinism and bounds for training-only scenario randomization."""

from __future__ import annotations

from pathlib import Path

from resume_validation.config_io import load_config
from resume_validation.training_randomization import sample_training_scenario
from resume_validation.training_randomization import cache_independent_reset_root_xz
import torch


TRAIN_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "obstacle_train.yaml"


def test_training_randomization_is_deterministic_and_bounded() -> None:
    levels = load_config(TRAIN_CONFIG)["randomization_levels"]
    first = sample_training_scenario(
        seed=11,
        env_id=7,
        episode_index=3,
        nominal_distance_m=0.268,
        level_cfg=levels["full"],
    )
    repeated = sample_training_scenario(
        seed=11,
        env_id=7,
        episode_index=3,
        nominal_distance_m=0.268,
        level_cfg=levels["full"],
    )
    assert first == repeated
    assert 0.243 <= first["initial_distance_m"] <= 0.293
    assert -0.020 <= first["initial_pitch_rad"] <= 0.020
    assert 0.90 <= first["friction"] <= 1.20
    assert first["actuator_delay_steps"] in (0, 1, 2)
    assert 0.0 <= first["sensor_noise_std"] <= 0.005


def test_nominal_level_has_no_random_variation() -> None:
    nominal = load_config(TRAIN_CONFIG)["randomization_levels"]["nominal"]
    sample = sample_training_scenario(
        seed=47,
        env_id=9,
        episode_index=12,
        nominal_distance_m=0.268,
        level_cfg=nominal,
    )
    assert sample["initial_distance_m"] == 0.268
    assert sample["initial_pitch_rad"] == 0.0
    assert sample["friction"] == 1.0
    assert sample["actuator_delay_steps"] == 0
    assert sample["sensor_noise_std"] == 0.0
    assert sample["obstacle_observation_noise"] == [0.0, 0.0, 0.0, 0.0]


def test_reset_geometry_enforces_distance_and_clearance_without_terminal_pose() -> None:
    relative = torch.tensor(
        [
            [[0.30, 0.2, -0.20], [0.29, -0.2, -0.19], [-0.30, 0.2, -0.21], [-0.29, -0.2, -0.20]],
            [[0.31, 0.2, -0.18], [0.30, -0.2, -0.17], [-0.28, 0.2, -0.22], [-0.27, -0.2, -0.21]],
        ],
        dtype=torch.float32,
    )
    distance = torch.tensor([0.25, 0.29])
    radius = torch.tensor([0.10, 0.11])
    root_xz = cache_independent_reset_root_xz(
        obstacle_front_x_m=0.75,
        desired_distance_m=distance,
        desired_wheel_relative_m=relative,
        wheel_radius_m=radius,
    )
    torch.testing.assert_close(
        root_xz[:, 0] + relative[:, :, 0].amax(dim=1),
        0.75 - distance,
    )
    torch.testing.assert_close(
        root_xz[:, 1] + relative[:, :, 2].amin(dim=1),
        radius + 0.002,
    )
