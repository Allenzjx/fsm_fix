from __future__ import annotations

import json
from pathlib import Path

from torch.utils.tensorboard import SummaryWriter

from resume_validation.report_generator import (
    HEIGHTS,
    _aggregate_rows,
    _comparison_summary,
    _method_summary,
    _write_plots,
)


PLOT_NAMES = {
    "training_return.png",
    "validation_success.png",
    "success_by_height.png",
    "margin_by_method.png",
    "pitch_rate_by_method.png",
    "action_saturation.png",
    "paired_margin_delta.png",
    "paired_pitch_delta.png",
    "failure_distribution.png",
}


def _row(height: int, *, success: bool, offset: float = 0.0) -> dict:
    return {
        "scenario_id": f"scenario-h{height}",
        "obstacle_height_m": height / 1000.0,
        "success": success,
        "failure_reason": "" if success else "TIMEOUT",
        "min_longitudinal_support_margin_m": height / 10_000.0 + offset,
        "pitch_rate_rms_rad_s": 0.5 - offset,
        "residual_saturation_rate": 0.1,
    }


def test_all_required_report_plots_render_with_local_versions(
    tmp_path: Path,
) -> None:
    data = {
        ("fsm", None): [
            _row(height, success=height != 100) for height in HEIGHTS
        ]
    }
    for method, offset in (("B", 0.001), ("C", 0.002)):
        for seed in (11, 29, 47):
            data[(method, seed)] = [
                {
                    **_row(height, success=height != 100, offset=offset),
                    "training_seed": seed,
                }
                for height in HEIGHTS
            ]
    method_summaries = {
        method: _method_summary(_aggregate_rows(data, method))
        for method in ("fsm", "B", "C")
    }
    comparisons = {
        "C_vs_A": _comparison_summary(data, "fsm", "C"),
        "C_vs_B": _comparison_summary(data, "B", "C"),
        "B_vs_A": _comparison_summary(data, "fsm", "B"),
    }

    run_dir = tmp_path / "training-run"
    run_dir.mkdir()
    (run_dir / "training_result.json").write_text("{}\n", encoding="utf-8")
    writer = SummaryWriter(str(run_dir))
    writer.add_scalar("Reward / Total reward (mean)", 1.0, 64)
    writer.add_scalar("Reward / Total reward (mean)", 2.0, 128)
    writer.close()

    selections = []
    for method in ("B", "C"):
        for seed in (11, 29, 47):
            summary = (
                tmp_path
                / f"method-{method}"
                / f"seed-{seed}"
                / "candidate"
                / "validation_summary.json"
            )
            summary.parent.mkdir(parents=True)
            checkpoint = tmp_path / f"{method}-{seed}" / "checkpoints" / "agent.pt"
            checkpoint.parent.mkdir(parents=True)
            checkpoint.write_bytes(b"checkpoint")
            payload = {
                "checkpoint": str(checkpoint),
                "checkpoint_sha256": f"{method}-{seed}",
                "selection_metrics": {"success_rate": 2 / 3},
            }
            summary.write_text(json.dumps(payload), encoding="utf-8")
            selections.append(
                {
                    "method": method,
                    "seed": seed,
                    "selected_checkpoint_sha256": f"{method}-{seed}",
                    "candidate_summaries": [str(summary)],
                }
            )
    fsm_summary = tmp_path / "fsm_validation_summary.json"
    fsm_summary.write_text(
        json.dumps({"selection_metrics": {"success_rate": 2 / 3}}),
        encoding="utf-8",
    )
    freeze = {
        "all_matching_training_runs": [
            {
                "status": "COMPLETED",
                "method": "B",
                "seed": 11,
                "height_mm": 50,
                "run_name": "method-B-v34_seed-11_stage-50mm_attempt001",
                "training_result": str(run_dir / "training_result.json"),
            }
        ],
        "selections": selections,
        "fsm_validation_summary": str(fsm_summary),
    }
    plot_dir = tmp_path / "plots"
    plot_dir.mkdir()
    _write_plots(
        plot_dir=plot_dir,
        project_root=tmp_path,
        freeze=freeze,
        data=data,
        method_summaries=method_summaries,
        comparisons=comparisons,
    )
    assert {path.name for path in plot_dir.iterdir()} == PLOT_NAMES
    assert all(
        path.stat().st_size > 1024
        and path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        for path in plot_dir.iterdir()
    )
