from __future__ import annotations

from pathlib import Path


VALIDATION_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = VALIDATION_ROOT.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
ISAACLAB_ROOT = WORKSPACE_ROOT / "IsaacLab"
ISAACLAB_LAUNCHER = ISAACLAB_ROOT / "isaaclab.bat"
REFERENCE_REPLAY_ROOT = PROJECT_ROOT / "height_based_obstacle_replay"
CANONICAL_USD = PROJECT_ROOT / "usd" / "wlr_robot_drive_test.usd"
CANONICAL_URDF = PROJECT_ROOT / "sw2urdf_output" / "wlr_robot_isaac" / "urdf" / "wlr_robot_isaac.urdf"
SOURCE_DIR = VALIDATION_ROOT / "src"
CONFIG_DIR = VALIDATION_ROOT / "configs"
DATA_DIR = VALIDATION_ROOT / "data"
RUNS_DIR = VALIDATION_ROOT / "runs"
REPORTS_DIR = VALIDATION_ROOT / "reports"


def ensure_output_dirs() -> None:
    for path in (
        VALIDATION_ROOT / "assets" / "manifests",
        DATA_DIR / "replay_reference",
        DATA_DIR / "scenario_manifests",
        DATA_DIR / "locked_test",
        RUNS_DIR / "fsm",
        RUNS_DIR / "ppo_without_com",
        RUNS_DIR / "ppo_with_com",
        RUNS_DIR / "diagnostics",
        REPORTS_DIR / "tables",
        REPORTS_DIR / "plots",
        REPORTS_DIR / "videos",
    ):
        path.mkdir(parents=True, exist_ok=True)
