"""Shared, non-Isaac utilities for development-only controller capture.

This module intentionally never imports Isaac Lab and never discovers or reads the
locked-test manifest.  It only describes the already-completed development runs
listed in the visualization handoff.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(r"C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo")
ISAACLAB_ROOT = Path(r"C:\robotics_sim\IsaacLab")
CONDA_CANDIDATES = (
    Path(r"C:\Users\kskzz\miniconda3\Scripts\conda.exe"),
    Path(r"C:\Users\kskzz\miniconda3\condabin\conda.bat"),
)
ENV_PYTHON = Path(r"C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe")
DEVELOPMENT_MANIFEST = PROJECT_ROOT / "data" / "scenario_manifests" / "development_v2.json"
FSM_CONFIG = PROJECT_ROOT / "configs" / "fsm.yaml"
ROBOT_ASSET = PROJECT_ROOT / "assets" / "converted" / "wlr_robot_validation.usd"
EVALUATOR = PROJECT_ROOT / "tools" / "visualization" / "launch_existing_evaluator.py"

TERMINAL_STATES = {
    "COMPLETED",
    "FAILED",
    "SKIPPED_NO_MATCHING_SCENARIO",
    "REPRODUCTION_MISMATCH",
}

FSM_EVIDENCE = {
    50: PROJECT_ROOT / "runs" / "fsm" / "development_50mm_current_config_attempt043" / "episodes.jsonl",
    75: PROJECT_ROOT / "runs" / "fsm" / "development_75mm_formal_full_attempt042" / "episodes.jsonl",
    100: PROJECT_ROOT / "runs" / "fsm" / "development_100mm_current_config_attempt044" / "episodes.jsonl",
}
B_TRAINING = {
    height: PROJECT_ROOT
    / "runs"
    / "ppo_without_com"
    / "training"
    / f"method-B-v34_seed-29_stage-{height}mm_attempt002"
    for height in (50, 75, 100)
}
B_EVIDENCE = {
    height: PROJECT_ROOT
    / "runs"
    / "ppo_without_com"
    / "development_gates"
    / f"method-B-v34_seed-29_stage-{height}mm_attempt002"
    / "episodes.jsonl"
    for height in (50, 75, 100)
}
C_TRAINING = (
    PROJECT_ROOT
    / "runs"
    / "ppo_with_com"
    / "training"
    / "method-C-v34_seed-11_stage-50mm_attempt001"
)
C_EVIDENCE = (
    PROJECT_ROOT
    / "runs"
    / "ppo_with_com"
    / "development_gates"
    / "method-C-v34_seed-11_stage-50mm_attempt001"
    / "episodes.jsonl"
)


@dataclass(frozen=True)
class CaptureCase:
    case_id: str
    controller: str
    method: str
    seed: int | None
    height_mm: int
    checkpoint: str | None
    checkpoint_label: str
    evidence_episodes: str
    scenario_id: str
    requested_outcome: str
    evidence_outcome: str
    evidence_failure_reason: str
    output_filename: str
    video_category: str = "primary"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    # Antivirus, indexers, and read-only status polling can briefly hold the
    # destination on Windows.  Observability writes must not abort an otherwise
    # healthy Isaac episode because of a transient sharing violation.
    for attempt in range(100):
        try:
            os.replace(temporary, target)
            break
        except PermissionError:
            if attempt == 99:
                raise
            time.sleep(0.02)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def resolve_conda() -> Path:
    for path in CONDA_CANDIDATES:
        if path.is_file():
            return path
    for name in ("conda.exe", "conda"):
        discovered = shutil.which(name)
        if discovered:
            return Path(discovered).resolve()
    raise FileNotFoundError("Could not locate conda.exe or conda.bat")


def _assert_development_inputs() -> None:
    required = [DEVELOPMENT_MANIFEST, FSM_CONFIG, ROBOT_ASSET, EVALUATOR]
    required.extend(FSM_EVIDENCE.values())
    required.extend(B_EVIDENCE.values())
    required.extend(path / "checkpoints" / "final_agent.pt" for path in B_TRAINING.values())
    required.extend((C_EVIDENCE, C_TRAINING / "checkpoints" / "final_agent.pt"))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required development artifact(s):\n" + "\n".join(missing))
    if "locked_test" in str(DEVELOPMENT_MANIFEST).lower():
        raise RuntimeError("Development capture may not use a locked-test manifest")
    for run in (*B_TRAINING.values(), C_TRAINING):
        result = read_json(run / "training_result.json")
        if result.get("status") != "COMPLETED":
            raise RuntimeError(f"Formal checkpoint run is not COMPLETED: {run}")


def _select_episode(evidence: Path, success: bool) -> tuple[dict[str, Any], bool]:
    rows = load_jsonl(evidence)
    matches = [row for row in rows if bool(row.get("success")) is success]
    if matches:
        return matches[0], True
    # A requested class can genuinely be absent.  Use maximum registered
    # forward progress, preserving an explicit no-available label.
    failures = [row for row in rows if not bool(row.get("success"))]
    pool = failures or rows
    if not pool:
        raise ValueError(f"No episodes found in {evidence}")
    return max(pool, key=lambda row: float(row.get("forward_progress_m") or float("-inf"))), False


def build_primary_plan() -> list[CaptureCase]:
    _assert_development_inputs()
    cases: list[CaptureCase] = []

    def add_controller(
        controller: str,
        method: str,
        seed: int | None,
        heights: Iterable[int],
        evidence_for: dict[int, Path],
        checkpoint_for: dict[int, Path] | None,
    ) -> None:
        for height in heights:
            for requested, wanted_success in (("success", True), ("failure", False)):
                evidence = evidence_for[height]
                episode, exact = _select_episode(evidence, wanted_success)
                scenario = str(episode["scenario_id"])
                actual_evidence = "success" if bool(episode.get("success")) else "failure"
                suffix = requested if exact else f"no_{requested}_available_best_progress"
                prefix = (
                    f"fsm_h{height:03d}"
                    if controller == "fsm"
                    else f"method_{controller}_seed{seed}_final_h{height:03d}"
                )
                case_id = f"{prefix}_{suffix}_{scenario}"
                checkpoint = checkpoint_for[height] if checkpoint_for else None
                cases.append(
                    CaptureCase(
                        case_id=case_id,
                        controller=controller,
                        method=method,
                        seed=seed,
                        height_mm=height,
                        checkpoint=str(checkpoint) if checkpoint else None,
                        checkpoint_label="final_agent.pt" if checkpoint else "none",
                        evidence_episodes=str(evidence),
                        scenario_id=scenario,
                        requested_outcome=requested,
                        evidence_outcome=actual_evidence,
                        evidence_failure_reason=str(episode.get("failure_reason") or ""),
                        output_filename=case_id + ".mp4",
                    )
                )

    add_controller("fsm", "Frozen FSM", None, (50, 75, 100), FSM_EVIDENCE, None)
    add_controller(
        "B",
        "Method B",
        29,
        (50, 75, 100),
        B_EVIDENCE,
        {height: path / "checkpoints" / "final_agent.pt" for height, path in B_TRAINING.items()},
    )
    add_controller(
        "C",
        "Method C",
        11,
        (50,),
        {50: C_EVIDENCE},
        {50: C_TRAINING / "checkpoints" / "final_agent.pt"},
    )
    return cases


def case_map() -> dict[str, CaptureCase]:
    return {case.case_id: case for case in build_primary_plan()}


def initial_capture_state(cases: Iterable[CaptureCase]) -> dict[str, Any]:
    return {
        "schema": "resume_validation.visualization_capture_state.v1",
        "updated_at": time.time(),
        "cases": {
            case.case_id: {
                "status": "PENDING",
                "attempts": 0,
                "scenario_id": case.scenario_id,
                "requested_outcome": case.requested_outcome,
            }
            for case in cases
        },
    }


def load_or_create_state(report_root: Path, cases: Iterable[CaptureCase]) -> dict[str, Any]:
    path = report_root / "capture_state.json"
    planned = list(cases)
    if path.is_file():
        state = read_json(path)
        for case in planned:
            state.setdefault("cases", {}).setdefault(
                case.case_id,
                {
                    "status": "PENDING",
                    "attempts": 0,
                    "scenario_id": case.scenario_id,
                    "requested_outcome": case.requested_outcome,
                },
            )
        return state
    state = initial_capture_state(planned)
    write_json(path, state)
    return state


def initialize_report_tree(report_root: Path) -> None:
    for relative in (
        "crash_diagnostics/kit_logs",
        "crash_diagnostics/windows_events",
        "crash_diagnostics/stdout",
        "crash_diagnostics/stderr",
        "crash_diagnostics/process_snapshots",
        "videos/primary",
        "videos/comparisons",
        "videos/optional",
        "videos/failed_encodes",
        "thumbnails",
        "screenshots",
        "telemetry",
        "results",
        "logs",
        "frames_failed_only",
    ):
        (report_root / relative).mkdir(parents=True, exist_ok=True)


def format_command(command: Iterable[str]) -> str:
    return subprocess.list2cmdline([str(value) for value in command])


def owned_project_workloads(exclude_pids: set[int] | None = None) -> list[dict[str, Any]]:
    """Return exact project workloads using a read-only PowerShell CIM query."""
    exclude = exclude_pids or set()
    project_pattern = re.escape(str(PROJECT_ROOT))
    workload_pattern = (
        r"train_residual_ppo\.py|evaluate_controller\.py|record_existing_controller\.py|"
        r"run_until_success\.ps1|06_train_C\.ps1|full_pipeline_supervisor\.ps1|"
        r"pipeline_keep_awake\.ps1|isaac_startup_smoke\.py"
    )
    script = (
        "$rows=@(Get-CimInstance Win32_Process | Where-Object { "
        "$_.CommandLine -and $_.CommandLine -match '"
        + project_pattern.replace("'", "''")
        + "' -and $_.CommandLine -match '"
        + workload_pattern
        + "' } | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine); "
        "$rows | ConvertTo-Json -Depth 4 -Compress"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    text = completed.stdout.strip()
    if not text:
        return []
    parsed = json.loads(text)
    rows = parsed if isinstance(parsed, list) else [parsed]
    return [row for row in rows if int(row["ProcessId"]) not in exclude]


def validate_no_locked_reference(command: Iterable[str]) -> None:
    text = " ".join(str(value) for value in command).lower()
    forbidden = ("locked_test", "locked-test", "method_freeze", "09_run_locked_test")
    hit = next((token for token in forbidden if token in text), None)
    if hit:
        raise RuntimeError(f"Forbidden locked-test/freeze token in visualization command: {hit}")


def csv_write(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def plan_as_json(cases: Iterable[CaptureCase]) -> list[dict[str, Any]]:
    return [asdict(case) for case in cases]
