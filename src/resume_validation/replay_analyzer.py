from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .actuator_mapping import SERVO_JOINT_NAMES, WHEEL_JOINT_NAMES
from .replay_loader import ReplayStep, flatten_events, load_jsonl, load_replay
from .source_audit import sha256_file


def analyze_replay(path: str | Path) -> dict[str, Any]:
    path = Path(path).resolve()
    rows = load_jsonl(path)
    steps = load_replay(path)
    duplicate_commands = 0
    last_command: str | None = None
    event_kinds: Counter[str] = Counter()
    zero_duration_steps: list[int] = []
    long_idle_steps: list[int] = []
    snapshot_mismatches: list[dict[str, Any]] = []
    range_values: dict[str, list[float]] = {
        name: [] for name in (*SERVO_JOINT_NAMES, *WHEEL_JOINT_NAMES)
    }
    for row, step in zip(rows, steps):
        if step.duration_s <= 0.0:
            zero_duration_steps.append(step.index)
        if step.duration_s > 30.0:
            long_idle_steps.append(step.index)
        for event, raw_event in zip(step.events, row.get("events") or []):
            event_kinds[event.kind] += 1
            if event.command == last_command:
                duplicate_commands += 1
            last_command = event.command
            reconstructed = {
                "servos": event.servo_targets_deg,
                "wheels": event.wheel_targets_rad_s,
            }
            snapshot = raw_event.get("command_state_after") or {}
            if any(
                float((snapshot.get(group) or {}).get(name, 0.0))
                != float(reconstructed[group][name])
                for group, names in (
                    ("servos", SERVO_JOINT_NAMES),
                    ("wheels", WHEEL_JOINT_NAMES),
                )
                for name in names
            ):
                snapshot_mismatches.append(
                    {
                        "step": step.index,
                        "event_index": event.event_index,
                        "command": event.command,
                    }
                )
            for name, value in event.servo_targets_deg.items():
                range_values[name].append(float(value))
            for name, value in event.wheel_targets_rad_s.items():
                range_values[name].append(float(value))
    fast_no_cap = flatten_events(steps, max_idle_gap_s=1.0e12)
    fast_cap_1s = flatten_events(steps, max_idle_gap_s=1.0)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "height_m": sorted({step.height_m for step in steps}),
        "step_count": len(steps),
        "event_count": sum(len(step.events) for step in steps),
        "dispatched_command_count": sum(
            len(event.playback_commands) for step in steps for event in step.events
        ),
        "recorded_duration_s": sum(step.duration_s for step in steps),
        "playback_profiles": {
            "raw": {
                "duration_s": sum(step.duration_s for step in steps),
                "state_event_count": sum(len(step.events) for step in steps),
            },
            "fast_no_idle_cap": {
                "duration_s": max((event.time_s for event in fast_no_cap), default=0.0) + 0.05,
                "state_event_count": len(fast_no_cap),
            },
            "fast_1s_idle_cap": {
                "duration_s": max((event.time_s for event in fast_cap_1s), default=0.0) + 0.05,
                "state_event_count": len(fast_cap_1s),
            },
            "note": "expanded_commands dispatch at the same event timestamp; state_event_count is smaller than dispatched_command_count",
        },
        "zero_duration_steps": zero_duration_steps,
        "long_idle_steps_gt_30s": long_idle_steps,
        "adjacent_duplicate_command_count": duplicate_commands,
        "event_kinds": dict(event_kinds),
        "recorded_ranges": {
            name: [min(values), max(values)] for name, values in range_values.items() if values
        },
        "state_reconstruction": {
            "semantics": "dispatch expanded_commands when present, otherwise command",
            "stale_event_snapshot_count": len(snapshot_mismatches),
            "stale_event_snapshots": snapshot_mismatches,
        },
        "command_sequence": [
            {
                "step": step.index,
                "duration_s": step.duration_s,
                "commands": [event.command for event in step.events],
            }
            for step in steps
        ],
    }
