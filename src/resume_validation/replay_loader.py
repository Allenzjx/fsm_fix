from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .actuator_mapping import REPLAY_COMMAND_LIMITS_DEG, SERVO_JOINT_NAMES, WHEEL_JOINT_NAMES


WHEEL_SHORT_NAMES = {
    "fl": "front_left_ankle",
    "fr": "front_right_ankle",
    "rl": "rear_left_ankle",
    "rr": "rear_right_ankle",
}
SERVO_GROUPS = {
    "fl": ("front_left_hip", "front_left_knee"),
    "fr": ("front_right_hip", "front_right_knee"),
    "rl": ("rear_left_hip", "rear_left_knee"),
    "rr": ("rear_right_hip", "rear_right_knee"),
    "front_left": ("front_left_hip", "front_left_knee"),
    "front_right": ("front_right_hip", "front_right_knee"),
    "rear_left": ("rear_left_hip", "rear_left_knee"),
    "rear_right": ("rear_right_hip", "rear_right_knee"),
    "front": ("front_left_hip", "front_left_knee", "front_right_hip", "front_right_knee"),
    "rear": ("rear_left_hip", "rear_left_knee", "rear_right_hip", "rear_right_knee"),
    "left": ("front_left_hip", "front_left_knee", "rear_left_hip", "rear_left_knee"),
    "right": ("front_right_hip", "front_right_knee", "rear_right_hip", "rear_right_knee"),
    "hips": ("front_left_hip", "front_right_hip", "rear_left_hip", "rear_right_hip"),
    "hip": ("front_left_hip", "front_right_hip", "rear_left_hip", "rear_right_hip"),
    "knees": ("front_left_knee", "front_right_knee", "rear_left_knee", "rear_right_knee"),
    "knee": ("front_left_knee", "front_right_knee", "rear_left_knee", "rear_right_knee"),
    "all": SERVO_JOINT_NAMES,
}
SERVO_SHORT_NAMES = {
    "fl_hip": "front_left_hip",
    "fl_knee": "front_left_knee",
    "fr_hip": "front_right_hip",
    "fr_knee": "front_right_knee",
    "rl_hip": "rear_left_hip",
    "rl_knee": "rear_left_knee",
    "rr_hip": "rear_right_hip",
    "rr_knee": "rear_right_knee",
}


@dataclass(frozen=True)
class ReplayEvent:
    step_index: int
    event_index: int
    time_s: float
    command: str
    kind: str
    servo_targets_deg: dict[str, float]
    wheel_targets_rad_s: dict[str, float]
    playback_commands: tuple[str, ...]


@dataclass(frozen=True)
class ReplayStep:
    index: int
    height_m: float
    duration_s: float
    name: str
    events: tuple[ReplayEvent, ...]
    raw: dict[str, Any]


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, text in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not text.strip():
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: expected an object")
        rows.append(row)
    return rows


def _float_dict(values: Any) -> dict[str, float]:
    return {str(key): float(value) for key, value in dict(values or {}).items()}


def _command_state(values: Any) -> dict[str, dict[str, float]]:
    source = values if isinstance(values, dict) else {}
    servos = {name: 0.0 for name in SERVO_JOINT_NAMES}
    wheels = {name: 0.0 for name in WHEEL_JOINT_NAMES}
    for name, value in dict(source.get("servos") or {}).items():
        resolved = SERVO_SHORT_NAMES.get(str(name).lower(), str(name).lower())
        if resolved in servos:
            servos[resolved] = float(value)
    for name, value in dict(source.get("wheels") or {}).items():
        resolved = WHEEL_SHORT_NAMES.get(str(name).lower(), str(name).lower())
        if resolved in wheels:
            wheels[resolved] = float(value)
    return {"servos": servos, "wheels": wheels}


def event_playback_commands(event: dict[str, Any]) -> tuple[str, ...]:
    """Return commands dispatched by the original height-replay implementation."""
    expanded = event.get("expanded_commands") or event.get("playback_commands") or []
    if isinstance(expanded, str):
        expanded = [expanded]
    if isinstance(expanded, list) and expanded:
        return tuple(str(command).strip() for command in expanded if str(command).strip())
    command = str(event.get("command", "")).strip()
    return (command,) if command else ()


