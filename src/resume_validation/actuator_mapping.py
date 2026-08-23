from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

SERVO_JOINT_NAMES = (
    "front_left_hip", "front_left_knee",
    "front_right_hip", "front_right_knee",
    "rear_left_hip", "rear_left_knee",
    "rear_right_hip", "rear_right_knee",
)
WHEEL_JOINT_NAMES = (
    "front_left_ankle", "front_right_ankle", "rear_left_ankle", "rear_right_ankle"
)
JOINT_COMMAND_SIGN = {
    "front_left_hip": 1.0, "front_left_knee": 1.0,
    "front_right_hip": 1.0, "front_right_knee": 1.0,
    "rear_left_hip": -1.0, "rear_left_knee": -1.0,
    "rear_right_hip": -1.0, "rear_right_knee": -1.0,
}
WHEEL_FORWARD_SIGN = {
    "front_left_ankle": -1.0, "front_right_ankle": 1.0,
    "rear_left_ankle": -1.0, "rear_right_ankle": 1.0,
}
REPLAY_COMMAND_LIMITS_DEG = {"hip": (-135.0, 135.0), "knee": (-60.0, 210.0)}
WHEEL_MAX_SPEED_RAD_S = 20.0 * 2.0 * math.pi / 60.0
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
FSM_REFERENCE_MARGIN_DEG = 1.0


@dataclass(frozen=True)
class SafeLimit:
    lower: float
    upper: float
    sources: tuple[str, ...]


def joint_part(name: str) -> str:
    return "knee" if name.endswith("_knee") else "hip"


def command_to_raw_rad(joint_name: str, command_deg: float, standing_raw_rad: float) -> float:
    return float(standing_raw_rad) + JOINT_COMMAND_SIGN[joint_name] * math.radians(float(command_deg))


def raw_rad_to_command(joint_name: str, raw_rad: float, standing_raw_rad: float) -> float:
    return math.degrees((float(raw_rad) - float(standing_raw_rad)) / JOINT_COMMAND_SIGN[joint_name])


def wheel_physical_to_raw(joint_name: str, physical_rad_s: float) -> float:
    clipped = max(-WHEEL_MAX_SPEED_RAD_S, min(WHEEL_MAX_SPEED_RAD_S, float(physical_rad_s)))
    return WHEEL_FORWARD_SIGN[joint_name] * clipped


def intersect_limits(*limits: tuple[float, float]) -> tuple[float, float]:
    if not limits:
        raise ValueError("At least one limit pair is required")
    lower = max(float(item[0]) for item in limits)
    upper = min(float(item[1]) for item in limits)
    if lower > upper:
        raise ValueError(f"Empty limit intersection: {limits}")
    return lower, upper


def recorded_ranges(rows: list[dict]) -> dict[str, tuple[float, float]]:
    values: dict[str, list[float]] = {name: [] for name in (*SERVO_JOINT_NAMES, *WHEEL_JOINT_NAMES)}
    for row in rows:
        for event in row.get("events", []):
            state = event.get("command_state_after") or {}
            for name, value in (state.get("servos") or {}).items():
                if name in values:
                    values[name].append(float(value))
            for name, value in (state.get("wheels") or {}).items():
                if name in values:
                    values[name].append(float(value))
    return {name: (min(items), max(items)) for name, items in values.items() if items}


def clamp_mapping(values: Mapping[str, float], limits: Mapping[str, tuple[float, float]]) -> dict[str, float]:
    return {name: max(limits[name][0], min(limits[name][1], float(value))) for name, value in values.items()}
