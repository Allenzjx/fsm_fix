from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Iterable

from .actuator_mapping import SERVO_JOINT_NAMES, WHEEL_JOINT_NAMES
from .replay_loader import ReplayEvent, ReplayStep, flatten_events


@dataclass(frozen=True)
class CommandReference:
    normalized_time: float
    servo_deg: dict[str, float]
    wheel_rad_s: dict[str, float]
    source_step: int
    source_command: str


@dataclass(frozen=True)
class ReferenceTrajectory:
    height_m: float
    duration_s: float
    samples: tuple[CommandReference, ...]

    def at(self, normalized_time: float) -> CommandReference:
        if not self.samples:
            raise ValueError("Reference trajectory is empty")
        u = max(0.0, min(1.0, float(normalized_time)))
        times = [sample.normalized_time for sample in self.samples]
        right = bisect.bisect_right(times, u)
        if right <= 0:
            return self.samples[0]
        if right >= len(self.samples):
            return self.samples[-1]
        a, b = self.samples[right - 1], self.samples[right]
        return CommandReference(
            normalized_time=u,
            # The accepted events are actuator target updates, not samples of a
            # smooth geometric curve. Interpolating between unrelated manual
            # waypoints can sweep a link through the obstacle. Preserve their
            # zero-order-hold semantics; the physical drive supplies dynamics.
            servo_deg=dict(a.servo_deg),
            wheel_rad_s=dict(a.wheel_rad_s),
            source_step=a.source_step,
            source_command=f"hold({a.source_command!r})",
        )


def trajectory_from_replay(
    steps: Iterable[ReplayStep],
    *,
    max_idle_gap_s: float = 5.0,
    playback_speed: float = 1.0,
    preserve_wheel_distance: bool = True,
) -> ReferenceTrajectory:
    steps = list(steps)
    if not steps:
        raise ValueError("Cannot build trajectory from an empty replay")
    events = flatten_events(
        steps,
        max_idle_gap_s=max_idle_gap_s,
        preserve_wheel_active_gaps=preserve_wheel_distance,
    )
    total = (
        max((event.time_s for event in events), default=0.0)
        + 0.05
    ) / playback_speed
    if total <= 0.0:
        raise ValueError("Replay duration must be positive")
    servo = {name: 0.0 for name in SERVO_JOINT_NAMES}
    wheels = {name: 0.0 for name in WHEEL_JOINT_NAMES}
    samples = [CommandReference(0.0, dict(servo), dict(wheels), 0, "initial")]
    for event in events:
        servo.update(event.servo_targets_deg)
        wheels.update(event.wheel_targets_rad_s)
        event_time = event.time_s / playback_speed
        samples.append(
            CommandReference(
                normalized_time=max(0.0, min(1.0, event_time / total)),
                servo_deg=dict(servo),
                wheel_rad_s=dict(wheels),
                source_step=event.step_index,
                source_command=event.command,
            )
        )
    samples.append(CommandReference(1.0, dict(servo), dict(wheels), steps[-1].index, "final"))
    return ReferenceTrajectory(steps[0].height_m, total, tuple(samples))


def interpolate_height(
    low: ReferenceTrajectory,
    high: ReferenceTrajectory,
    target_height_m: float,
    normalized_time: float,
) -> CommandReference:
    if high.height_m <= low.height_m:
        raise ValueError("high trajectory height must exceed low trajectory height")
    alpha = (float(target_height_m) - low.height_m) / (high.height_m - low.height_m)
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("target height is outside the interpolation interval")
    a, b = low.at(normalized_time), high.at(normalized_time)
    return CommandReference(
        normalized_time=normalized_time,
        servo_deg={name: a.servo_deg[name] + alpha * (b.servo_deg[name] - a.servo_deg[name]) for name in SERVO_JOINT_NAMES},
        wheel_rad_s={name: a.wheel_rad_s[name] + alpha * (b.wheel_rad_s[name] - a.wheel_rad_s[name]) for name in WHEEL_JOINT_NAMES},
        source_step=-1,
        source_command=f"height_interpolation_{low.height_m:.3f}_{high.height_m:.3f}",
    )
