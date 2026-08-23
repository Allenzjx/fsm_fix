from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np


VIS_ROOT = Path(__file__).resolve().parents[1] / "tools" / "visualization"
if str(VIS_ROOT) not in sys.path:
    sys.path.insert(0, str(VIS_ROOT))

from build_video_index import MANIFEST_FIELDS
from record_existing_controller import (
    descendants,
    draw_result_card,
    read_telemetry_summary,
    video_probe,
)
from visualization_common import (
    DEVELOPMENT_MANIFEST,
    EVALUATOR,
    FSM_CONFIG,
    ROBOT_ASSET,
    build_primary_plan,
    csv_write,
    initial_capture_state,
    load_or_create_state,
    sha256_file,
    validate_no_locked_reference,
)


def test_config_controller_scenario_and_checkpoint_discovery() -> None:
    assert DEVELOPMENT_MANIFEST.is_file()
    assert FSM_CONFIG.is_file()
    assert ROBOT_ASSET.is_file()
    assert EVALUATOR.name == "launch_existing_evaluator.py"
    assert not (EVALUATOR.parent / "statistics.py").exists()
    plan = build_primary_plan()
    assert len(plan) == 14
    assert {case.controller for case in plan} == {"fsm", "B", "C"}
    assert all(case.scenario_id.startswith("development-h") for case in plan)
    assert all("locked" not in case.evidence_episodes.lower() for case in plan)
    b_cases = [case for case in plan if case.controller == "B"]
    assert all(case.seed == 29 and case.checkpoint and Path(case.checkpoint).name == "final_agent.pt" for case in b_cases)
    c_cases = [case for case in plan if case.controller == "C"]
    assert len(c_cases) == 2
    assert all(case.height_mm == 50 and case.seed == 11 for case in c_cases)
    assert sha256_file(FSM_CONFIG) == "3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9"


def test_capture_plan_uses_reusable_comparison_scenarios() -> None:
    plan = build_primary_plan()
    selected = {(case.controller, case.height_mm, case.requested_outcome): case.scenario_id for case in plan}
    assert selected[("fsm", 50, "success")] == selected[("B", 50, "success")] == "development-h050-0000"
    assert selected[("fsm", 75, "failure")] == selected[("B", 75, "failure")] == "development-h075-0000"
    assert selected[("fsm", 100, "failure")] == selected[("B", 100, "failure")] == "development-h100-0001"


def test_camera_transform_and_result_overlay() -> None:
    root_x = 0.8
    obstacle_x = 0.5213122012213478
    desired_anchor = 0.55 * root_x + 0.45 * obstacle_x
    prior_anchor = 0.60
    anchor = 0.88 * prior_anchor + 0.12 * desired_anchor
    eye = (anchor - 0.65, -2.30, 1.00)
    target = (anchor, 0.0, 0.24)
    assert eye[0] < target[0]
    assert eye[1] < target[1]
    assert eye[2] > target[2]
    frame = np.full((720, 1280, 3), 80, dtype=np.uint8)
    card = draw_result_card(
        frame,
        outcome="SUCCESS",
        failure_reason="",
        final_phase=10,
        duration_s=42.0,
        min_margin=-0.02,
        pitch_rate_rms=0.04,
        scenario_id="development-h050-0000",
        checkpoint_sha="abc123" * 10,
    )
    assert card.shape == frame.shape
    assert float(np.mean(np.abs(card.astype(float) - frame.astype(float)))) > 5.0


def test_manifest_writer(tmp_path: Path) -> None:
    row = {field: "" for field in MANIFEST_FIELDS}
    row.update({"case_id": "case", "controller": "fsm", "height_mm": 50})
    target = tmp_path / "manifest.csv"
    csv_write(target, [row], MANIFEST_FIELDS)
    with target.open(encoding="utf-8-sig", newline="") as stream:
        read = list(csv.DictReader(stream))
    assert read[0]["case_id"] == "case"
    assert list(read[0]) == MANIFEST_FIELDS


def test_video_validation(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 20.0, (320, 180))
    assert writer.isOpened()
    for index in range(45):
        frame = np.zeros((180, 320, 3), dtype=np.uint8)
        frame[:, :, 1] = 40 + index
        cv2.circle(frame, (30 + index * 3, 90), 18, (255, 180, 50), thickness=-1)
        writer.write(frame)
    writer.release()
    probe = video_probe(path, 320, 180)
    assert probe["passed"], probe["failures"]
    assert probe["frame_count"] == 45


def test_result_parsing(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.csv"
    path.write_text(
        "time_s,base_x_m,fsm_phase\n"
        "0.0,0.0,0\n"
        "1.0,0.1,1\n"
        "11.0,0.101,1\n",
        encoding="utf-8",
    )
    summary = read_telemetry_summary(path)
    assert summary["duration_s"] == 11.0
    assert summary["final_phase"] == 1
    assert summary["phase_transitions_s"] == [1.0]
    assert summary["stall_start_s"] == 1.0


def test_pid_ownership_descendants() -> None:
    snapshot = [
        {"ProcessId": 11, "ParentProcessId": 10, "Name": "python.exe"},
        {"ProcessId": 12, "ParentProcessId": 11, "Name": "kit.exe"},
        {"ProcessId": 20, "ParentProcessId": 1, "Name": "python.exe"},
    ]
    assert {int(row["ProcessId"]) for row in descendants(10, snapshot)} == {11, 12}


def test_resume_state(tmp_path: Path) -> None:
    plan = build_primary_plan()
    state = initial_capture_state(plan)
    assert all(item["status"] == "PENDING" for item in state["cases"].values())
    write_path = tmp_path / "capture_state.json"
    write_path.write_text(json.dumps(state), encoding="utf-8")
    loaded = load_or_create_state(tmp_path, plan)
    first = plan[0].case_id
    loaded["cases"][first]["status"] = "COMPLETED"
    write_path.write_text(json.dumps(loaded), encoding="utf-8")
    assert load_or_create_state(tmp_path, plan)["cases"][first]["status"] == "COMPLETED"


def test_locked_and_training_command_guard() -> None:
    validate_no_locked_reference(["python", "evaluate_controller.py", "--manifest", str(DEVELOPMENT_MANIFEST)])
    try:
        validate_no_locked_reference(["python", "evaluate_controller.py", "--manifest", "data/locked_test/manifest.json"])
    except RuntimeError:
        pass
    else:
        raise AssertionError("locked-test path was not rejected")
