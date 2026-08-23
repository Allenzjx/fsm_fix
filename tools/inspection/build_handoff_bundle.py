from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the small read-only ChatGPT handoff bundle.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output-name", default="CHATGPT_HANDOFF_BUNDLE.zip")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project.resolve()
    report = args.report.resolve()
    if report.parent != project / "reports" or not report.name.startswith("chatgpt_handoff_"):
        raise ValueError("report must be reports/chatgpt_handoff_<timestamp>")
    if Path(args.output_name).name != args.output_name or not args.output_name.lower().endswith(".zip"):
        raise ValueError("output-name must be a plain .zip filename")
    output = report / args.output_name
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")

    report_files = [
        path
        for path in report.rglob("*")
        if path.is_file()
        and ".artifact_tool" not in path.parts
        and path.suffix.lower() != ".zip"
        and path.name not in {"AUDIT_TABLES.xlsx.inspect.ndjson", "_tables.json"}
        and not any(part == "gui_runs" for part in path.parts)
    ]
    evidence_relatives = [
        "configs/fsm.yaml",
        "configs/metrics.yaml",
        "configs/ppo_common.yaml",
        "configs/ppo_without_com.yaml",
        "configs/ppo_with_com.yaml",
        "configs/environment.yaml",
        "configs/obstacle_train.yaml",
        "configs/robot.yaml",
        "configs/config_freeze.json",
        "configs/experiment_protocol.yaml",
        "src/resume_validation/residual_rl_env.py",
        "src/resume_validation/residual_safety.py",
        "src/resume_validation/ppo_models.py",
        "src/resume_validation/train_residual_ppo.py",
        "src/resume_validation/evaluate_controller.py",
        "src/resume_validation/fsm_controller.py",
        "src/resume_validation/fsm_phase_schedule.py",
        "src/resume_validation/fsm_trajectory.py",
        "src/resume_validation/reference_tensor.py",
        "src/resume_validation/reward.py",
        "src/resume_validation/curriculum_gate.py",
        "src/resume_validation/checkpoint_selection.py",
        "scripts/train_curriculum.ps1",
        "scripts/run_until_success.ps1",
        "scripts/formal_training_recovery_supervisor.ps1",
        "scripts/full_pipeline_supervisor.ps1",
    ]
    evidence = [project / relative for relative in evidence_relatives if (project / relative).is_file()]
    inspection_scripts = sorted((project / "scripts" / "inspection").glob("*.ps1"))
    inspection_tools = sorted((project / "tools" / "inspection").glob("*"))
    targeted = []
    targeted_roots = [
        project / "runs/fsm/development_75mm_formal_full_attempt042",
        project / "runs/fsm/development_100mm_current_config_attempt044",
        project / "runs/ppo_without_com/development_gates/method-B-v34_seed-29_stage-75mm_attempt002",
        project / "runs/ppo_without_com/development_gates/method-B-v34_seed-29_stage-100mm_attempt002",
    ]
    for root in targeted_roots:
        for name in ("result.json", "episodes.jsonl", "gate_decision.json"):
            path = root / name
            if path.is_file():
                targeted.append(path)

    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(report_files):
            archive.write(path, Path("audit") / path.relative_to(report))
        for path in evidence:
            archive.write(path, Path("project_evidence") / path.relative_to(project))
        for path in inspection_scripts:
            archive.write(path, Path("project_evidence") / path.relative_to(project))
        for path in inspection_tools:
            if path.is_file() and path.suffix.lower() in {".py", ".ps1"}:
                archive.write(path, Path("project_evidence") / path.relative_to(project))
        for path in targeted:
            archive.write(path, Path("targeted_development_evidence") / path.relative_to(project / "runs"))
    print(f"{output}\nfiles={len(zipfile.ZipFile(output).infolist())}\nbytes={output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
