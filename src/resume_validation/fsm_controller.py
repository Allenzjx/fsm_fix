from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from .fsm_trajectory import CommandReference, ReferenceTrajectory


class Phase(IntEnum):
    INIT = 0
    SETTLE = 1
    APPROACH = 2
    FIRST_CONTACT_CONFIRM = 3
    FRONT_OR_FIRST_WHEEL_LIFT = 4
    FRONT_OR_FIRST_WHEEL_PLACE = 5
    BODY_TRANSFER = 6
    REAR_OR_REMAINING_WHEEL_LIFT = 7
    REAR_OR_REMAINING_WHEEL_PLACE = 8
    RECOVER = 9
    DRIVE_CLEAR = 10
    SUCCESS = 11
    FAIL = 12


@dataclass(frozen=True)
class FSMObservation:
    elapsed_s: float
    obstacle_distance_m: float
    top_contact_count: int
    ground_contact_count: int
    stable: bool
    all_wheels_clear: bool
    front_contact: bool = False
    front_top_count: int = 0
    rear_top_count: int = 0
    failed: bool = False
    failure_reason: str = ""


@dataclass(frozen=True)
class FSMOutput:
    phase: Phase
    phase_progress: float
    reference: CommandReference
    transition_reason: str
    terminal: bool


class FSMController:
    """Contact-debounced FSM that indexes a recorded continuous reference."""

    _PHASE_WINDOWS = {
        Phase.INIT: (0.00, 0.01),
        Phase.SETTLE: (0.01, 0.04),
        Phase.APPROACH: (0.04, 0.16),
        Phase.FIRST_CONTACT_CONFIRM: (0.16, 0.20),
        Phase.FRONT_OR_FIRST_WHEEL_LIFT: (0.20, 0.38),
        Phase.FRONT_OR_FIRST_WHEEL_PLACE: (0.38, 0.50),
        Phase.BODY_TRANSFER: (0.50, 0.64),
        Phase.REAR_OR_REMAINING_WHEEL_LIFT: (0.64, 0.78),
        Phase.REAR_OR_REMAINING_WHEEL_PLACE: (0.78, 0.88),
        Phase.RECOVER: (0.88, 0.94),
        Phase.DRIVE_CLEAR: (0.94, 1.00),
    }

    def __init__(self, trajectory: ReferenceTrajectory, *, debounce_steps: int = 3, timeout_scale: float = 1.25):
        self.trajectory = trajectory
        self.debounce_steps = max(1, int(debounce_steps))
        self.timeout_s = float(trajectory.duration_s) * float(timeout_scale)
        self.reset()

    def reset(self) -> None:
        self.phase = Phase.INIT
        self._last_phase = self.phase
        self._top_debounce = 0
        self._stable_debounce = 0
        self._exit_debounce = 0
        self._transition_reason = "reset"

    @property
    def phase_one_hot(self) -> tuple[float, ...]:
        return tuple(1.0 if index == int(self.phase) else 0.0 for index in range(len(Phase)))

    def _time_phase(self, u: float) -> Phase:
        for phase, (_, upper) in self._PHASE_WINDOWS.items():
            if u <= upper:
                return phase
        return Phase.DRIVE_CLEAR

    def step(self, observation: FSMObservation) -> FSMOutput:
        if observation.failed:
            self.phase = Phase.FAIL
            self._transition_reason = observation.failure_reason or "external_failure"
        elif observation.elapsed_s >= self.timeout_s:
            self.phase = Phase.FAIL
            self._transition_reason = "fsm_timeout"
        elif self.phase not in (Phase.SUCCESS, Phase.FAIL):
            u = min(1.0, observation.elapsed_s / max(self.trajectory.duration_s, 1e-9))
            desired = self._time_phase(u)
            self._top_debounce = self._top_debounce + 1 if observation.top_contact_count > 0 else 0
            self._stable_debounce = self._stable_debounce + 1 if observation.stable else 0
            exit_condition = self._phase_exit_condition(observation)
            self._exit_debounce = self._exit_debounce + 1 if exit_condition else 0
            if desired > self.phase and self._exit_debounce >= self.debounce_steps:
                self.phase = Phase(int(self.phase) + 1)
                self._exit_debounce = 0
                self._transition_reason = "reference_progress_and_debounced_phase_exit"
            if observation.all_wheels_clear and self._stable_debounce >= self.debounce_steps:
                self.phase = Phase.SUCCESS
                self._transition_reason = "all_wheels_clear_stable_debounce"
        terminal = self.phase in (Phase.SUCCESS, Phase.FAIL)
        if terminal:
            u = 1.0
            progress = 1.0
        else:
            lower, upper = self._PHASE_WINDOWS[self.phase]
            u = min(1.0, observation.elapsed_s / max(self.trajectory.duration_s, 1e-9))
            progress = max(0.0, min(1.0, (u - lower) / max(upper - lower, 1e-9)))
        return FSMOutput(self.phase, progress, self.trajectory.at(u), self._transition_reason, terminal)

    def _phase_exit_condition(self, observation: FSMObservation) -> bool:
        if self.phase in (Phase.INIT, Phase.SETTLE):
            return True
        if self.phase in (Phase.APPROACH, Phase.FIRST_CONTACT_CONFIRM):
            return bool(observation.front_contact or observation.front_top_count > 0)
        if self.phase == Phase.FRONT_OR_FIRST_WHEEL_LIFT:
            return observation.front_top_count >= 1
        if self.phase in (Phase.FRONT_OR_FIRST_WHEEL_PLACE, Phase.BODY_TRANSFER):
            return observation.front_top_count >= 2
        if self.phase == Phase.REAR_OR_REMAINING_WHEEL_LIFT:
            return observation.rear_top_count >= 1
        if self.phase == Phase.REAR_OR_REMAINING_WHEEL_PLACE:
            return observation.rear_top_count >= 2
        if self.phase == Phase.RECOVER:
            return observation.all_wheels_clear
        if self.phase == Phase.DRIVE_CLEAR:
            return observation.all_wheels_clear and observation.stable
        return False

    def state_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.name,
            "top_debounce": self._top_debounce,
            "stable_debounce": self._stable_debounce,
            "exit_debounce": self._exit_debounce,
            "transition_reason": self._transition_reason,
        }
