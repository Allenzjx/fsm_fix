"""Build deterministic side-by-side comparisons, manifests, and HTML index."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import os
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import quote

import cv2
import imageio.v2 as imageio
import numpy as np

from record_existing_controller import _writer, video_probe
from visualization_common import PROJECT_ROOT, csv_write, read_json, sha256_file, write_json


MANIFEST_FIELDS = [
    "case_id",
    "controller",
    "method",
    "seed",
    "height_mm",
    "checkpoint",
    "checkpoint_sha256",
    "scenario_id",
    "requested_outcome",
    "actual_outcome",
    "failure_reason",
    "final_phase",
    "simulation_duration_s",
    "video_path",
    "video_format",
    "video_width",
    "video_height",
    "video_fps",
    "frame_count",
    "file_size",
    "video_sha256",
    "telemetry_path",
    "result_path",
    "stdout_path",
    "stderr_path",
    "kit_log_path",
    "validation_status",
    "notes",
]


COMPARISON_SPECS = [
    {
        "case_id": "fsm_vs_B_h050_development-h050-0000",
        "height_mm": 50,
        "scenario_id": "development-h050-0000",
        "left": ("fsm", None),
        "right": ("B", 29),
        "left_label": "LEFT: Frozen FSM",
        "right_label": "RIGHT: Method B seed 29 final",
    },
    {
        "case_id": "fsm_vs_B_h075_development-h075-0000",
        "height_mm": 75,
        "scenario_id": "development-h075-0000",
        "left": ("fsm", None),
        "right": ("B", 29),
        "left_label": "LEFT: Frozen FSM",
        "right_label": "RIGHT: Method B seed 29 final",
    },
    {
        "case_id": "fsm_vs_B_h100_development-h100-0001",
        "height_mm": 100,
        "scenario_id": "development-h100-0001",
        "left": ("fsm", None),
        "right": ("B", 29),
        "left_label": "LEFT: Frozen FSM",
        "right_label": "RIGHT: Method B seed 29 final",
    },
    {
        "case_id": "fsm_vs_C_h050_development-h050-0000",
        "height_mm": 50,
        "scenario_id": "development-h050-0000",
        "left": ("fsm", None),
        "right": ("C", 11),
        "left_label": "LEFT: Frozen FSM",
        "right_label": "RIGHT: Method C seed 11 final",
    },
]


def all_primary_metadata(report_root: Path) -> list[dict[str, Any]]:
    values = []
    for path in sorted((report_root / "results").glob("*/metadata.json")):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if payload.get("schema") == "resume_validation.visualization_case.v1":
            values.append(payload)
    return values


def find_primary(
    metadata: list[dict[str, Any]], controller: str, seed: int | None, height: int, scenario: str
) -> dict[str, Any]:
    matches = [
        row
        for row in metadata
        if row["case"]["controller"] == controller
        and row["case"].get("seed") == seed
        and int(row["case"]["height_mm"]) == height
        and row["case"]["scenario_id"] == scenario
        and row.get("validation_status") == "PASSED"
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one completed source: controller={controller}, seed={seed}, height={height}, "
            f"scenario={scenario}; found {len(matches)}"
        )
    return matches[0]


def comparison_encode(
    left_path: Path,
    right_path: Path,
    output_path: Path,
    left_label: str,
    right_label: str,
    left_outcome: str,
    right_outcome: str,
    scenario: str,
    fps: float = 20.0,
) -> None:
    left = cv2.VideoCapture(str(left_path))
    right = cv2.VideoCapture(str(right_path))
    if not left.isOpened() or not right.isOpened():
        raise RuntimeError("Could not open comparison source video")
    left_count = int(round(left.get(cv2.CAP_PROP_FRAME_COUNT)))
    right_count = int(round(right.get(cv2.CAP_PROP_FRAME_COUNT)))
    total = max(left_count, right_count)
    writer = _writer(output_path, fps)
    last_left = None
    last_right = None
    try:
        for index in range(total):
            ok_left, frame_left = left.read() if index < left_count else (False, None)
            ok_right, frame_right = right.read() if index < right_count else (False, None)
            if ok_left:
                last_left = frame_left
            if ok_right:
                last_right = frame_right
            if last_left is None or last_right is None:
                raise RuntimeError("Comparison source produced no first frame")
            panel_left = cv2.resize(last_left, (960, 540), interpolation=cv2.INTER_AREA)
            panel_right = cv2.resize(last_right, (960, 540), interpolation=cv2.INTER_AREA)
            canvas = np.hstack((panel_left, panel_right))
            cv2.rectangle(canvas, (0, 0), (1920, 50), (8, 12, 20), thickness=-1)
            cv2.putText(canvas, left_label, (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(canvas, right_label, (980, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(
                canvas,
                f"t={index / fps:7.2f}s  scenario={scenario}",
                (700, 525),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (245, 245, 245),
                2,
                cv2.LINE_AA,
            )
            if index >= left_count:
                cv2.putText(canvas, f"ENDED: {left_outcome.upper()}", (25, 505), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 220, 255), 2, cv2.LINE_AA)
            if index >= right_count:
                cv2.putText(canvas, f"ENDED: {right_outcome.upper()}", (985, 505), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 220, 255), 2, cv2.LINE_AA)
            writer.append_data(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    finally:
        left.release()
        right.release()
        writer.close()


def build_comparisons(
    report_root: Path, comparison_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    primary = all_primary_metadata(report_root)
    output: list[dict[str, Any]] = []
    for spec in COMPARISON_SPECS:
        if comparison_ids is not None and spec["case_id"] not in comparison_ids:
            continue
        metadata_path = report_root / "results" / "comparisons" / f"{spec['case_id']}.json"
        if metadata_path.is_file():
            existing = read_json(metadata_path)
            video = Path(existing["video"])
            if video.is_file() and existing.get("validation_status") == "PASSED":
                output.append(existing)
                continue
        left = find_primary(primary, spec["left"][0], spec["left"][1], spec["height_mm"], spec["scenario_id"])
        right = find_primary(primary, spec["right"][0], spec["right"][1], spec["height_mm"], spec["scenario_id"])
        video = report_root / "videos" / "comparisons" / f"{spec['case_id']}.mp4"
        temporary = video.with_suffix(".encoding.mp4")
        comparison_encode(
            Path(left["video"]),
            Path(right["video"]),
            temporary,
            spec["left_label"],
            spec["right_label"],
            left["actual_outcome"],
            right["actual_outcome"],
            spec["scenario_id"],
        )
        os.replace(temporary, video)
        probe = video_probe(video, 1920, 540)
        if not probe["passed"]:
            raise RuntimeError(f"Comparison validation failed for {spec['case_id']}: {probe['failures']}")
        cap = cv2.VideoCapture(str(video))
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, probe["frame_count"] // 2))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError(f"Could not extract comparison thumbnail: {video}")
        thumbnail = report_root / "thumbnails" / f"{spec['case_id']}.jpg"
        cv2.imwrite(str(thumbnail), cv2.resize(frame, (640, 180), interpolation=cv2.INTER_AREA))
        payload = {
            "schema": "resume_validation.visualization_comparison.v1",
            **spec,
            "left_source": left["case"]["case_id"],
            "right_source": right["case"]["case_id"],
            "left_outcome": left["actual_outcome"],
            "right_outcome": right["actual_outcome"],
            "video": str(video),
            "thumbnail": str(thumbnail),
            "video_probe": probe,
            "validation_status": "PASSED",
            "alignment": "simulation_time_at_20_fps; shorter source holds its final frame",
        }
        write_json(metadata_path, payload)
        output.append(payload)
    return output


def _primary_manifest_row(metadata: dict[str, Any]) -> dict[str, Any]:
    case = metadata["case"]
    provenance = metadata["provenance"]
    probe = metadata["video_probe"]
    return {
        "case_id": case["case_id"],
        "controller": case["controller"],
        "method": case["method"],
        "seed": case.get("seed"),
        "height_mm": case["height_mm"],
        "checkpoint": provenance.get("checkpoint") or "",
        "checkpoint_sha256": provenance.get("checkpoint_sha256") or "",
        "scenario_id": case["scenario_id"],
        "requested_outcome": case["requested_outcome"],
        "actual_outcome": metadata["actual_outcome"],
        "failure_reason": metadata["failure_reason"],
        "final_phase": metadata["final_phase"],
        "simulation_duration_s": metadata["simulation_duration_s"],
        "video_path": metadata["video"],
        "video_format": Path(metadata["video"]).suffix.lstrip("."),
        "video_width": probe["width"],
        "video_height": probe["height"],
        "video_fps": probe["fps"],
        "frame_count": probe["frame_count"],
        "file_size": probe["file_size"],
        "video_sha256": probe["sha256"],
        "telemetry_path": metadata["telemetry"],
        "result_path": metadata["result"],
        "stdout_path": metadata["stdout"],
        "stderr_path": metadata["stderr"],
        "kit_log_path": metadata["kit_log"],
        "validation_status": metadata["validation_status"],
        "notes": metadata["notes"],
    }


def _highlight_manifest_row(metadata: dict[str, Any]) -> dict[str, Any]:
    row = _primary_manifest_row(metadata)
    highlight = metadata["highlight"]
    probe = highlight["probe"]
    row.update(
        {
            "case_id": "highlight_" + row["case_id"],
            "requested_outcome": "timeout_highlight",
            "video_path": highlight["path"],
            "video_format": Path(highlight["path"]).suffix.lstrip("."),
            "video_width": probe["width"],
            "video_height": probe["height"],
            "video_fps": probe["fps"],
            "frame_count": probe["frame_count"],
            "file_size": probe["file_size"],
            "video_sha256": probe["sha256"],
            "validation_status": "PASSED" if probe["passed"] else "FAILED",
            "notes": f"TIMEOUT highlight ranges: {highlight['ranges_s']}; full video retained.",
        }
    )
    return row


def _comparison_manifest_row(metadata: dict[str, Any], report_root: Path) -> dict[str, Any]:
    probe = metadata["video_probe"]
    return {
        "case_id": metadata["case_id"],
        "controller": "comparison",
        "method": f"{metadata['left_label']} | {metadata['right_label']}",
        "seed": "",
        "height_mm": metadata["height_mm"],
        "checkpoint": "see source metadata",
        "checkpoint_sha256": "",
        "scenario_id": metadata["scenario_id"],
        "requested_outcome": "comparison",
        "actual_outcome": f"{metadata['left_outcome']} | {metadata['right_outcome']}",
        "failure_reason": "",
        "final_phase": "",
        "simulation_duration_s": probe["duration_s"],
        "video_path": metadata["video"],
        "video_format": Path(metadata["video"]).suffix.lstrip("."),
        "video_width": probe["width"],
        "video_height": probe["height"],
        "video_fps": probe["fps"],
        "frame_count": probe["frame_count"],
        "file_size": probe["file_size"],
        "video_sha256": probe["sha256"],
        "telemetry_path": "see source metadata",
        "result_path": str(report_root / "results" / "comparisons" / f"{metadata['case_id']}.json"),
        "stdout_path": "",
        "stderr_path": "",
        "kit_log_path": "",
        "validation_status": metadata["validation_status"],
        "notes": metadata["alignment"],
    }


def relative_url(report_root: Path, target: str | Path) -> str:
    try:
        relative = Path(target).resolve().relative_to(report_root.resolve()).as_posix()
        return quote(relative)
    except ValueError:
        return quote(Path(target).resolve().as_uri(), safe=":/")


def build_html(report_root: Path, primary: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for item in primary:
        case = item["case"]
        video_url = relative_url(report_root, item["video"])
        thumb_url = relative_url(report_root, item["screenshots"]["thumbnail"])
        result_url = relative_url(report_root, item["result"])
        telemetry_url = relative_url(report_root, item["telemetry"])
        cards.append(
            f"""
