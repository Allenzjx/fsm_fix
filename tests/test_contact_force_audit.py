from pathlib import Path


def test_evaluator_records_magnitude_and_upward_contact_force_separately() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "evaluate_controller.py"
    ).read_text(encoding="utf-8")
    for field in (
        "fl_contact_force_n",
        "fl_contact_upward_force_n",
        "contact_force_magnitude_n",
        "contact_upward_force_n",
        "terminal_wheel_contact_force_magnitude_n",
        "terminal_wheel_contact_upward_force_n",
        "fl_full_wheel_on_top",
        "all_wheels_on_top",
        "support_score",
        "fl_wheel_y_m",
    ):
        assert field in source


def test_diagnostic_grid_tracks_upward_force_quality_over_time() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "diagnose_fsm_recovery_grid.py"
    ).read_text(encoding="utf-8")
    for field in (
        "diagnostic_post_transfer_top_maximum_minimum_wheel_upward_force_n",
        "diagnostic_longest_success_condition_dwell_s",
        "eligible_without_force",
        "diagnostic_post_transfer_top_eligible_sample_count",
        "diagnostic_post_transfer_top_maximum_wheel_upward_force_n",
        "diagnostic_best_minimum_upward_force_snapshot",
    ):
        assert field in source


def test_formal_evaluator_records_per_leg_reachability_and_clamp_counts() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "evaluate_controller.py"
    ).read_text(encoding="utf-8")
    assert "terminal_fsm_baseline_ik_invalid_count_per_leg" in source
    assert "terminal_fsm_diagnostic_front_support_clamp_count" in source


def test_formal_all_wheels_on_top_excludes_legacy_geometry_collision_proxy() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "residual_rl_env.py"
    ).read_text(encoding="utf-8")
    method = source.split("    def _refresh_contact_state(self) -> None:", 1)[1].split(
        "\n    def ", 1
    )[0]
    assert "super()._refresh_contact_state()" in method
    assert "torch.all(self._full_wheel_on_top, dim=1)" in method
    assert 'support["score"] >= 0.45' in method
    assert "_nonwheel_obstacle_contact_count" not in method.split(
        "self._all_wheels_on_top =", 1
    )[1]


def test_metric_config_declares_sensor_based_nonwheel_contact_policy() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "configs" / "metrics.yaml"
    ).read_text(encoding="utf-8")
    assert "ContactSensor net external force magnitude" in source
    assert "bounding-box estimates are diagnostic only" in source


def test_partial_training_reset_subsets_per_environment_wheel_radius() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "residual_rl_env.py"
    ).read_text(encoding="utf-8")
    method = source.split(
        "    def _apply_training_randomization(self, env_ids: torch.Tensor) -> None:",
        1,
    )[1].split("\n    def ", 1)[0]
    assert "self._estimated_wheel_radius[env_ids]" in method
    assert "\n            + self._estimated_wheel_radius\n" not in method


def test_occupancy_rewards_are_integrated_in_seconds() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "residual_rl_env.py"
    ).read_text(encoding="utf-8")
    method = source.split("    def _get_rewards(self) -> torch.Tensor:", 1)[1].split(
        "\n    def ", 1
    )[0]
    top_contact = method.split('"top_contact":', 1)[1].split('"recovery":', 1)[0]
    recovery = method.split('"recovery":', 1)[1].split('"com_margin":', 1)[0]
    assert "float(self.step_dt)" in top_contact
    assert "float(self.step_dt)" in recovery


def test_evaluator_records_complete_residual_action_chain() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "evaluate_controller.py"
    ).read_text(encoding="utf-8")
    for field in (
        "policy_action_",
        "executed_action_",
        "scaled_wheel_center_residual_m_",
        "scaled_wheel_speed_residual_rad_s_",
        "requested_wheel_center_target_m_",
        "final_wheel_center_target_m_",
        "final_servo_target_rad_",
        "final_wheel_target_rad_s_",
    ):
        assert field in source
