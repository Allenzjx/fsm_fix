import unittest
from types import SimpleNamespace


class ReferenceTensorCompositionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch

        from resume_validation.reference_tensor import TorchReferenceBank

        cls.torch = torch
        cls.bank = TorchReferenceBank.__new__(TorchReferenceBank)
        cls.bank.torch = torch
        cls.bank.low = SimpleNamespace(duration_s=131.0, height_m=0.05)
        cls.bank.high = SimpleNamespace(duration_s=65.0, height_m=0.10)

    def test_fsm_uses_low_rear_channels_for_entire_episode(self):
        bank = self.bank
        bank.sample = lambda normalized, height: self.torch.tensor(
            [[10.0, 11.0, 12.0, 13.0, 90.0, 91.0, 92.0, 93.0, 1.0, 2.0, 3.0, 4.0]]
        )
        bank.sample_low = lambda normalized: self.torch.tensor(
            [[20.0, 21.0, 22.0, 23.0, 20.0, 31.0, 20.0, -20.0, 5.0, 6.0, 7.0, 8.0]]
        )

        reference = bank.sample_fsm(
            self.torch.tensor([0.1]), self.torch.tensor([0.1])
        )

        self.assertEqual(reference[0, :4].tolist(), [10.0, 11.0, 12.0, 13.0])
        self.assertEqual(reference[0, 4:8].tolist(), [20.0, 31.0, 20.0, -20.0])
        self.assertEqual(reference[0, 8:].tolist(), [1.0, 2.0, 3.0, 4.0])

    def test_fsm_servo_reference_keeps_one_degree_inside_recorded_envelope(self):
        from resume_validation.actuator_mapping import (
            FSM_REFERENCE_MARGIN_DEG,
            RECORDED_SAFE_COMMAND_DEG,
            SERVO_JOINT_NAMES,
        )

        bank = self.bank
        endpoints = [
            RECORDED_SAFE_COMMAND_DEG[name][0 if index % 2 == 0 else 1]
            for index, name in enumerate(SERVO_JOINT_NAMES)
        ]
        bank.sample = lambda normalized, height: self.torch.tensor(
            [[*endpoints, 1.0, 2.0, 3.0, 4.0]]
        )
        bank.sample_low = lambda normalized: self.torch.tensor(
            [[*endpoints, 5.0, 6.0, 7.0, 8.0]]
        )

        reference = bank.sample_fsm(
            self.torch.tensor([0.1]), self.torch.tensor([0.05])
        )

        for index, name in enumerate(SERVO_JOINT_NAMES):
            lower, upper = RECORDED_SAFE_COMMAND_DEG[name]
            expected = (
                lower + FSM_REFERENCE_MARGIN_DEG
                if index % 2 == 0
                else upper - FSM_REFERENCE_MARGIN_DEG
            )
            self.assertAlmostEqual(float(reference[0, index]), expected, places=5)

    def test_duration_uses_slower_complete_source_for_every_height(self):
        duration = self.bank.duration_s(self.torch.tensor([0.05, 0.075, 0.10]))
        self.assertEqual(duration.tolist(), [131.0, 131.0, 131.0])

    def test_rear_time_warp_is_continuous_and_height_conditioned(self):
        low = self.bank.rear_normalized_time(
            self.torch.tensor([0.25, 0.50, 0.75, 1.0]),
            self.torch.tensor([0.05, 0.05, 0.05, 0.05]),
        )
        self.assertEqual(low.tolist(), [0.25, 0.50, 0.75, 1.0])

        high = self.bank.rear_normalized_time(
            self.torch.tensor([0.0, 0.525, 0.574, 1.0]),
            self.torch.tensor([0.10, 0.10, 0.10, 0.10]),
        )
        self.assertEqual(float(high[0]), 0.0)
        self.assertLess(float(high[1]), 0.50)
        self.assertAlmostEqual(float(high[2]), 0.50, places=6)
        self.assertEqual(float(high[3]), 1.0)

    def test_coordinated_100mm_rear_preparation_matches_recorded_endpoints(self):
        commands, active, alpha = self.bank.coordinated_rear_preparation(
            self.torch.tensor([0.574, 0.64]),
            self.torch.tensor([0.10, 0.10]),
        )
        self.assertEqual(active.tolist(), [True, True])
        self.assertEqual(alpha.tolist(), [1.0, 1.0])
        for actual, target in zip(
            commands[0].tolist(), [0.7, 0.0, 0.7, -0.0], strict=True
        ):
            self.assertAlmostEqual(actual, target, places=6)
        expected = [24.2, 0.0, 29.8, -44.8]
        for actual, target in zip(commands[1].tolist(), expected, strict=True):
            self.assertAlmostEqual(actual, target, places=4)

    def test_100mm_front_support_reaches_recorded_recovery_before_rear_motion(self):
        target, support_progress, active, alpha = self.bank.front_support_preparation(
            self.torch.tensor([0.574, 0.60, 0.64]),
            self.torch.tensor([0.10, 0.10, 0.10]),
        )
        self.assertEqual(active.tolist(), [True, True, True])
        self.assertEqual(alpha.tolist(), [1.0, 1.0, 1.0])
        self.assertAlmostEqual(float(support_progress[0]), 0.0, places=6)
        self.assertEqual(float(support_progress[-1]), 1.0)
        expected = [6.2, 2.3, 1.8, -4.4]
        for actual, wanted in zip(target[-1].tolist(), expected, strict=True):
            self.assertAlmostEqual(actual, wanted, places=5)

        rear, _, _ = self.bank.coordinated_rear_preparation(
            self.torch.tensor([0.59]),
            self.torch.tensor([0.10]),
        )
        for actual, wanted in zip(rear[0].tolist(), [0.7, 0.0, 0.7, 0.0], strict=True):
            self.assertAlmostEqual(actual, wanted, places=5)

    def test_100mm_rear_recovery_is_smooth_and_50mm_is_not_overridden(self):
        bank = self.bank
        bank.sample_low = lambda normalized: self.torch.tensor(
            [[0.0, 0.0, 0.0, 0.0, -0.7, 0.9, -0.7, -6.0, 0.0, 0.0, 0.0, 0.0]]
        ).expand(normalized.shape[0], -1)

        target, progress, high_alpha = bank.rear_recovery_after_transfer(
            self.torch.tensor([0.88, 0.91, 0.94]),
            self.torch.tensor([0.10, 0.10, 0.10]),
        )
        self.assertEqual(high_alpha.tolist(), [1.0, 1.0, 1.0])
        self.assertAlmostEqual(float(progress[0]), 0.0, places=6)
        self.assertAlmostEqual(float(progress[1]), 0.05, places=5)
        self.assertAlmostEqual(float(progress[2]), 0.10, places=6)
        for actual, expected in zip(
            target[-1].tolist(), [-0.7, 0.9, -0.7, -6.0], strict=True
        ):
            self.assertAlmostEqual(actual, expected, places=5)

        _, _, low_alpha = bank.rear_recovery_after_transfer(
            self.torch.tensor([0.94]), self.torch.tensor([0.05])
        )
        self.assertEqual(float(low_alpha[0]), 0.0)

    def test_rear_recovery_accepts_per_environment_diagnostic_blends(self):
        bank = self.bank
        bank.sample_low = lambda normalized: self.torch.zeros(
            (normalized.shape[0], 12)
        )
        _, progress, alpha = bank.rear_recovery_after_transfer(
            self.torch.tensor([0.94, 0.94]),
            self.torch.tensor([0.10, 0.10]),
            self.torch.tensor([0.0, 0.20]),
        )
        self.assertEqual(alpha.tolist(), [1.0, 1.0])
        self.assertAlmostEqual(float(progress[0]), 0.0, places=6)
        self.assertAlmostEqual(float(progress[1]), 0.20, places=6)


if __name__ == "__main__":
    unittest.main()
