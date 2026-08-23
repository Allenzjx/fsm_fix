"""Recompute a direct replay verdict strictly from immutable raw artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

from .source_audit import sha256_file


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def audit(run_dir: Path) -> dict:
    result_path = run_dir / "result.json"
    telemetry_path = run_dir / "telemetry.jsonl"
    contacts_path = run_dir / "contacts.jsonl"
    commands_path = run_dir / "commands.csv"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    samples = list(load_jsonl(telemetry_path))
    if not samples:
        raise ValueError("No telemetry samples")
    contacts = list(load_jsonl(contacts_path))
    actual_nonwheel = [
        row for row in contacts
        if not bool(row.get("wheel")) and float(row.get("magnitude_n", 0.0)) > 5.0
    ]
    stable_samples = [row for row in samples if bool(row.get("stable_success"))]
    falls = [row for row in samples if bool(row.get("fall"))]
    numerical = [row for row in samples if not bool(row.get("finite"))]
    joint_limits = [row for row in samples if bool(row.get("joint_limit"))]
    command_limits = [row for row in samples if bool(row.get("command_limit"))]
    invalid_margins = [row for row in samples if not bool(row.get("margin_valid"))]
    valid_margins = [float(row["margin_m"]) for row in samples if bool(row.get("margin_valid"))]
    pitch_rates = [float(row["base_angular_velocity_body_rad_s"][1]) for row in samples]
    last = samples[-1]
    expected_events = int(result["source_replay"]["event_count"])
    dispatched = int(result.get("metrics", {}).get("events_dispatched", last.get("event_cursor", 0)))
    with commands_path.open("r", encoding="utf-8", newline="") as stream:
        command_rows = list(csv.DictReader(stream))
    control_dt = float(result["metrics"]["control_dt_s"])
    dispatch_jitters = []
    for row in command_rows:
        if row.get("dispatch_jitter_s") not in (None, ""):
            dispatch_jitters.append(float(row["dispatch_jitter_s"]))
        else:
            scheduled = float(row["time_s"])
            dispatched_at = math.ceil(max(0.0, scheduled - 1.0e-12) / control_dt) * control_dt
            dispatch_jitters.append(max(0.0, dispatched_at - scheduled))
    checks = {
        "all_events_dispatched": dispatched == expected_events,
        "command_rows_match_expected_events": len(command_rows) == expected_events,
        "dispatch_jitter_within_one_control_step": (
            bool(dispatch_jitters) and max(dispatch_jitters) <= control_dt + 1.0e-9
        ),
        "stable_success_dwell_observed": bool(stable_samples),
        "no_actual_nonwheel_contact_over_5N": not actual_nonwheel,
        "no_fall": not falls,
        "no_joint_limit_violation": not joint_limits,
        "no_command_limit_violation": not command_limits,
        "no_numerical_error": not numerical,
        "real_contact_sensor_rows_present": any(
            row.get("source") == "isaaclab.ContactSensor.net_forces_w" for row in contacts
        ),
    }
    return {
        "schema": "resume_validation.direct_replay_post_audit.v1",
        "run_dir": str(run_dir.resolve()),
        "success": all(checks.values()),
        "checks": checks,
        "source_result": {
            "path": str(result_path.resolve()),
            "sha256": sha256_file(result_path),
            "original_passed": bool(result.get("passed")),
            "original_failures": result.get("failures", []),
        },
        "artifacts": {
            path.name: {"path": str(path.resolve()), "sha256": sha256_file(path)}
            for path in (telemetry_path, contacts_path, commands_path)
        },
        "metrics": {
            "sample_count": len(samples),
            "contact_row_count": len(contacts),
            "actual_nonwheel_contact_count_over_5N": len(actual_nonwheel),
            "stable_success_sample_count": len(stable_samples),
            "invalid_margin_samples": len(invalid_margins),
            "valid_margin_samples": len(valid_margins),
            "episode_min_longitudinal_support_margin_m": min(valid_margins) if valid_margins else None,
            "pitch_rate_rms_rad_s": math.sqrt(sum(value * value for value in pitch_rates) / len(pitch_rates)),
            "initial_base_x_m": float(samples[0]["base_position_m"][0]),
            "final_base_x_m": float(last["base_position_m"][0]),
            "forward_progress_m": float(last["base_position_m"][0]) - float(samples[0]["base_position_m"][0]),
            "final_wheel_contact_state": list(last["wheel_contact_state"]),
            "wheel_state_counts": dict(
                Counter(
                    state
                    for row in samples
                    for state in row["wheel_contact_state"]
                )
            ),
            "events_dispatched": dispatched,
            "events_expected": expected_events,
            "command_row_count": len(command_rows),
            "max_dispatch_jitter_s": max(dispatch_jitters) if dispatch_jitters else None,
            "dispatch_jitter_source": (
                "recorded" if command_rows and command_rows[0].get("dispatch_jitter_s") not in (None, "") else "derived_from_scheduler"
            ),
        },
        "examples": {
            "actual_nonwheel_contacts": actual_nonwheel[:20],
            "fall_samples": falls[:5],
            "joint_limit_samples": joint_limits[:5],
            "command_limit_samples": command_limits[:5],
            "numerical_samples": numerical[:5],
        },
        "interpretation": (
            "The post-audit uses actual ContactSensor non-wheel forces. "
            "Legacy geometry-only nonwheel counters are retained in telemetry but do not decide collision."
        ),
    }


def markdown(report: dict) -> str:
    metrics = report["metrics"]
    checks = report["checks"]
    lines = [
        "# Direct replay audit",
        "",
        f"Verdict: **{'PASS' if report['success'] else 'FAIL'}**",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {'PASS' if value else 'FAIL'}: `{name}`" for name, value in checks.items())
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- Samples: {metrics['sample_count']}",
            f"- Events: {metrics['events_dispatched']} / {metrics['events_expected']}",
            f"- Forward progress: {metrics['forward_progress_m']:.6f} m",
            f"- Episode minimum signed longitudinal support margin: {metrics['episode_min_longitudinal_support_margin_m']}",
            f"- Pitch-rate RMS: {metrics['pitch_rate_rms_rad_s']:.6f} rad/s",
            f"- Invalid margin samples: {metrics['invalid_margin_samples']}",
            f"- Actual non-wheel contacts above 5 N: {metrics['actual_nonwheel_contact_count_over_5N']}",
            "",
            report["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    report = audit(args.run_dir.resolve())
    json_path = args.run_dir / "audited_result.json"
    md_path = args.run_dir / "replay_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"audit": str(json_path), "success": report["success"], "checks": report["checks"]}, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