<article class="card">
  <h2>{html.escape(case['method'])} · {case['height_mm']} mm · {html.escape(case['requested_outcome'])}</h2>
  <video controls preload="metadata" poster="{thumb_url}"><source src="{video_url}" type="video/mp4"></video>
  <dl>
    <dt>Scenario</dt><dd>{html.escape(case['scenario_id'])}</dd>
    <dt>Actual outcome</dt><dd>{html.escape(item['actual_outcome'].upper())}</dd>
    <dt>Failure reason</dt><dd>{html.escape(item['failure_reason'] or 'none')}</dd>
    <dt>Checkpoint</dt><dd>{html.escape(case['checkpoint_label'])}</dd>
    <dt>Validation</dt><dd>{html.escape(item['validation_status'])}</dd>
  </dl>
  <p><a href="{result_url}">result JSON</a> · <a href="{telemetry_url}">telemetry CSV</a></p>
</article>"""
        )
        if item.get("highlight"):
            highlight = item["highlight"]
            highlight_url = relative_url(report_root, highlight["path"])
            cards.append(
                f"""
<article class="card highlight">
  <h2>TIMEOUT highlight · {html.escape(case['method'])} · {case['height_mm']} mm</h2>
  <video controls preload="metadata"><source src="{highlight_url}" type="video/mp4"></video>
  <p>Full TIMEOUT video is retained in the primary card above.</p>
