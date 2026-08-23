from __future__ import annotations

import math

import pytest
import torch

from resume_validation.residual_safety import (
    apply_phase_action_gain,
    phase_aware_imu_emergency_masks,
    phase_aware_roll_imu_emergency_masks,
    positive_pitch_hazard_mask,
    project_balanced_z_signed_magnitude,
    project_confidence_balanced_z_gate,
    project_phase_aware_emergency_balanced_z_gate,
    project_phase_aware_emergency_support_counter_yaw_gate,
    project_pitch_corrective_balanced_z_gate,
    project_zero_preserving_balanced_z_gate,
    residual_phase_mask,
    update_phase8_corrective_latch,
)


def test_only_contact_maneuver_phases_enable_physical_residuals() -> None:
    phases = torch.arange(13, dtype=torch.long)
    expected = torch.tensor(
        [False, False, False, False, False, False, False, True, True, True, False, False, False]
    )
    torch.testing.assert_close(
        residual_phase_mask(phases, phase_min=7, phase_max=9),
        expected,
    )


def test_invalid_phase_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid residual phase window"):
        residual_phase_mask(torch.tensor([0]), phase_min=4, phase_max=3)


def test_phase_action_gain_preserves_zero_and_clamps_normalized_action() -> None:
    actions = torch.tensor(
        [
            [0.0] * 12,
            [0.0, -0.5, 0.0, -0.5, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0],
            [0.0, -0.8, 0.0, -0.8, 0.0, 0.8, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0],
        ]
    )
    phases = torch.tensor([7, 8, 9])
    phase_gains = torch.ones(13)
    phase_gains[9] = 1.5
    gained = apply_phase_action_gain(
        actions,
        phases,
        phase_gains=phase_gains,
    )
    torch.testing.assert_close(gained[0], torch.zeros(12))
    torch.testing.assert_close(gained[1], actions[1])
    torch.testing.assert_close(
        gained[2, [1, 3, 5, 7]],
        torch.tensor([-1.0, -1.0, 1.0, 1.0]),
    )


def test_phase_action_gain_rejects_misaligned_shapes() -> None:
    with pytest.raises(ValueError, match="phase shape"):
        apply_phase_action_gain(
            torch.zeros((2, 12)),
            torch.zeros(3, dtype=torch.long),
            phase_gains=torch.ones(13),
        )


def test_phase_action_gain_rejects_nonunit_hard_clip() -> None:
    with pytest.raises(ValueError, match="hard clip"):
        apply_phase_action_gain(
            torch.zeros((1, 12)),
            torch.zeros(1, dtype=torch.long),
            phase_gains=torch.ones(13),
            hard_clip=0.9,
        )


def test_balanced_z_signed_magnitude_masks_and_ties() -> None:
    actions = torch.tensor(
        [
            [
                0.1,
                0.2,
                0.3,
                -0.4,
                0.5,
                -0.6,
                0.7,
                0.8,
                0.9,
                -1.0,
                0.2,
                -0.3,
            ],
            [
                -0.1,
                -0.2,
                -0.3,
                0.4,
                -0.5,
                0.6,
                -0.7,
                -0.8,
                -0.9,
                1.0,
                -0.2,
                0.3,
            ],
        ]
    )
    original = actions.clone()
    projected = project_balanced_z_signed_magnitude(
        actions,
        wheel_center_z_signs=(-1, -1, 1, 1),
    )
    torch.testing.assert_close(
        projected[:, [1, 3, 5, 7]],
        torch.tensor([[-0.5, -0.5, 0.5, 0.5], [-0.5, -0.5, 0.5, 0.5]]),
    )
    torch.testing.assert_close(
        projected[:, [0, 2, 4, 6, 8, 9, 10, 11]],
        torch.zeros((2, 8)),
    )
    torch.testing.assert_close(actions, original)


