import unittest

import torch

from resume_validation.reward import (
    integrate_boolean_occupancy,
    integrate_rate,
    monotonic_phase_progress_delta,
    reward_terms,
)


class RewardAblationTest(unittest.TestCase):
    def test_only_com_term_differs(self):
        state = {
            "progress_delta": 0.01,
            "phase_progress_delta": 0.02,
            "success": 0.0,
            "pitch_rate": 0.2,
            "action_rate_sq": 0.1,
            "residual_sq": 0.1,
            "margin_m": 0.02,
            "margin_valid": 1.0,
            "support_transfer_window": 1.0,
        }
        without = reward_terms(state, com_weight=0.0)
        with_com = reward_terms(state, com_weight=8.0)
        for key in without:
            if key == "com_margin":
                self.assertNotEqual(without[key], with_com[key])
            else:
                self.assertEqual(without[key], with_com[key])

    def test_phase_progress_is_monotonic_across_phase_transition(self):
        delta, coordinate = monotonic_phase_progress_delta(
            torch.tensor([7, 8, 7]),
            torch.tensor([0.90, 0.00, 0.50]),
            torch.tensor([7.80, 7.90, 7.80]),
        )
        torch.testing.assert_close(
            delta,
            torch.tensor([0.10, 0.10, 0.00]),
        )
        torch.testing.assert_close(
            coordinate,
            torch.tensor([7.90, 8.00, 7.50]),
        )

    def test_stuck_occupancy_is_integrated_in_seconds(self):
        raw = integrate_boolean_occupancy(
            torch.tensor([False, True, True]),
            1.0 / 60.0,
        )
        torch.testing.assert_close(
            raw,
            torch.tensor([0.0, 1.0 / 60.0, 1.0 / 60.0]),
        )
        self.assertAlmostEqual(float(raw[1] * -6.0 * 60.0), -6.0, places=5)

    def test_continuous_rate_is_invariant_over_one_second(self):
        per_step = integrate_rate(
            torch.ones(60, dtype=torch.float32),
            1.0 / 60.0,
        )
        self.assertAlmostEqual(float(per_step.sum()), 1.0, places=6)
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            integrate_rate(torch.ones(1), 0.0)


if __name__ == "__main__":
    unittest.main()
