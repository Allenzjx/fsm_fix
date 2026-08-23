from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class BodyCoM:
    name: str
    mass_kg: float
    position_world_m: tuple[float, float, float]


def whole_body_com(bodies: Iterable[BodyCoM]) -> tuple[float, float, float]:
    rows = list(bodies)
    total_mass = sum(item.mass_kg for item in rows)
    if not rows or not math.isfinite(total_mass) or total_mass <= 0.0:
        raise ValueError("Whole-body CoM requires finite positive mass")
    for item in rows:
        if item.mass_kg <= 0 or not all(math.isfinite(value) for value in item.position_world_m):
            raise ValueError(f"Invalid CoM sample for {item.name}")
    return tuple(
        sum(item.mass_kg * item.position_world_m[axis] for item in rows) / total_mass
        for axis in range(3)
    )  # type: ignore[return-value]
