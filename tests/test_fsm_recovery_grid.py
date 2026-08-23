"""Registered-candidate checks for vectorized FSM recovery diagnostics."""

from __future__ import annotations

from resume_validation.fsm_recovery_grid import recovery_grid_candidates


def test_front_right_grid_preserves_the_original_25_candidates() -> None:
    rows = recovery_grid_candidates("front_right")
    assert len(rows) == 25
    assert rows[12]["parameters"] == {
        "front_right_offset_x_m": 0.0,
        "front_right_offset_z_m": 0.0,
    }
    assert rows[12]["wheel_center_offsets_m"] == [[0.0, 0.0]] * 4


def test_common_right_grid_has_baseline_and_bounded_offsets() -> None:
    rows = recovery_grid_candidates("common_right_z")
    assert len(rows) == 25
    assert rows[12]["parameters"] == {
        "common_offset_z_m": 0.0,
        "right_side_delta_z_m": 0.0,
    }
    assert rows[12]["wheel_center_offsets_m"] == [[0.0, 0.0]] * 4
    assert max(
        abs(offset[1])
        for row in rows
        for offset in row["wheel_center_offsets_m"]
    ) <= 0.015


def test_front_support_grid_stays_inside_registered_safe_envelope() -> None:
    from resume_validation.actuator_mapping import (
        FSM_REFERENCE_MARGIN_DEG,
        RECORDED_SAFE_COMMAND_DEG,
    )

    rows = recovery_grid_candidates("front_support_fr")
    assert len(rows) == 25
    assert any(
        row["parameters"]
        == {
            "front_right_hip_delta_deg": 0.0,
            "front_right_knee_delta_deg": 0.0,
        }
        for row in rows
    )
    target = [6.2, 2.3, 4.8, 10.6]
    for row in rows:
        offsets = row["front_support_command_offsets_deg"]
        hip = target[2] + offsets[2]
        knee = target[3] + offsets[3]
        hip_limits = RECORDED_SAFE_COMMAND_DEG["front_right_hip"]
        knee_limits = RECORDED_SAFE_COMMAND_DEG["front_right_knee"]
        assert hip_limits[0] + FSM_REFERENCE_MARGIN_DEG <= hip
        assert hip <= hip_limits[1] - FSM_REFERENCE_MARGIN_DEG
        assert knee_limits[0] + FSM_REFERENCE_MARGIN_DEG <= knee
        assert knee <= knee_limits[1] - FSM_REFERENCE_MARGIN_DEG


def test_front_support_unloaded_diagonal_grid_has_exact_control_and_bounded_extensions() -> None:
    rows = recovery_grid_candidates("front_support_unloaded_diagonal_z")
    assert len(rows) == 25
    assert rows[0]["parameters"] == {
        "front_right_hip_delta_deg": -3.0,
        "front_right_knee_delta_deg": -15.0,
        "front_left_extension_m": 0.0,
        "rear_right_extension_m": 0.0,
    }
    assert rows[0]["wheel_center_offsets_m"] == [[0.0, 0.0]] * 4
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[1] == [0.0, 0.0]
        assert offsets[2] == [0.0, 0.0]
        assert 0.0 <= offsets[0][1] <= 0.006
        assert 0.0 <= offsets[3][1] <= 0.006
        assert row["front_support_command_offsets_deg"] == [
            0.0,
            0.0,
            -3.0,
            -15.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]


def test_rear_recovery_grid_replicates_each_single_variable_value() -> None:
    rows = recovery_grid_candidates("rear_recovery_blend")
    assert len(rows) == 25
    values = [row["rear_recovery_max_blend"] for row in rows]
    for value in (0.0, 0.05, 0.10, 0.15, 0.20):
        assert values.count(value) == 5
    for row in rows:
        assert row["wheel_center_offsets_m"] == [[0.0, 0.0]] * 4
        assert row["front_support_command_offsets_deg"] == [0.0] * 8


