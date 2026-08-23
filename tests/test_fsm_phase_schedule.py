import unittest

from resume_validation.fsm_phase_schedule import phase_boundaries_for_height


class FSMPhaseScheduleTest(unittest.TestCase):
    def test_source_endpoints_are_preserved(self):
        self.assertEqual(phase_boundaries_for_height(0.05)[5], 0.50)
        self.assertEqual(phase_boundaries_for_height(0.10)[5], 0.574)

    def test_75mm_boundary_is_interpolated(self):
        self.assertAlmostEqual(phase_boundaries_for_height(0.075)[5], 0.537)

    def test_out_of_range_height_clamps_to_source_endpoint(self):
        self.assertEqual(
            phase_boundaries_for_height(0.0),
            phase_boundaries_for_height(0.05),
        )
        self.assertEqual(
            phase_boundaries_for_height(1.0),
            phase_boundaries_for_height(0.10),
        )


if __name__ == "__main__":
    unittest.main()
