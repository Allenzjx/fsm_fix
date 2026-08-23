"""Capture one or more existing development FSM/PPO controllers offscreen.

The Isaac physics/controller execution is delegated to the existing
``evaluate_controller.py`` entrypoint.  This program owns process supervision,
resume state, video post-processing, validation, and artifact indexing.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

import cv2
import imageio.v2 as imageio
import numpy as np

from visualization_common import (
    DEVELOPMENT_MANIFEST,
    EVALUATOR,
    FSM_CONFIG,
    ISAACLAB_ROOT,
    PROJECT_ROOT,
    ROBOT_ASSET,
    TERMINAL_STATES,
    build_primary_plan,
    format_command,
    initialize_report_tree,
    load_or_create_state,
    read_json,
    resolve_conda,
    sha256_file,
    validate_no_locked_reference,
    write_json,
)


KIT_LOG_ROOT = Path(
    r"C:\Users\kskzz\miniconda3\envs\env_isaaclab\Lib\site-packages\isaacsim\kit\logs\Kit\Isaac-Sim\5.1"
)


def process_snapshot() -> list[dict[str, Any]]:
    script = (
        "$rows=@(Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -match 'python|kit|isaac|conda|cmd|powershell' } | "
        "Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine); "
        "$rows | ConvertTo-Json -Depth 4 -Compress"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    text = completed.stdout.strip()
    if not text:
        return []
    value = json.loads(text)
    return value if isinstance(value, list) else [value]


def descendants(root_pid: int, snapshot: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = snapshot or process_snapshot()
    by_parent: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_parent.setdefault(int(row.get("ParentProcessId") or -1), []).append(row)
    found: list[dict[str, Any]] = []
    frontier = [root_pid]
    visited = {root_pid}
    while frontier:
        parent = frontier.pop()
        for row in by_parent.get(parent, []):
            pid = int(row["ProcessId"])
            if pid not in visited:
                visited.add(pid)
                frontier.append(pid)
                found.append(row)
    return found


def terminate_owned_tree(root_pid: int, marker: str) -> list[int]:
    """Stop exactly one capture's process tree after validating the root marker."""
    escaped_marker = marker.replace("'", "''")
    script = rf"""
$rootPid={int(root_pid)}
$marker='{escaped_marker}'
$root=Get-CimInstance Win32_Process -Filter "ProcessId=$rootPid"
if(-not $root -or -not $root.CommandLine -or $root.CommandLine -notmatch [regex]::Escape($marker)){{
  throw 'Owned process root identity check failed'
}}
$all=@(Get-CimInstance Win32_Process)
$ids=[System.Collections.Generic.List[int]]::new()
$ids.Add($rootPid)
do{{
  $added=$false
  foreach($p in $all){{
    if($ids.Contains([int]$p.ParentProcessId)-and -not $ids.Contains([int]$p.ProcessId)){{
      $ids.Add([int]$p.ProcessId);$added=$true
    }}
  }}
}}while($added)
$targets=@($all|Where-Object{{$ids.Contains([int]$_.ProcessId)}})
foreach($p in ($targets|Sort-Object ProcessId -Descending)){{
  Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}}
$ids | ConvertTo-Json -Compress
"""
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    text = completed.stdout.strip()
    if not text:
        return []
    value = json.loads(text)
    return [int(item) for item in (value if isinstance(value, list) else [value])]


