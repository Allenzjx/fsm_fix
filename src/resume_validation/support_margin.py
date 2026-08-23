from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SupportPoint:
    position_world_m: tuple[float, float, float]
    upward_force_n: float
    valid: bool = True


@dataclass(frozen=True)
class MarginResult:
    margin_m: float | None
    valid: bool
    support_min_m: float | None
    support_max_m: float | None
    com_s_m: float
    total_upward_force_n: float
    reason: str


def longitudinal_support_margin(
    com_world_m: tuple[float, float, float],
    supports: Iterable[SupportPoint],
    *,
    travel_axis: tuple[float, float, float] = (1.0, 0.0, 0.0),
    min_span_m: float = 0.03,
    min_total_upward_force_n: float = 1.0,
) -> MarginResult:
    axis_norm = math.sqrt(sum(value * value for value in travel_axis))
    if axis_norm <= 0:
        raise ValueError("travel_axis must be non-zero")
    axis = tuple(value / axis_norm for value in travel_axis)
    com_s = sum(com_world_m[index] * axis[index] for index in range(3))
    rows = [item for item in supports if item.valid and item.upward_force_n > 0.0]
    total_force = sum(item.upward_force_n for item in rows)
    projections = [sum(item.position_world_m[index] * axis[index] for index in range(3)) for item in rows]
    if len(projections) < 2:
        return MarginResult(None, False, None, None, com_s, total_force, "fewer_than_two_valid_supports")
    support_min, support_max = min(projections), max(projections)
    if support_max - support_min < min_span_m:
        return MarginResult(None, False, support_min, support_max, com_s, total_force, "support_span_too_small")
    if total_force < min_total_upward_force_n:
        return MarginResult(None, False, support_min, support_max, com_s, total_force, "upward_force_too_small")
    margin = min(com_s - support_min, support_max - com_s)
    return MarginResult(margin, True, support_min, support_max, com_s, total_force, "")
