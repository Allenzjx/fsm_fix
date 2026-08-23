"""Fairness checks for the two residual-PPO method configurations."""

from __future__ import annotations

from pathlib import Path

from resume_validation.config_io import differing_leaf_paths, load_config


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "configs"


def test_b_and_c_configs_only_differ_by_label_and_com_reward() -> None:
    without_com = load_config(CONFIG_ROOT / "ppo_without_com.yaml")
    with_com = load_config(CONFIG_ROOT / "ppo_with_com.yaml")
    assert differing_leaf_paths(without_com, with_com) == {
        "method",
        "reward.com_margin_weight",
    }
    assert without_com["reward"]["com_margin_weight"] == 0.0
    assert with_com["reward"]["com_margin_weight"] == 8.0


def test_common_runtime_v34_records_selected_phase9_counter_yaw_support() -> None:
    common = load_config(CONFIG_ROOT / "ppo_common.yaml")
    assert common["method_version"] == (
        "runtime-v34-selected-phase9-bound-counter-yaw-skid-steer-emergency"
    )
    assert common["protocol_version"] == "34.0.0"
    assert common["network"]["initial_log_std"] == -4.0
    assert common["network"]["min_log_std"] == -5.0
    assert common["network"]["max_log_std"] == -4.0
    assert "0.09158 mm" in common["network"][
        "stochastic_deterministic_alignment_policy"
    ]
    assert common["ppo"]["entropy_loss_scale"] == 0.0
    weights = common["reward"]["weights"]
    assert weights["success"] == 200.0
    assert weights["body_collision"] == -200.0
    assert weights["fall"] == -200.0
    assert weights["numerical"] == -200.0
    assert weights["phase_timeout"] == -200.0
    assert weights["joint_limit"] == -200.0
    assert weights["residual_magnitude"] == -120.0
    assert weights["residual_left_right_asymmetry"] == -180.0
    assert weights["action_rate"] == -0.1
    assert common["action"]["residual_bounds"]["wheel_speed_rad_s"] == 0.10
    assert common["action"]["residual_bounds"] == {
        "wheel_center_x_m": 0.0075,
        "wheel_center_z_m": 0.010,
        "wheel_speed_rad_s": 0.10,
    }
    assert common["action"]["execution_phase_window"] == [8, 10]
    assert common["action"]["execution_phase_gains"] == [3.0, 4.0, 3.0]
    assert common["action"]["applied_action_hard_clip"] == 1.0
    assert "phases 0 through 7" in common["action"]["execution_phase_policy"]
    assert "11 through 12" in common["action"]["execution_phase_policy"]
    state_gate = common["action"]["execution_state_gate"]
    assert state_gate["type"] == "phase_aware_roll_imu_emergency"
    assert state_gate["minimum_pitch_rad"] == 0.09
    assert state_gate["minimum_roll_rad"] == 0.10
    assert state_gate["early_roll_rad"] == 0.06
    assert state_gate["early_pitch_rate_rad_s"] == 0.35
    assert state_gate["corrective_latch_until_phase_exit"] is True
    assert "real-IMU" in state_gate["policy"]
    assert "scenario identity" in state_gate["policy"]
    assert "+0.330464 rad/s" in state_gate["threshold_derivation"]
    assert common["action"]["execution_projection"][
        "wheel_center_z_signs"
    ] == [-1, -1, 1, 1]
    assert common["action"]["execution_projection"][
        "executed_wheel_center_z_signs"
    ] == [0, -1, -1, 0]
    assert common["action"]["execution_projection"][
        "corrective_wheel_center_z_scales"
    ] == [0.0, 1.0, 1.0, 0.0]
    assert common["action"]["execution_projection"][
        "corrective_minimum_shared_magnitude"
    ] == 0.1
    assert common["action"]["execution_projection"]["type"] == (
        "wheel_center_z_deficient_diagonal_downward_support_phase9_counter_yaw_emergency_gate"
    )
    assert "0.068788 rad" in common["action"]["execution_projection"]["policy"]
    assert "[0,-1,-1,0]" in common["action"]["execution_projection"]["policy"]
    assert "preserve the FSM exactly" in common["action"][
        "execution_projection"
    ]["policy"]
    assert common["action"]["execution_projection"]["action_mask"] == [
        0,
        1,
        0,
        1,
        0,
        1,
        0,
        1,
        1,
        1,
        1,
        1,
    ]
    assert common["action"]["execution_projection"][
        "corrective_wheel_speed_signs"
    ] == [-1, 1, -1, 1]
    assert common["action"]["execution_projection"][
        "corrective_wheel_speed_minimum_shared_magnitudes"
    ] == [0.25]
    assert common["action"]["execution_projection"][
        "corrective_wheel_speed_scales"
    ] == [1.0, 1.0, 1.0, 1.0]
    assert common["action"]["execution_projection"][
        "corrective_wheel_speed_phases"
    ] == [9]
    assert common["training_budget"]["local_timesteps_by_stage"] == {
        "50": 76800,
        "75": 76800,
        "100": 76800,
    }
    assert "stuck" in common["reward"]["occupancy_integration"]
    assert "control step_dt" in common["reward"]["occupancy_integration"]
    assert "monotonic" in common["reward"]["phase_progress_definition"]
    assert "joint_acceleration" in common["reward"]["rate_integration"]
    assert "control step_dt" in common["reward"]["rate_integration"]
    assert "one-shot -200" in common["reward"]["terminal_safety"]
    assert "no current terminal root/body pose cache" in common["reward"][
        "reset_initialization"
    ]
    assert "-120/-180 per second" in common["reward"][
        "baseline_regularization_timebase"
    ]
    assert common["curriculum"]["stage_50_training_randomization"] == "full"
