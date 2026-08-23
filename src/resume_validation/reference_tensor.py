"""Vectorized, auditable FSM references derived from the two replay logs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .actuator_mapping import (
    FSM_REFERENCE_MARGIN_DEG,
    RECORDED_SAFE_COMMAND_DEG,
    SERVO_JOINT_NAMES,
    WHEEL_JOINT_NAMES,
)
from .fsm_trajectory import ReferenceTrajectory, trajectory_from_replay
from .replay_loader import load_replay

REAR_RECOVERY_MAX_BLEND = 0.10


@dataclass(frozen=True)
class ReferenceSources:
    replay_50mm: Path
    replay_100mm: Path
    max_idle_gap_s: float = 1.0
    preserve_wheel_distance: bool = True


class TorchReferenceBank:
    """Compose continuous FSM references from the two recorded traversals."""

    def __init__(self, sources: ReferenceSources, *, device: str):
        import torch

        self.torch = torch
        self.device = device
        self.low = trajectory_from_replay(
            load_replay(sources.replay_50mm),
            max_idle_gap_s=sources.max_idle_gap_s,
            preserve_wheel_distance=sources.preserve_wheel_distance,
        )
        self.high = trajectory_from_replay(
            load_replay(sources.replay_100mm),
            max_idle_gap_s=sources.max_idle_gap_s,
            preserve_wheel_distance=sources.preserve_wheel_distance,
        )
        self.low_tensor = self._pack(self.low)
        self.high_tensor = self._pack(self.high)

    def _pack(self, trajectory: ReferenceTrajectory) -> tuple[object, object]:
        torch = self.torch
        times = torch.tensor([row.normalized_time for row in trajectory.samples], dtype=torch.float32, device=self.device)
        commands = torch.tensor(
            [
                [row.servo_deg[name] for name in SERVO_JOINT_NAMES]
                + [row.wheel_rad_s[name] for name in WHEEL_JOINT_NAMES]
                for row in trajectory.samples
            ],
            dtype=torch.float32,
            device=self.device,
        )
        return times, commands

    def _sample_one(self, packed: tuple[object, object], normalized_time):
        torch = self.torch
        times, commands = packed
        u = torch.clamp(normalized_time, 0.0, 1.0)
        right = torch.searchsorted(times, u, right=True)
        right = torch.clamp(right, 1, times.numel() - 1)
        left = right - 1
        return commands[left]

    def sample(self, normalized_time, obstacle_height_m):
        torch = self.torch
        low = self._sample_one(self.low_tensor, normalized_time)
        high = self._sample_one(self.high_tensor, normalized_time)
        height_alpha = torch.clamp(
            (obstacle_height_m - float(self.low.height_m)) / (float(self.high.height_m) - float(self.low.height_m)),
            0.0,
            1.0,
        ).unsqueeze(1)
        return low + height_alpha * (high - low)

    def sample_low(self, normalized_time):
        """Sample the complete 50 mm reference at normalized time."""

        return self._sample_one(self.low_tensor, normalized_time)

    def rear_normalized_time(self, normalized_time, obstacle_height_m):
        """Continuously align rear preparation with height-specific front placement.

        At 50 mm the mapping is the identity. At 100 mm, low-reference time
        0.50 is aligned to source time 0.574, after the recorded 100 mm
        front-leg placement. The two linear pieces meet exactly at that anchor,
        so no command splice or target jump is introduced.
        """

        torch = self.torch
        alpha = torch.clamp(
            (obstacle_height_m - float(self.low.height_m))
            / (float(self.high.height_m) - float(self.low.height_m)),
            0.0,
            1.0,
        )
        anchor = 0.50 + alpha * (0.574 - 0.50)
        before = normalized_time * 0.50 / torch.clamp(anchor, min=1.0e-6)
        after = 0.50 + (normalized_time - anchor) * 0.50 / torch.clamp(
            1.0 - anchor, min=1.0e-6
        )
        return torch.clamp(torch.where(normalized_time <= anchor, before, after), 0.0, 1.0)

    def coordinated_rear_preparation(self, normalized_time, obstacle_height_m):
        """Synchronize the two rear hips before the recorded right-knee tuck.

        The 50 mm source prepares the rear legs sequentially. That ordering
        creates a diagonal load transient when the base is straddling a 100 mm
        edge. This height-blended override connects the exact recorded start
        and end commands using simultaneous smooth hip motion, followed by the
        recorded rear-right knee tuck.
        """

        torch = self.torch
        alpha = torch.clamp(
            (obstacle_height_m - float(self.low.height_m))
            / (float(self.high.height_m) - float(self.low.height_m)),
            0.0,
            1.0,
        )
        start = 0.50 + alpha * (0.574 - 0.50)
        progress = torch.clamp(
            (normalized_time - start) / torch.clamp(0.64 - start, min=1.0e-6),
            0.0,
            1.0,
        )
        # The first 35% of BODY_TRANSFER is reserved for extending the front
        # support legs (see front_support_preparation). Only then shorten both
        # rear legs together, followed by the right-knee tuck.
        hip_progress = torch.clamp((progress - 0.35) / 0.40, 0.0, 1.0)
        knee_progress = torch.clamp((progress - 0.75) / 0.25, 0.0, 1.0)
        hip_smooth = hip_progress.square() * (3.0 - 2.0 * hip_progress)
        knee_smooth = knee_progress.square() * (3.0 - 2.0 * knee_progress)
        commands = torch.stack(
            (
                0.7 + (24.2 - 0.7) * hip_smooth,
                torch.zeros_like(progress),
                0.7 + (29.8 - 0.7) * hip_smooth,
                -44.8 * knee_smooth,
            ),
            dim=1,
        )
        active = (normalized_time >= start) & (normalized_time <= 0.64)
        return commands, active, alpha

    def front_support_preparation(self, normalized_time, obstacle_height_m):
        """Extend the front support using the recorded 100 mm recovery pose."""

        torch = self.torch
        alpha = torch.clamp(
            (obstacle_height_m - float(self.low.height_m))
            / (float(self.high.height_m) - float(self.low.height_m)),
            0.0,
            1.0,
        )
        start = 0.50 + alpha * (0.574 - 0.50)
        phase_progress = torch.clamp(
            (normalized_time - start) / torch.clamp(0.64 - start, min=1.0e-6),
            0.0,
            1.0,
        )
        support_progress = torch.clamp(phase_progress / 0.35, 0.0, 1.0)
        support_smooth = support_progress.square() * (3.0 - 2.0 * support_progress)
        target = torch.tensor(
            [6.2, 2.3, 1.8, -4.4],
            dtype=torch.float32,
            device=normalized_time.device,
        ).unsqueeze(0).expand(normalized_time.shape[0], -1)
        active = normalized_time >= start
        return target, support_smooth, active, alpha

    def rear_recovery_after_transfer(
        self,
        normalized_time,
        obstacle_height_m,
        maximum_blend=None,
    ):
        """Level the rear support after all wheels have reached the top.

        The complete 50 mm source naturally recovers both rear legs near the
        end of the traversal. At 100 mm its continuously time-warped rear
        channels otherwise remain in an asymmetric lift/place posture through
        phases 9--10. Blend toward the exact 50 mm final rear command across
        phase 9; use the same height interpolation as the transfer override.

        Legacy 100 mm telemetry appeared balanced at approximately 10% of that
        path, but attempt 020 proved those fields were force magnitudes and
        that the world-Z all-wheel threshold was never met.  The 10% cap is
        retained only as the unchanged formal baseline while a registered
        development grid measures nearby path fractions explicitly.
        """

        torch = self.torch
        alpha = torch.clamp(
            (obstacle_height_m - float(self.low.height_m))
            / (float(self.high.height_m) - float(self.low.height_m)),
            0.0,
            1.0,
        )
        progress = torch.clamp((normalized_time - 0.88) / (0.94 - 0.88), 0.0, 1.0)
        smooth = progress.square() * (3.0 - 2.0 * progress)
        final_rear = self.sample_low(torch.ones_like(normalized_time))[:, 4:8]
        if maximum_blend is None:
            maximum = torch.full_like(smooth, REAR_RECOVERY_MAX_BLEND)
        else:
            maximum = torch.as_tensor(
                maximum_blend,
                dtype=smooth.dtype,
                device=smooth.device,
            )
            if maximum.ndim == 0:
                maximum = maximum.expand_as(smooth)
            if maximum.shape != smooth.shape:
                raise ValueError(
                    "rear recovery maximum blend must be scalar or match the batch"
                )
        return final_rear, maximum * smooth, alpha

    def sample_fsm(
        self,
        normalized_time,
        obstacle_height_m,
        rear_recovery_max_blend=None,
    ):
        """Return the deployed FSM reference without a phase-boundary splice.

        The accepted 100 mm recording is only a partial traversal: its rear-leg
        channels do not contain the lift/place motion needed to clear the
        obstacle. The complete, physically successful 50 mm rear-leg channels
        are therefore used from time zero, preserving zero-order-hold
        continuity.
        """

        torch = self.torch
        reference = self.sample(normalized_time, obstacle_height_m)
        front_target, support_progress, support_active, height_alpha = (
            self.front_support_preparation(normalized_time, obstacle_height_m)
        )
        prepared_front = reference[:, :4] + (
            height_alpha * support_progress
        ).unsqueeze(1) * (front_target - reference[:, :4])
        reference[:, :4] = torch.where(
            support_active.unsqueeze(1),
            prepared_front,
            reference[:, :4],
        )
        rear_time = self.rear_normalized_time(normalized_time, obstacle_height_m)
        low_reference = self.sample_low(rear_time)
        coordinated, preparation_active, rear_height_alpha = self.coordinated_rear_preparation(
            normalized_time, obstacle_height_m
        )
        prepared_rear = low_reference[:, 4:8] + rear_height_alpha.unsqueeze(1) * (
            coordinated - low_reference[:, 4:8]
        )
        reference[:, 4:8] = torch.where(
            preparation_active.unsqueeze(1),
            prepared_rear,
            low_reference[:, 4:8],
        )
        final_rear, recovery_progress, recovery_height_alpha = (
            self.rear_recovery_after_transfer(
                normalized_time,
                obstacle_height_m,
                rear_recovery_max_blend,
            )
        )
        recovery_blend = (recovery_progress * recovery_height_alpha).unsqueeze(1)
        reference[:, 4:8] = reference[:, 4:8] + recovery_blend * (
            final_rear - reference[:, 4:8]
        )
        servo_lower = torch.tensor(
            [
                RECORDED_SAFE_COMMAND_DEG[name][0] + FSM_REFERENCE_MARGIN_DEG
                for name in SERVO_JOINT_NAMES
            ],
            dtype=reference.dtype,
            device=reference.device,
        )
        servo_upper = torch.tensor(
            [
                RECORDED_SAFE_COMMAND_DEG[name][1] - FSM_REFERENCE_MARGIN_DEG
                for name in SERVO_JOINT_NAMES
            ],
            dtype=reference.dtype,
            device=reference.device,
        )
        reference[:, :8] = torch.maximum(
            torch.minimum(reference[:, :8], servo_upper),
            servo_lower,
        )
        return reference

    def duration_s(self, obstacle_height_m):
        torch = self.torch
        # The complete rear-leg reference comes from the slower 50 mm replay.
        # Use the slower source duration at every height so none of its accepted
        # command intervals are time-compressed at 75/100 mm.
        execution_duration_s = max(float(self.low.duration_s), float(self.high.duration_s))
        return torch.full_like(obstacle_height_m, execution_duration_s)
