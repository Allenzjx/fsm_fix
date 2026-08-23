import unittest
from pathlib import Path


class LoadBalanceTest(unittest.TestCase):
    def test_front_support_offset_ramps_then_holds_without_phase_jump(self):
        import torch

        from resume_validation.load_balance import front_support_offset_scale

        phase = torch.tensor([5, 6, 6, 7, 10, 11])
        progress = torch.tensor([1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
        scale = front_support_offset_scale(phase, progress)
        self.assertEqual(scale.tolist(), [0.0, 0.0, 1.0, 1.0, 1.0, 0.0])

    def test_formal_unload_policy_is_enabled_only_at_75mm_anchor(self):
        from resume_validation.config_io import load_config
        from resume_validation.load_balance import formal_support_unload_policy

        config = load_config(
            Path(__file__).resolve().parents[1] / "configs" / "fsm.yaml"
        )
        self.assertTrue(config["support_load_balance"]["enabled"])
        policy_50 = formal_support_unload_policy(config, 0.05)
        policy_75 = formal_support_unload_policy(config, 0.075)
        policy_100 = formal_support_unload_policy(config, 0.10)
        self.assertEqual(policy_50, (4.0, 8.0, 0.00075, 0.0))
        self.assertEqual(policy_75, (4.0, 8.0, 0.00075, 0.002))
        self.assertEqual(policy_100, (4.0, 8.0, 0.00075, 0.0))

    def test_formal_config_records_deployed_support_target_and_drive_speed(self):
        from resume_validation.config_io import load_config

        config = load_config(
            Path(__file__).resolve().parents[1] / "configs" / "fsm.yaml"
        )
        coordination = config["rear_transfer_reference"][
            "body_transfer_coordination"
        ]
        self.assertEqual(
            coordination["front_support_target_deg"],
            [6.2, 2.3, 1.8, -4.4],
        )
        self.assertEqual(
            config["rear_transfer_reference"]["post_transfer_drive"][
                "maximum_physical_forward_speed_rad_s"
            ],
            0.3,
        )

    def test_formal_drive_anchors_preserve_endpoints_and_select_grid040_at_75mm(self):
        from resume_validation.config_io import load_config
        from resume_validation.load_balance import (
            formal_post_transfer_drive_speed,
            formal_rear_transfer_wheel_speed,
        )

        config = load_config(
            Path(__file__).resolve().parents[1] / "configs" / "fsm.yaml"
        )
        self.assertEqual(
            formal_rear_transfer_wheel_speed(config, 0.05),
            (0.3, 0.3, 0.3, 0.3),
        )
        self.assertEqual(
            formal_rear_transfer_wheel_speed(config, 0.075),
            (0.0, 0.0, 0.3, 0.3),
        )
        self.assertEqual(
            formal_rear_transfer_wheel_speed(config, 0.10),
            (0.3, 0.3, 0.3, 0.3),
        )
        self.assertEqual(formal_post_transfer_drive_speed(config, 0.05), 0.0)
        self.assertEqual(formal_post_transfer_drive_speed(config, 0.075), 0.075)
        self.assertEqual(formal_post_transfer_drive_speed(config, 0.10), 0.3)

    def test_formal_config_promotes_reachable_grid_022_geometry(self):
        from resume_validation.config_io import load_config
        from resume_validation.load_balance import (
            formal_post_transfer_support_geometry,
        )

        config = load_config(
            Path(__file__).resolve().parents[1] / "configs" / "fsm.yaml"
        )
        offsets, starts = formal_post_transfer_support_geometry(config)
        self.assertEqual(
            offsets,
            (
                (0.0, 0.0),
                (0.0, 0.0185),
                (0.0, 0.01125),
                (0.0, 0.015),
            ),
        )
        self.assertEqual(starts, (0.4, 0.4, 0.4, 0.4))

    def test_formal_geometry_is_height_conditioned_without_changing_100mm_target(self):
        from resume_validation.config_io import load_config
        from resume_validation.load_balance import (
            formal_post_transfer_support_geometry,
        )

        config = load_config(
            Path(__file__).resolve().parents[1] / "configs" / "fsm.yaml"
        )
        offsets_50, _ = formal_post_transfer_support_geometry(config, 0.05)
        offsets_75, _ = formal_post_transfer_support_geometry(config, 0.075)
        offsets_100, _ = formal_post_transfer_support_geometry(config, 0.10)
        self.assertEqual(offsets_50, ((0.0, 0.0),) * 4)
        expected_75 = (
            (0.0, 0.0),
            (0.0, 0.00925),
            (0.0, 0.005625),
            (0.0, 0.0075),
        )
        for actual_row, expected_row in zip(
            offsets_75, expected_75, strict=True
        ):
            for actual, expected in zip(actual_row, expected_row, strict=True):
                self.assertAlmostEqual(actual, expected, places=12)
        self.assertEqual(
            offsets_100,
            (
                (0.0, 0.0),
                (0.0, 0.0185),
                (0.0, 0.01125),
                (0.0, 0.015),
            ),
        )

    def test_formal_geometry_rejects_offsets_above_diagnostic_limit(self):
        from resume_validation.load_balance import (
            formal_post_transfer_support_geometry,
        )

        with self.assertRaisesRegex(ValueError, "20 mm limit"):
            formal_post_transfer_support_geometry(
                {
                    "post_transfer_support_geometry": {
                        "enabled": True,
                        "wheel_center_offsets_m": [
                            [0.0, 0.0],
                            [0.0, 0.0201],
                            [0.0, 0.0],
                            [0.0, 0.0],
                        ],
                        "offset_start_progress_per_leg": [0.4] * 4,
                    }
                }
            )

    def test_post_transfer_offset_is_continuous_across_recover_and_drive_clear(self):
        import torch

        from resume_validation.load_balance import post_transfer_offset_scale

        phase = torch.tensor([8, 9, 9, 10, 10, 11])
        progress = torch.tensor([1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
        scale = post_transfer_offset_scale(phase, progress)
        self.assertEqual(scale.tolist(), [0.0, 0.0, 1.0, 1.0, 1.0, 0.0])

    def test_post_transfer_offset_can_delay_phase9_ramp_without_phase10_gap(self):
        import torch

        from resume_validation.load_balance import post_transfer_offset_scale

        phase = torch.tensor([9, 9, 9, 9, 10])
        progress = torch.tensor([0.0, 0.4, 0.7, 1.0, 0.0])
        start = torch.tensor([0.4] * 5)
        scale = post_transfer_offset_scale(phase, progress, start)
        self.assertEqual(scale[0].item(), 0.0)
        self.assertEqual(scale[1].item(), 0.0)
        self.assertAlmostEqual(scale[2].item(), 0.5, places=6)
        self.assertEqual(scale[3].item(), 1.0)
        self.assertEqual(scale[4].item(), 1.0)

    def test_post_transfer_offset_can_ramp_in_phase7_and_hold_to_phase10(self):
        import torch

        from resume_validation.load_balance import post_transfer_offset_scale

        phase = torch.tensor([6, 7, 7, 8, 9, 10, 11])
        progress = torch.tensor([1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
        scale = post_transfer_offset_scale(
            phase,
            progress,
            start_phase=torch.tensor([7] * 7),
        )
        self.assertEqual(scale.tolist(), [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0])

    def test_post_transfer_forward_speed_is_height_conditioned_and_phase_limited(self):
        import torch

        from resume_validation.load_balance import post_transfer_forward_speed

        phase = torch.tensor([9, 9, 10, 8, 11])
        height = torch.tensor([0.05, 0.075, 0.10, 0.10, 0.10])
        speed = post_transfer_forward_speed(
            phase,
            height,
            maximum_rad_s=0.3,
        )
        expected = [0.0, 0.15, 0.3, 0.0, 0.0]
        for actual, target in zip(speed.tolist(), expected, strict=True):
            self.assertAlmostEqual(actual, target, places=6)

    def test_rear_transfer_wheel_speed_uses_only_finite_diagnostic_overrides(self):
        import torch

        from resume_validation.load_balance import rear_transfer_wheel_speed

        speed = rear_transfer_wheel_speed(
            torch.tensor(
                [
                    [float("nan"), float("nan"), float("nan"), float("nan")],
                    [-0.15, -0.15, 0.3, 0.3],
                ]
            )
        )
        torch.testing.assert_close(
            speed,
            torch.tensor(
                [
                    [0.3, 0.3, 0.3, 0.3],
                    [-0.15, -0.15, 0.3, 0.3],
                ]
            ),
        )

    def test_rear_transfer_wheel_speed_broadcasts_formal_per_wheel_default(self):
        import torch

        from resume_validation.load_balance import rear_transfer_wheel_speed

        speed = rear_transfer_wheel_speed(
            torch.full((2, 4), float("nan")),
            default_physical_forward_rad_s=(0.0, 0.0, 0.3, 0.3),
        )
        torch.testing.assert_close(
            speed,
            torch.tensor(
                [
                    [0.0, 0.0, 0.3, 0.3],
                    [0.0, 0.0, 0.3, 0.3],
                ]
            ),
        )

    def test_post_transfer_forward_speed_stops_to_capture_all_wheel_support(self):
        import torch

        from resume_validation.load_balance import post_transfer_forward_speed

        speed = post_transfer_forward_speed(
            torch.tensor([9, 10, 10]),
            torch.tensor([0.10, 0.10, 0.075]),
            torch.tensor([False, True, True]),
            maximum_rad_s=0.3,
        )
        self.assertEqual(speed.tolist(), [0.30000001192092896, 0.0, 0.0])

    def test_post_transfer_forward_speed_uses_only_finite_diagnostic_overrides(self):
        import torch

        from resume_validation.load_balance import post_transfer_forward_speed

        speed = post_transfer_forward_speed(
            torch.tensor([9, 10, 10, 8]),
            torch.tensor([0.075, 0.075, 0.10, 0.075]),
            torch.tensor([False, False, True, False]),
            maximum_rad_s=0.3,
            diagnostic_active_speed_rad_s=torch.tensor(
                [float("nan"), 0.0375, 0.15, 0.15]
            ),
        )
        torch.testing.assert_close(
            speed,
            torch.tensor([0.15, 0.0375, 0.0, 0.0]),
        )

    def test_post_transfer_forward_speed_accepts_formal_anchor_before_diagnostic(self):
        import torch

        from resume_validation.load_balance import post_transfer_forward_speed

        speed = post_transfer_forward_speed(
            torch.tensor([9, 10, 8]),
            torch.tensor([0.075, 0.075, 0.075]),
            maximum_rad_s=0.3,
            formal_active_speed_rad_s=0.075,
            diagnostic_active_speed_rad_s=torch.tensor(
                [float("nan"), 0.1125, float("nan")]
            ),
        )
        torch.testing.assert_close(
            speed,
            torch.tensor([0.075, 0.1125, 0.0]),
        )

    def test_post_transfer_capture_stops_on_geometry_before_force_builds(self):
        import torch

        from resume_validation.load_balance import post_transfer_capture_ready

        ready = post_transfer_capture_ready(
            torch.tensor([True, False, False]),
            torch.tensor(
                [
                    [0.0, 0.0, 0.0, 0.0],
                    [2.0, 3.0, 4.0, 5.0],
                    [2.0, 3.0, 4.0, 0.0],
                ]
            ),
            force_threshold_n=2.0,
        )
        self.assertEqual(ready.tolist(), [True, True, False])

    def test_hysteresis_increases_holds_decreases_and_resets(self):
        import torch

        from resume_validation.load_balance import update_load_trim

        current = torch.tensor([[0.001, 0.001, 0.009, 0.001]])
        force = torch.tensor([[1.0, 3.0, 1.0, 5.0]])
        active = torch.tensor([True])
        updated = update_load_trim(
            current,
            force,
            active,
            dt_s=0.1,
            low_force_n=2.0,
            high_force_n=4.0,
            rate_m_s=0.01,
            maximum_m=0.01,
        )
        expected = [0.002, 0.001, 0.01, 0.0]
        for actual, target in zip(updated[0].tolist(), expected, strict=True):
            self.assertAlmostEqual(actual, target, places=6)

        reset = update_load_trim(
            updated,
            force,
            torch.tensor([False]),
            dt_s=0.1,
            low_force_n=2.0,
            high_force_n=4.0,
            rate_m_s=0.01,
            maximum_m=0.01,
        )
        self.assertEqual(reset.tolist(), [[0.0, 0.0, 0.0, 0.0]])

    def test_unload_trim_shortens_high_force_legs(self):
        import torch

        from resume_validation.load_balance import update_unload_trim

        updated = update_unload_trim(
            torch.tensor([[0.001, 0.001, 0.004, 0.001]]),
            torch.tensor([[9.0, 6.0, 9.0, 3.0]]),
            torch.tensor([True]),
            dt_s=0.1,
            low_force_n=4.0,
            high_force_n=8.0,
            rate_m_s=0.01,
            maximum_m=0.005,
        )
        expected = [0.002, 0.001, 0.005, 0.0]
        for actual, target in zip(updated[0].tolist(), expected, strict=True):
            self.assertAlmostEqual(actual, target, places=6)

    def test_unload_trim_supports_per_environment_rate_and_limit(self):
        import torch

        from resume_validation.load_balance import update_unload_trim

        updated = update_unload_trim(
            torch.zeros((2, 4)),
            torch.full((2, 4), 9.0),
            torch.tensor([True, True]),
            dt_s=1.0,
            low_force_n=4.0,
            high_force_n=8.0,
            rate_m_s=torch.tensor([0.0005, 0.0020]),
            maximum_m=torch.tensor([0.0010, 0.0015]),
        )
        torch.testing.assert_close(
            updated,
            torch.tensor(
                [
                    [0.0005, 0.0005, 0.0005, 0.0005],
                    [0.0015, 0.0015, 0.0015, 0.0015],
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
