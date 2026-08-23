"""Audit an Isaac height-replay telemetry directory against frozen geometry.

The legacy telemetry collector supplies real ContactSensor net forces and body
positions, but its opposing-body label is intentionally conservative
(``ground_or_obstacle``).  This audit classifies the approximated contact point
against the known box top and front riser, explicitly excludes riser forces
from support, and retains every invalid sample count in the result.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .contact_processing import Contact, ContactClass, classify_contact, is_valid_support
from .source_audit import sha256_file
from .support_margin import SupportPoint, longitudinal_support_margin

WHEEL_BODIES = {
    "front_left_wheel",
    "front_right_wheel",
    "rear_left_wheel",
    "rear_right_wheel",
}


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _vector(value: str) -> tuple[float, float, float]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or len(parsed) < 3:
        raise ValueError(f"Expected JSON xyz vector, got {value!r}")
    return float(parsed[0]), float(parsed[1]), float(parsed[2])


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _finite(values: Iterable[float]) -> bool:
    return all(math.isfinite(value) for value in values)


def audit_replay_run(
    run_dir: str | Path,
    *,
    obstacle_center_x_m: float = 1.55,
    obstacle_length_m: float = 1.65,
    stable_dwell_s: float = 1.5,
    max_abs_roll_rad: float = 0.45,
    max_abs_pitch_rad: float = 0.45,
    max_angular_velocity_rad_s: float = 0.50,
    contact_force_threshold_n: float = 2.0,
    top_z_tolerance_m: float = 0.012,
    riser_x_tolerance_m: float = 0.012,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    telemetry_path = run / "telemetry_samples.csv"
    contacts_path = run / "contacts.csv"
    joints_path = run / "joint_timeseries.csv"
    metadata_path = run / "metadata.json"
    audit_path = run / "model_audit.json"
    required = [telemetry_path, contacts_path, joints_path, metadata_path, audit_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Replay telemetry directory is incomplete: {missing}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    model_audit = json.loads(audit_path.read_text(encoding="utf-8"))
    telemetry = _rows(telemetry_path)
    contacts = _rows(contacts_path)
    joints = _rows(joints_path)
    if not telemetry:
        raise ValueError("telemetry_samples.csv is empty")

    height_m = float(metadata["obstacle_height_m"])
    front_x = obstacle_center_x_m - obstacle_length_m / 2.0
    back_x = obstacle_center_x_m + obstacle_length_m / 2.0
    sensor = model_audit.get("contact_sensor") or {}
    contact_sources = sorted({row.get("source", "") for row in contacts})
    real_force_rows = sum(row.get("source") == "isaaclab.ContactSensor.net_forces_w" for row in contacts)

    contacts_by_time: dict[float, list[dict[str, str]]] = defaultdict(list)
    collision_rows: list[dict[str, Any]] = []
    class_counts: dict[str, int] = defaultdict(int)
    for row in contacts:
        time_s = _float(row.get("time_s"))
        if math.isfinite(time_s):
            contacts_by_time[time_s].append(row)
        is_wheel = _bool(row.get("wheel_contact")) or row.get("body_name") in WHEEL_BODIES
        force_n = _float(row.get("normal_force_n"), 0.0)
        contact = Contact(
            body_name=str(row.get("body_name", "")),
            point=_vector(str(row.get("contact_point_w", "[0,0,0]"))),
            force=(0.0, 0.0, force_n),
            other=str(row.get("other_body", "")),
            is_wheel=is_wheel,
        )
        contact_class = classify_contact(
            contact,
            obstacle_top_z=height_m,
            obstacle_front_x=front_x,
            top_tolerance_m=top_z_tolerance_m,
            riser_tolerance_m=riser_x_tolerance_m,
            min_upward_force_n=contact_force_threshold_n,
        )
        row["_class"] = contact_class.value
        class_counts[contact_class.value] += 1
        if contact_class in {ContactClass.BODY_COLLISION, ContactClass.LINK_COLLISION}:
            collision_rows.append(
                {
                    "time_s": time_s,
                    "body_name": contact.body_name,
                    "class": contact_class.value,
                    "normal_force_n": force_n,
                }
            )

    margin_samples: list[dict[str, Any]] = []
    invalid_margin_reasons: dict[str, int] = defaultdict(int)
    for sample in telemetry:
        time_s = _float(sample.get("time_s"))
        time_contacts = contacts_by_time.get(time_s, [])
        supports: list[SupportPoint] = []
        support_classes: list[str] = []
        for contact_row in time_contacts:
            contact_class = ContactClass(contact_row["_class"])
            force_n = _float(contact_row.get("normal_force_n"), 0.0)
            point = _vector(str(contact_row.get("contact_point_w", "[0,0,0]")))
            valid = is_valid_support(contact_class, force_n, contact_force_threshold_n)
            supports.append(SupportPoint(point, force_n, valid))
            if valid:
                support_classes.append(contact_class.value)
        margin = longitudinal_support_margin(
            (
                _float(sample.get("com_x_m")),
                _float(sample.get("com_y_m")),
                _float(sample.get("com_z_m")),
            ),
            supports,
            min_span_m=0.03,
            min_total_upward_force_n=contact_force_threshold_n,
        )
        if not margin.valid:
            invalid_margin_reasons[margin.reason] += 1
        margin_samples.append(
            {
                "time_s": time_s,
                "margin_m": margin.margin_m,
                "margin_valid": margin.valid,
                "support_min_m": margin.support_min_m,
                "support_max_m": margin.support_max_m,
                "valid_support_classes": support_classes,
                "pitch_rate_rad_s": _float(sample.get("base_wy_rad_s")),
            }
        )

    final_time = max(_float(row.get("time_s")) for row in telemetry)
    dwell_rows = [row for row in telemetry if _float(row.get("time_s")) >= final_time - stable_dwell_s]
    dwell_evaluations: list[dict[str, Any]] = []
    for sample in dwell_rows:
        time_s = _float(sample.get("time_s"))
        wheel_contacts: dict[str, dict[str, str]] = {}
        for contact_row in contacts_by_time.get(time_s, []):
            body_name = str(contact_row.get("body_name", ""))
            if body_name in WHEEL_BODIES and _bool(contact_row.get("active", True)):
                wheel_contacts[body_name] = contact_row
        wheel_state: dict[str, Any] = {}
        all_wheels_valid = len(wheel_contacts) == len(WHEEL_BODIES)
        for wheel in sorted(WHEEL_BODIES):
            row = wheel_contacts.get(wheel)
            if row is None:
                wheel_state[wheel] = {"present": False}
                continue
            point = _vector(str(row.get("contact_point_w", "[0,0,0]")))
            contact_class = ContactClass(row["_class"])
            beyond_front = point[0] > front_x + 0.005
            on_top = contact_class == ContactClass.STEP_TOP and point[0] <= back_x + 0.02
            safely_clear = point[0] > back_x + 0.05 and contact_class == ContactClass.LOWER_GROUND
            valid = beyond_front and (on_top or safely_clear)
            all_wheels_valid = all_wheels_valid and valid
            wheel_state[wheel] = {
                "present": True,
                "point_w_m": point,
                "class": contact_class.value,
                "beyond_front": beyond_front,
                "on_top": on_top,
                "safely_clear": safely_clear,
                "valid": valid,
            }
        angular_velocity = math.sqrt(
            sum(_float(sample.get(name)) ** 2 for name in ("base_wx_rad_s", "base_wy_rad_s", "base_wz_rad_s"))
        )
        finite = _finite(
            _float(sample.get(name))
            for name in (
                "base_x_m",
                "base_z_m",
                "com_x_m",
                "base_roll_rad",
                "base_pitch_rad",
                "base_wx_rad_s",
                "base_wy_rad_s",
                "base_wz_rad_s",
            )
        )
        stable = (
            finite
            and all_wheels_valid
            and _float(sample.get("base_x_m")) > front_x
            and _float(sample.get("com_x_m")) > front_x
            and abs(_float(sample.get("base_roll_rad"))) <= max_abs_roll_rad
            and abs(_float(sample.get("base_pitch_rad"))) <= max_abs_pitch_rad
            and angular_velocity <= max_angular_velocity_rad_s
        )
        dwell_evaluations.append(
            {
                "time_s": time_s,
                "stable": stable,
                "angular_velocity_rad_s": angular_velocity,
                "wheel_state": wheel_state,
            }
        )

    last = telemetry[-1]
    replay_finished = str(last.get("replay_state", "")).lower() in {"finished", "complete", "completed", "idle"}
    sequence_success = _bool(last.get("sequence_success"))
    dwell_duration = (
        max(row["time_s"] for row in dwell_evaluations) - min(row["time_s"] for row in dwell_evaluations)
        if len(dwell_evaluations) >= 2
        else 0.0
    )
    stable_dwell = dwell_duration >= stable_dwell_s - 0.05 and all(row["stable"] for row in dwell_evaluations)
    joint_limit_rows = [
        {
            "time_s": _float(row.get("time_s")),
            "joint_name": row.get("joint_name"),
            "position_rad": _float(row.get("position_rad")),
        }
        for row in joints
        if _bool(row.get("position_limit_warning"))
    ]
    valid_margins = [row["margin_m"] for row in margin_samples if row["margin_valid"]]
    pitch_rates = [_float(row.get("base_wy_rad_s")) for row in telemetry]
    checks = {
        "contact_sensor_requested": bool(sensor.get("requested")),
        "contact_sensor_available": bool(sensor.get("available")),
        "real_contact_force_rows_present": real_force_rows > 0,
        "replay_finished": replay_finished,
        "replay_reported_sequence_success": sequence_success,
        "stable_dwell": stable_dwell,
        "no_body_or_link_collision": not collision_rows,
        "no_joint_limit_warning": not joint_limit_rows,
        "all_telemetry_finite": all(
            _finite(
                _float(row.get(name))
                for name in (
                    "base_x_m",
                    "base_y_m",
                    "base_z_m",
                    "com_x_m",
                    "com_y_m",
                    "com_z_m",
                    "base_roll_rad",
                    "base_pitch_rad",
                    "base_wy_rad_s",
                )
            )
            for row in telemetry
        ),
    }
    return {
        "schema": "resume_validation.replay_physical_audit.v1",
        "run_dir": str(run),
        "success": all(checks.values()),
        "checks": checks,
        "asset": {
            "path": metadata.get("robot_usd"),
            "sha256": sha256_file(metadata["robot_usd"]) if Path(str(metadata.get("robot_usd", ""))).exists() else None,
        },
        "source_files": {
            path.name: {"path": str(path), "sha256": sha256_file(path)}
            for path in required
        },
        "geometry": {
            "obstacle_height_m": height_m,
            "obstacle_front_x_m": front_x,
            "obstacle_back_x_m": back_x,
            "stable_dwell_s": stable_dwell_s,
        },
        "contact_data": {
            "sensor": sensor,
            "sources": contact_sources,
            "real_force_rows": real_force_rows,
            "class_counts": dict(sorted(class_counts.items())),
            "collision_count": len(collision_rows),
            "collision_examples": collision_rows[:20],
        },
        "metrics": {
            "telemetry_sample_count": len(telemetry),
            "contact_row_count": len(contacts),
            "duration_s": final_time - min(_float(row.get("time_s")) for row in telemetry),
            "initial_base_x_m": _float(telemetry[0].get("base_x_m")),
            "final_base_x_m": _float(last.get("base_x_m")),
            "forward_progress_m": _float(last.get("base_x_m")) - _float(telemetry[0].get("base_x_m")),
            "episode_min_longitudinal_support_margin_m": min(valid_margins) if valid_margins else None,
            "valid_margin_samples": len(valid_margins),
            "invalid_margin_samples": len(margin_samples) - len(valid_margins),
            "invalid_margin_reasons": dict(sorted(invalid_margin_reasons.items())),
            "pitch_rate_rms_rad_s": math.sqrt(sum(value * value for value in pitch_rates) / len(pitch_rates)),
            "max_abs_pitch_rad": max(abs(_float(row.get("base_pitch_rad"))) for row in telemetry),
            "max_abs_roll_rad": max(abs(_float(row.get("base_roll_rad"))) for row in telemetry),
            "dwell_observed_s": dwell_duration,
        },
        "final_dwell": dwell_evaluations,
        "joint_limit_warning_count": len(joint_limit_rows),
        "joint_limit_examples": joint_limit_rows[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_replay_run(args.run_dir)
    output = args.output or (args.run_dir / "resume_validation_audit.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "success": result["success"], "checks": result["checks"]}, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
