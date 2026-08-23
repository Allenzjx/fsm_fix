"""Build an isolated WLR USD with audited servo limits.

The source USD is never modified. This script requires Isaac Sim's pxr runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ISAACLAB_ROOT = Path("C:/robotics_sim/IsaacLab")
for extension in (ISAACLAB_ROOT / "source").iterdir():
    if extension.is_dir() and str(extension) not in sys.path:
        sys.path.append(str(extension))
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--manifest", required=True, type=Path)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
simulation_app = launcher.app

from pxr import Usd

JOINT_COMMAND_SIGN = {
    "front_left_hip": 1.0,
    "front_left_knee": 1.0,
    "front_right_hip": 1.0,
    "front_right_knee": 1.0,
    "rear_left_hip": -1.0,
    "rear_left_knee": -1.0,
    "rear_right_hip": -1.0,
    "rear_right_knee": -1.0,
}
STANDING_DEG = {
    "front_left_hip": 0.07935156363204786,
    "front_left_knee": 0.02684400080484552,
    "front_right_hip": -0.006745560524854715,
    "front_right_knee": 0.1251883495021952,
    "rear_left_hip": -0.1794263347525243,
    "rear_left_knee": 0.16301483092001173,
    "rear_right_hip": -0.3229814231186408,
    "rear_right_knee": 0.21524399350241663,
}
# Union of the observed ranges in both successful 50/100 mm recordings.
RECORDED_COMMAND_RANGE_DEG = {
    "front_left_hip": (-32.5, 63.0),
    "front_left_knee": (-42.0, 23.1),
    "front_right_hip": (0.0, 39.5),
    "front_right_knee": (-15.7, 31.4),
    "rear_left_hip": (-11.8, 24.2),
    "rear_left_knee": (0.0, 45.2),
    "rear_right_hip": (-35.3, 29.8),
    "rear_right_knee": (-60.0, 0.0),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    source = args.source.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.Open(str(source))
    if stage is None:
        raise RuntimeError(f"Could not open {source}")
    if not stage.Export(str(output)):
        raise RuntimeError(f"Could not export source stage to {output}")
    converted = Usd.Stage.Open(str(output))
    changes = []
    for name, command_range in RECORDED_COMMAND_RANGE_DEG.items():
        matches = [prim for prim in converted.Traverse() if prim.GetName() == name]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one joint prim named {name}, found {len(matches)}")
        prim = matches[0]
        lower_attr = prim.GetAttribute("physics:lowerLimit")
        upper_attr = prim.GetAttribute("physics:upperLimit")
        before = [float(lower_attr.Get()), float(upper_attr.Get())]
        raw_a = STANDING_DEG[name] + JOINT_COMMAND_SIGN[name] * command_range[0]
        raw_b = STANDING_DEG[name] + JOINT_COMMAND_SIGN[name] * command_range[1]
        # The imported articulation default is exactly zero even though the
        # settled measured pose has small offsets. Zero must remain a valid
        # reset configuration.
        after = [min(raw_a, raw_b, 0.0), max(raw_a, raw_b, 0.0)]
        lower_attr.Set(after[0])
        upper_attr.Set(after[1])
        changes.append(
            {
                "joint": name,
                "command_range_deg": list(command_range),
                "standing_raw_deg": STANDING_DEG[name],
                "command_sign": JOINT_COMMAND_SIGN[name],
                "source_physical_limit_deg": before,
                "validation_physical_limit_deg": after,
            }
        )
    converted.GetRootLayer().Save()
    manifest = {
        "source": str(source),
        "source_sha256": sha256(source),
        "output": str(output),
        "output_sha256": sha256(output),
        "modification_scope": "physics:lowerLimit and physics:upperLimit on eight hip/knee joints only",
        "limit_policy": "per-joint union of observed commands across successful 50/100 mm recordings, transformed using measured standing pose and direction sign",
        "changes": changes,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


try:
    raise SystemExit(main())
finally:
    simulation_app.close()
