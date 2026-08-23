"""Pure candidate generation for registered FSM recovery diagnostics."""

from __future__ import annotations

from typing import Any


def recovery_grid_candidates(kind: str) -> list[dict[str, Any]]:
    if kind == "front_right":
        x_values = (-0.015, -0.0075, 0.0, 0.0075, 0.015)
        z_values = (-0.010, -0.005, 0.0, 0.005, 0.010)
        rows = []
        for dx in x_values:
            for dz in z_values:
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1] = [dx, dz]
                rows.append(
                    {
                        "parameters": {
                            "front_right_offset_x_m": dx,
                            "front_right_offset_z_m": dz,
                        },
                        "wheel_center_offsets_m": offsets,
                    }
                )
        return rows
    if kind == "common_right_z":
        common_values = (-0.010, -0.005, 0.0, 0.005, 0.010)
        right_delta_values = (-0.005, -0.0025, 0.0, 0.0025, 0.005)
        rows = []
        for common_z in common_values:
            for right_delta_z in right_delta_values:
                offsets = [
                    [0.0, common_z],
                    [0.0, common_z + right_delta_z],
                    [0.0, common_z],
                    [0.0, common_z + right_delta_z],
                ]
                rows.append(
                    {
                        "parameters": {
                            "common_offset_z_m": common_z,
                            "right_side_delta_z_m": right_delta_z,
                        },
                        "wheel_center_offsets_m": offsets,
                    }
                )
        return rows
    if kind == "front_support_fr":
        hip_delta_values = (-3.0, 0.0, 5.0, 10.0, 15.0)
        knee_delta_values = (-15.0, -7.5, 0.0, 7.5, 15.0)
        rows = []
        for hip_delta_deg in hip_delta_values:
            for knee_delta_deg in knee_delta_values:
                command_offsets = [0.0] * 8
                command_offsets[2] = hip_delta_deg
                command_offsets[3] = knee_delta_deg
                rows.append(
                    {
                        "parameters": {
                            "front_right_hip_delta_deg": hip_delta_deg,
                            "front_right_knee_delta_deg": knee_delta_deg,
                        },
                        "wheel_center_offsets_m": [[0.0, 0.0] for _ in range(4)],
                        "front_support_command_offsets_deg": command_offsets,
                    }
                )
        return rows
    if kind == "front_support_unloaded_diagonal_z":
        # Grid 005 showed that the only collision-free phase-10 posture
        # (front-right hip/knee -3/-15 deg) transferred load onto the
        # front-right/rear-left diagonal, leaving front-left/rear-right at
        # 0.09/0.00 N.  Extend only that measured unloaded diagonal after the
        # rear transfer; candidate 0 is an exact zero-offset reproduction.
        extension_values = (0.0, 0.0015, 0.0030, 0.0045, 0.0060)
        rows = []
        for front_left_extension_m in extension_values:
            for rear_right_extension_m in extension_values:
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[0][1] = front_left_extension_m
                offsets[3][1] = rear_right_extension_m
                command_offsets = [0.0] * 8
                command_offsets[2] = -3.0
                command_offsets[3] = -15.0
                rows.append(
                    {
                        "parameters": {
                            "front_right_hip_delta_deg": -3.0,
                            "front_right_knee_delta_deg": -15.0,
                            "front_left_extension_m": front_left_extension_m,
                            "rear_right_extension_m": rear_right_extension_m,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": command_offsets,
                    }
                )
        return rows
    if kind == "rear_recovery_blend":
        # Attempt 020 proved that the formal 10% rear recovery never produced
        # even one sample with all four world-Z forces >= 2 N.  Sweep only this
        # path fraction.  Five exact replicates per value distribute each
        # intervention across environment indices because prior vectorized
        # diagnostics exposed contact-solver sensitivity before phase 9.
        blend_values = (0.0, 0.05, 0.10, 0.15, 0.20)
        rows = []
        for replicate in range(5):
            for maximum_blend in blend_values:
                rows.append(
                    {
                        "parameters": {
                            "rear_recovery_max_blend": maximum_blend,
                            "diagnostic_replicate": replicate,
                        },
                        "wheel_center_offsets_m": [[0.0, 0.0] for _ in range(4)],
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "rear_recovery_max_blend": maximum_blend,
                    }
                )
        return rows
    if kind == "rear_right_support_extension":
        # Attempt 020 measured the rear-right wheel center near 0.170 m during
        # phase 10 while the supported top plane was near 0.150 m. Extend only
        # that leg over the measured 0--20 mm gap. Rotate values through each
        # block so every value occupies every index residue, reducing the
        # pre-intervention solver-index confound observed in grid 008.
        extension_values = (0.0, 0.005, 0.010, 0.015, 0.020)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                extension_m = extension_values[(slot + replicate) % 5]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[3][1] = extension_m
                rows.append(
                    {
                        "parameters": {
                            "rear_right_extension_m": extension_m,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                    }
                )
        return rows
    if kind == "front_right_rear_left_support_extension":
        # Grid 009 established 15 mm rear-right extension as reachable and
        # loaded, but its collision-free branches then unloaded the
        # front-right/rear-left diagonal. Hold that rear-right geometry and
        # vary only a common extension on the measured unloaded diagonal.
        diagonal_values = (0.0, 0.002, 0.004, 0.006, 0.008)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                extension_m = diagonal_values[(slot + replicate) % 5]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = extension_m
                offsets[2][1] = extension_m
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "fixed_rear_right_extension_m": 0.015,
                            "front_right_rear_left_extension_m": extension_m,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                    }
                )
        return rows
    if kind == "front_right_rear_left_support_extension_wide":
        # Grid 012 showed that 2--8 mm candidates can enter the corrected
        # force-independent full-top window, but their best simultaneous
        # minimum upward force remains 0 N. Continue the same single variable
        # from the previous upper bound through the registered 20 mm
        # diagnostic limit; keep rear-right fixed at its reachable 15 mm.
        diagonal_values = (0.008, 0.011, 0.014, 0.017, 0.020)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                extension_m = diagonal_values[(slot + replicate) % 5]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = extension_m
                offsets[2][1] = extension_m
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "fixed_rear_right_extension_m": 0.015,
                            "front_right_rear_left_extension_m": extension_m,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "range_continuation_from_grid": 12,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                    }
                )
        return rows
    if kind == "post_transfer_offset_activation_start":
        # Grid 013 produced strict four-point support at 14 mm, but only after
        # the early phase-9 IK path had accumulated fallback steps. Hold the
        # successful lower amplitude and vary only when its smooth ramp starts
        # within phase 9. A zero-start candidate exactly reproduces the grid
        # 013 command path.
        start_values = (0.0, 0.2, 0.4, 0.6, 0.8)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                start_progress = start_values[(slot + replicate) % 5]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = 0.014
                offsets[2][1] = 0.014
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_front_right_rear_left_extension_m": 0.014,
                            "post_transfer_offset_start_progress": start_progress,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 13,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": start_progress,
                    }
                )
        return rows
    if kind == "rear_left_extension_relief":
        # Grid 014 isolated every successful-path IK fallback to the rear-left
        # leg. Keep the reachable front-right/rear-right amplitudes and the
        # best repeated phase-9 start, then reduce only rear-left extension.
        rear_left_values = (0.008, 0.0095, 0.011, 0.0125, 0.014)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                rear_left_extension_m = rear_left_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = 0.014
                offsets[2][1] = rear_left_extension_m
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "fixed_front_right_extension_m": 0.014,
                            "rear_left_extension_m": rear_left_extension_m,
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 14,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "rear_left_extension_boundary":
        # Grid 015 found a zero-fallback 11 mm branch with a one-step 2.073 N
        # four-wheel minimum, while 12.5 mm was unreachable. Resolve the
        # narrow admissible load/dwell boundary without changing any other
        # command.
        rear_left_values = (0.011, 0.01125, 0.0115, 0.01175, 0.012)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                rear_left_extension_m = rear_left_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = 0.014
                offsets[2][1] = rear_left_extension_m
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "fixed_front_right_extension_m": 0.014,
                            "rear_left_extension_m": rear_left_extension_m,
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 15,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "rear_left_activation_start":
        # Grid 016 found strong strict support at 11.5 mm, with every fallback
        # isolated to rear-left before that target became reachable. Preserve
        # all amplitudes and the other three start values, then delay only the
        # rear-left phase-9 ramp.
        rear_left_start_values = (0.4, 0.5, 0.6, 0.7, 0.8)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                rear_left_start = rear_left_start_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = 0.014
                offsets[2][1] = 0.0115
                offsets[3][1] = 0.015
                per_leg_start = [0.4, 0.4, rear_left_start, 0.4]
                rows.append(
                    {
                        "parameters": {
                            "fixed_front_right_extension_m": 0.014,
                            "fixed_rear_left_extension_m": 0.0115,
                            "fixed_rear_right_extension_m": 0.015,
                            "rear_left_offset_start_progress": rear_left_start,
                            "other_leg_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 16,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_leg_offset_start_progress": per_leg_start,
                    }
                )
        return rows
    if kind == "rear_right_extension_boundary":
        # With rear-left held at its zero-fallback 11.25 mm limit, grid 016
        # showed rear-right as the only unloaded wheel (0.245 N best). Increase
        # only rear-right from its known-reachable 15 mm value in 0.5 mm steps
        # and reject any value that introduces per-leg fallback.
        rear_right_values = (0.015, 0.0155, 0.016, 0.0165, 0.017)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                rear_right_extension_m = rear_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = 0.014
                offsets[2][1] = 0.01125
                offsets[3][1] = rear_right_extension_m
                rows.append(
                    {
                        "parameters": {
                            "fixed_front_right_extension_m": 0.014,
                            "fixed_rear_left_extension_m": 0.01125,
                            "rear_right_extension_m": rear_right_extension_m,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 17,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "front_right_extension_balance":
        # Grid 018 proved rear-right cannot exceed 15 mm without fallback.
        # At the reachable FR/RL/RR=14/11.25/15 mm state, front-right carried
        # about 14 N while rear-right carried only 0.245 N. Reduce only
        # front-right extension to transfer load to the opposite right corner.
        front_right_values = (0.010, 0.011, 0.012, 0.013, 0.014)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_right_extension_m = front_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.01125
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "fixed_rear_left_extension_m": 0.01125,
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 18,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "front_right_extension_upper_boundary":
        # Grid 019 falsified the proposed downward redistribution: reducing
        # front-right from 14 mm never improved the rear-right load. The best
        # fully reachable snapshot instead occurred at 14 mm (1.652 N
        # simultaneous minimum). Resolve the immediately adjacent upper
        # boundary in 0.25 mm steps and reject any value that introduces a
        # front-right IK fallback.
        front_right_values = (0.014, 0.01425, 0.0145, 0.01475, 0.015)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_right_extension_m = front_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.01125
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "fixed_rear_left_extension_m": 0.01125,
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 19,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "front_right_extension_reach_boundary":
        # Grid 020 obtained the first fully reachable threshold crossing at
        # 14.5 mm (2.165 N), but it lasted only one control step. Since every
        # value through 15 mm remained zero-fallback, continue upward in
        # 0.5 mm steps to locate sustained support or the actual front-right
        # reach boundary.
        front_right_values = (0.015, 0.0155, 0.016, 0.0165, 0.017)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_right_extension_m = front_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.01125
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "fixed_rear_left_extension_m": 0.01125,
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 20,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "front_right_extension_diagnostic_limit":
        # Grid 021 remained zero-fallback through 17 mm and extended the
        # admissible full-force dwell to 0.15 s. Cover the remaining legal
        # diagnostic interval through the declared 20 mm limit.
        front_right_values = (0.017, 0.01775, 0.0185, 0.01925, 0.020)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_right_extension_m = front_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.01125
                offsets[3][1] = 0.015
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "fixed_rear_left_extension_m": 0.01125,
                            "fixed_rear_right_extension_m": 0.015,
                            "fixed_post_transfer_offset_start_progress": 0.4,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 21,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "post_transfer_geometry_height_scale_75":
        # Formal 75 mm attempt 029 applied 50% of the selected 100 mm
        # support geometry. Every target remained reachable, but no candidate
        # environment ever entered complete all-wheel top geometry and all 20
        # collided at front_right_bot. Vary only the common amplitude scale;
        # Latin rotation distributes each value across every index residue.
        scale_values = (0.50, 0.625, 0.75, 0.875, 1.00)
        selected_100mm_offsets = (
            (0.0, 0.0),
            (0.0, 0.0185),
            (0.0, 0.01125),
            (0.0, 0.015),
        )
        rows = []
        for replicate in range(5):
            for slot in range(5):
                scale = scale_values[(slot + replicate) % 5]
                offsets = [
                    [value_x * scale, value_z * scale]
                    for value_x, value_z in selected_100mm_offsets
                ]
                rows.append(
                    {
                        "parameters": {
                            "selected_100mm_geometry_scale": scale,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_attempt": 29,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "front_right_extension_75_with_half_rear_support":
        # Grid 030 proved that common scales above 50% become unreachable
        # only on rear-left, while front-right remains reachable through the
        # full 18.5 mm selected endpoint. Hold both rear offsets at their
        # reachable 50% values and continue only front-right.
        front_right_values = (
            0.00925,
            0.0115625,
            0.013875,
            0.0161875,
            0.0185,
        )
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_right_extension_m = front_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.005625
                offsets[3][1] = 0.0075
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "fixed_rear_left_extension_m": 0.005625,
                            "fixed_rear_right_extension_m": 0.0075,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 30,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                    }
                )
        return rows
    if kind == "front_right_early_activation_75":
        # Attempt 029 telemetry had front-right fully on top at 105 s in
        # phase 7, but it was already off top by 110 s in phase 8. Grid 031
        # proved the full front-right amplitude range reachable when applied
        # late. Ramp only that leg during phase 7; retain phase-9 activation
        # and reachable half-scale values on both rear legs.
        front_right_values = (
            0.00925,
            0.0115625,
            0.013875,
            0.0161875,
            0.0185,
        )
        start_progress_values = (0.0, 0.2, 0.4, 0.6, 0.8)
        rows = []
        for front_right_extension_m in front_right_values:
            for start_progress in start_progress_values:
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.005625
                offsets[3][1] = 0.0075
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "front_right_phase7_start_progress": start_progress,
                            "fixed_rear_left_extension_m": 0.005625,
                            "fixed_rear_right_extension_m": 0.0075,
                            "source_grid": 31,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_leg_offset_start_progress": [
                            0.4,
                            start_progress,
                            0.4,
                            0.4,
                        ],
                        "post_transfer_leg_offset_start_phase": [9, 7, 9, 9],
                    }
                )
        return rows
    if kind == "rear_transfer_front_wheel_speed_75":
        # Grids 031/032 proved that reachable front-right support geometry
        # cannot compensate for the all-wheel +0.3 rad/s phase-7/8 fallback.
        # Keep the rear wheels at the measured forward speed and vary only
        # the two front wheels, with five Latin replicates per value.
        front_speed_values = (-0.3, -0.15, 0.0, 0.15, 0.3)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_speed = front_speed_values[(slot + replicate) % 5]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = 0.00925
                offsets[2][1] = 0.005625
                offsets[3][1] = 0.0075
                rows.append(
                    {
                        "parameters": {
                            "rear_transfer_front_wheel_speed_rad_s": front_speed,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 32,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            front_speed,
                            front_speed,
                            0.3,
                            0.3,
                        ],
                    }
                )
        return rows
    if kind == "front_right_extension_zero_transfer_front_speed_75":
        # Grid 033 found that zero front-wheel speed during phases 7--8 is the
        # only tested split with repeatable complete-top eligibility. Hold it
        # and vary only the reachable phase-9 front-right support amplitude.
        front_right_values = (
            0.00925,
            0.0115625,
            0.013875,
            0.0161875,
            0.0185,
        )
        rows = []
        for replicate in range(5):
            for slot in range(5):
                front_right_extension_m = front_right_values[
                    (slot + replicate) % 5
                ]
                offsets = [[0.0, 0.0] for _ in range(4)]
                offsets[1][1] = front_right_extension_m
                offsets[2][1] = 0.005625
                offsets[3][1] = 0.0075
                rows.append(
                    {
                        "parameters": {
                            "front_right_extension_m": front_right_extension_m,
                            "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 33,
                        },
                        "wheel_center_offsets_m": offsets,
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            0.0,
                            0.0,
                            0.3,
                            0.3,
                        ],
                    }
                )
        return rows
    if kind == "post_transfer_forward_speed_zero_transfer_front_speed_75":
        # Grid 034 showed that phase-9 front-right amplitude does not extend
        # the transient four-wheel force window. Hold the reachable half-scale
        # geometry and the grid-033 rear-transfer speed split, then vary only
        # the exact phase-9/10 forward speed below the formal 0.15 rad/s value.
        post_transfer_speed_values = (0.0, 0.0375, 0.075, 0.1125, 0.15)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                post_transfer_speed = post_transfer_speed_values[
                    (slot + replicate) % 5
                ]
                rows.append(
                    {
                        "parameters": {
                            "post_transfer_forward_speed_rad_s": (
                                post_transfer_speed
                            ),
                            "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 34,
                        },
                        "wheel_center_offsets_m": [
                            [0.0, 0.0],
                            [0.0, 0.00925],
                            [0.0, 0.005625],
                            [0.0, 0.0075],
                        ],
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            0.0,
                            0.0,
                            0.3,
                            0.3,
                        ],
                        "diagnostic_post_transfer_forward_speed_rad_s": (
                            post_transfer_speed
                        ),
                    }
                )
        return rows
    if kind == "support_activation_zero_post_speed_75":
        # Grid 035 found a 0.5667 s strict run that was still active at the
        # immutable 150 s timeout with zero post-transfer drive. Move only the
        # same reachable support geometry earlier so its settling window is
        # available before timeout. The final schedule is the grid-035
        # baseline; the other four are progressively earlier.
        activation_schedules = (
            (8, 0.50),
            (8, 0.75),
            (9, 0.00),
            (9, 0.20),
            (9, 0.40),
        )
        rows = []
        for replicate in range(5):
            for slot in range(5):
                start_phase, start_progress = activation_schedules[
                    (slot + replicate) % 5
                ]
                rows.append(
                    {
                        "parameters": {
                            "support_activation_phase": start_phase,
                            "support_activation_progress": start_progress,
                            "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "fixed_post_transfer_forward_speed_rad_s": 0.0,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 35,
                        },
                        "wheel_center_offsets_m": [
                            [0.0, 0.0],
                            [0.0, 0.00925],
                            [0.0, 0.005625],
                            [0.0, 0.0075],
                        ],
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_leg_offset_start_progress": [
                            start_progress
                        ] * 4,
                        "post_transfer_leg_offset_start_phase": [
                            start_phase
                        ] * 4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            0.0,
                            0.0,
                            0.3,
                            0.3,
                        ],
                        "diagnostic_post_transfer_forward_speed_rad_s": 0.0,
                    }
                )
        return rows
    if kind == "support_unload_zero_post_speed_75":
        # Grids 035/036 show late diagonal rocking: front-left/rear-right
        # remain highly loaded while front-right/rear-left repeatedly cross
        # the 2 N threshold. Keep the best late-settling timing and gently
        # shorten only legs above the existing 8 N hysteresis threshold.
        unload_maximum_values = (0.0, 0.0005, 0.0010, 0.0015, 0.0020)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                maximum_m = unload_maximum_values[(slot + replicate) % 5]
                rows.append(
                    {
                        "parameters": {
                            "support_unload_maximum_m": maximum_m,
                            "support_unload_rate_m_s": 0.0005,
                            "fixed_support_activation_phase": 9,
                            "fixed_support_activation_progress": 0.4,
                            "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "fixed_post_transfer_forward_speed_rad_s": 0.0,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 36,
                        },
                        "wheel_center_offsets_m": [
                            [0.0, 0.0],
                            [0.0, 0.00925],
                            [0.0, 0.005625],
                            [0.0, 0.0075],
                        ],
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            0.0,
                            0.0,
                            0.3,
                            0.3,
                        ],
                        "diagnostic_post_transfer_forward_speed_rad_s": 0.0,
                        "diagnostic_support_unload_maximum_m": maximum_m,
                        "diagnostic_support_unload_rate_m_s": 0.0005,
                    }
                )
        return rows
    if kind == "support_unload_rate_zero_post_speed_75":
        # Grid 037 moved load in the measured direction with zero fallback:
        # the 2 mm candidates ended with roughly balanced wheel forces and up
        # to 1.25 s strict dwell, but the 0.5 mm/s controller reached its
        # bound late. Hold the 2 mm limit and vary only convergence rate.
        unload_rate_values = (0.00025, 0.0005, 0.00075, 0.0010, 0.0015)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                rate_m_s = unload_rate_values[(slot + replicate) % 5]
                rows.append(
                    {
                        "parameters": {
                            "support_unload_maximum_m": 0.0020,
                            "support_unload_rate_m_s": rate_m_s,
                            "fixed_support_activation_phase": 9,
                            "fixed_support_activation_progress": 0.4,
                            "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "fixed_post_transfer_forward_speed_rad_s": 0.0,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 37,
                        },
                        "wheel_center_offsets_m": [
                            [0.0, 0.0],
                            [0.0, 0.00925],
                            [0.0, 0.005625],
                            [0.0, 0.0075],
                        ],
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            0.0,
                            0.0,
                            0.3,
                            0.3,
                        ],
                        "diagnostic_post_transfer_forward_speed_rad_s": 0.0,
                        "diagnostic_support_unload_maximum_m": 0.0020,
                        "diagnostic_support_unload_rate_m_s": rate_m_s,
                    }
                )
        return rows
    if kind == "post_transfer_speed_with_support_unload_75":
        # Grid 038 produced the first strict 75 mm success at a 2 mm bound and
        # 0.75 mm/s rate. Earlier speed grids showed that modest post-transfer
        # drive greatly increases complete-top samples but could not hold the
        # force state. Combine those independently measured mechanisms while
        # varying only phase-9/10 forward speed.
        post_transfer_speed_values = (0.0, 0.0375, 0.075, 0.1125, 0.15)
        rows = []
        for replicate in range(5):
            for slot in range(5):
                post_transfer_speed = post_transfer_speed_values[
                    (slot + replicate) % 5
                ]
                rows.append(
                    {
                        "parameters": {
                            "post_transfer_forward_speed_rad_s": (
                                post_transfer_speed
                            ),
                            "fixed_support_unload_maximum_m": 0.0020,
                            "fixed_support_unload_rate_m_s": 0.00075,
                            "fixed_support_activation_phase": 9,
                            "fixed_support_activation_progress": 0.4,
                            "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                            "fixed_rear_wheel_speed_rad_s": 0.3,
                            "diagnostic_replicate": replicate,
                            "latin_slot": slot,
                            "source_grid": 38,
                        },
                        "wheel_center_offsets_m": [
                            [0.0, 0.0],
                            [0.0, 0.00925],
                            [0.0, 0.005625],
                            [0.0, 0.0075],
                        ],
                        "front_support_command_offsets_deg": [0.0] * 8,
                        "post_transfer_offset_start_progress": 0.4,
                        "diagnostic_rear_transfer_wheel_speed_rad_s": [
                            0.0,
                            0.0,
                            0.3,
                            0.3,
                        ],
                        "diagnostic_post_transfer_forward_speed_rad_s": (
                            post_transfer_speed
                        ),
                        "diagnostic_support_unload_maximum_m": 0.0020,
                        "diagnostic_support_unload_rate_m_s": 0.00075,
                    }
                )
        return rows
    if kind == "selected_combined_repeat_75":
        # Grid 039 selected 0.075 rad/s by group evidence: it had the highest
        # mean strict dwell and four of five replicates reached at least
        # 0.833 s, including one strict success. Repeat the exact combined
        # controller in all 25 environments before any formal promotion.
        rows = []
        for replicate in range(25):
            rows.append(
                {
                    "parameters": {
                        "post_transfer_forward_speed_rad_s": 0.075,
                        "support_unload_maximum_m": 0.0020,
                        "support_unload_rate_m_s": 0.00075,
                        "fixed_support_activation_phase": 9,
                        "fixed_support_activation_progress": 0.4,
                        "fixed_rear_transfer_front_wheel_speed_rad_s": 0.0,
                        "fixed_rear_wheel_speed_rad_s": 0.3,
                        "diagnostic_replicate": replicate,
                        "source_grid": 39,
                    },
                    "wheel_center_offsets_m": [
                        [0.0, 0.0],
                        [0.0, 0.00925],
                        [0.0, 0.005625],
                        [0.0, 0.0075],
                    ],
                    "front_support_command_offsets_deg": [0.0] * 8,
                    "post_transfer_offset_start_progress": 0.4,
                    "diagnostic_rear_transfer_wheel_speed_rad_s": [
                        0.0,
                        0.0,
                        0.3,
                        0.3,
                    ],
                    "diagnostic_post_transfer_forward_speed_rad_s": 0.075,
                    "diagnostic_support_unload_maximum_m": 0.0020,
                    "diagnostic_support_unload_rate_m_s": 0.00075,
                }
            )
        return rows
    raise ValueError(f"Unknown recovery grid kind: {kind}")
