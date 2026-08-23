from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .source_audit import sha256_file


@dataclass(frozen=True)
class JointRecord:
    name: str
    joint_type: str
    parent: str
    child: str
    origin_xyz: tuple[float, float, float]
    origin_rpy: tuple[float, float, float]
    axis: tuple[float, float, float]
    lower: float | None
    upper: float | None
    velocity: float | None
    effort: float | None


def _vec(text: str | None, default: str = "0 0 0") -> tuple[float, float, float]:
    values = tuple(float(item) for item in (text or default).split())
    if len(values) != 3:
        raise ValueError(f"Expected a 3-vector, got {text!r}")
    return values  # type: ignore[return-value]


def parse_urdf(path: str | Path) -> dict[str, Any]:
    path = Path(path).resolve()
    root = ET.parse(path).getroot()
    links: dict[str, dict[str, Any]] = {}
    for link in root.findall("link"):
        name = link.attrib["name"]
        inertial = link.find("inertial")
        mass = None
        inertia = None
        com = None
        if inertial is not None:
            mass_node = inertial.find("mass")
            origin_node = inertial.find("origin")
            inertia_node = inertial.find("inertia")
            mass = float(mass_node.attrib["value"]) if mass_node is not None else None
            com = _vec(origin_node.attrib.get("xyz")) if origin_node is not None else (0.0, 0.0, 0.0)
            if inertia_node is not None:
                inertia = {key: float(inertia_node.attrib[key]) for key in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz")}
        links[name] = {
            "mass": mass,
            "com": com,
            "inertia": inertia,
            "has_visual": link.find("visual") is not None,
            "has_collision": link.find("collision") is not None,
        }
    joints: list[JointRecord] = []
    for joint in root.findall("joint"):
        origin = joint.find("origin")
        axis_node = joint.find("axis")
        axis = _vec(axis_node.attrib.get("xyz") if axis_node is not None else "1 0 0")
        norm = math.sqrt(sum(value * value for value in axis))
        if norm <= 0.0:
            raise ValueError(f"Joint {joint.attrib['name']} has a zero axis")
        limit = joint.find("limit")
        joints.append(
            JointRecord(
                name=joint.attrib["name"],
                joint_type=joint.attrib["type"],
                parent=joint.find("parent").attrib["link"],  # type: ignore[union-attr]
                child=joint.find("child").attrib["link"],  # type: ignore[union-attr]
                origin_xyz=_vec(origin.attrib.get("xyz")) if origin is not None else (0.0, 0.0, 0.0),
                origin_rpy=_vec(origin.attrib.get("rpy")) if origin is not None else (0.0, 0.0, 0.0),
                axis=tuple(value / norm for value in axis),
                lower=float(limit.attrib["lower"]) if limit is not None and "lower" in limit.attrib else None,
                upper=float(limit.attrib["upper"]) if limit is not None and "upper" in limit.attrib else None,
                velocity=float(limit.attrib["velocity"]) if limit is not None and "velocity" in limit.attrib else None,
                effort=float(limit.attrib["effort"]) if limit is not None and "effort" in limit.attrib else None,
            )
        )
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "robot_name": root.attrib.get("name"),
        "links": links,
        "joints": [asdict(item) for item in joints],
    }


def validate_urdf_model(model: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for name, link in model["links"].items():
        if link["mass"] is None or link["mass"] <= 0:
            failures.append(f"{name}: mass must be positive")
        if not link["has_collision"]:
            failures.append(f"{name}: collision is missing")
        inertia = link["inertia"]
        if inertia is None:
            failures.append(f"{name}: inertia is missing")
        elif min(inertia["ixx"], inertia["iyy"], inertia["izz"]) <= 0:
            failures.append(f"{name}: inertia diagonal must be positive")
    parents: dict[str, str] = {}
    for joint in model["joints"]:
        child = joint["child"]
        if child in parents:
            failures.append(f"{child}: multiple parents")
        parents[child] = joint["parent"]
        if abs(math.sqrt(sum(value * value for value in joint["axis"])) - 1.0) > 1e-9:
            failures.append(f"{joint['name']}: non-unit axis")
    for child in parents:
        seen: set[str] = set()
        node = child
        while node in parents:
            if node in seen:
                failures.append(f"cycle detected at {node}")
                break
            seen.add(node)
            node = parents[node]
    return failures
