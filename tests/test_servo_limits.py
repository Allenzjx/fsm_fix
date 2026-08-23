import unittest

from resume_validation.actuator_mapping import intersect_limits


class ServoLimitTest(unittest.TestCase):
    def test_intersection_is_conservative(self):
        self.assertEqual(intersect_limits((-135, 135), (-90, 90), (-32.5, 63)), (-32.5, 63.0))

    def test_empty_intersection_rejected(self):
        with self.assertRaises(ValueError):
            intersect_limits((-1, 0), (1, 2))


if __name__ == "__main__":
    unittest.main()
