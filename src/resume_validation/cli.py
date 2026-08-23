from __future__ import annotations

import argparse
import json
from pathlib import Path

from .asset_discovery import parse_urdf, validate_urdf_model
from .config_io import write_json
from .paths import (
    CANONICAL_URDF,
    DATA_DIR,
    REFERENCE_REPLAY_ROOT,
    REPORTS_DIR,
    VALIDATION_ROOT,
)
from .replay_analyzer import analyze_replay
from .scenario_manifest import make_scenarios, write_locked_manifest
from .source_audit import run_inventory


def command_inventory(_: argparse.Namespace) -> int:
    print(json.dumps(run_inventory(), indent=2))
    return 0


def command_asset(_: argparse.Namespace) -> int:
    model = parse_urdf(CANONICAL_URDF)
    failures = validate_urdf_model(model)
    output = {
        "urdf": model,
        "validation": {"passed": not failures, "failures": failures},
        "note": "USD/PhysX runtime properties are validated separately inside Isaac Sim.",
    }
    path = VALIDATION_ROOT / "assets" / "validation" / "urdf_validation.json"
    write_json(path, output)
    print(json.dumps({"path": str(path), "passed": not failures, "failures": failures}, indent=2))
    return 0 if not failures else 1


def command_replays(_: argparse.Namespace) -> int:
    output_dir = DATA_DIR / "replay_reference"
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    for height_cm in (5, 10):
        source = REFERENCE_REPLAY_ROOT / "saved_height_steps" / f"height_{height_cm:02d}cm" / "accepted_steps.jsonl"
        report = analyze_replay(source)
        destination = output_dir / f"parsed_replay_{height_cm * 10:03d}mm.json"
        write_json(destination, report)
        reports[str(height_cm)] = report
    print(json.dumps(reports, indent=2))
    return 0


def command_scenarios(args: argparse.Namespace) -> int:
    default_output = (
        DATA_DIR / "locked_test" / "manifest.json"
        if args.split == "locked_test"
        else DATA_DIR / "scenario_manifests" / f"{args.split}.json"
    )
    output = args.output.resolve() if args.output else default_output
    if output.exists() and not args.force:
        raise RuntimeError("Locked test manifest already exists; refusing to overwrite without --force")
    scenarios = make_scenarios(
        split=args.split,
        seed=args.seed,
        episodes_per_height=args.episodes_per_height,
    )
    digest = write_locked_manifest(
        output,
        scenarios,
        {
            "protocol_version": "1.0.0",
            "split": args.split,
            "seed": args.seed,
            "episodes_per_height": args.episodes_per_height,
            "training_code_must_not_read_locked_results": args.split == "locked_test",
            "generator_version": "v2_reference_replay_geometry",
            "obstacle_position_policy": "fixed translationally-equivalent reference front",
            "initial_distance_policy": "reference settled distance +/- 0.025 m",
        },
    )
    print(json.dumps({"path": str(output), "sha256": digest, "count": len(scenarios)}, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    inventory = subparsers.add_parser("inventory")
    inventory.set_defaults(func=command_inventory)
    asset = subparsers.add_parser("asset-audit")
    asset.set_defaults(func=command_asset)
    replays = subparsers.add_parser("analyze-replays")
    replays.set_defaults(func=command_replays)
    scenarios = subparsers.add_parser("make-scenarios")
    scenarios.add_argument("--split", choices=("development", "validation", "locked_test"), required=True)
    scenarios.add_argument("--seed", type=int, required=True)
    scenarios.add_argument("--episodes-per-height", type=int, default=100)
    scenarios.add_argument("--force", action="store_true")
    scenarios.add_argument("--output", type=Path)
    scenarios.set_defaults(func=command_scenarios)
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
