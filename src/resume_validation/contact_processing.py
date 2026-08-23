from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContactClass(str, Enum):
    NONE = "NONE"
    LOWER_GROUND = "LOWER_GROUND"
    STEP_TOP = "STEP_TOP"
    STEP_RISER = "STEP_RISER"
    STEP_EDGE_OR_AMBIGUOUS = "STEP_EDGE_OR_AMBIGUOUS"
    BODY_COLLISION = "BODY_COLLISION"
    LINK_COLLISION = "LINK_COLLISION"


@dataclass(frozen=True)
class Contact:
    body_name: str
    point: tuple[float, float, float]
    force: tuple[float, float, float]
    other: str
    is_wheel: bool = True

    @property
    def upward_force(self) -> float:
        return self.force[2]


def classify_contact(
    contact: Contact,
    *,
    obstacle_top_z: float,
    obstacle_front_x: float,
    top_tolerance_m: float,
    riser_tolerance_m: float,
    min_upward_force_n: float,
) -> ContactClass:
    if not contact.is_wheel:
        return ContactClass.BODY_COLLISION if "base" in contact.body_name.lower() else ContactClass.LINK_COLLISION
    other = contact.other.lower()
    dz = abs(contact.point[2] - obstacle_top_z)
    dx = abs(contact.point[0] - obstacle_front_x)
    # Isaac Lab's net-force ContactSensor identifies the contacted robot body
    # but not the opposing shape.  Its explicit marker is therefore
    # "ground_or_obstacle"; resolve that case geometrically before checking the
    # ordinary ground label.  This is also what prevents a riser force from
    # entering the vertical support interval.
    ambiguous_surface = "ground" in other and ("obstacle" in other or "step" in other)
    if not ambiguous_surface and "ground" in other:
        return ContactClass.LOWER_GROUND if contact.upward_force >= min_upward_force_n else ContactClass.NONE
    if not ambiguous_surface and "obstacle" not in other and "step" not in other:
        return ContactClass.NONE
    if dz <= top_tolerance_m and contact.upward_force >= min_upward_force_n:
        return ContactClass.STEP_TOP
    if dx <= riser_tolerance_m and contact.point[2] < obstacle_top_z - top_tolerance_m:
        return ContactClass.STEP_RISER
    if ambiguous_surface and abs(contact.point[2]) <= top_tolerance_m:
        return ContactClass.LOWER_GROUND if contact.upward_force >= min_upward_force_n else ContactClass.NONE
    return ContactClass.STEP_EDGE_OR_AMBIGUOUS


def is_valid_support(contact_class: ContactClass, upward_force_n: float, threshold_n: float) -> bool:
    return contact_class in {ContactClass.LOWER_GROUND, ContactClass.STEP_TOP} and upward_force_n >= threshold_n
