from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from .actuator_mapping import (
    JOINT_COMMAND_SIGN,
    SERVO_JOINT_NAMES,
    WHEEL_JOINT_NAMES,
    WHEEL_MAX_SPEED_RAD_S,
)
from .kinematics import IKError, PlanarLegKinematics

LEG_NAMES = ("front_left", "front_right", "rear_left", "rear_right")


@dataclass(frozen=True)
class ResidualBounds:
    wheel_center_x_m: float
    wheel_center_z_m: float
    wheel_speed_rad_s: float


@dataclass(frozen=True)
class ResidualResult:
    servo_deg: dict[str, float]
    wheel_rad_s: dict[str, float]
    scaled_residual: tuple[float, ...]
    saturation: tuple[bool, ...]
    ik_valid: bool
    ik_error: str


def apply_residual(
    reference_servo_deg: Mapping[str, float],
    reference_wheel_rad_s: Mapping[str, float],
    action: Sequence[float],
    *,
    leg_models: Mapping[str, PlanarLegKinematics],
    bounds: ResidualBounds,
    servo_limits_deg: Mapping[str, tuple[float, float]],
) -> ResidualResult:
    if len(action) != 12:
        raise ValueError(f"Expected 12 residual actions, got {len(action)}")
    clipped = tuple(max(-1.0, min(1.0, float(value))) for value in action)
    saturation = tuple(abs(float(value)) > 1.0 for value in action)
    scaled = tuple(
        clipped[index] * (
            bounds.wheel_center_x_m if index % 2 == 0 else bounds.wheel_center_z_m
        )
        if index < 8
        else clipped[index] * bounds.wheel_speed_rad_s
        for index in range(12)
    )
    # Exact bypass is intentional and tested: no round-trip numerical drift is
    # allowed to break zero-residual equivalence with the FSM baseline.
    if all(value == 0.0 for value in clipped):
        return ResidualResult(
            dict(reference_servo_deg),
            dict(reference_wheel_rad_s),
            scaled,
            saturation,
            True,
            "",
        )
    servo_out = dict(reference_servo_deg)
    previous: dict[str, tuple[float, float]] = {}
    try:
        for leg_index, leg in enumerate(LEG_NAMES):
            hip_name, knee_name = f"{leg}_hip", f"{leg}_knee"
            q1 = JOINT_COMMAND_SIGN[hip_name] * math.radians(reference_servo_deg[hip_name])
            q2 = JOINT_COMMAND_SIGN[knee_name] * math.radians(reference_servo_deg[knee_name])
            previous[leg] = (q1, q2)
            x, z = leg_models[leg].fk(q1, q2)
            target = (x + scaled[2 * leg_index], z + scaled[2 * leg_index + 1])
            hip_limit = tuple(
                JOINT_COMMAND_SIGN[hip_name] * math.radians(value)
                for value in servo_limits_deg[hip_name]
            )
            knee_limit = tuple(
                JOINT_COMMAND_SIGN[knee_name] * math.radians(value)
                for value in servo_limits_deg[knee_name]
            )
            raw_limits = (
                (min(hip_limit), max(hip_limit)),
                (min(knee_limit), max(knee_limit)),
            )
            solution = leg_models[leg].ik(*target, previous=previous[leg], joint_limits=raw_limits)
            servo_out[hip_name] = math.degrees(solution.hip_rad / JOINT_COMMAND_SIGN[hip_name])
            servo_out[knee_name] = math.degrees(solution.knee_rad / JOINT_COMMAND_SIGN[knee_name])
    except IKError as exc:
        return ResidualResult(dict(reference_servo_deg), dict(reference_wheel_rad_s), scaled, saturation, False, str(exc))
    wheels = {
        name: max(-WHEEL_MAX_SPEED_RAD_S, min(WHEEL_MAX_SPEED_RAD_S, float(reference_wheel_rad_s[name]) + scaled[8 + index]))
        for index, name in enumerate(WHEEL_JOINT_NAMES)
    }
    return ResidualResult(servo_out, wheels, scaled, saturation, True, "")
