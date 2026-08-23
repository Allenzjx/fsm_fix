import math
import unittest

from resume_validation.actuator_mapping import SERVO_JOINT_NAMES, WHEEL_JOINT_NAMES
from resume_validation.kinematics import PlanarLegKinematics
from resume_validation.residual_action import LEG_NAMES, ResidualBounds, apply_residual


class ResidualEquivalenceTest(unittest.TestCase):
    def test_zero_is_bitwise_equal(self):
        servo = {name: float(index - 3) for index, name in enumerate(SERVO_JOINT_NAMES)}
        wheels = {name: 0.3 for name in WHEEL_JOINT_NAMES}
        model = PlanarLegKinematics(0.1478, math.sqrt(0.1559**2 + 0.02**2 + 0.0784**2))
        result = apply_residual(
            servo,
            wheels,
            [0.0] * 12,
            leg_models={name: model for name in LEG_NAMES},
            bounds=ResidualBounds(0.015, 0.020, 0.35),
            servo_limits_deg={name: (-60.0, 60.0) for name in SERVO_JOINT_NAMES},
        )
        self.assertEqual(result.servo_deg, servo)
        self.assertEqual(result.wheel_rad_s, wheels)
        self.assertTrue(result.ik_valid)


if __name__ == "__main__":
    unittest.main()