def test_rear_right_extension_grid_is_latin_rotated_and_bounded() -> None:
    rows = recovery_grid_candidates("rear_right_support_extension")
    assert len(rows) == 25
    values = [row["parameters"]["rear_right_extension_m"] for row in rows]
    for value in (0.0, 0.005, 0.010, 0.015, 0.020):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["rear_right_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.0, 0.005, 0.010, 0.015, 0.020}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[:3] == [[0.0, 0.0]] * 3
        assert offsets[3][0] == 0.0
        assert 0.0 <= offsets[3][1] <= 0.020


def test_unloaded_diagonal_grid_holds_rear_right_and_latin_rotates_one_value() -> None:
    rows = recovery_grid_candidates("front_right_rear_left_support_extension")
    assert len(rows) == 25
    values = [
        row["parameters"]["front_right_rear_left_extension_m"] for row in rows
    ]
    for value in (0.0, 0.002, 0.004, 0.006, 0.008):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_rear_left_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.0, 0.002, 0.004, 0.006, 0.008}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[0] == [0.0, 0.0]
        assert offsets[1][1] == offsets[2][1]
        assert 0.0 <= offsets[1][1] <= 0.008
        assert offsets[3] == [0.0, 0.015]


def test_wide_unloaded_diagonal_grid_continues_range_without_new_variables() -> None:
    rows = recovery_grid_candidates(
        "front_right_rear_left_support_extension_wide"
    )
    assert len(rows) == 25
    values = [
        row["parameters"]["front_right_rear_left_extension_m"] for row in rows
    ]
    for value in (0.008, 0.011, 0.014, 0.017, 0.020):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_rear_left_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.008, 0.011, 0.014, 0.017, 0.020}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[0] == [0.0, 0.0]
        assert offsets[1][1] == offsets[2][1]
        assert 0.008 <= offsets[1][1] <= 0.020
        assert offsets[3] == [0.0, 0.015]
        assert row["parameters"]["range_continuation_from_grid"] == 12


def test_activation_start_grid_holds_successful_amplitude_and_rotates_start() -> None:
    rows = recovery_grid_candidates("post_transfer_offset_activation_start")
    assert len(rows) == 25
    values = [
        row["parameters"]["post_transfer_offset_start_progress"] for row in rows
    ]
    for value in (0.0, 0.2, 0.4, 0.6, 0.8):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["post_transfer_offset_start_progress"]
            for index in range(residue, 25, 5)
        } == {0.0, 0.2, 0.4, 0.6, 0.8}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets == [
            [0.0, 0.0],
            [0.0, 0.014],
            [0.0, 0.014],
            [0.0, 0.015],
        ]
        assert row["parameters"]["source_grid"] == 13