</article>"""
            )
    comparison_cards = []
    for item in comparisons:
        comparison_cards.append(
            f"""
<article class="card wide">
  <h2>{html.escape(item['case_id'])}</h2>
  <video controls preload="metadata" poster="{relative_url(report_root, item['thumbnail'])}">
    <source src="{relative_url(report_root, item['video'])}" type="video/mp4">
  </video>
  <p>{html.escape(item['left_label'])} · {html.escape(item['right_label'])}</p>
  <p>Scenario: {html.escape(item['scenario_id'])}; alignment: simulation time.</p>
</article>"""
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FSM / Residual PPO Development Visualization</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; background:#09101d; color:#edf3ff; }}
body {{ margin:0; padding:28px; }} h1 {{ margin:0 0 8px; }} .note {{ color:#aebbd1; margin-bottom:24px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:20px; }}
.card {{ background:#111b2d; border:1px solid #273653; border-radius:14px; padding:16px; box-shadow:0 12px 28px #0007; }}
.card h2 {{ font-size:18px; margin:0 0 12px; }} video {{ width:100%; border-radius:9px; background:#000; }}
dl {{ display:grid; grid-template-columns:140px 1fr; gap:6px 12px; }} dt {{ color:#8fa1bd; }} dd {{ margin:0; overflow-wrap:anywhere; }}
a {{ color:#72b7ff; }} .wide {{ grid-column:1/-1; }} .highlight {{ border-color:#9b7731; }}
</style></head><body>
<h1>Existing FSM / PPO development behavior</h1>
<p class="note">Development-scenario deterministic replays only. These are not locked-test results and no training was run.</p>
<h1>Primary cases</h1><section class="grid">{''.join(cards)}</section>
<h1 style="margin-top:32px">Same-scenario comparisons</h1><section class="grid">{''.join(comparison_cards)}</section>
</body></html>"""


