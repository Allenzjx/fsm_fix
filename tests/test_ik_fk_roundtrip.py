import math
import random
import unittest

from resume_validation.kinematics import IKError, PlanarLegKinematics


class KinematicsTest(unittest.TestCase):
    def setUp(self):
        self.model = PlanarLegKinematics(0.1478, math.sqrt(0.1559**2 + 0.02**2 + 0.0784**2))

    def test_1000_fk_ik_fk_samples(self):
        generator = random.Random(20260727)
        for _ in range(1000):
            hip = generator.uniform(-1.2, 1.2)
            knee = generator.uniform(0.10, 2.8)
            target = self.model.fk(hip, knee)
            result = self.model.ik(*target, previous=(hip, knee))
            rebuilt = self.model.fk(result.hip_rad, result.knee_rad)
            self.assertAlmostEqual(target[0], rebuilt[0], places=10)
            self.assertAlmostEqual(target[1], rebuilt[1], places=10)

    def test_unreachable_is_explicit(self):
        with self.assertRaises(IKError):
            self.model.ik(1.0, 1.0)


if __name__ == "__main__":
    unittest.main()
