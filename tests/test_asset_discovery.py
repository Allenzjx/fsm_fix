import unittest

from resume_validation.asset_discovery import parse_urdf, validate_urdf_model
from resume_validation.paths import CANONICAL_URDF


class AssetDiscoveryTest(unittest.TestCase):
    def test_canonical_urdf_structure(self):
        model = parse_urdf(CANONICAL_URDF)
        self.assertEqual(len(model["joints"]), 12)
        self.assertEqual(len(model["links"]), 13)
        self.assertEqual(validate_urdf_model(model), [])


if __name__ == "__main__":
    unittest.main()