def _set_all_wheels(state: dict[str, dict[str, float]], value: float) -> None:
    for name in WHEEL_JOINT_NAMES:
        state["wheels"][name] = float(value)


def _apply_command_to_state(state: dict[str, dict[str, float]], command: str) -> None:
    """Mirror the reference sequence_model command-state transition semantics."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return
    if not tokens:
        return
    verb = tokens[0].lower()
    try:
        if verb in {"servo", "angle"}:
            if len(tokens) == 4 and tokens[2].lower() in {"hip", "knee"}:
                targets = tuple(
                    name for name in SERVO_GROUPS.get(tokens[1].lower(), ())
                    if name.endswith(f"_{tokens[2].lower()}")
                )
                value = float(tokens[3])
            elif len(tokens) == 3:
                key = tokens[1].lower()
                targets = SERVO_GROUPS.get(key, (SERVO_SHORT_NAMES.get(key, key),))
                value = float(tokens[2])
            else:
                return
            for target in targets:
                if target not in state["servos"]:
                    continue
                part = "knee" if target.endswith("_knee") else "hip"
                lower, upper = REPLAY_COMMAND_LIMITS_DEG[part]
                state["servos"][target] = max(lower, min(upper, value))
        elif verb in {"wheel", "wheels", "speed"}:
            args = tokens[1:]
            if verb in {"wheels", "speed"} or (
                verb == "wheel" and len(args) == 2 and _is_float(args[0])
            ):
                if len(args) == 2:
                    left, right = float(args[0]), float(args[1])
                    state["wheels"]["front_left_ankle"] = left
                    state["wheels"]["rear_left_ankle"] = left
                    state["wheels"]["front_right_ankle"] = right
                    state["wheels"]["rear_right_ankle"] = right
            elif verb == "wheel" and args:
                sub = args[0].lower()
                if sub == "stop":
                    _set_all_wheels(state, 0.0)
                elif sub == "all" and len(args) == 2:
                    _set_all_wheels(state, float(args[1]))
                elif len(args) == 2:
                    target = WHEEL_SHORT_NAMES.get(sub, sub)
                    if target in state["wheels"]:
                        state["wheels"][target] = float(args[1])
        elif verb == "w":
            _set_all_wheels(state, 1.0)
        elif verb == "s":
            _set_all_wheels(state, -1.0)
        elif verb in {"x", "stop"}:
            _set_all_wheels(state, 0.0)
        elif verb == "home":
            for name in SERVO_JOINT_NAMES:
                state["servos"][name] = 0.0
            _set_all_wheels(state, 0.0)
    except (TypeError, ValueError):
        # The reference implementation also ignores malformed commands.
        return


def _is_float(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def parse_steps(rows: Iterable[dict[str, Any]]) -> list[ReplayStep]:
    parsed: list[ReplayStep] = []
    for position, row in enumerate(rows, 1):
        duration = float(row.get("duration", 0.0))
        if duration < 0.0:
            raise ValueError(f"Step {position} has negative duration")
        events: list[ReplayEvent] = []
        # Event snapshots in older accepted logs are not uniformly post-command:
        # ordinary UI commands may carry a stale "after" snapshot.  The reference
        # playback dispatches command/expanded_commands, so reconstruct the state.
        state = _command_state(row.get("command_state_before"))
        for event_index, event in enumerate(row.get("events") or []):
            time_s = float(event.get("time", 0.0))
            if time_s < 0.0 or time_s > duration + 1e-6:
                raise ValueError(f"Step {position} event {event_index} time {time_s} outside [0, {duration}]")
            commands = event_playback_commands(event)
            for command in commands:
                _apply_command_to_state(state, command)
            events.append(
                ReplayEvent(
                    step_index=int(row.get("index", position)),
                    event_index=event_index,
                    time_s=time_s,
                    command=str(event.get("command", "")),
                    kind=str(event.get("kind", "")),
                    servo_targets_deg=dict(state["servos"]),
                    wheel_targets_rad_s=dict(state["wheels"]),
                    playback_commands=commands,
                )
            )
        parsed.append(
            ReplayStep(
                index=int(row.get("index", position)),
                height_m=float(row.get("height_m", float(row.get("height_cm", 0.0)) / 100.0)),
                duration_s=duration,
                name=str(row.get("name", f"step_{position:03d}")),
                events=tuple(sorted(events, key=lambda item: (item.time_s, item.event_index))),
                raw=row,
            )
        )
    return parsed


def load_replay(path: str | Path) -> list[ReplayStep]:
    return parse_steps(load_jsonl(path))


def flatten_events(
    steps: Iterable[ReplayStep],
    *,
    max_idle_gap_s: float | None = None,
    trailing_pad_s: float = 0.05,
    preserve_wheel_active_gaps: bool = False,
) -> list[ReplayEvent]:
    """Flatten steps using the reference player's raw or fast timing.

    ``max_idle_gap_s=None`` is exact raw timing. Supplying a gap selects the
    reference fast profile: the first motion event in each step starts at zero,
    each subsequent inter-event gap is capped independently, and a short
    trailing pad separates steps.  When ``preserve_wheel_active_gaps`` is set,
    an interval whose held command has any non-zero wheel speed is never
    shortened.  This preserves wheel angle/travel without exceeding the source
    wheel-speed command.
    """
    flattened: list[ReplayEvent] = []
    offset = 0.0
    for step in steps:
        if max_idle_gap_s is None:
            timed_events = [(event, event.time_s) for event in step.events]
            effective_duration = step.duration_s
        else:
            usable = [
                event for event in step.events
                if event.command.strip().split(maxsplit=1)[0].lower() not in {"record_start", "record_stop"}
            ]
            first_time = usable[0].time_s if usable else 0.0
            previous = 0.0
            compressed = 0.0
            timed_events: list[tuple[ReplayEvent, float]] = []
            previous_event: ReplayEvent | None = None
            for event in usable:
                shifted = max(0.0, event.time_s - first_time)
                gap = max(0.0, shifted - previous)
                wheel_active = (
                    preserve_wheel_active_gaps
                    and previous_event is not None
                    and any(abs(value) > 1.0e-12 for value in previous_event.wheel_targets_rad_s.values())
                )
                compressed += gap if wheel_active else min(gap, max(0.0, float(max_idle_gap_s)))
                previous = shifted
                timed_events.append((event, compressed))
                previous_event = event
            effective_duration = compressed + max(0.0, float(trailing_pad_s))
        for event, local_time in timed_events:
            flattened.append(
                ReplayEvent(
                    step_index=event.step_index,
                    event_index=event.event_index,
                    time_s=offset + local_time,
                    command=event.command,
                    kind=event.kind,
                    servo_targets_deg=event.servo_targets_deg,
                    wheel_targets_rad_s=event.wheel_targets_rad_s,
                    playback_commands=event.playback_commands,
                )
            )
        offset += effective_duration
    return flattened


def playback_scaled_event(event: ReplayEvent, speed_scale: float, preserve_wheel_distance: bool, max_wheel_speed: float) -> ReplayEvent:
    if speed_scale <= 0.0:
        raise ValueError("speed_scale must be positive")
    wheel_targets = dict(event.wheel_targets_rad_s)
    if preserve_wheel_distance:
        wheel_targets = {
            name: max(-max_wheel_speed, min(max_wheel_speed, value * speed_scale))
            for name, value in wheel_targets.items()
        }
    return ReplayEvent(
        step_index=event.step_index,
        event_index=event.event_index,
        time_s=event.time_s / speed_scale,
        command=event.command,
        kind=event.kind,
        servo_targets_deg=dict(event.servo_targets_deg),
        wheel_targets_rad_s=wheel_targets,
        playback_commands=event.playback_commands,
    )
