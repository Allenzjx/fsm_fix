import unittest

from resume_validation.statistics import (
    bootstrap_mean_ci,
    paired_bootstrap_ci,
    stratified_bootstrap_mean_ci,
    wilson_interval,
)


class StatisticsTest(unittest.TestCase):
    def test_wilson(self):
        lower, upper = wilson_interval(84, 100)
        self.assertLess(lower, 0.84)
        self.assertGreater(upper, 0.84)

    def test_bootstrap_is_deterministic(self):
        self.assertEqual(bootstrap_mean_ci([1, 2, 3], draws=100), bootstrap_mean_ci([1, 2, 3], draws=100))
        self.assertEqual(paired_bootstrap_ci([0, 1], [1, 3], draws=100), paired_bootstrap_ci([0, 1], [1, 3], draws=100))

    def test_stratified_bootstrap_equal_weights_strata(self):
        left = stratified_bootstrap_mean_ci(
            {"short": [0.0], "long": [10.0, 10.0, 10.0]},
            draws=100,
        )
        self.assertEqual(left, (5.0, 5.0))


if __name__ == "__main__":
    unittest.main()
