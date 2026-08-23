"""Compare physical/joint metadata of WLR USD asset candidates.

This script uses pxr and must be launched with Isaac Sim's Python.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ISAACLAB_ROOT = Path("C:/robotics_sim/IsaacLab")
for extension in (ISAACLAB_ROOT / "source").iterdir():
    if extension.is_dir() and str(extension) not in sys.path:
        sys.path.append(str(extension))
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("assets", nargs="+", type=Path)
parser.add_argument("--output", required=True, type=Path)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
simulation_app = launcher.app

from pxr import Usd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if hasattr(value, "__len__") and not isinstance(value, str):
        try:
            if len(value) <= 16:
                return [value_json(item) for item in value]
            return {"type": type(value).__name__, "length": len(value)}
        except Exception:
            pass
    return str(value)


def audit(path: Path) -> dict[str, Any]:
    stage = Usd.Stage.Open(str(path))
    if stage is None:
        raise RuntimeError(f"Could not open {path}")
    prims: dict[str, Any] = {}
    relevant_tokens = (
        "physics:", "physx", "drive:", "joint", "axis", "limit", "mass", "density",
        "centerofmass", "diagonalinertia", "principalaxes", "collision",
    )
    for prim in stage.Traverse():
        attributes = {}
        for attr in prim.GetAttributes():
            name = attr.GetName()
            if any(token in name.lower() for token in relevant_tokens):
                attributes[name] = value_json(attr.Get())
        relationships = {
            rel.GetName(): [str(item) for item in rel.GetTargets()]
            for rel in prim.GetRelationships()
            if any(token in rel.GetName().lower() for token in ("body", "joint", "collision", "material"))
        }
        if attributes or relationships or "joint" in prim.GetTypeName().lower():
            prims[str(prim.GetPath())] = {
                "name": prim.GetName(),
                "type": prim.GetTypeName(),
                "attributes": attributes,
                "relationships": relationships,
            }
    return {
        "path": str(path),
        "sha256": sha256(path),
        "prim_count": sum(1 for _ in stage.Traverse()),
        "physical_prims": prims,
    }


def main() -> int:
    try:
        records = [audit(path.resolve()) for path in args.assets]
        baseline, candidate = records[0], records[1]
        differences = []
        paths = sorted(set(baseline["physical_prims"]) | set(candidate["physical_prims"]))
        for path in paths:
            left = baseline["physical_prims"].get(path)
            right = candidate["physical_prims"].get(path)
            if left != right:
                differences.append({"prim_path": path, "baseline": left, "candidate": right})
        result = {
            "assets": records,
            "same_prim_count": baseline["prim_count"] == candidate["prim_count"],
            "physical_metadata_difference_count": len(differences),
            "physical_metadata_differences": differences,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "output": str(args.output),
            "same_prim_count": result["same_prim_count"],
            "physical_metadata_difference_count": len(differences),
        }, indent=2))
        return 0
    finally:
        simulation_app.close()


if __name__ == "__main__":
    raise SystemExit(main())
