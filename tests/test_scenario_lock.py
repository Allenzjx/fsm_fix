import tempfile
import unittest
from pathlib import Path

from resume_validation.scenario_manifest import (
    REFERENCE_INITIAL_DISTANCE_M,
    REFERENCE_OBSTACLE_FRONT_X_M,
    make_scenarios,
    verify_manifest,
    write_locked_manifest,
)


class ScenarioLockTest(unittest.TestCase):
    def test_hash_detects_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            scenarios = make_scenarios(split="test", seed=42, episodes_per_height=2)
            write_locked_manifest(path, scenarios)
            self.assertTrue(verify_manifest(path))
            path.write_text(path.read_text() + " ", encoding="utf-8")
            self.assertFalse(verify_manifest(path))

    def test_scenarios_use_fresh_reference_replay_geometry(self):
        scenarios = make_scenarios(split="test", seed=42, episodes_per_height=3)
        self.assertTrue(
            all(item.obstacle_front_x_m == REFERENCE_OBSTACLE_FRONT_X_M for item in scenarios)
        )
        self.assertTrue(
            all(abs(item.initial_distance_m - REFERENCE_INITIAL_DISTANCE_M) <= 0.025 for item in scenarios)
        )


if __name__ == "__main__":
    unittest.main()
