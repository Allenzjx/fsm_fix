from __future__ import annotations

SCHEMA_VERSION = "1.0.0"

REQUIRED_STEP_FIELDS = (
    "wall_time",
    "simulation_time",
    "physics_step",
    "control_step",
    "environment_id",
    "episode_id",
    "scenario_id",
    "method",
    "training_seed",
    "environment_seed",
    "base_x",
    "base_y",
    "base_z",
    "roll",
    "pitch",
    "yaw",
    "pitch_rate",
    "com_x",
    "com_y",
    "com_z",
    "margin_m",
    "margin_valid",
    "fsm_phase",
    "reward_total",
    "termination_reason",
)

UNITS = {
    "wall_time": "s_unix",
    "simulation_time": "s",
    "base_x": "m",
    "base_y": "m",
    "base_z": "m",
    "roll": "rad",
    "pitch": "rad",
    "yaw": "rad",
    "pitch_rate": "rad/s",
    "com_x": "m",
    "com_y": "m",
    "com_z": "m",
    "margin_m": "m",
}
