"""Safe module launcher for the existing evaluator.

Executing ``src/resume_validation/evaluate_controller.py`` as a file makes its
package directory ``sys.path[0]``.  The local ``statistics.py`` then shadows the
Python standard-library module required by visible Kit extensions.  Launching
the unchanged evaluator as a package module keeps that filename namespaced as
``resume_validation.statistics``.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(r"C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo")
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

runpy.run_module("resume_validation.evaluate_controller", run_name="__main__")
