from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


class IKError(ValueError):
    pass


@dataclass(frozen=True)
class IKResult:
    hip_rad: float
    knee_rad: float
    branch: str
    reachable: bool
    condition: float


@dataclass(frozen=True)
class PlanarLegKinematics:
    """Planar two-revolute wheel-center model.

    ``knee_zero_rad`` represents the fixed URDF angle between the lower-link
    vector and the conventional two-link x axis. Inputs and outputs are raw
    articulation coordinates relative to the imported standing pose.
    """

    upper_length_m: float
    lower_length_m: float
    hip_zero_rad: float = 0.0
    knee_zero_rad: float = 0.0

    def __post_init__(self) -> None:
        if self.upper_length_m <= 0.0 or self.lower_length_m <= 0.0:
            raise ValueError("Link lengths must be positive")

    def fk(self, hip_rad: float, knee_rad: float) -> tuple[float, float]:
        q1 = float(hip_rad) + self.hip_zero_rad
        q2 = float(knee_rad) + self.knee_zero_rad
        x = self.upper_length_m * math.cos(q1) + self.lower_length_m * math.cos(q1 + q2)
        z = self.upper_length_m * math.sin(q1) + self.lower_length_m * math.sin(q1 + q2)
        return x, z

    def jacobian(self, hip_rad: float, knee_rad: float) -> tuple[tuple[float, float], tuple[float, float]]:
        q1 = float(hip_rad) + self.hip_zero_rad
        q2 = float(knee_rad) + self.knee_zero_rad
        return (
            (
                -self.upper_length_m * math.sin(q1) - self.lower_length_m * math.sin(q1 + q2),
                -self.lower_length_m * math.sin(q1 + q2),
            ),
            (
                self.upper_length_m * math.cos(q1) + self.lower_length_m * math.cos(q1 + q2),
                self.lower_length_m * math.cos(q1 + q2),
            ),
        )

    def condition_number(self, hip_rad: float, knee_rad: float) -> float:
        try:
            import numpy as np
            return float(np.linalg.cond(np.asarray(self.jacobian(hip_rad, knee_rad), dtype=float)))
        except Exception:
            determinant = self.upper_length_m * self.lower_length_m * math.sin(float(knee_rad) + self.knee_zero_rad)
            return math.inf if abs(determinant) < 1e-12 else 1.0 / abs(determinant)

    def ik_candidates(self, x_m: float, z_m: float, tolerance_m: float = 1e-10) -> tuple[IKResult, IKResult]:
        x, z = float(x_m), float(z_m)
        l1, l2 = self.upper_length_m, self.lower_length_m
        radius_sq = x * x + z * z
        cosine = (radius_sq - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
        if cosine < -1.0 - tolerance_m or cosine > 1.0 + tolerance_m:
            raise IKError(f"Unreachable wheel center ({x:.6f}, {z:.6f}); cosine={cosine:.9f}")
        cosine = max(-1.0, min(1.0, cosine))
        magnitude = math.acos(cosine)
        results: list[IKResult] = []
        for branch, q2_effective in (("elbow_down", magnitude), ("elbow_up", -magnitude)):
            q1 = math.atan2(z, x) - math.atan2(l2 * math.sin(q2_effective), l1 + l2 * math.cos(q2_effective))
            hip = q1 - self.hip_zero_rad
            knee = q2_effective - self.knee_zero_rad
            results.append(IKResult(hip, knee, branch, True, self.condition_number(hip, knee)))
        return results[0], results[1]

    def ik(
        self,
        x_m: float,
        z_m: float,
        *,
        previous: tuple[float, float] | None = None,
        joint_limits: tuple[tuple[float, float], tuple[float, float]] | None = None,
    ) -> IKResult:
        candidates = list(self.ik_candidates(x_m, z_m))
        if joint_limits is not None:
            candidates = [
                item
                for item in candidates
                if joint_limits[0][0] <= item.hip_rad <= joint_limits[0][1]
                and joint_limits[1][0] <= item.knee_rad <= joint_limits[1][1]
            ]
        if not candidates:
            raise IKError("No IK branch satisfies the configured safe joint limits")
        if previous is None:
            return candidates[0]
        return min(
            candidates,
            key=lambda item: (item.hip_rad - previous[0]) ** 2 + (item.knee_rad - previous[1]) ** 2,
        )


def rms_position_error(model: PlanarLegKinematics, configurations: Iterable[tuple[float, float]]) -> float:
    squared: list[float] = []
    previous: tuple[float, float] | None = None
    for hip, knee in configurations:
        target = model.fk(hip, knee)
        solution = model.ik(*target, previous=previous)
        rebuilt = model.fk(solution.hip_rad, solution.knee_rad)
        squared.append((target[0] - rebuilt[0]) ** 2 + (target[1] - rebuilt[1]) ** 2)
        previous = (solution.hip_rad, solution.knee_rad)
    return math.sqrt(sum(squared) / max(1, len(squared)))
