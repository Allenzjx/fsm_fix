import unittest

from resume_validation.com_estimator import BodyCoM, whole_body_com


class CoMEstimatorTest(unittest.TestCase):
    def test_mass_weighted_com(self):
        result = whole_body_com([BodyCoM("a", 1.0, (0.0, 0.0, 0.0)), BodyCoM("b", 3.0, (4.0, 0.0, 0.0))])
        self.assertEqual(result, (3.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