def build_indexes(report_root: Path) -> None:
    primary = all_primary_metadata(report_root)
    comparison_paths = sorted((report_root / "results" / "comparisons").glob("*.json"))
    comparisons = [read_json(path) for path in comparison_paths]
    rows = [_primary_manifest_row(item) for item in primary]
    rows.extend(_highlight_manifest_row(item) for item in primary if item.get("highlight"))
    rows.extend(_comparison_manifest_row(item, report_root) for item in comparisons)
    csv_write(report_root / "capture_manifest.csv", rows, MANIFEST_FIELDS)
    write_json(report_root / "capture_manifest.json", rows)
    (report_root / "index.html").write_text(build_html(report_root, primary, comparisons), encoding="utf-8")
    backup = PROJECT_ROOT / "src" / "resume_validation" / "evaluate_controller.py.pre_visualization_20260731_215648.bak"
    current = PROJECT_ROOT / "src" / "resume_validation" / "evaluate_controller.py"
    if backup.is_file() and current.is_file():
        diff = difflib.unified_diff(
            backup.read_text(encoding="utf-8").splitlines(keepends=True),
            current.read_text(encoding="utf-8").splitlines(keepends=True),
            fromfile=str(backup),
            tofile=str(current),
        )
        (report_root / "crash_diagnostics" / "evaluate_controller_visualization.diff").write_text(
            "".join(diff), encoding="utf-8"
        )

    completed = [row for row in rows if row["validation_status"] == "PASSED"]
    failed = [row for row in rows if row["validation_status"] != "PASSED"]
    mismatches = [
        metadata
        for metadata in primary
        if metadata.get("status") == "REPRODUCTION_MISMATCH"
    ]
    state = read_json(report_root / "capture_state.json") if (report_root / "capture_state.json").is_file() else {"cases": {}}
    skipped = [case_id for case_id, item in state.get("cases", {}).items() if item.get("status") == "SKIPPED_NO_MATCHING_SCENARIO"]
    total_size = sum(int(row.get("file_size") or 0) for row in rows)
    video_lines = "\n".join(
        f"- `{row['case_id']}` — {row['actual_outcome']}"
        + (f" / {row['failure_reason']}" if row["failure_reason"] else "")
        + f" — `{row['video_path']}` — {row['validation_status']}"
        for row in rows
    )
    report = f"""# Recording report

- Required primary cases: 14
- Completed/validated primary cases: {sum(row['controller'] != 'comparison' and not str(row['case_id']).startswith('highlight_') and row['validation_status'] == 'PASSED' for row in rows)}
- Completed/validated comparison cases: {sum(row['controller'] == 'comparison' and row['validation_status'] == 'PASSED' for row in rows)}
- Outcome reproduction mismatches (video still validated): {len(mismatches)}
- Failed manifest entries: {len(failed)}
- Skipped cases: {len(skipped)}
- Total indexed videos: {len(rows)}
- Total indexed video size: {total_size / (1024 ** 3):.3f} GiB

No training, method freeze, locked manifest, locked test, or validation selection was run.

## Videos

{video_lines or '- No videos indexed.'}

## New tools and entrypoints

- `tools/visualization/diagnose_isaac_startup.py`
- `tools/visualization/isaac_startup_smoke.py`
- `tools/visualization/visualization_common.py`
- `tools/visualization/record_existing_controller.py`
- `tools/visualization/build_video_index.py`
- `tools/visualization/launch_existing_evaluator.py`
- `scripts/visualization/01_diagnose_isaac_startup.ps1` through `06_open_results.ps1`
- `scripts/visualization/show_recorded_or_live.ps1`
- `tests/test_visualization_capture.py`

## Modified existing file

- `src/resume_validation/evaluate_controller.py` — visualization-only camera/frame/heartbeat and shutdown lifecycle support.
- Backup: `src/resume_validation/evaluate_controller.py.pre_visualization_20260731_215648.bak`.
"""
    (report_root / "RECORDING_REPORT.md").write_text(report, encoding="utf-8")
    (report_root / "VIDEO_INDEX.md").write_text(
        "# Video index\n\n" + (video_lines or "- No videos indexed.") + "\n",
        encoding="utf-8",
    )
    opener = f"""$root = '{str(report_root).replace("'", "''")}'
Start-Process (Join-Path $root 'index.html')
Start-Process (Join-Path $root 'videos')
"""
    (report_root / "open_results.ps1").write_text(opener, encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--comparisons", action="store_true")
    parser.add_argument(
        "--comparison-id",
        action="append",
        default=[],
        choices=[spec["case_id"] for spec in COMPARISON_SPECS],
        help="Build only the selected comparison; repeat for more than one.",
    )
    parser.add_argument("--index", action="store_true")
    args = parser.parse_args()
    report_root = args.report_root.resolve()
    if args.comparisons:
        built = build_comparisons(report_root, set(args.comparison_id) or None)
        print(f"Built/verified {len(built)} comparison(s)")
    if args.index:
        build_indexes(report_root)
        print(report_root / "index.html")
    if not args.comparisons and not args.index:
        parser.error("Choose --comparisons and/or --index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