def test_zero_preserving_balanced_z_gate_has_exact_off_half_space() -> None:
    actions = torch.tensor(
        [
            [0.1, -0.2, 0.3, -0.4, 0.5, 0.6, 0.7, 0.8, 0.9, -1.0, 0.2, -0.3],
            [0.1, 0.2, 0.3, 0.4, 0.5, -0.6, 0.7, -0.8, 0.9, -1.0, 0.2, -0.3],
            [0.0] * 12,
        ]
    )
    original = actions.clone()
    projected = project_zero_preserving_balanced_z_gate(
        actions,
        wheel_center_z_signs=(-1, -1, 1, 1),
    )
    torch.testing.assert_close(
        projected[0, [1, 3, 5, 7]],
        torch.tensor([-0.5, -0.5, 0.5, 0.5]),
    )
    torch.testing.assert_close(projected[1], torch.zeros(12))
    torch.testing.assert_close(projected[2], torch.zeros(12))
    torch.testing.assert_close(
        projected[:, [0, 2, 4, 6, 8, 9, 10, 11]],
        torch.zeros((3, 8)),
    )
    torch.testing.assert_close(actions, original)


def test_pitch_corrective_gate_preserves_drive_and_reverses_output() -> None:
    actions = torch.tensor(
        [
            [0.1, -0.2, 0.3, -0.4, 0.5, 0.6, 0.7, 0.8, 0.9, -1.0, 0.2, -0.3],
            [0.1, 0.2, 0.3, 0.4, 0.5, -0.6, 0.7, -0.8, 0.9, -1.0, 0.2, -0.3],
            [0.0] * 12,
        ]
    )
    original = actions.clone()
    projected = project_pitch_corrective_balanced_z_gate(
        actions,
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(1, 1, -1, -1),
    )
    torch.testing.assert_close(
        projected[0, [1, 3, 5, 7]],
        torch.tensor([0.5, 0.5, -0.5, -0.5]),
    )
    torch.testing.assert_close(projected[1:], torch.zeros((2, 12)))
    torch.testing.assert_close(
        projected[:, [0, 2, 4, 6, 8, 9, 10, 11]],
        torch.zeros((3, 8)),
    )
    torch.testing.assert_close(actions, original)


def test_pitch_corrective_gate_rejects_direction_drift() -> None:
    with pytest.raises(ValueError, match="executed direction"):
        project_pitch_corrective_balanced_z_gate(
            torch.zeros(12),
            wheel_center_z_signs=(-1, -1, 1, 1),
            executed_wheel_center_z_signs=(-1, -1, 1, 1),
        )


def test_positive_pitch_hazard_gate_is_signed_and_inclusive() -> None:
    pitch = torch.tensor([-0.2, 0.089999, 0.09, 0.2])
    torch.testing.assert_close(
        positive_pitch_hazard_mask(
            pitch,
            minimum_pitch_rad=0.09,
        ),
        torch.tensor([False, False, True, True]),
    )


@pytest.mark.parametrize(
    "threshold",
    [-0.1, 0.0, math.pi / 2.0, float("nan")],
)
def test_positive_pitch_hazard_gate_rejects_invalid_threshold(
    threshold: float,
) -> None:
    with pytest.raises(ValueError, match="positive-pitch hazard threshold"):
        positive_pitch_hazard_mask(
            torch.zeros(2),
            minimum_pitch_rad=threshold,
        )


def test_positive_pitch_hazard_gate_rejects_nonfinite_pitch() -> None:
    with pytest.raises(ValueError, match="pitch_rad must be finite"):
        positive_pitch_hazard_mask(
            torch.tensor([0.1, float("nan")]),
            minimum_pitch_rad=0.09,
        )


def test_phase_aware_imu_emergency_separates_rear_and_post_transfer() -> None:
    phases = torch.tensor([7, 8, 8, 8, 9, 10, 11])
    pitch = torch.tensor([0.2, 0.05, 0.09, 0.05, 0.09, 0.09, 0.2])
    pitch_rate = torch.tensor([1.0, 0.34, 0.2, 0.35, 0.0, 1.0, 1.0])
    enabled, corrective = phase_aware_imu_emergency_masks(
        phases,
        pitch,
        pitch_rate,
        rear_transfer_phase=8,
        post_transfer_phase_min=9,
        post_transfer_phase_max=10,
        minimum_pitch_rad=0.09,
        early_pitch_rad=0.04,
        early_pitch_rate_rad_s=0.35,
    )
    torch.testing.assert_close(
        enabled,
        torch.tensor([False, False, True, True, True, True, False]),
    )
    torch.testing.assert_close(
        corrective,
        torch.tensor([False, False, False, True, True, True, False]),
    )