def latest_kit_log(after_timestamp: float) -> Path | None:
    candidates = [
        path
        for path in KIT_LOG_ROOT.glob("kit_*.log")
        if path.stat().st_mtime >= after_timestamp - 5.0
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def read_episode(result: dict[str, Any]) -> dict[str, Any]:
    episodes_path = Path(result["artifacts"]["episodes"])
    rows = [json.loads(line) for line in episodes_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one episode, found {len(rows)} in {episodes_path}")
    return rows[0]


def read_telemetry_summary(path: Path) -> dict[str, Any]:
    first: dict[str, str] | None = None
    last: dict[str, str] | None = None
    phase_transitions: list[float] = []
    previous_phase: str | None = None
    times: list[float] = []
    base_x: list[float] = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if first is None:
                first = row
            last = row
            phase = row.get("fsm_phase", "")
            timestamp = float(row.get("time_s") or 0.0)
            if previous_phase is not None and phase != previous_phase:
                phase_transitions.append(timestamp)
            previous_phase = phase
            times.append(timestamp)
            base_x.append(float(row.get("base_x_m") or 0.0))
    if first is None or last is None:
        raise RuntimeError(f"Telemetry is empty: {path}")
    stall_start = None
    # Find the first 10-second window with less than 1 cm net progress.
    left = 0
    for right, timestamp in enumerate(times):
        while left < right and timestamp - times[left] > 10.0:
            left += 1
        if timestamp - times[left] >= 9.5 and abs(base_x[right] - base_x[left]) < 0.01:
            stall_start = times[left]
            break
    return {
        "first": first,
        "last": last,
        "duration_s": float(last.get("time_s") or 0.0),
        "final_phase": int(round(float(last.get("fsm_phase") or 0.0))),
        "phase_transitions_s": phase_transitions,
        "stall_start_s": stall_start,
    }


def _writer(path: Path, fps: float):
    path.parent.mkdir(parents=True, exist_ok=True)
    return imageio.get_writer(
        path,
        fps=fps,
        codec="libx264",
        quality=8,
        macro_block_size=None,
    )


def encode_png_fallback(frames_dir: Path, video_path: Path, fps: float) -> None:
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        raise RuntimeError(f"No PNG frames available for fallback encoding: {frames_dir}")
    writer = _writer(video_path, fps)
    try:
        for path in frames:
            frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if frame is None:
                raise RuntimeError(f"Could not read fallback frame: {path}")
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        writer.close()


def export_video_to_png(source: Path, frames_dir: Path) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open failed-encode source for PNG preservation: {source}")
    count = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            target = frames_dir / f"frame_{count:06d}.png"
            if not cv2.imwrite(str(target), frame):
                raise RuntimeError(f"Could not preserve failed-encode PNG: {target}")
            count += 1
    finally:
        capture.release()
    if count == 0:
        raise RuntimeError(f"Failed-encode source had no decodable frames: {source}")
    return count


def draw_result_card(
    frame: np.ndarray,
    *,
    outcome: str,
    failure_reason: str,
    final_phase: int,
    duration_s: float,
    min_margin: float | None,
    pitch_rate_rms: float | None,
    scenario_id: str,
    checkpoint_sha: str,
) -> np.ndarray:
    card = frame.copy()
    overlay = np.zeros_like(card)
    cv2.rectangle(overlay, (0, 0), (card.shape[1], card.shape[0]), (8, 12, 20), thickness=-1)
    card = cv2.addWeighted(card, 0.18, overlay, 0.82, 0.0)
    color = (65, 220, 110) if outcome == "SUCCESS" else (70, 105, 245)
    lines = [
        outcome,
        f"Failure reason: {failure_reason or 'none'}",
        f"Final FSM phase: {final_phase}",
        f"Simulation duration: {duration_s:.2f} s",
        f"Minimum support margin: {'n/a' if min_margin is None else f'{min_margin:+.4f} m'}",
        f"Pitch-rate RMS: {'n/a' if pitch_rate_rms is None else f'{pitch_rate_rms:.4f} rad/s'}",
        f"Scenario: {scenario_id}",
        f"Checkpoint SHA-256: {checkpoint_sha[:12] if checkpoint_sha else 'FSM-only'}",
    ]
    for index, text in enumerate(lines):
        scale = 1.55 if index == 0 else 0.78
        thickness = 4 if index == 0 else 2
        cv2.putText(
            card,
            text,
            (70, 105 + index * 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color if index == 0 else (238, 242, 248),
            thickness,
            cv2.LINE_AA,
        )
    return card


def finalize_video(
    raw_path: Path,
    output_path: Path,
    fps: float,
    episode: dict[str, Any],
    telemetry: dict[str, Any],
    scenario_id: str,
    checkpoint_sha: str,
) -> None:
    capture = cv2.VideoCapture(str(raw_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not decode raw video: {raw_path}")
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not math.isfinite(source_fps) or source_fps <= 0.0:
        raise RuntimeError(f"Raw video reports invalid FPS: {source_fps}")
    writer = _writer(output_path, fps)
    last_rgb = None
    source_index = 0
    emitted_frames = 0
    try:
        while True:
            ok, bgr = capture.read()
            if not ok:
                break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            # Rendering every controller frame is the dominant Isaac/RTX cost.
            # The raw capture is sampled at 2 Hz and each sample is held for the
            # corresponding interval in the 20 FPS delivery file.  This keeps
            # playback duration exactly tied to simulation time without touching
            # physics/control dt or accelerating the controller.
            target_emitted = int(round((source_index + 1) * fps / source_fps))
            for _ in range(max(1, target_emitted - emitted_frames)):
                writer.append_data(rgb)
            emitted_frames = target_emitted
            source_index += 1
            last_rgb = rgb
        if last_rgb is None:
            raise RuntimeError(f"Raw video has no frames: {raw_path}")
        outcome = "SUCCESS" if bool(episode.get("success")) else "FAILED"
        card_bgr = draw_result_card(
            cv2.cvtColor(last_rgb, cv2.COLOR_RGB2BGR),
            outcome=outcome,
            failure_reason=str(episode.get("failure_reason") or ""),
            final_phase=int(telemetry["final_phase"]),
            duration_s=float(telemetry["duration_s"]),
            min_margin=(
                float(episode["min_longitudinal_support_margin_m"])
                if episode.get("min_longitudinal_support_margin_m") is not None
                else None
            ),
            pitch_rate_rms=(
                float(episode["pitch_rate_rms_rad_s"])
                if episode.get("pitch_rate_rms_rad_s") is not None
                else None
            ),
            scenario_id=scenario_id,
            checkpoint_sha=checkpoint_sha,
        )
        card_rgb = cv2.cvtColor(card_bgr, cv2.COLOR_BGR2RGB)
        for _ in range(int(round(fps * 2.5))):
            writer.append_data(card_rgb)
    finally:
        capture.release()
        writer.close()


def video_probe(path: Path, expected_width: int | None = None, expected_height: int | None = None) -> dict[str, Any]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        return {"passed": False, "failures": ["video cannot be opened"]}
    width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
    height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))

    def at(index: int) -> np.ndarray | None:
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, index))
        ok, frame = capture.read()
        return frame if ok else None

    first = at(0)
    middle = at(max(0, frame_count // 2))
    last = at(max(0, frame_count - 1))
    capture.release()
    failures: list[str] = []
    if not path.is_file() or path.stat().st_size <= 0:
        failures.append("empty video file")
    if frame_count <= 30:
        failures.append(f"frame_count={frame_count} <= 30")
    duration = frame_count / fps if fps > 0 else 0.0
    if duration <= 1.0:
        failures.append(f"duration={duration:.3f} <= 1")
    if expected_width is not None and width != expected_width:
        failures.append(f"width={width}, expected={expected_width}")
    if expected_height is not None and height != expected_height:
        failures.append(f"height={height}, expected={expected_height}")
    if any(frame is None for frame in (first, middle, last)):
        failures.append("failed to decode key frame")
        means = []
        change = 0.0
    else:
        assert first is not None and middle is not None and last is not None
        means = [float(frame.mean()) for frame in (first, middle, last)]
        scene_means = [
            float(frame[int(frame.shape[0] * 0.30) :, :].mean())
            for frame in (first, middle, last)
        ]
        scene_stds = [
            float(frame[int(frame.shape[0] * 0.30) :, :].std())
            for frame in (first, middle, last)
        ]
        if any(mean < 2.0 or std < 2.0 for mean, std in zip(scene_means, scene_stds)):
            failures.append(
                f"blank key-frame scene region mean(s)={scene_means}, std(s)={scene_stds}"
            )
        if any(value > 253.0 for value in means):
            failures.append(f"white key frame mean(s)={means}")
        change = float(np.mean(np.abs(first.astype(np.float32) - middle.astype(np.float32))))
        if change < 0.5:
            failures.append(f"insufficient pixel change={change:.4f}")
    return {
        "passed": not failures,
        "failures": failures,
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "duration_s": duration,
        "key_frame_means": means,
        "key_frame_scene_means": scene_means if all(frame is not None for frame in (first, middle, last)) else [],
        "key_frame_scene_stds": scene_stds if all(frame is not None for frame in (first, middle, last)) else [],
        "first_middle_mean_absolute_change": change,
        "file_size": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256_file(path) if path.is_file() else "",
    }


def repair_blank_frames(path: Path, maximum_consecutive_blank_s: float = 2.0) -> int:
    """Replace short blank render-product segments while preserving duration.

    Blank detection excludes the diagnostic overlay. Initial blanks use the
    first valid scene frame; later isolated blanks hold the preceding valid
    frame. A prolonged blank segment remains a hard capture failure.
    """
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video for blank-frame inspection: {path}")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    temporary = path.with_suffix(".blank-repair.mp4")
    writer = _writer(temporary, fps)
    replaced_count = 0
    consecutive_blank = 0
    pending_initial_blank = 0
    last_valid = None
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            scene = frame[int(frame.shape[0] * 0.30) :, :]
            blank = float(scene.mean()) < 2.0 or float(scene.std()) < 2.0
            if blank:
                replaced_count += 1
                consecutive_blank += 1
                if consecutive_blank > int(round(fps * maximum_consecutive_blank_s)):
                    raise RuntimeError(
                        "Blank render segment exceeds "
                        f"{maximum_consecutive_blank_s:.1f}s: {path}"
                    )
                if last_valid is None:
                    pending_initial_blank += 1
                    continue
                delivery_frame = last_valid
            else:
                consecutive_blank = 0
                if last_valid is None and pending_initial_blank:
                    first_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    for _ in range(pending_initial_blank):
                        writer.append_data(first_rgb)
                last_valid = frame
                delivery_frame = frame
            writer.append_data(cv2.cvtColor(delivery_frame, cv2.COLOR_BGR2RGB))
        if last_valid is None:
            raise RuntimeError(f"Video never produced a valid scene frame: {path}")
        writer.close()
        capture.release()
        if replaced_count:
            os.replace(temporary, path)
        else:
            temporary.unlink(missing_ok=True)
        return replaced_count
    except Exception:
        try:
            writer.close()
        except Exception:
            pass
        temporary.unlink(missing_ok=True)
        raise
    finally:
        capture.release()


def extract_key_images(video: Path, report_root: Path, case_id: str) -> dict[str, str]:
    capture = cv2.VideoCapture(str(video))
    count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
    outputs: dict[str, str] = {}
    for label, index in (("first", 0), ("middle", count // 2), ("last", max(0, count - 1))):
        capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = capture.read()
        if not ok:
            capture.release()
            raise RuntimeError(f"Failed extracting {label} from {video}")
        path = report_root / "screenshots" / f"{case_id}_{label}.png"
        cv2.imwrite(str(path), frame)
        outputs[label] = str(path)
        if label == "middle":
            thumbnail = report_root / "thumbnails" / f"{case_id}.jpg"
            resized = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(thumbnail), resized, [cv2.IMWRITE_JPEG_QUALITY, 88])
            outputs["thumbnail"] = str(thumbnail)
    capture.release()
    return outputs


def _merge_ranges(ranges: list[tuple[float, float]], duration: float) -> list[tuple[float, float]]:
    normalized = sorted((max(0.0, start), min(duration, end)) for start, end in ranges if end > start)
    merged: list[list[float]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1] + 0.25:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def make_timeout_highlight(source: Path, target: Path, telemetry: dict[str, Any], fps: float) -> dict[str, Any]:
    duration = float(telemetry["duration_s"])
    ranges = [(0.0, 10.0), (max(0.0, duration - 20.0), duration)]
    ranges.extend((value - 1.5, value + 1.5) for value in telemetry["phase_transitions_s"])
    if telemetry.get("stall_start_s") is not None:
        stall = float(telemetry["stall_start_s"])
        ranges.append((max(0.0, stall - 10.0), stall + 2.0))
    merged = _merge_ranges(ranges, duration)
    capture = cv2.VideoCapture(str(source))
    writer = _writer(target, fps)
    written = 0
    try:
        for start, end in merged:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(math.floor(start * fps)))
            final_index = int(math.ceil(end * fps))
            while int(capture.get(cv2.CAP_PROP_POS_FRAMES)) < final_index:
                ok, bgr = capture.read()
                if not ok:
                    break
                cv2.putText(
                    bgr,
                    "TIMEOUT HIGHLIGHT",
                    (bgr.shape[1] - 360, bgr.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (40, 220, 255),
                    2,
                    cv2.LINE_AA,
                )
                writer.append_data(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
                written += 1
    finally:
        capture.release()
        writer.close()
    return {"ranges_s": merged, "frame_count": written, "path": str(target)}


def postprocess_case(case, report_root: Path, sim_dir: Path, process_meta: dict[str, Any]) -> dict[str, Any]:
    result_path = sim_dir / "result.json"
    if not result_path.is_file():
        raise RuntimeError(f"Evaluation produced no result.json: {result_path}")
    result = read_json(result_path)
    if not bool(result.get("passed_execution")):
        raise RuntimeError(f"Evaluation failed: {result.get('failures')}")
    if str(result.get("controller")) != case.controller:
        raise RuntimeError("Controller mismatch in result.json")
    if int(result.get("height_mm")) != case.height_mm:
        raise RuntimeError("Height mismatch in result.json")
    replay = result.get("video_replay", {})
    if str(replay.get("scenario_id")) != case.scenario_id:
        raise RuntimeError("Scenario mismatch in result.json")
    provenance = result.get("provenance", {})
    if str(provenance.get("manifest")) != str(DEVELOPMENT_MANIFEST.resolve()):
        raise RuntimeError("Result does not use the exact development manifest")
    if case.checkpoint and str(Path(provenance.get("checkpoint", "")).resolve()) != str(Path(case.checkpoint).resolve()):
        raise RuntimeError("Checkpoint mismatch in result.json")
    if str(provenance.get("fsm_config_sha256")) != sha256_file(FSM_CONFIG):
        raise RuntimeError("FSM hash mismatch in result.json")
    if str(provenance.get("asset_sha256")) != sha256_file(ROBOT_ASSET):
        raise RuntimeError("Robot asset hash mismatch in result.json")
    if str(provenance.get("manifest_sha256")) != sha256_file(DEVELOPMENT_MANIFEST):
        raise RuntimeError("Development manifest hash mismatch in result.json")

    episode = read_episode(result)
    if str(episode.get("scenario_id")) != case.scenario_id:
        raise RuntimeError("Scenario mismatch in episodes.jsonl")
    actual_outcome = "success" if bool(episode.get("success")) else "failure"
    actual_failure = str(episode.get("failure_reason") or "")
    telemetry_path = Path(result["artifacts"]["telemetry"])
    telemetry = read_telemetry_summary(telemetry_path)
    raw_path = Path(replay.get("path") or (sim_dir / "raw.avi"))
    frames_dir = Path(result.get("artifacts", {}).get("video_frames") or (sim_dir / "frames"))
    if replay.get("encoding_error") or not raw_path.is_file() or raw_path.stat().st_size <= 0:
        failed_copy = report_root / "videos" / "failed_encodes" / f"{case.case_id}_raw_failed.mp4"
        if raw_path.is_file():
            shutil.copy2(raw_path, failed_copy)
        encode_png_fallback(frames_dir, raw_path, 2.0)

    base_name = case.output_filename
    if actual_failure == "TIMEOUT":
        base_name = "full_" + base_name
    final_video = report_root / "videos" / "primary" / base_name
    final_temp = final_video.with_suffix(".encoding.mp4")
    try:
        finalize_video(
            raw_path,
            final_temp,
            20.0,
            episode,
            telemetry,
            case.scenario_id,
            str(provenance.get("checkpoint_sha256") or ""),
        )
    except Exception:
        preserved = report_root / "frames_failed_only" / f"{case.case_id}_final_encode_failure"
        if not preserved.exists():
            export_video_to_png(raw_path, preserved)
        raise
    os.replace(final_temp, final_video)
    blank_frames_replaced = repair_blank_frames(final_video)
    probe = video_probe(final_video, 1280, 720)
    if not probe["passed"]:
        raise RuntimeError(f"Final video validation failed: {probe['failures']}")
    screenshots = extract_key_images(final_video, report_root, case.case_id)

    highlight = None
    if actual_failure == "TIMEOUT":
        highlight_path = report_root / "videos" / "primary" / ("highlight_" + case.output_filename)
        highlight = make_timeout_highlight(final_video, highlight_path, telemetry, 20.0)
        highlight["probe"] = video_probe(highlight_path, 1280, 720)
        if not highlight["probe"]["passed"]:
            raise RuntimeError(f"Timeout highlight validation failed: {highlight['probe']['failures']}")

    telemetry_copy = report_root / "telemetry" / f"{case.case_id}.csv"
    result_copy = report_root / "results" / f"{case.case_id}.json"
    episodes_copy = report_root / "results" / f"{case.case_id}_episodes.jsonl"
    shutil.copy2(telemetry_path, telemetry_copy)
    shutil.copy2(result_path, result_copy)
    shutil.copy2(Path(result["artifacts"]["episodes"]), episodes_copy)

    requested_matches = actual_outcome == case.requested_outcome
    status = "COMPLETED" if requested_matches else "REPRODUCTION_MISMATCH"
    metadata = {
        "schema": "resume_validation.visualization_case.v1",
        "case": asdict(case),
        "status": status,
        "actual_outcome": actual_outcome,
        "failure_reason": actual_failure,
        "final_phase": telemetry["final_phase"],
        "simulation_duration_s": telemetry["duration_s"],
        "provenance": provenance,
        "video": str(final_video),
        "video_probe": probe,
        "video_sha256": probe["sha256"],
        "blank_delivery_frames_replaced": blank_frames_replaced,
        "highlight": highlight,
        "screenshots": screenshots,
        "telemetry": str(telemetry_copy),
        "result": str(result_copy),
        "episodes": str(episodes_copy),
        "stdout": process_meta["stdout_path"],
        "stderr": process_meta["stderr_path"],
        "kit_log": process_meta.get("kit_log_path", ""),
        "process": process_meta,
        "validation_status": "PASSED" if probe["passed"] else "FAILED",
        "notes": (
            "Requested outcome reproduced."
            if requested_matches
            else f"Requested {case.requested_outcome}, replay produced {actual_outcome}."
        ),
    }
    metadata_path = report_root / "results" / case.case_id / "metadata.json"
    write_json(metadata_path, metadata)
    # Full PNG sequences are retained only for encoding/capture failures.  The
    # first/middle/last screenshots and thumbnail above are permanent.
    if frames_dir.is_dir():
        shutil.rmtree(frames_dir)
    return metadata


def repair_completed_case(report_root: Path, case_id: str) -> dict[str, Any]:
    metadata_path = report_root / "results" / case_id / "metadata.json"
    metadata = read_json(metadata_path)
    video = Path(metadata["video"])
    replaced = repair_blank_frames(video)
    probe = video_probe(video, int(metadata["video_probe"]["width"]), int(metadata["video_probe"]["height"]))
    if not probe["passed"]:
        raise RuntimeError(f"Repaired video validation failed: {probe['failures']}")
    metadata["blank_delivery_frames_replaced"] = (
        int(metadata.get("blank_delivery_frames_replaced", 0)) + replaced
    )
    metadata["video_probe"] = probe
    metadata["video_sha256"] = probe["sha256"]
    metadata["screenshots"] = extract_key_images(video, report_root, case_id)
    metadata["validation_status"] = "PASSED"
    metadata["notes"] = str(metadata.get("notes") or "") + (
        f" {replaced} short render-product blank delivery frames replaced with a neighboring valid scene frame."
        if replaced
        else " Initial scene frame already valid."
    )
    write_json(metadata_path, metadata)
    return metadata


def reprocess_attempt(report_root: Path, case_id: str, attempt: int) -> dict[str, Any]:
    cases = {case.case_id: case for case in build_primary_plan()}
    if case_id not in cases:
        raise KeyError(f"Unknown case ID: {case_id}")
    case_root = report_root / "results" / case_id
    sim_dir = case_root / f"sim_attempt_{attempt:03d}"
    process_path = case_root / f"process_attempt_{attempt:03d}.json"
    if not (sim_dir / "result.json").is_file() or not process_path.is_file():
        raise FileNotFoundError(f"Attempt is not complete enough to reprocess: {sim_dir}")
    metadata = postprocess_case(cases[case_id], report_root, sim_dir, read_json(process_path))
    state = load_or_create_state(report_root, cases.values())
    state["cases"][case_id].update(
        {
            "status": metadata["status"],
            "video": metadata["video"],
            "validation_status": metadata["validation_status"],
            "reprocessed_attempt": attempt,
        }
    )
    state["updated_at"] = time.time()
    write_json(report_root / "capture_state.json", state)
    return metadata


def run_case(case, report_root: Path, startup_timeout: float, shutdown_grace: float, frozen_timeout: float) -> dict[str, Any]:
    state = load_or_create_state(report_root, build_primary_plan())
    record = state["cases"][case.case_id]
    metadata_path = report_root / "results" / case.case_id / "metadata.json"
    if record.get("status") in TERMINAL_STATES and metadata_path.is_file():
        existing = read_json(metadata_path)
        if existing.get("validation_status") == "PASSED" and Path(existing["video"]).is_file():
            print(f"[resume] {case.case_id}: {record['status']}")
            return existing

    # Do not overwrite an incomplete simulation directory.  Preserve it and use
    # a numbered attempt directory inside the case result folder.
    record["attempts"] = int(record.get("attempts", 0)) + 1
    attempt = record["attempts"]
    case_root = report_root / "results" / case.case_id
    sim_dir = case_root / f"sim_attempt_{attempt:03d}"
    stdout_path = report_root / "logs" / f"{case.case_id}_attempt{attempt:03d}.stdout.log"
    stderr_path = report_root / "logs" / f"{case.case_id}_attempt{attempt:03d}.stderr.log"
    heartbeat_path = sim_dir / "heartbeat.json"
    raw_video = sim_dir / "raw.avi"
    raw_frames = sim_dir / "frames"
    checkpoint_sha = sha256_file(case.checkpoint) if case.checkpoint else ""

    command = [
        str(resolve_conda()),
        "run",
        "--no-capture-output",
        "-n",
        "env_isaaclab",
        str(ISAACLAB_ROOT / "isaaclab.bat"),
        "-p",
        str(EVALUATOR),
        "--controller",
        case.controller,
        "--manifest",
        str(DEVELOPMENT_MANIFEST),
        "--height_mm",
        str(case.height_mm),
        "--output_dir",
        str(sim_dir),
        "--scenario_id",
        case.scenario_id,
        "--record_stride",
        "3",
        "--video_path",
        str(raw_video),
        "--video_stride",
        "30",
        "--video_fps",
        "2",
        "--video_width",
        "1280",
        "--video_height",
        "720",
        "--video_category",
        "development-visualization",
        "--video_outcome_label",
        case.requested_outcome,
        "--video_seed",
        str(case.seed if case.seed is not None else -1),
        "--video_checkpoint_label",
        case.checkpoint_label,
        "--video_codec",
        "mjpeg",
        "--no-video_follow_camera",
        "--heartbeat_path",
        str(heartbeat_path),
        "--enable_cameras",
        "--headless",
    ]
    if case.checkpoint:
        command.extend(("--checkpoint", case.checkpoint))
    validate_no_locked_reference(command)
    if any(token in " ".join(command).lower() for token in ("train_residual_ppo", "06_train_c", "run_until_success")):
        raise RuntimeError("Training/supervisor token found in capture command")

    case_root.mkdir(parents=True, exist_ok=True)
    record.update(
        {
            "status": "RUNNING",
            "started_at": time.time(),
            "command": format_command(command),
            "simulation_dir": str(sim_dir),
        }
    )
    state["updated_at"] = time.time()
    write_json(report_root / "capture_state.json", state)
    start_snapshot = process_snapshot()
    write_json(
        report_root / "crash_diagnostics" / "process_snapshots" / f"{case.case_id}_attempt{attempt:03d}_start.json",
        start_snapshot,
    )

    started = time.time()
    process_meta: dict[str, Any] = {
        "command": format_command(command),
        "working_directory": str(ISAACLAB_ROOT),
        "parent_pid": os.getpid(),
        "started_at": started,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "checkpoint_sha256": checkpoint_sha,
    }
    forced_shutdown = False
    killed_pids: list[int] = []
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        proc = subprocess.Popen(
            command,
            cwd=ISAACLAB_ROOT,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        process_meta["child_pid"] = proc.pid
        record["parent_pid"] = os.getpid()
        record["child_pid"] = proc.pid
        state["updated_at"] = time.time()
        write_json(report_root / "capture_state.json", state)
        startup_deadline = started + startup_timeout
        result_seen_at: float | None = None
        last_heartbeat_mtime: float | None = None
        last_heartbeat_change = time.time()
        next_snapshot = time.time()
        failure = None
        while proc.poll() is None:
            now = time.time()
            if heartbeat_path.is_file():
                mtime = heartbeat_path.stat().st_mtime
                if last_heartbeat_mtime != mtime:
                    last_heartbeat_mtime = mtime
                    last_heartbeat_change = now
                    try:
                        heartbeat = read_json(heartbeat_path)
                        record["simulation_time_s"] = heartbeat.get("simulation_time_s", 0.0)
                        record["frame_count"] = heartbeat.get("frame_count", 0)
                    except Exception:
                        pass
            elif now > startup_deadline:
                failure = f"startup timeout after {startup_timeout:.0f}s"
                break
            if (sim_dir / "result.json").is_file():
                result_seen_at = result_seen_at or now
                if now - result_seen_at > shutdown_grace:
                    forced_shutdown = True
                    break
            elif last_heartbeat_mtime is not None and now - last_heartbeat_change > frozen_timeout:
                failure = f"heartbeat frozen for {frozen_timeout:.0f}s"
                break
            if now >= next_snapshot:
                snap = process_snapshot()
                process_meta["descendant_pids"] = [int(row["ProcessId"]) for row in descendants(proc.pid, snap)]
                next_snapshot = now + 30.0
            record["heartbeat_wall_time"] = now
            state["updated_at"] = now
            write_json(report_root / "capture_state.json", state)
            time.sleep(2.0)
        if proc.poll() is None and (forced_shutdown or failure):
            killed_pids = terminate_owned_tree(proc.pid, case.case_id)
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                failure = (failure or "shutdown grace exceeded") + "; conda root did not exit after owned-tree cleanup"
        exit_code = proc.poll()

    ended = time.time()
    process_meta.update(
        {
            "ended_at": ended,
            "duration_s": ended - started,
            "exit_code": exit_code,
            "forced_shutdown_after_result": forced_shutdown,
            "owned_pids_stopped": killed_pids,
        }
    )
    kit_log = latest_kit_log(started)
    if kit_log:
        copied_kit = report_root / "logs" / f"{case.case_id}_attempt{attempt:03d}_{kit_log.name}"
        shutil.copy2(kit_log, copied_kit)
        process_meta["kit_log_path"] = str(copied_kit)
    write_json(case_root / f"process_attempt_{attempt:03d}.json", process_meta)
    write_json(
        report_root / "crash_diagnostics" / "process_snapshots" / f"{case.case_id}_attempt{attempt:03d}_end.json",
        process_snapshot(),
    )

    try:
        if failure:
            raise RuntimeError(failure)
        metadata = postprocess_case(case, report_root, sim_dir, process_meta)
        record.update(
            {
                "status": metadata["status"],
                "ended_at": ended,
                "video": metadata["video"],
                "validation_status": metadata["validation_status"],
            }
        )
        return metadata
    except Exception as exc:
        record.update(
            {
                "status": "FAILED",
                "ended_at": ended,
                "failure": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
        if raw_frames.is_dir():
            preserved = report_root / "frames_failed_only" / f"{case.case_id}_attempt{attempt:03d}"
            if not preserved.exists():
                shutil.move(str(raw_frames), str(preserved))
        raise
    finally:
        state["updated_at"] = time.time()
        write_json(report_root / "capture_state.json", state)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--all-primary", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--repair-completed-case", type=str, default="")
    parser.add_argument("--reprocess-case", type=str, default="")
    parser.add_argument("--reprocess-attempt", type=int, default=0)
    parser.add_argument("--startup-timeout", type=float, default=300.0)
    parser.add_argument("--shutdown-grace", type=float, default=30.0)
    parser.add_argument("--frozen-timeout", type=float, default=300.0)
    args = parser.parse_args()
    report_root = args.report_root.resolve()
    initialize_report_tree(report_root)
    plan = build_primary_plan()
    write_json(report_root / "capture_plan.json", [asdict(case) for case in plan])
    load_or_create_state(report_root, plan)
    if args.repair_completed_case:
        repaired = repair_completed_case(report_root, args.repair_completed_case)
        print(json.dumps({"case_id": args.repair_completed_case, "video_probe": repaired["video_probe"]}, indent=2))
        return 0
    if args.reprocess_case:
        if args.reprocess_attempt <= 0:
            parser.error("--reprocess-case requires a positive --reprocess-attempt")
        reprocessed = reprocess_attempt(report_root, args.reprocess_case, args.reprocess_attempt)
        print(json.dumps({"case_id": args.reprocess_case, "metadata": reprocessed}, indent=2))
        return 0
    if args.plan_only:
        print(json.dumps([asdict(case) for case in plan], indent=2))
        return 0
    if not args.all_primary and not args.case_id:
        parser.error("Choose --all-primary or at least one --case-id")
    by_id = {case.case_id: case for case in plan}
    missing = [case_id for case_id in args.case_id if case_id not in by_id]
    if missing:
        parser.error("Unknown case ID(s): " + ", ".join(missing))
    selected = plan if args.all_primary else [by_id[case_id] for case_id in args.case_id]
    failures = 0
    for index, case in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {case.case_id}", flush=True)
        try:
            metadata = run_case(
                case,
                report_root,
                args.startup_timeout,
                args.shutdown_grace,
                args.frozen_timeout,
            )
            print(f"[{metadata['status']}] {metadata['video']}", flush=True)
        except Exception:
            failures += 1
            traceback.print_exc()
            # A supervisor-side exception must never orphan the active conda /
            # Isaac child before the batch proceeds to the next independent case.
            try:
                cleanup_state = load_or_create_state(report_root, plan)
                child_pid = int(cleanup_state["cases"][case.case_id].get("child_pid") or 0)
                if child_pid:
                    stopped = terminate_owned_tree(child_pid, case.case_id)
                    print(f"[cleanup] {case.case_id}: stopped owned PID tree {stopped}", flush=True)
            except Exception as cleanup_exc:
                print(
                    f"[cleanup-warning] {case.case_id}: {type(cleanup_exc).__name__}: {cleanup_exc}",
                    file=sys.stderr,
                    flush=True,
                )
            # Independent cases continue after diagnostics are persisted.
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
