"""Auditable development-set promotion gate for residual-PPO curriculum stages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALIDATION_ROOT = Path("C:/robotics_sim/wlr_robot/resume_validation_fsm_residual_ppo")
if str(VALIDATION_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT / "src"))

from resume_validation.config_io import load_config, write_json
from resume_validation.source_audit import sha256_file


def decide_curriculum_gate(
    evaluation: dict[str, Any],
    common_cfg: dict[str, Any],
    *,
    method: str,
    seed: int,
    height_mm: int,
    checkpoint_sha256: str,
) -> dict[str, Any]:
    stages = common_cfg["curriculum"]["promotion_stages"]
    stage = stages.get(height_mm, stages.get(str(height_mm)))
    if stage is None:
        raise ValueError(f"No curriculum promotion stage is registered for {height_mm} mm")
    required_episodes = int(
        common_cfg["curriculum"]["development_episodes_required_per_height"]
    )
    required_success = float(stage["minimum_development_success_rate"])
    aggregate = evaluation.get("aggregate", {})
    actual_episodes = int(aggregate.get("episode_count", 0))
    actual_success = float(aggregate.get("success_rate", 0.0))
    provenance = evaluation.get("provenance", {})
    checks = {
        "evaluation_completed": bool(evaluation.get("passed_execution", False)),
        "controller_matches": evaluation.get("controller") == method,
        "height_matches": int(evaluation.get("height_mm", -1)) == int(height_mm),
        "episode_count_sufficient": actual_episodes >= required_episodes,
        "checkpoint_hash_matches": provenance.get("checkpoint_sha256")
        == checkpoint_sha256,
        "success_rate_sufficient": actual_success >= required_success,
    }
    return {
        "schema": "resume_validation.curriculum_gate.v1",
        "method": method,
        "seed": int(seed),
        "height_mm": int(height_mm),
        "checkpoint_sha256": checkpoint_sha256,
        "required": {
            "development_episode_count": required_episodes,
            "minimum_development_success_rate": required_success,
        },
        "actual": {
            "development_episode_count": actual_episodes,
            "development_success_rate": actual_success,
        },
        "checks": checks,
        "promote": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--common_config", type=Path, required=True)
    parser.add_argument("--method", choices=("B", "C"), required=True)
    parser.add_argument("--seed", type=int, choices=(11, 29, 47), required=True)
    parser.add_argument("--height_mm", type=int, choices=(50, 75, 100), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    decision = decide_curriculum_gate(
        json.loads(args.evaluation.read_text(encoding="utf-8")),
        load_config(args.common_config),
        method=args.method,
        seed=args.seed,
        height_mm=args.height_mm,
        checkpoint_sha256=sha256_file(args.checkpoint),
    )
    decision["evaluation"] = str(args.evaluation.resolve())
    decision["evaluation_sha256"] = sha256_file(args.evaluation)
    decision["checkpoint"] = str(args.checkpoint.resolve())
    decision["common_config"] = str(args.common_config.resolve())
    decision["common_config_sha256"] = sha256_file(args.common_config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, decision)
    return 0 if decision["promote"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