def test_rear_left_relief_grid_changes_only_isolated_unreachable_leg() -> None:
    rows = recovery_grid_candidates("rear_left_extension_relief")
    assert len(rows) == 25
    values = [row["parameters"]["rear_left_extension_m"] for row in rows]
    for value in (0.008, 0.0095, 0.011, 0.0125, 0.014):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["rear_left_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.008, 0.0095, 0.011, 0.0125, 0.014}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[0] == [0.0, 0.0]
        assert offsets[1] == [0.0, 0.014]
        assert 0.008 <= offsets[2][1] <= 0.014
        assert offsets[3] == [0.0, 0.015]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_rear_left_boundary_grid_resolves_zero_fallback_load_threshold() -> None:
    rows = recovery_grid_candidates("rear_left_extension_boundary")
    assert len(rows) == 25
    values = [row["parameters"]["rear_left_extension_m"] for row in rows]
    for value in (0.011, 0.01125, 0.0115, 0.01175, 0.012):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["rear_left_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.011, 0.01125, 0.0115, 0.01175, 0.012}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[1] == [0.0, 0.014]
        assert 0.011 <= offsets[2][1] <= 0.012
        assert offsets[3] == [0.0, 0.015]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_rear_left_activation_grid_delays_only_isolated_leg() -> None:
    rows = recovery_grid_candidates("rear_left_activation_start")
    assert len(rows) == 25
    values = [
        row["parameters"]["rear_left_offset_start_progress"] for row in rows
    ]
    for value in (0.4, 0.5, 0.6, 0.7, 0.8):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["rear_left_offset_start_progress"]
            for index in range(residue, 25, 5)
        } == {0.4, 0.5, 0.6, 0.7, 0.8}
    for row in rows:
        assert row["wheel_center_offsets_m"] == [
            [0.0, 0.0],
            [0.0, 0.014],
            [0.0, 0.0115],
            [0.0, 0.015],
        ]
        starts = row["post_transfer_leg_offset_start_progress"]
        assert starts[:2] == [0.4, 0.4]
        assert starts[3] == 0.4
        assert 0.4 <= starts[2] <= 0.8


def test_rear_right_boundary_grid_holds_rear_left_at_reachable_limit() -> None:
    rows = recovery_grid_candidates("rear_right_extension_boundary")
    assert len(rows) == 25
    values = [row["parameters"]["rear_right_extension_m"] for row in rows]
    for value in (0.015, 0.0155, 0.016, 0.0165, 0.017):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["rear_right_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.015, 0.0155, 0.016, 0.0165, 0.017}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[1] == [0.0, 0.014]
        assert offsets[2] == [0.0, 0.01125]
        assert 0.015 <= offsets[3][1] <= 0.017
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_front_right_balance_grid_stays_inside_reachable_offsets() -> None:
    rows = recovery_grid_candidates("front_right_extension_balance")
    assert len(rows) == 25
    values = [row["parameters"]["front_right_extension_m"] for row in rows]
    for value in (0.010, 0.011, 0.012, 0.013, 0.014):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.010, 0.011, 0.012, 0.013, 0.014}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert 0.010 <= offsets[1][1] <= 0.014
        assert offsets[2] == [0.0, 0.01125]
        assert offsets[3] == [0.0, 0.015]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_front_right_upper_boundary_grid_has_quarter_mm_resolution() -> None:
    rows = recovery_grid_candidates("front_right_extension_upper_boundary")
    assert len(rows) == 25
    values = [row["parameters"]["front_right_extension_m"] for row in rows]
    for value in (0.014, 0.01425, 0.0145, 0.01475, 0.015):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.014, 0.01425, 0.0145, 0.01475, 0.015}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert 0.014 <= offsets[1][1] <= 0.015
        assert offsets[2] == [0.0, 0.01125]
        assert offsets[3] == [0.0, 0.015]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_front_right_reach_boundary_grid_continues_upward() -> None:
    rows = recovery_grid_candidates("front_right_extension_reach_boundary")
    assert len(rows) == 25
    values = [row["parameters"]["front_right_extension_m"] for row in rows]
    for value in (0.015, 0.0155, 0.016, 0.0165, 0.017):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.015, 0.0155, 0.016, 0.0165, 0.017}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert 0.015 <= offsets[1][1] <= 0.017
        assert offsets[2] == [0.0, 0.01125]
        assert offsets[3] == [0.0, 0.015]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_front_right_limit_grid_stops_at_declared_diagnostic_bound() -> None:
    rows = recovery_grid_candidates("front_right_extension_diagnostic_limit")
    assert len(rows) == 25
    values = [row["parameters"]["front_right_extension_m"] for row in rows]
    for value in (0.017, 0.01775, 0.0185, 0.01925, 0.020):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_extension_m"]
            for index in range(residue, 25, 5)
        } == {0.017, 0.01775, 0.0185, 0.01925, 0.020}
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert 0.017 <= offsets[1][1] <= 0.020
        assert offsets[2] == [0.0, 0.01125]
        assert offsets[3] == [0.0, 0.015]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_75mm_geometry_scale_grid_varies_only_selected_amplitude() -> None:
    rows = recovery_grid_candidates("post_transfer_geometry_height_scale_75")
    assert len(rows) == 25
    values = [
        row["parameters"]["selected_100mm_geometry_scale"] for row in rows
    ]
    for value in (0.50, 0.625, 0.75, 0.875, 1.00):
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["selected_100mm_geometry_scale"]
            for index in range(residue, 25, 5)
        } == {0.50, 0.625, 0.75, 0.875, 1.00}
    for row in rows:
        scale = row["parameters"]["selected_100mm_geometry_scale"]
        assert row["wheel_center_offsets_m"] == [
            [0.0, 0.0],
            [0.0, 0.0185 * scale],
            [0.0, 0.01125 * scale],
            [0.0, 0.015 * scale],
        ]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_75mm_front_right_grid_holds_reachable_half_rear_support() -> None:
    rows = recovery_grid_candidates(
        "front_right_extension_75_with_half_rear_support"
    )
    assert len(rows) == 25
    values = [row["parameters"]["front_right_extension_m"] for row in rows]
    expected = (0.00925, 0.0115625, 0.013875, 0.0161875, 0.0185)
    for value in expected:
        assert values.count(value) == 5
    for residue in range(5):
        assert {
            rows[index]["parameters"]["front_right_extension_m"]
            for index in range(residue, 25, 5)
        } == set(expected)
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[0] == [0.0, 0.0]
        assert offsets[1][0] == 0.0
        assert 0.00925 <= offsets[1][1] <= 0.0185
        assert offsets[2] == [0.0, 0.005625]
        assert offsets[3] == [0.0, 0.0075]
        assert row["post_transfer_offset_start_progress"] == 0.4


