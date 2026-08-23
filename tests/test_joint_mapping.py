import math
import unittest

from resume_validation.actuator_mapping import (
    JOINT_COMMAND_SIGN,
    WHEEL_FORWARD_SIGN,
    command_to_raw_rad,
    raw_rad_to_command,
    wheel_physical_to_raw,
)


class JointMappingTest(unittest.TestCase):
    def test_command_roundtrip(self):
        for name in JOINT_COMMAND_SIGN:
            raw = command_to_raw_rad(name, 17.25, 0.013)
            self.assertAlmostEqual(raw_rad_to_command(name, raw, 0.013), 17.25)

    def test_wheel_forward_signs(self):
        for name, sign in WHEEL_FORWARD_SIGN.items():
            self.assertAlmostEqual(wheel_physical_to_raw(name, 0.5), sign * 0.5)


if __name__ == "__main__":
    unittest.main()