def test_phase_aware_imu_emergency_rejects_bad_thresholds() -> None:
    with pytest.raises(ValueError, match="emergency thresholds"):
        phase_aware_imu_emergency_masks(
            torch.tensor([8]),
            torch.tensor([0.1]),
            torch.tensor([0.4]),
            rear_transfer_phase=8,
            post_transfer_phase_min=9,
            post_transfer_phase_max=10,
            minimum_pitch_rad=0.09,
            early_pitch_rad=0.1,
            early_pitch_rate_rad_s=0.35,
        )


def test_phase_aware_roll_emergency_preserves_climb_and_selects_roll() -> None:
    phases = torch.tensor([7, 8, 8, 8, 9, 10, 11])
    roll = torch.tensor([0.2, 0.05, 0.05, 0.06, 0.10, 0.10, 0.2])
    pitch = torch.tensor([0.2, 0.05, 0.09, 0.05, 0.09, 0.05, 0.2])
    pitch_rate = torch.tensor([1.0, 0.34, 0.2, 0.35, 0.0, 1.0, 1.0])
    enabled, corrective = phase_aware_roll_imu_emergency_masks(
        phases,
        roll,
        pitch,
        pitch_rate,
        rear_transfer_phase=8,
        post_transfer_phase_min=9,
        post_transfer_phase_max=10,
        minimum_pitch_rad=0.09,
        minimum_roll_rad=0.10,
        early_roll_rad=0.06,
        early_pitch_rate_rad_s=0.35,
    )
    torch.testing.assert_close(
        enabled,
        torch.tensor([False, False, True, True, True, True, False]),
    )
    torch.testing.assert_close(
        corrective,
        torch.tensor([False, False, False, True, True, True, False]),
    )


def test_phase_aware_roll_emergency_rejects_bad_thresholds() -> None:
    with pytest.raises(ValueError, match="roll IMU emergency thresholds"):
        phase_aware_roll_imu_emergency_masks(
            torch.tensor([8]),
            torch.tensor([0.1]),
            torch.tensor([0.1]),
            torch.tensor([0.4]),
            rear_transfer_phase=8,
            post_transfer_phase_min=9,
            post_transfer_phase_max=10,
            minimum_pitch_rad=0.09,
            minimum_roll_rad=0.06,
            early_roll_rad=0.06,
            early_pitch_rate_rad_s=0.35,
        )


def test_phase8_corrective_latch_persists_and_clears_on_exit() -> None:
    previous = torch.tensor([False, False, True, True])
    phase = torch.tensor([8, 8, 8, 9])
    rapid = torch.tensor([False, True, False, False])
    torch.testing.assert_close(
        update_phase8_corrective_latch(
            phase,
            rapid,
            previous,
            rear_transfer_phase=8,
        ),
        torch.tensor([False, True, True, False]),
    )


