from __future__ import annotations

import argparse
from pathlib import Path


SCRIPT_REASONS = {
    "inspection_common.ps1": "shared read-only process safety, scenario, run, hash, and command helpers",
    "inspect_project_status.ps1": "show live pipeline/process/gate/Method-C/GUI-safety status without modifying it",
    "list_available_controllers.ps1": "list frozen FSM and explicit PPO best/final checkpoint choices with hashes and gate status",
    "show_fsm_gui.ps1": "safe single-scenario visible frozen-FSM viewer command with DryRun/video support",
    "show_ppo_gui.ps1": "safe deterministic PPO viewer with explicit checkpoint selection and no method fallback",
    "show_fsm_vs_ppo.ps1": "sequential same-scenario FSM/PPO comparison with unified diagnostic summary",
    "open_training_dashboard.ps1": "safe TensorBoard command/URL without starting training",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def report_reason(path: Path, report: Path) -> str:
    relative = path.relative_to(report)
    text = str(relative).replace("\\", "/")
    if path.name == "NEW_FILES_CREATED.md":
        return "complete disclosure of files created by this audit"
    if path.name.startswith("CHATGPT_HANDOFF_BUNDLE") and path.suffix.lower() == ".zip":
        return "small validated ChatGPT upload bundle excluding checkpoints, full telemetry, and locked scenarios"
    if path.name == "AUDIT_TABLES.xlsx":
        return "formatted workbook containing the 17 audit tables"
    if path.name.endswith(".inspect.ndjson"):
        return "machine-readable workbook range/layout/error inspection output"
    if "/previews/" in f"/{text}":
        return "rendered worksheet preview used for spreadsheet visual QA"
    if path.name == "build_tables.mjs":
        return "artifact-tool workbook import, formatting, rendering, inspection, and export helper"
    if path.name == "artifact_verification.json":
        return "spreadsheet parse/render/formula-error verification record"
    if path.suffix.lower() == ".csv":
        return "structured audit table requested for technical handoff"
    if path.suffix.lower() == ".png":
        return "offline plot generated from completed TensorBoard or episode evidence"
    if path.suffix.lower() == ".md":
        return "human-readable audit, analysis, safety, runbook, or handoff report"
    if path.suffix.lower() == ".json":
        return "structured audit metadata, process snapshot, or analysis summary"
    if path.name == "folder_tree.txt":
        return "summarized project tree with checkpoint and telemetry counts"
    if path.suffix.lower() == ".jsonl":
        return "machine-readable workbook inspection trace"
    return "supporting audit artifact"


def main() -> int:
    args = parse_args()
    project = args.project.resolve()
    report = args.report.resolve()
    output = report / "NEW_FILES_CREATED.md"
    report_files = sorted(
        {
            path
            for path in report.rglob("*")
            if path.is_file() and not (".artifact_tool" in path.parts and "node_modules" in path.parts)
        }
        | {output}
    )
    inspection_scripts = sorted((project / "scripts" / "inspection").rglob("*"))
    inspection_tools = sorted((project / "tools" / "inspection").rglob("*"))

    lines = [
        "# New files created by the read-only audit",
        "",
        "All files below were created only in the user-authorized report, `scripts\\inspection`, or `tools\\inspection` locations. Existing project files were not overwritten, moved, deleted, or edited.",
        "",
        "## Report artifacts",
        "",
        "| File | Why it was created |",
        "|---|---|",
    ]
    for path in report_files:
        relative = path.relative_to(project)
        lines.append(f"| `{relative}` | {report_reason(path, report)} |")
    lines.extend(["", "## Inspection scripts", "", "| File | Why it was created |", "|---|---|"])
    for path in inspection_scripts:
        if not path.is_file():
            continue
        relative = path.relative_to(project)
        lines.append(f"| `{relative}` | {SCRIPT_REASONS.get(path.name, 'inspection support file')} |")
    lines.extend(["", "## Audit build tools", "", "| File | Why it was created |", "|---|---|"])
    for path in inspection_tools:
        if not path.is_file():
            continue
        relative = path.relative_to(project)
        if path.name == "build_handoff_audit.py":
            reason = "reproducible offline extraction of tables, plots, and technical reports"
        elif path.name == "build_handoff_bundle.py":
            reason = "construct the small validated upload bundle without locked/checkpoint/full-telemetry payloads"
        elif path.name == "write_active_process_report.ps1":
            reason = "capture the final read-only process snapshot and safety report"
        elif path.name == "write_new_files_manifest.py":
            reason = "generate this complete new-file disclosure"
        elif path.suffix.lower() == ".pyc":
            reason = "Python bytecode cache created by syntax validation"
        else:
            reason = "audit build support file"
        lines.append(f"| `{relative}` | {reason} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