def test_75mm_early_front_right_grid_varies_amplitude_and_phase7_timing() -> None:
    rows = recovery_grid_candidates("front_right_early_activation_75")
    assert len(rows) == 25
    pairs = {
        (
            row["parameters"]["front_right_extension_m"],
            row["parameters"]["front_right_phase7_start_progress"],
        )
        for row in rows
    }
    assert len(pairs) == 25
    for row in rows:
        offsets = row["wheel_center_offsets_m"]
        assert offsets[2] == [0.0, 0.005625]
        assert offsets[3] == [0.0, 0.0075]
        assert row["post_transfer_leg_offset_start_phase"] == [9, 7, 9, 9]
        starts = row["post_transfer_leg_offset_start_progress"]
        assert starts[0] == starts[2] == starts[3] == 0.4
        assert starts[1] == row["parameters"][
            "front_right_phase7_start_progress"
        ]


def test_75mm_rear_transfer_grid_varies_only_front_wheel_speed() -> None:
    rows = recovery_grid_candidates("rear_transfer_front_wheel_speed_75")
    assert len(rows) == 25
    values = [
        row["parameters"]["rear_transfer_front_wheel_speed_rad_s"]
        for row in rows
    ]
    for value in (-0.3, -0.15, 0.0, 0.15, 0.3):
        assert values.count(value) == 5
    for row in rows:
        front_speed = row["parameters"][
            "rear_transfer_front_wheel_speed_rad_s"
        ]
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            front_speed,
            front_speed,
            0.3,
            0.3,
        ]
        assert row["wheel_center_offsets_m"] == [
            [0.0, 0.0],
            [0.0, 0.00925],
            [0.0, 0.005625],
            [0.0, 0.0075],
        ]


def test_75mm_zero_front_speed_grid_varies_only_front_right_extension() -> None:
    rows = recovery_grid_candidates(
        "front_right_extension_zero_transfer_front_speed_75"
    )
    assert len(rows) == 25
    values = [row["parameters"]["front_right_extension_m"] for row in rows]
    for value in (0.00925, 0.0115625, 0.013875, 0.0161875, 0.0185):
        assert values.count(value) == 5
    for row in rows:
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]
        offsets = row["wheel_center_offsets_m"]
        assert offsets[2] == [0.0, 0.005625]
        assert offsets[3] == [0.0, 0.0075]


def test_75mm_post_transfer_speed_grid_varies_only_post_transfer_speed() -> None:
    rows = recovery_grid_candidates(
        "post_transfer_forward_speed_zero_transfer_front_speed_75"
    )
    assert len(rows) == 25
    values = [
        row["parameters"]["post_transfer_forward_speed_rad_s"]
        for row in rows
    ]
    for value in (0.0, 0.0375, 0.075, 0.1125, 0.15):
        assert values.count(value) == 5
    for row in rows:
        speed = row["parameters"]["post_transfer_forward_speed_rad_s"]
        assert row["diagnostic_post_transfer_forward_speed_rad_s"] == speed
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]
        assert row["wheel_center_offsets_m"] == [
            [0.0, 0.0],
            [0.0, 0.00925],
            [0.0, 0.005625],
            [0.0, 0.0075],
        ]


