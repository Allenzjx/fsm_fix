import unittest

from resume_validation.support_margin import SupportPoint, longitudinal_support_margin


class SupportMarginTest(unittest.TestCase):
    def test_signed_margin(self):
        supports = [SupportPoint((0.0, 0.0, 0.0), 10.0), SupportPoint((1.0, 0.0, 0.0), 10.0)]
        inside = longitudinal_support_margin((0.4, 0.0, 0.2), supports)
        outside = longitudinal_support_margin((1.2, 0.0, 0.2), supports)
        self.assertTrue(inside.valid)
        self.assertAlmostEqual(inside.margin_m, 0.4)
        self.assertAlmostEqual(outside.margin_m, -0.2)

    def test_single_support_is_invalid(self):
        result = longitudinal_support_margin((0.0, 0.0, 0.0), [SupportPoint((0.0, 0.0, 0.0), 10.0)])
        self.assertFalse(result.valid)
        self.assertIsNone(result.margin_m)


if __name__ == "__main__":
    unittest.main()
