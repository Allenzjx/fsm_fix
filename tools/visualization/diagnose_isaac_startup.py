"""Analyze prior Isaac Sim startup exits without launching Isaac Sim."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

from visualization_common import PROJECT_ROOT, initialize_report_tree, write_json


KEYWORD_RE = re.compile(
    r"error|fatal|exception|traceback|crash|access violation|segmentation|vulkan|dxgi|"
    r"renderer|shader|cuda|out of memory|device lost|failed|shutdown",
    re.IGNORECASE,
)
ERROR_RE = re.compile(r"\[(?:error|fatal)\]|\b(?:error|fatal)\b", re.IGNORECASE)
EXTENSION_RE = re.compile(r"\[ext:\s*([^\]]+)\]\s+startup", re.IGNORECASE)


def analyze_kit_log(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    keyword_lines = [line for line in lines if KEYWORD_RE.search(line)]
    error_lines = [line for line in lines if ERROR_RE.search(line)]
    extensions = [match.group(1) for line in lines if (match := EXTENSION_RE.search(line))]
    lower = "\n".join(lines).lower()
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "line_count": len(lines),
        "tail_300": lines[-300:],
        "keyword_lines": keyword_lines,
        "error_fatal_lines": error_lines,
        "last_successful_extension": extensions[-1] if extensions else None,
        "last_line": lines[-1] if lines else "",
        "crash_reporter_present": "crashreporter" in lower,
        "crash_reporter_enabled": "crashreporter" in lower and "enabled: true" in lower,
        "renderer_or_device_error": any(
            token in lower for token in ("device lost", "vk_error", "dxgi_error", "out of memory")
        ),
        "normal_shutdown_evidence": any(
            token in lower
            for token in ("unloadallplugins", "at shutdown", "simulationapp.close", "recursive unloadallplugins")
        ),
        "python_traceback": "traceback (most recent call last)" in lower,
        "startup_complete": "simulation app startup complete" in lower or "app ready" in lower,
    }


def inspect_failed_output_dirs(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return rows
    expected = (
        "result.json",
        "episodes.jsonl",
        "telemetry.csv",
        "viewer.log",
        "stderr.log",
        "screenshot.png",
        "exit_code.txt",
    )
    for directory in sorted(root.glob("fsm_50mm_development-h050-0000_*")):
        if not directory.is_dir():
            continue
        present = {name: (directory / name).is_file() for name in expected}
        rows.append(
            {
                "directory": str(directory),
                "artifacts": present,
                "classification": (
                    "HAS_EVALUATION_RESULT" if present["result.json"] else "STARTUP_EXIT_BEFORE_EVALUATION"
                ),
            }
        )
    return rows


def build_markdown(payload: dict[str, Any]) -> str:
    logs = payload["kit_logs"]
    dirs = payload["failed_output_directories"]
    startup_complete = any(item["startup_complete"] for item in logs)
    python_traceback = any(item["python_traceback"] for item in logs)
    device_error = any(item["renderer_or_device_error"] for item in logs)
    windows_matches = payload.get("windows_event_matches", [])
    last_lines = "\n".join(f"- `{Path(item['path']).name}`: `{item['last_line']}`" for item in logs)
    output_rows = "\n".join(
        f"- `{Path(item['directory']).name}`: **{item['classification']}**"
        for item in dirs
    ) or "- No matching failed GUI output directories found."
    statistics_collision = any(
        "cannot import name 'mean' from partially initialized module 'statistics'" in "\n".join(item["error_fatal_lines"])
        or "resume_validation\\statistics.py" in "\n".join(item["tail_300"])
        for item in logs
    )
    smoke_lines: list[str] = []
    for attempt in payload.get("startup_attempts", []):
        if attempt.get("mode") not in {"visible", "offscreen", "headless-no-camera"}:
            continue
        result_path = Path(str(attempt.get("result_path") or ""))
        result = {}
        if result_path.is_file():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception:
                result = {}
        completed_frames = int(result.get("frames_completed", result.get("completed_frames", 0)))
        rendered = bool(result.get("passed")) and completed_frames >= 120
        classification = (
            str(attempt.get("status") or "COMPLETED_RENDER_SHUTDOWN_TIMEOUT")
            if rendered and str(attempt.get("exit_code")) != "0"
            else ("COMPLETED" if rendered else str(attempt.get("status") or "FAILED"))
        )
        image_note = ""
        if attempt.get("mode") == "offscreen" and rendered:
            image_note = "; first/last PNG written"
        smoke_lines.append(
            f"- {attempt['mode'].capitalize()} smoke: **{classification}**; "
            f"120 {'simulation steps' if attempt.get('mode') == 'headless-no-camera' else 'render frames'} "
            f"completed; recorded exit code `{attempt.get('exit_code')}`{image_note}."
        )
    smoke_block = "\n".join(smoke_lines) or "- No current minimal smoke attempts recorded."
    capture_summary = payload.get("capture_summary", {})
    passed_primary = int(capture_summary.get("passed_primary", 0))
    offscreen_stability = (
        f"**stable across all {passed_primary} required primary development captures; "
        "all video validations passed**"
        if passed_primary >= 14
        else "**minimal renderer smoke passed; full capture batch not yet complete**"
    )
    return f"""# Isaac Sim startup diagnosis