def test_75mm_support_activation_grid_moves_only_common_start_earlier() -> None:
    rows = recovery_grid_candidates("support_activation_zero_post_speed_75")
    assert len(rows) == 25
    schedules = [
        (
            row["parameters"]["support_activation_phase"],
            row["parameters"]["support_activation_progress"],
        )
        for row in rows
    ]
    for schedule in ((8, 0.5), (8, 0.75), (9, 0.0), (9, 0.2), (9, 0.4)):
        assert schedules.count(schedule) == 5
    for row in rows:
        phase = row["parameters"]["support_activation_phase"]
        progress = row["parameters"]["support_activation_progress"]
        assert row["post_transfer_leg_offset_start_phase"] == [phase] * 4
        assert row["post_transfer_leg_offset_start_progress"] == [progress] * 4
        assert row["diagnostic_post_transfer_forward_speed_rad_s"] == 0.0
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]
        assert row["wheel_center_offsets_m"] == [
            [0.0, 0.0],
            [0.0, 0.00925],
            [0.0, 0.005625],
            [0.0, 0.0075],
        ]


def test_75mm_support_unload_grid_varies_only_bounded_shortening() -> None:
    rows = recovery_grid_candidates("support_unload_zero_post_speed_75")
    assert len(rows) == 25
    values = [
        row["parameters"]["support_unload_maximum_m"] for row in rows
    ]
    for value in (0.0, 0.0005, 0.0010, 0.0015, 0.0020):
        assert values.count(value) == 5
    for row in rows:
        maximum = row["parameters"]["support_unload_maximum_m"]
        assert row["diagnostic_support_unload_maximum_m"] == maximum
        assert row["diagnostic_support_unload_rate_m_s"] == 0.0005
        assert row["diagnostic_post_transfer_forward_speed_rad_s"] == 0.0
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]
        assert row["wheel_center_offsets_m"] == [
            [0.0, 0.0],
            [0.0, 0.00925],
            [0.0, 0.005625],
            [0.0, 0.0075],
        ]


def test_75mm_support_unload_rate_grid_fixes_two_mm_limit() -> None:
    rows = recovery_grid_candidates("support_unload_rate_zero_post_speed_75")
    assert len(rows) == 25
    values = [row["parameters"]["support_unload_rate_m_s"] for row in rows]
    for value in (0.00025, 0.0005, 0.00075, 0.0010, 0.0015):
        assert values.count(value) == 5
    for row in rows:
        rate = row["parameters"]["support_unload_rate_m_s"]
        assert row["parameters"]["support_unload_maximum_m"] == 0.002
        assert row["diagnostic_support_unload_maximum_m"] == 0.002
        assert row["diagnostic_support_unload_rate_m_s"] == rate
        assert row["diagnostic_post_transfer_forward_speed_rad_s"] == 0.0
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]


def test_75mm_combined_grid_varies_only_post_transfer_speed() -> None:
    rows = recovery_grid_candidates("post_transfer_speed_with_support_unload_75")
    assert len(rows) == 25
    values = [
        row["parameters"]["post_transfer_forward_speed_rad_s"]
        for row in rows
    ]
    for value in (0.0, 0.0375, 0.075, 0.1125, 0.15):
        assert values.count(value) == 5
    for row in rows:
        speed = row["parameters"]["post_transfer_forward_speed_rad_s"]
        assert row["diagnostic_post_transfer_forward_speed_rad_s"] == speed
        assert row["diagnostic_support_unload_maximum_m"] == 0.002
        assert row["diagnostic_support_unload_rate_m_s"] == 0.00075
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]


def test_75mm_selected_combined_grid_repeats_exact_candidate_25_times() -> None:
    rows = recovery_grid_candidates("selected_combined_repeat_75")
    assert len(rows) == 25
    assert [
        row["parameters"]["diagnostic_replicate"] for row in rows
    ] == list(range(25))
    for row in rows:
        assert row["parameters"]["post_transfer_forward_speed_rad_s"] == 0.075
        assert row["diagnostic_post_transfer_forward_speed_rad_s"] == 0.075
        assert row["diagnostic_support_unload_maximum_m"] == 0.002
        assert row["diagnostic_support_unload_rate_m_s"] == 0.00075
        assert row["diagnostic_rear_transfer_wheel_speed_rad_s"] == [
            0.0,
            0.0,
            0.3,
            0.3,
        ]