def test_phase_aware_projection_switches_direction_and_preserves_zero() -> None:
    actions = torch.tensor(
        [
            [0.1, -0.2, 0.3, -0.4, 0.5, 0.6, 0.7, 0.8, 0.9, -1.0, 0.2, -0.3],
            [0.1, -0.2, 0.3, -0.4, 0.5, 0.6, 0.7, 0.8, 0.9, -1.0, 0.2, -0.3],
            [0.0] * 12,
        ]
    )
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([False, True, True]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(1, 1, -1, -1),
    )
    torch.testing.assert_close(
        projected[:, [1, 3, 5, 7]],
        torch.tensor(
            [
                [-0.5, -0.5, 0.5, 0.5],
                [0.5, 0.5, -0.5, -0.5],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )
    torch.testing.assert_close(
        projected[:, [0, 2, 4, 6, 8, 9, 10, 11]],
        torch.zeros((3, 8)),
    )


def test_phase_aware_corrective_floor_requires_positive_actor_drive() -> None:
    actions = torch.zeros((3, 12))
    signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = signs * 0.05
    actions[1, [1, 3, 5, 7]] = signs * -0.05
    actions[2, [1, 3, 5, 7]] = signs * 0.05
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([True, True, False]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(1, 1, -1, -1),
        corrective_minimum_shared_magnitude=0.1,
    )
    torch.testing.assert_close(
        projected[:, [1, 3, 5, 7]],
        torch.tensor(
            [
                [0.1, 0.1, -0.1, -0.1],
                [0.0, 0.0, 0.0, 0.0],
                [-0.05, -0.05, 0.05, 0.05],
            ]
        ),
    )


def test_phase_aware_roll_projection_is_zero_sum_and_zero_pitch_moment() -> None:
    actions = torch.zeros((2, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = drive_signs * 0.05
    actions[1, [1, 3, 5, 7]] = drive_signs * -0.05
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([True, True]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(1, -1, 1, -1),
        corrective_minimum_shared_magnitude=0.1,
    )
    z = projected[:, [1, 3, 5, 7]]
    torch.testing.assert_close(
        z,
        torch.tensor(
            [
                [0.1, -0.1, 0.1, -0.1],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )
    torch.testing.assert_close(z.sum(dim=1), torch.zeros(2))
    torch.testing.assert_close(z[:, :2].sum(dim=1), torch.zeros(2))
    torch.testing.assert_close(z[:, 2:].sum(dim=1), torch.zeros(2))


def test_phase_aware_diagonal_projection_targets_only_failed_diagonal() -> None:
    actions = torch.zeros((2, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = drive_signs * 0.05
    actions[1, [1, 3, 5, 7]] = drive_signs * -0.05
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([True, True]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(0, -1, 1, 0),
        corrective_minimum_shared_magnitude=0.1,
    )
    z = projected[:, [1, 3, 5, 7]]
    torch.testing.assert_close(
        z,
        torch.tensor(
            [
                [0.0, -0.1, 0.1, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )
    torch.testing.assert_close(z.sum(dim=1), torch.zeros(2))


def test_phase_aware_front_right_only_projection_is_ik_feasible_candidate() -> None:
    actions = torch.zeros((2, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = drive_signs * 0.05
    actions[1, [1, 3, 5, 7]] = drive_signs * -0.05
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([True, True]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(0, -1, 0, 0),
        corrective_minimum_shared_magnitude=0.1,
    )
    z = projected[:, [1, 3, 5, 7]]
    torch.testing.assert_close(
        z,
        torch.tensor(
            [
                [0.0, -0.1, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )
    torch.testing.assert_close(z[:, [0, 2, 3]], torch.zeros((2, 3)))


def test_phase_aware_asymmetric_diagonal_projection_applies_ik_margin_scale() -> None:
    actions = torch.zeros((2, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = drive_signs * 0.05
    actions[1, [1, 3, 5, 7]] = drive_signs * -0.05
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([True, True]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(0, -1, 1, 0),
        corrective_wheel_center_z_scales=(0.0, 1.0, 0.8, 0.0),
        corrective_minimum_shared_magnitude=0.1,
    )
    torch.testing.assert_close(
        projected[:, [1, 3, 5, 7]],
        torch.tensor(
            [
                [0.0, -0.1, 0.08, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )


def test_phase_aware_asymmetric_diagonal_projection_rejects_bad_scales() -> None:
    with pytest.raises(ValueError, match="explicit corrective"):
        project_phase_aware_emergency_balanced_z_gate(
            torch.zeros(12),
            torch.tensor(True),
            wheel_center_z_signs=(-1, -1, 1, 1),
            executed_wheel_center_z_signs=(0, -1, 1, 0),
            corrective_wheel_center_z_scales=(0.1, 1.0, 0.8, 0.0),
        )


def test_phase_aware_deficient_diagonal_projection_extends_both_legs() -> None:
    actions = torch.zeros((2, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = drive_signs * 0.05
    actions[1, [1, 3, 5, 7]] = drive_signs * -0.05
    projected = project_phase_aware_emergency_balanced_z_gate(
        actions,
        torch.tensor([True, True]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(0, -1, -1, 0),
        corrective_wheel_center_z_scales=(0.0, 1.0, 1.0, 0.0),
        corrective_minimum_shared_magnitude=0.1,
    )
    torch.testing.assert_close(
        projected[:, [1, 3, 5, 7]],
        torch.tensor(
            [
                [0.0, -0.1, -0.1, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )


def test_phase_aware_counter_yaw_projection_is_phase9_only() -> None:
    actions = torch.zeros((3, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[:, [1, 3, 5, 7]] = drive_signs * 0.05
    projected = project_phase_aware_emergency_support_counter_yaw_gate(
        actions,
        torch.tensor([True, True, True]),
        torch.tensor([8, 9, 10]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(0, -1, -1, 0),
        corrective_wheel_center_z_scales=(0.0, 1.0, 1.0, 0.0),
        corrective_minimum_shared_magnitude=0.1,
        corrective_wheel_speed_minimum_shared_magnitudes=(0.25,),
        corrective_wheel_speed_signs=(-1, 1, -1, 1),
        corrective_wheel_speed_scales=(1.0, 1.0, 1.0, 1.0),
        corrective_wheel_speed_phases=(9,),
    )
    torch.testing.assert_close(
        projected[:, [1, 3, 5, 7]],
        torch.tensor(
            [
                [0.0, -0.1, -0.1, 0.0],
                [0.0, -0.1, -0.1, 0.0],
                [0.0, -0.1, -0.1, 0.0],
            ]
        ),
    )
    torch.testing.assert_close(
        projected[:, 8:],
        torch.tensor(
            [
                [0.0, 0.0, 0.0, 0.0],
                [-0.25, 0.25, -0.25, 0.25],
                [0.0, 0.0, 0.0, 0.0],
            ]
        ),
    )


def test_phase_aware_counter_yaw_projection_preserves_off_half_space() -> None:
    actions = torch.zeros((2, 12))
    drive_signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = drive_signs * -0.05
    projected = project_phase_aware_emergency_support_counter_yaw_gate(
        actions,
        torch.tensor([True, False]),
        torch.tensor([9, 9]),
        wheel_center_z_signs=(-1, -1, 1, 1),
        executed_wheel_center_z_signs=(0, -1, -1, 0),
        corrective_wheel_center_z_scales=(0.0, 1.0, 1.0, 0.0),
        corrective_minimum_shared_magnitude=0.1,
        corrective_wheel_speed_minimum_shared_magnitudes=(0.25,),
        corrective_wheel_speed_signs=(-1, 1, -1, 1),
        corrective_wheel_speed_scales=(1.0, 1.0, 1.0, 1.0),
        corrective_wheel_speed_phases=(9,),
    )
    torch.testing.assert_close(projected, torch.zeros_like(projected))


def test_phase_aware_counter_yaw_projection_rejects_invalid_speed_floor() -> None:
    with pytest.raises(ValueError, match="wheel-speed minimum"):
        project_phase_aware_emergency_support_counter_yaw_gate(
            torch.zeros((1, 12)),
            torch.tensor([True]),
            torch.tensor([9]),
            wheel_center_z_signs=(-1, -1, 1, 1),
            executed_wheel_center_z_signs=(0, -1, -1, 0),
            corrective_wheel_center_z_scales=(0.0, 1.0, 1.0, 0.0),
            corrective_minimum_shared_magnitude=0.1,
            corrective_wheel_speed_minimum_shared_magnitudes=(1.0, 0.25),
            corrective_wheel_speed_signs=(-1, 1, -1, 1),
            corrective_wheel_speed_scales=(1.0, 1.0, 1.0, 1.0),
            corrective_wheel_speed_phases=(8, 9),
        )


def test_phase_aware_counter_yaw_projection_rejects_unsorted_phases() -> None:
    with pytest.raises(ValueError, match="sorted"):
        project_phase_aware_emergency_support_counter_yaw_gate(
            torch.zeros((1, 12)),
            torch.tensor([True]),
            torch.tensor([9]),
            wheel_center_z_signs=(-1, -1, 1, 1),
            executed_wheel_center_z_signs=(0, -1, -1, 0),
            corrective_wheel_center_z_scales=(0.0, 1.0, 1.0, 0.0),
            corrective_minimum_shared_magnitude=0.1,
            corrective_wheel_speed_minimum_shared_magnitudes=(0.25, 0.25),
            corrective_wheel_speed_signs=(-1, 1, -1, 1),
            corrective_wheel_speed_scales=(1.0, 1.0, 1.0, 1.0),
            corrective_wheel_speed_phases=(9, 8),
        )


def test_phase_aware_counter_yaw_projection_rejects_misaligned_floors() -> None:
    with pytest.raises(ValueError, match="align with phases"):
        project_phase_aware_emergency_support_counter_yaw_gate(
            torch.zeros((1, 12)),
            torch.tensor([True]),
            torch.tensor([9]),
            wheel_center_z_signs=(-1, -1, 1, 1),
            executed_wheel_center_z_signs=(0, -1, -1, 0),
            corrective_wheel_center_z_scales=(0.0, 1.0, 1.0, 0.0),
            corrective_minimum_shared_magnitude=0.1,
            corrective_wheel_speed_minimum_shared_magnitudes=(0.25,),
            corrective_wheel_speed_signs=(-1, 1, -1, 1),
            corrective_wheel_speed_scales=(1.0, 1.0, 1.0, 1.0),
            corrective_wheel_speed_phases=(8, 9),
        )


def test_phase_aware_corrective_floor_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="minimum shared magnitude"):
        project_phase_aware_emergency_balanced_z_gate(
            torch.zeros(12),
            torch.tensor(True),
            wheel_center_z_signs=(-1, -1, 1, 1),
            executed_wheel_center_z_signs=(1, 1, -1, -1),
            corrective_minimum_shared_magnitude=1.0,
        )


def test_confidence_gate_subtracts_threshold_and_preserves_deadband() -> None:
    threshold = torch.exp(torch.tensor(-4.0)).item()
    actions = torch.zeros((3, 12))
    signs = torch.tensor([-1.0, -1.0, 1.0, 1.0])
    actions[0, [1, 3, 5, 7]] = signs * (threshold + 0.2)
    actions[1, [1, 3, 5, 7]] = signs * threshold
    actions[2, [1, 3, 5, 7]] = signs * -0.4
    projected = project_confidence_balanced_z_gate(
        actions,
        wheel_center_z_signs=(-1, -1, 1, 1),
        activation_threshold=threshold,
    )
    torch.testing.assert_close(
        projected[0, [1, 3, 5, 7]],
        torch.tensor([-0.2, -0.2, 0.2, 0.2]),
    )
    torch.testing.assert_close(projected[1:], torch.zeros((2, 12)))


@pytest.mark.parametrize("threshold", [-0.1, 1.0, float("nan")])
def test_confidence_gate_rejects_invalid_threshold(threshold: float) -> None:
    with pytest.raises(ValueError, match="confidence activation threshold"):
        project_confidence_balanced_z_gate(
            torch.zeros(12),
            wheel_center_z_signs=(-1, -1, 1, 1),
            activation_threshold=threshold,
        )


@pytest.mark.parametrize(
    ("actions", "signs", "message"),
    [
        (torch.zeros(11), (-1, -1, 1, 1), "trailing dimension 12"),
        (
            torch.zeros(12),
            (-1, 0, 1, 1),
            "four values in",
        ),
    ],
)
def test_invalid_vertical_projection_is_rejected(
    actions: torch.Tensor,
    signs: tuple[int, int, int, int],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        project_balanced_z_signed_magnitude(
            actions,
            wheel_center_z_signs=signs,
        )


def test_non_z_only_mask_is_rejected() -> None:
    with pytest.raises(ValueError, match="z-only physical authority"):
        project_balanced_z_signed_magnitude(
            torch.zeros(12),
            wheel_center_z_signs=(-1, -1, 1, 1),
            action_mask=(1,) * 12,
        )