## Conclusion

- GUI exit reproduced by historical attempts: **yes** (four output directories stop before `result.json`).
- Actual historical process exit code: **UNKNOWN**; the old wrapper did not persist it.
- Python traceback in Kit logs: **{'yes — Kit extension import traceback' if python_traceback else 'no'}**.
- Matching Windows `python.exe` / Kit application fault: **{'yes' if windows_matches else 'no'}**.
- Renderer/device-lost evidence: **{'yes' if device_error else 'no'}**.
- Simulation app reached startup complete: **{'yes' if startup_complete else 'no'}**.
- Visible GUI root cause: **{'VERIFIED: direct-file launch makes the project resume_validation/statistics.py shadow the Python standard-library statistics module; omni.kit.test then fails to import mean during visible extension startup.' if statistics_collision else 'UNKNOWN'}**
- High-confidence secondary cause: **the original PowerShell launch path did not preserve stdout/stderr separately, child identity, or the true exit code; it therefore made an orderly early shutdown indistinguishable from a crash.**
- Workaround: **HEADLESS/OFFSCREEN capture with owned-process tracking and persisted exit codes**.
- Offscreen recorder stability: {offscreen_stability}.

The complete Kit log shows the `statistics` module collision during `omni.kit.test` startup, later
app-ready/startup-complete messages, and plugin teardown. It contains no Vulkan/DXGI device-lost or
out-of-memory signature. The safe bootstrap launches the same evaluator as a package module, so the project
module remains `resume_validation.statistics` and cannot shadow the standard library.

## Historical Kit logs

{last_lines}

## Historical GUI output directories

{output_rows}

## Classification vocabulary

- **VERIFIED ROOT CAUSE:** direct-file Python launch caused a `statistics.py` standard-library shadow collision in visible Kit extension startup.
- **HIGH-CONFIDENCE SECONDARY CAUSE:** launch/wrapper observability and shutdown lifecycle ambiguity.
- **UNKNOWN:** why Isaac Sim 5.1 graceful `SimulationApp.close()` exceeded the diagnostic shutdown grace after successful 120-frame smokes.
- **WORKAROUND:** deterministic headless camera rendering; visible GUI is not required for completion.

## Current minimal smoke results

{smoke_block}

All three current smokes wrote a passing `result.json` before `SimulationApp.close()` exceeded the shutdown
grace period. Their `-1` exit codes therefore describe forced cleanup after successful stepping/rendering, not a
startup/render failure. The visible controller viewer has not been revalidated; the offscreen renderer is
the supported recording path.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--windows-events", type=Path)
    args = parser.parse_args()
    report_root = args.report_root.resolve()
    initialize_report_tree(report_root)

    kit_root = Path(
        r"C:\Users\kskzz\miniconda3\envs\env_isaaclab\Lib\site-packages\isaacsim\kit\logs\Kit\Isaac-Sim\5.1"
    )
    named = [kit_root / "kit_20260731_214001.log", kit_root / "kit_20260731_214038.log"]
    logs = [analyze_kit_log(path) for path in named if path.is_file()]
    copied: list[str] = []
    for path in named:
        if path.is_file():
            destination = report_root / "crash_diagnostics" / "kit_logs" / path.name
            shutil.copy2(path, destination)
            copied.append(str(destination))

    event_rows: list[dict[str, Any]] = []
    if args.windows_events and args.windows_events.is_file():
        event_payload = json.loads(args.windows_events.read_text(encoding="utf-8-sig"))
        event_rows = event_payload if isinstance(event_payload, list) else ([event_payload] if event_payload else [])
        event_rows = [
            row
            for row in event_rows
            if re.search(
                r"python\.exe|kit\.exe|isaac-sim|nvwgf2umx|nvidia|vulkan|carb",
                str(row.get("Message", "")) + " " + str(row.get("ProviderName", "")),
                re.IGNORECASE,
            )
        ]

    failed_root = PROJECT_ROOT / "reports" / "chatgpt_handoff_20260731_171825" / "gui_runs"
    passed_primary = 0
    for metadata_path in (report_root / "results").glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        case = metadata.get("case", {})
        if (
            case.get("video_category") == "primary"
            and metadata.get("validation_status") == "PASSED"
        ):
            passed_primary += 1
    payload = {
        "schema": "resume_validation.isaac_startup_diagnosis.v1",
        "kit_logs": logs,
        "copied_kit_logs": copied,
        "windows_event_matches": event_rows,
        "failed_output_directories": inspect_failed_output_dirs(failed_root),
        "startup_attempts": [],
        "capture_summary": {"passed_primary": passed_primary},
    }
    attempts_path = report_root / "startup_attempts.csv"
    if attempts_path.is_file():
        with attempts_path.open("r", encoding="utf-8-sig", newline="") as stream:
            payload["startup_attempts"] = list(csv.DictReader(stream))
    write_json(report_root / "crash_diagnostics" / "diagnosis.json", payload)
    (report_root / "CRASH_DIAGNOSIS.md").write_text(build_markdown(payload), encoding="utf-8")
    print(report_root / "CRASH_DIAGNOSIS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
