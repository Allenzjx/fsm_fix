from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PHASES = [
    "INIT",
    "SETTLE",
    "APPROACH",
    "FIRST_CONTACT_CONFIRM",
    "FRONT_OR_FIRST_WHEEL_LIFT",
    "FRONT_OR_FIRST_WHEEL_PLACE",
    "BODY_TRANSFER",
    "REAR_OR_REMAINING_WHEEL_LIFT",
    "REAR_OR_REMAINING_WHEEL_PLACE",
    "RECOVER",
    "DRIVE_CLEAR",
    "SUCCESS",
    "FAIL",
]

LOW_BOUNDS = [0.01, 0.04, 0.16, 0.20, 0.38, 0.50, 0.64, 0.78, 0.88, 0.94, 1.00]
HIGH_BOUNDS = [0.01, 0.04, 0.16, 0.20, 0.38, 0.574, 0.64, 0.78, 0.88, 0.94, 1.00]
REFERENCE_DURATION_S = 131.37400000030172
PHASE_TIMEOUT_SCALE = 4.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the offline ChatGPT handoff audit")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path, project: Path) -> str:
    try:
        return str(path.resolve().relative_to(project.resolve())).replace("/", "\\")
    except Exception:
        return str(path.resolve())


def iso_from_unix(value: Any) -> str:
    try:
        if value is None:
            return ""
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except Exception:
        return ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def dump_json(path: Path, value: Any) -> None:
    def compliant(item: Any) -> Any:
        if isinstance(item, float) and not math.isfinite(item):
            return None
        if isinstance(item, dict):
            return {str(key): compliant(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [compliant(child) for child in item]
        return item

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(compliant(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def json_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def mean(values: Iterable[float]) -> float:
    rows = [x for x in values if math.isfinite(x)]
    return sum(rows) / len(rows) if rows else float("nan")


def source_ref(project: Path, relative: str, line: int) -> str:
    return f"{relative}:{line}"


def build_folder_outputs(project: Path, report: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    # Use lexical absolute paths here: report/.artifact_tool/node_modules is a
    # junction to the bundled runtime, and resolve() would make it appear to be
    # outside the report tree and pollute the project inventory.
    excluded = {report.absolute()}

    def is_excluded(path: Path) -> bool:
        absolute = path.absolute()
        return any(absolute == item or item in absolute.parents for item in excluded)

    all_files = [p for p in project.rglob("*") if p.is_file() and not is_excluded(p)]
    top_rows: list[dict[str, Any]] = []
    for item in sorted(project.iterdir(), key=lambda p: p.name.lower()):
        if item.resolve() == report.resolve():
            continue
        if item.is_dir():
            files = [p for p in item.rglob("*") if p.is_file() and not is_excluded(p)]
            top_rows.append(
                {
                    "path": rel(item, project),
                    "type": "directory",
                    "file_count": len(files),
                    "bytes": sum(p.stat().st_size for p in files),
                    "last_modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                }
            )
        else:
            top_rows.append(
                {
                    "path": rel(item, project),
                    "type": "file",
                    "file_count": 1,
                    "bytes": item.stat().st_size,
                    "last_modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                }
            )

    checkpoints = [p for p in all_files if p.suffix.lower() == ".pt"]
    telemetry = [
        p
        for p in all_files
        if "telemetry" in p.name.lower()
        or "telemetry" in {part.lower() for part in p.parts}
        or p.name.lower() == "episodes.jsonl"
    ]
    top_rows.extend(
        [
            {
                "path": "[ALL CHECKPOINTS]",
                "type": "summary",
                "file_count": len(checkpoints),
                "bytes": sum(p.stat().st_size for p in checkpoints),
                "last_modified": "",
            },
            {
                "path": "[TELEMETRY + EPISODES]",
                "type": "summary",
                "file_count": len(telemetry),
                "bytes": sum(p.stat().st_size for p in telemetry),
                "last_modified": "",
            },
        ]
    )

    recent = []
    key_ext = {".py", ".ps1", ".yaml", ".json", ".jsonl", ".csv", ".md", ".pt", ".log", ".usd"}
    for path in sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True):
        if path.suffix.lower() not in key_ext:
            continue
        relative = rel(path, project)
        if "data\\locked_test\\" in relative.lower():
            # Listing the path is allowed; the audit never opens the locked scenarios.
            category = "locked_artifact_name_only"
        elif path.suffix.lower() == ".pt":
            category = "checkpoint"
        elif "telemetry" in path.name.lower() or path.name == "episodes.jsonl":
            category = "telemetry"
        elif relative.startswith("src\\"):
            category = "source"
        elif relative.startswith("configs\\"):
            category = "config"
        elif relative.startswith("scripts\\"):
            category = "script"
        else:
            category = "artifact"
        recent.append(
            {
                "file": relative,
                "category": category,
                "bytes": path.stat().st_size,
                "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }
        )
        if len(recent) >= 100:
            break

    lines = ["PROJECT TREE (summarized; checkpoints and telemetry are counted, not expanded)", ""]
    for row in top_rows:
        if row["type"] != "summary":
            lines.append(f"{row['path']}  [{row['type']}; files={row['file_count']}; bytes={row['bytes']}]")
            if row["type"] == "directory" and row["path"] in {"src", "configs", "scripts", "tests", "runs", "reports", "data", "assets"}:
                root = project / row["path"]
                if root.is_dir():
                    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                        if child.resolve() == report.resolve():
                            continue
                        if child.is_dir():
                            count = sum(1 for p in child.rglob("*") if p.is_file() and not is_excluded(p))
                            lines.append(f"  {rel(child, project)}  [directory; files={count}]")
                        else:
                            lines.append(f"  {rel(child, project)}  [file; bytes={child.stat().st_size}]")
    lines.extend(["", f"Checkpoint count: {len(checkpoints)}; total bytes: {sum(p.stat().st_size for p in checkpoints)}", f"Telemetry/episodes count: {len(telemetry)}; total bytes: {sum(p.stat().st_size for p in telemetry)}"])
    write_text(report / "folder_tree.txt", "\n".join(lines))

    readmes = [rel(p, project) for p in all_files if p.name.lower().startswith("readme")]
    return top_rows, recent, [{"file": item} for item in sorted(readmes)]


def build_entrypoints(project: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    key_files: list[dict[str, Any]] = []
    keywords = [
        "FSM",
        "residual",
        "com_margin",
        "support_margin",
        "pitch_rate",
        "success",
        "timeout",
        "collision",
        "checkpoint",
        "best_agent",
        "final_agent",
        "headless",
        "video",
        "viewer",
        "deterministic",
        "development_gate",
        "locked_test",
    ]
    candidates = list((project / "src").rglob("*.py")) + list((project / "scripts").rglob("*.ps1"))
    for path in sorted(candidates):
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = rel(path, project)
        hits: dict[str, list[int]] = {}
        for keyword in keywords:
            line_hits = [i for i, line in enumerate(text.splitlines(), 1) if keyword.lower() in line.lower()]
            if line_hits:
                hits[keyword] = line_hits[:12]
        if hits:
            key_files.append(
                {
                    "file": relative,
                    "keywords": "; ".join(sorted(hits)),
                    "representative_lines": json.dumps(hits, sort_keys=True),
                    "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }
            )
        is_py_entry = path.suffix.lower() == ".py" and ("if __name__" in text or "parser.parse_args()" in text)
        is_ps_entry = path.suffix.lower() == ".ps1"
        if not (is_py_entry or is_ps_entry):
            continue
        args = sorted(set(re.findall(r"add_argument\(\s*[\"'](--[a-zA-Z0-9_-]+)", text)))
        params = []
        if is_ps_entry:
            head = text[: text.find(")") + 1] if ")" in text else text[:3000]
            params = sorted(set(re.findall(r"\$(\w+)", head)))
        has_app = "AppLauncher" in text or "SimulationApp" in text
        if is_py_entry:
            if has_app:
                command = f"Set-Location C:\\robotics_sim\\IsaacLab; conda run --no-capture-output -n env_isaaclab .\\isaaclab.bat -p {path} --help"
            else:
                module = relative.removeprefix("src\\").replace("\\", ".").removesuffix(".py")
                command = f"$env:PYTHONPATH='{project / 'src'}'; python -m {module} --help"
        else:
            command = f"& '{path}'"
        rows.append(
            {
                "file": relative,
                "callable": "main/__main__" if is_py_entry else "PowerShell script",
                "CLI command": command,
                "headless support": "--headless" in text or "headless" in text.lower(),
                "GUI support": has_app and relative.endswith("evaluate_controller.py"),
                "checkpoint argument": "--checkpoint" if "--checkpoint" in args else ("Checkpoint" if "Checkpoint" in params else ""),
                "height argument": "--height_mm" if "--height_mm" in args else ("HeightMm" if "HeightMm" in params else ""),
                "method argument": "--method" if "--method" in args else ("Method" if "Method" in params else ""),
                "num_envs argument": "--num_envs" if "--num_envs" in args else ("NumEnvs" if "NumEnvs" in params else ""),
                "video argument": "--video_path" if "--video_path" in args else ("RecordVideo" if "RecordVideo" in params else ""),
                "current usability": "SOURCE_VERIFIED" if relative.endswith("evaluate_controller.py") else "SOURCE_DISCOVERED",
                "notes": f"args={','.join(args)}" if is_py_entry else f"params={','.join(params)}",
            }
        )
    return rows, key_files


def canonical_training_runs(project: Path) -> dict[tuple[int, int], tuple[Path, dict[str, Any]]]:
    root = project / "runs" / "ppo_without_com" / "training"
    found: dict[tuple[int, int], list[tuple[int, Path, dict[str, Any]]]] = defaultdict(list)
    pattern = re.compile(r"^method-B-v34_seed-(11|29|47)_stage-(50|75|100)mm_attempt(\d+)$")
    if not root.exists():
        return {}
    for directory in root.iterdir():
        if not directory.is_dir():
            continue
        match = pattern.match(directory.name)
        result_path = directory / "training_result.json"
        if not match or not result_path.is_file():
            continue
        result = read_json(result_path)
        if result.get("status") == "COMPLETED":
            found[(int(match.group(1)), int(match.group(2)))].append((int(match.group(3)), directory, result))
    return {key: (max(items, key=lambda item: item[0])[1], max(items, key=lambda item: item[0])[2]) for key, items in found.items()}


def gate_for_run(project: Path, run_dir: Path, method_folder: str = "ppo_without_com") -> tuple[dict[str, Any] | None, dict[str, Any] | None, Path | None]:
    gate_dir = project / "runs" / method_folder / "development_gates" / run_dir.name
    decision_path = gate_dir / "gate_decision.json"
    result_path = gate_dir / "result.json"
    return (
        read_json(decision_path) if decision_path.is_file() else None,
        read_json(result_path) if result_path.is_file() else None,
        gate_dir if gate_dir.exists() else None,
    )


def method_c_runtime_state(project: Path) -> dict[str, Any]:
    """Return the newest formal Method-C training state without starting or modifying it."""
    root = project / "runs" / "ppo_with_com" / "training"
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    pattern = re.compile(r"^method-C-v\d+_seed-(\d+)_stage-(\d+)mm_attempt(\d+)$")
    if root.exists():
        for result_path in root.rglob("training_result.json"):
            if not pattern.match(result_path.parent.name):
                continue
            try:
                result = read_json(result_path)
            except Exception:
                continue
            candidates.append((result_path.stat().st_mtime, result_path.parent, result))
    if not candidates:
        return {
            "exists": False,
            "status": "NOT_STARTED",
            "summary": "no formal Method C training result",
            "evidence": "runs\\ppo_with_com has no formal training_result.json",
            "run_dir": None,
            "checkpoint_count": 0,
            "gate_exists": False,
        }
    _, run_dir, result = max(candidates, key=lambda item: item[0])
    match = pattern.match(run_dir.name)
    checkpoint_count = len(list((run_dir / "checkpoints").glob("*.pt"))) if (run_dir / "checkpoints").exists() else 0
    decision, evaluation, gate_dir = gate_for_run(project, run_dir, "ppo_with_com")
    status = str(result.get("status", "UNKNOWN"))
    seed = int(match.group(1)) if match else result.get("seed")
    height = int(match.group(2)) if match else result.get("height_mm")
    gate_exists = bool(decision or evaluation or (gate_dir and gate_dir.exists()))
    return {
        "exists": True,
        "status": status,
        "seed": seed,
        "height_mm": height,
        "run_dir": run_dir,
        "run_name": run_dir.name,
        "checkpoint_count": checkpoint_count,
        "gate_exists": gate_exists,
        "decision": decision,
        "evaluation": evaluation,
        "evidence": rel(run_dir / "training_result.json", project),
        "summary": f"seed {seed} / {height} mm status={status}, checkpoints={checkpoint_count}, development_gate={gate_exists}",
    }


def build_experiment_matrix(project: Path) -> tuple[list[dict[str, Any]], dict[tuple[int, int], tuple[Path, dict[str, Any]]]]:
    rows: list[dict[str, Any]] = []
    for result_path in sorted((project / "runs").rglob("training_result.json")):
        if "chatgpt_handoff_" in str(result_path):
            continue
        try:
            result = read_json(result_path)
        except Exception:
            continue
        run_dir = result_path.parent
        args = result.get("arguments", {})
        method = str(result.get("method", ""))
        folder = "ppo_without_com" if method == "B" else "ppo_with_com"
        decision, evaluation, _ = gate_for_run(project, run_dir, folder)
        aggregate = (evaluation or {}).get("aggregate", {})
        budget = result.get("training_budget", result.get("budget", {}))
        checkpoints = list((run_dir / "checkpoints").glob("*.pt")) if (run_dir / "checkpoints").exists() else []
        resume = args.get("resume") or (result.get("resume_checkpoint") or {}).get("path")
        version_match = re.search(r"method-[BC]-(v\d+)", run_dir.name)
        failures = aggregate.get("failure_counts", {})
        rows.append(
            {
                "method": method,
                "version": version_match.group(1) if version_match else "legacy/unversioned",
                "seed": result.get("seed"),
                "height_mm": result.get("height_mm"),
                "attempt": (re.search(r"attempt(\d+)", run_dir.name).group(1) if re.search(r"attempt(\d+)", run_dir.name) else ""),
                "run_name": run_dir.name,
                "status": result.get("status"),
                "started_at": iso_from_unix(result.get("started_unix")),
                "completed_at": iso_from_unix(result.get("finished_unix")),
                "iterations": args.get("iterations"),
                "num_envs": args.get("num_envs", budget.get("parallel_environments")),
                "rollout": args.get("rollouts"),
                "local_timesteps": budget.get("local_timesteps_completed", budget.get("local_timesteps")),
                "simulated_transitions": budget.get("local_transitions_completed", budget.get("total_environment_transitions")),
                "randomization": args.get("randomization_level"),
                "resume_source": resume or "",
                "resume_source_sha256": (result.get("resume_checkpoint") or {}).get("sha256", ""),
                "optimizer_restored": bool(resume),
                "scheduler_restored": False if resume else "N/A",
                "observation_normalizer_restored": bool(resume),
                "value_normalizer_restored": bool(resume),
                "policy_restored": bool(resume),
                "critic_restored": bool(resume),
                "action_std_restored_with_policy": bool(resume),
                "checkpoint_count": len(checkpoints),
                "best_checkpoint": str(run_dir / "checkpoints" / "best_agent.pt") if (run_dir / "checkpoints" / "best_agent.pt").is_file() else "",
                "final_checkpoint": (result.get("final_checkpoint") or {}).get("path", ""),
                "evaluation_checkpoint": (decision or {}).get("checkpoint", ""),
                "development_episode_count": (decision or {}).get("actual", {}).get("development_episode_count", aggregate.get("episode_count")),
                "development_success_count": aggregate.get("success_count"),
                "development_success_rate": (decision or {}).get("actual", {}).get("development_success_rate", aggregate.get("success_rate")),
                "gate_threshold": (decision or {}).get("required", {}).get("minimum_development_success_rate"),
                "promote": (decision or {}).get("promote"),
                "failure reasons": json.dumps(failures, sort_keys=True),
                "margin": aggregate.get("mean_episode_min_margin_m"),
                "pitch-rate RMS": aggregate.get("mean_pitch_rate_rms_rad_s"),
                "evidence": rel(result_path, project),
            }
        )
    return rows, canonical_training_runs(project)


def checkpoint_top_keys(path: Path) -> list[str]:
    try:
        import torch

        data = torch.load(path, map_location="cpu", weights_only=False)
        return sorted(str(key) for key in data.keys()) if isinstance(data, dict) else [type(data).__name__]
    except Exception as exc:
        return [f"UNREADABLE:{type(exc).__name__}"]


def stable_checkpoint_sha256(path: Path) -> tuple[str, str]:
    """Hash a checkpoint only if its size/mtime stays stable during the read."""
    try:
        before = path.stat()
        digest = sha256(path)
        after = path.stat()
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            return "UNSTABLE_DURING_READ", "checkpoint changed while the externally owned process was writing"
        return digest, ""
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return f"UNREADABLE:{type(exc).__name__}", str(exc)


def compact_training_snapshot(result: dict[str, Any]) -> str:
    provenance = result.get("provenance", {})
    configs = provenance.get("configs", {})
    return json.dumps(
        {
            "config_sha256": {name: values.get("sha256") for name, values in configs.items()},
            "residual_projection": provenance.get("effective_residual_projection_type"),
            "residual_phase_window": provenance.get("effective_residual_execution_phase_window"),
            "residual_action_mask": provenance.get("effective_residual_action_mask"),
            "reward_weights": provenance.get("effective_reward_weights"),
        },
        sort_keys=True,
    )


def build_checkpoint_inventory(project: Path, canonical: dict[tuple[int, int], tuple[Path, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    gate_index: dict[str, dict[str, Any]] = {}
    for decision_path in (project / "runs").rglob("gate_decision.json"):
        if "chatgpt_handoff_" in str(decision_path):
            continue
        try:
            decision = read_json(decision_path)
            checkpoint = decision.get("checkpoint")
            if checkpoint:
                gate_index[str(Path(checkpoint).resolve()).lower()] = decision
        except Exception:
            continue
    special = [
        ("frozen_fsm_config", project / "configs" / "fsm.yaml"),
        ("selected_robot_asset", project / "assets" / "converted" / "wlr_robot_validation.usd"),
    ]
    for role, path in special:
        rows.append(
            {
                "method": "FSM" if role.startswith("frozen") else "ASSET",
                "seed": "",
                "height_mm": "",
                "run": "",
                "artifact_role": role,
                "path": str(path),
                "bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256(path) if path.is_file() else "MISSING",
                "checkpoint_modules": "N/A",
                "training_status": "FROZEN" if role.startswith("frozen") else "SELECTED",
                "config_snapshot": "N/A",
                "used_by_development_gate": False,
                "promoted": False,
                "visualization_recommendation": role == "frozen_fsm_config",
                "notes": "canonical non-checkpoint artifact",
            }
        )
    checkpoint_paths = sorted((project / "runs").rglob("*.pt"))
    pattern = re.compile(r"method-([BC])-v(\d+)_seed-(\d+)_stage-(\d+)mm_(?:smoke_)?attempt(\d+)", re.IGNORECASE)
    result_cache: dict[Path, dict[str, Any]] = {}
    modules_cache: dict[tuple[int, str], str] = {}
    for path in checkpoint_paths:
        if "chatgpt_handoff_" in str(path):
            continue
        run_dir = path.parent.parent if path.parent.name.lower() == "checkpoints" else path.parent
        match = pattern.search(run_dir.name)
        method = match.group(1).upper() if match else ("B" if "ppo_without_com" in str(path) else ("C" if "ppo_with_com" in str(path) else "UNKNOWN"))
        seed = int(match.group(3)) if match else ""
        height = int(match.group(4)) if match else ""
        attempt = int(match.group(5)) if match else ""
        lower_name = path.name.lower()
        if lower_name == "best_agent.pt":
            role = "best"
        elif lower_name == "final_agent.pt":
            role = "final"
        else:
            role = "intermediate"
        result_path = run_dir / "training_result.json"
        if run_dir not in result_cache:
            try:
                result_cache[run_dir] = read_json(result_path) if result_path.is_file() else {}
            except Exception:
                result_cache[run_dir] = {}
        result = result_cache[run_dir]
        snapshot = compact_training_snapshot(result) if result else ""
        digest, hash_note = stable_checkpoint_sha256(path)
        stat = path.stat() if path.exists() else None
        module_key = (stat.st_size if stat else -1, digest)
        if module_key not in modules_cache:
            modules_cache[module_key] = json.dumps(checkpoint_top_keys(path))
        decision = gate_index.get(str(path.resolve()).lower())
        notes = []
        if role == "best":
            notes.append("best=highest tracked training total reward, not development success")
        elif role == "final":
            notes.append("final=stage-end checkpoint when training completed")
        if hash_note:
            notes.append(hash_note)
        rows.append(
            {
                "method": method,
                "seed": seed,
                "height_mm": height,
                "attempt": attempt,
                "run": run_dir.name,
                "artifact_role": role,
                "path": str(path),
                "bytes": stat.st_size if stat else 0,
                "sha256": digest,
                "checkpoint_modules": modules_cache[module_key],
                "training_status": result.get("status", "UNKNOWN"),
                "config_snapshot": snapshot,
                "used_by_development_gate": bool(decision),
                "promoted": bool((decision or {}).get("promote", False)),
                "visualization_recommendation": method == "B" and role == "final" and height in {75, 100} and seed == 29 and result.get("status") == "COMPLETED",
                "notes": "; ".join(notes),
            }
        )
    return rows


def fsm_evidence_paths(project: Path) -> dict[int, Path]:
    return {
        50: project / "runs" / "fsm" / "development_50mm_current_config_attempt043",
        75: project / "runs" / "fsm" / "development_75mm_formal_full_attempt042",
        100: project / "runs" / "fsm" / "development_100mm_current_config_attempt044",
    }


def stream_last_phase(path: Path, episode_count: int) -> dict[int, int]:
    result: dict[int, int] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            env_id = safe_int(row.get("env_id"), -1)
            if 0 <= env_id < episode_count:
                result[env_id] = safe_int(safe_float(row.get("fsm_phase"), 0), 0)
    return result


def build_fsm_tables(project: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    evidence = fsm_evidence_paths(project)
    for height, directory in evidence.items():
        result = read_json(directory / "result.json")
        episodes = read_jsonl(directory / "episodes.jsonl")
        last_phase = stream_last_phase(directory / "telemetry.csv", len(episodes))
        successful_times = [safe_float(row.get("traversal_time_s")) for row in episodes if row.get("success")]
        aggregate = result["aggregate"]
        result_rows.append(
            {
                "height_mm": height,
                "episodes": aggregate.get("episode_count"),
                "successes": aggregate.get("success_count"),
                "success_rate": aggregate.get("success_rate"),
                "mean_min_margin_m": aggregate.get("mean_episode_min_margin_m"),
                "mean_pitch_rate_rms_rad_s": aggregate.get("mean_pitch_rate_rms_rad_s"),
                "mean_success_completion_time_s": mean(successful_times),
                "median_success_completion_time_s": statistics.median(successful_times) if successful_times else "",
                "result_evidence": rel(directory / "result.json", project),
                "episode_evidence": rel(directory / "episodes.jsonl", project),
                "telemetry_evidence": rel(directory / "telemetry.csv", project),
            }
        )
        counter: Counter[tuple[str, int]] = Counter()
        times: defaultdict[tuple[str, int], list[float]] = defaultdict(list)
        for index, episode in enumerate(episodes):
            if episode.get("success"):
                continue
            reason = str(episode.get("failure_reason") or "UNKNOWN")
            phase = last_phase.get(index, -1)
            counter[(reason, phase)] += 1
            times[(reason, phase)].append(safe_float(episode.get("traversal_time_s")))
        for (reason, phase), count in sorted(counter.items()):
            failure_rows.append(
                {
                    "height_mm": height,
                    "failure_reason": reason,
                    "count": count,
                    "final_phase": PHASES[phase] if 0 <= phase < len(PHASES) else phase,
                    "mean_episode_time_s": mean(times[(reason, phase)]),
                    "evidence": rel(directory / "episodes.jsonl", project),
                }
            )

    exits = {
        0: "planned reference window elapsed",
        1: "planned reference window elapsed",
        2: "either front wheel has front-face or top contact",
        3: "front contact remains true for 3 control steps",
        4: "at least one front wheel has top contact for 3 steps",
        5: "both front wheels have top contact for 3 steps",
        6: "both front wheels retain top contact for 3 steps",
        7: "at least one rear wheel has top contact for 3 steps",
        8: "both rear wheels have top contact for 3 steps",
        9: "all four wheels are on top for 3 steps",
        10: "all four wheels on top and tilt/angular speed bounded for 3 steps",
        11: "terminal",
        12: "terminal",
    }
    entries = {0: "reset"}
    for index in range(1, 11):
        entries[index] = f"phase {index - 1} exit latched AND normalized reference crosses boundary"
    entries[11] = "success dwell predicate reaches 1.5 s (separate environment termination)"
    entries[12] = "fall, body/link collision, numerical error, joint limit, phase timeout, or global timeout"
    phase_rows: list[dict[str, Any]] = []
    for height in (50, 75, 100):
        alpha = (height - 50) / 50.0
        bounds = [low + alpha * (high - low) for low, high in zip(LOW_BOUNDS, HIGH_BOUNDS)]
        lower = 0.0
        for index, name in enumerate(PHASES):
            upper = bounds[index] if index < 11 else 1.0
            width = max(0.0, upper - lower) if index < 11 else 0.0
            timeout = width * REFERENCE_DURATION_S * PHASE_TIMEOUT_SCALE if 2 <= index <= 10 else "N/A"
            phase_rows.append(
                {
                    "height_mm": height,
                    "phase_id": index,
                    "phase_name": name,
                    "normalized_start": lower if index < 11 else "",
                    "normalized_end": upper if index < 11 else "",
                    "entry_condition": entries[index],
                    "exit_condition": exits[index],
                    "phase_timeout_s": timeout,
                    "debounce_steps": 3 if 2 <= index <= 10 else 0,
                    "fallback": "terminal failure predicates; no backward phase transition",
                    "source": "src\\resume_validation\\residual_rl_env.py:957-1047; 1880-1911",
                }
            )
            if index < 11:
                lower = upper
    return phase_rows, result_rows, failure_rows


def build_observation_action_tables() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    obs = [
        ("actor", "0", "obstacle_height/0.10", "normalized", "/0.10", "noise; network clip [-20,20]", False),
        ("actor", "1", "obstacle_front_x - base_x", "m", "none", "noise; network clip [-20,20]", False),
        ("actor", "2", "-base_y/0.5", "normalized", "/0.5", "noise; network clip [-20,20]", False),
        ("actor", "3", "(obstacle_top_z-base_z)/0.20", "normalized", "/0.20", "noise; network clip [-20,20]", False),
        ("actor", "4", "obstacle_detection_valid", "bool", "none", "always 1 in current sim", False),
        ("actor", "5", "obstacle_detection_age", "s", "none", "always 0 in current sim", False),
        ("actor", "6:18", "FSM phase one-hot (13)", "bool", "none", "network clip [-20,20]", False),
        ("actor", "19", "FSM phase progress", "0..1", "none", "[0,1]", False),
        ("actor", "20", "elapsed/reference duration", "0..1", "none", "[0,1]", False),
        ("actor", "21:28", "FSM reference wheel centers x/z (4x2)", "m", "/0.35", "network clip [-20,20]", False),
        ("actor", "29:32", "FSM reference wheel speeds", "rad/s", "/wheel_max", "network clip [-20,20]", False),
        ("actor", "33:35", "projected gravity in body frame", "unit vector", "none", "network clip [-20,20]", False),
        ("actor", "36:37", "roll, pitch", "rad", "none", "network clip [-20,20]", False),
        ("actor", "38:40", "body angular velocity", "rad/s", "/5", "network clip [-20,20]", False),
        ("actor", "41:43", "body linear velocity", "m/s", "/2", "network clip [-20,20]", False),
        ("actor", "44:46", "finite-difference body acceleration", "m/s^2", "/20", "pre-clipped [-5,5]", False),
        ("actor", "47", "base height", "m", "/0.5", "network clip [-20,20]", False),
        ("actor", "48:55", "servo joint position within safe range", "normalized", "center/half-range", "network clip [-20,20]", False),
        ("actor", "56:63", "servo joint velocity", "rad/s", "/5", "network clip [-20,20]", False),
        ("actor", "64:67", "wheel joint velocity", "rad/s", "/wheel_max", "network clip [-20,20]", False),
        ("actor", "68:79", "previous raw PPO action", "normalized", "none", "delayed action already clipped [-1,1]", False),
        ("actor", "80:87", "servo target tracking error", "normalized", "/joint half-range", "network clip [-20,20]", False),
        ("actor", "88:95", "distance to nearest servo safe limit", "normalized", "/joint half-range", "network clip [-20,20]", False),
        ("critic", "96", "true obstacle height", "m", "none", "network clip [-20,20]", True),
        ("critic", "97:112", "wheel contact class one-hot (4x4)", "bool", "none", "network clip [-20,20]", True),
        ("critic", "113:116", "wheel contact force magnitude", "N", "/50", "network clip [-20,20]", True),
        ("critic", "117:128", "wheel positions relative to base (4x3)", "m", "none", "network clip [-20,20]", True),
        ("critic", "129:131", "CoM x/y relative to base plus zero z placeholder", "m", "none", "network clip [-20,20]", True),
        ("critic", "132", "longitudinal support margin", "m", "none", "invalid encoded 0", True),
        ("critic", "133", "support margin valid", "bool", "none", "network clip [-20,20]", True),
        ("critic", "134:139", "world root velocity", "m/s,rad/s", "/5", "network clip [-20,20]", True),
        ("critic", "140", "friction", "coefficient", "none", "network clip [-20,20]", True),
        ("critic", "141", "action delay", "steps", "/2", "network clip [-20,20]", True),
        ("critic", "142", "constant validity flag", "bool", "none", "always 1", True),
        ("critic", "143:145", "obstacle front x, zero y, height", "m", "none", "network clip [-20,20]", True),
    ]
    obs_rows = [
        {
            "consumer": a,
            "slice": b,
            "name": c,
            "unit": d,
            "normalization": e,
            "clip/encoding": f,
            "privileged": g,
            "source": "src\\resume_validation\\residual_rl_env.py:1721-1832",
        }
        for a, b, c, d, e, f, g in obs
    ]
    names = ["fl_dx", "fl_dz", "fr_dx", "fr_dz", "rl_dx", "rl_dz", "rr_dx", "rr_dz", "fl_wheel_speed", "fr_wheel_speed", "rl_wheel_speed", "rr_wheel_speed"]
    action_rows = []
    action_mask = [0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1]
    for index, name in enumerate(names):
        is_wheel = index >= 8
        action_rows.append(
            {
                "index": index,
                "configured_name": name,
                "semantic": "wheel speed residual" if is_wheel else ("wheel-center x residual" if index % 2 == 0 else "wheel-center z residual"),
                "raw_range": "Gaussian mean tanh; sampled/clipped [-1,1]",
                "effective_mask": action_mask[index],
                "scale": "0.10 rad/s" if is_wheel else ("0.0075 m" if index % 2 == 0 else "0.010 m"),
                "execution": "phase 9 only in corrective mode" if is_wheel else ("masked to exact zero" if index % 2 == 0 else "phase/state gated and projected to shared z correction"),
                "post_limits": "6 rad/s^2 acceleration then ±2.094 rad/s" if is_wheel else "IK nearest branch, servo rate limit, safe joint clamp; all-leg fallback to FSM on any invalid IK",
                "source": "configs\\ppo_common.yaml:13-56; src\\resume_validation\\residual_rl_env.py:1354-1689",
            }
        )
    return obs_rows, action_rows


def scalar_events(event_file: Path) -> dict[str, list[tuple[int, float]]]:
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

        accumulator = EventAccumulator(str(event_file), size_guidance={"scalars": 0})
        accumulator.Reload()
        return {
            tag: [(int(item.step), float(item.value)) for item in accumulator.Scalars(tag)]
            for tag in accumulator.Tags().get("scalars", [])
        }
    except Exception:
        return {}


def build_training_plots(project: Path, report: Path, canonical: dict[tuple[int, int], tuple[Path, dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    plot_dir = report / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    runs: dict[str, dict[str, list[tuple[int, float]]]] = {}
    summaries: list[dict[str, Any]] = []
    for (seed, height), (run_dir, _) in sorted(canonical.items()):
        events = sorted(run_dir.glob("events.out.tfevents.*"), key=lambda p: p.stat().st_mtime)
        if not events:
            continue
        data = scalar_events(events[-1])
        label = f"s{seed}-{height}mm"
        runs[label] = data
        for tag, points in data.items():
            if not points:
                continue
            values = [v for _, v in points if math.isfinite(v)]
            if not values:
                continue
            tail_n = max(1, len(values) // 10)
            summaries.append(
                {
                    "run": label,
                    "event_file": rel(events[-1], project),
                    "tag": tag,
                    "points": len(values),
                    "first": values[0],
                    "last": values[-1],
                    "minimum": min(values),
                    "maximum": max(values),
                    "tail_mean": mean(values[-tail_n:]),
                }
            )

    def line_plot(filename: str, tags: list[str], title: str, ylabel: str) -> None:
        fig, axes = plt.subplots(len(tags), 1, figsize=(12, 4 * len(tags)), squeeze=False)
        for axis, tag in zip(axes[:, 0], tags):
            any_data = False
            for label, data in runs.items():
                points = data.get(tag, [])
                if points:
                    any_data = True
                    axis.plot([p[0] for p in points], [p[1] for p in points], linewidth=1.1, label=label)
            axis.set_title(tag)
            axis.set_xlabel("local control timestep")
            axis.set_ylabel(ylabel)
            axis.grid(True, alpha=0.25)
            if any_data:
                axis.legend(ncol=3, fontsize=8)
            else:
                axis.text(0.5, 0.5, "Not logged", transform=axis.transAxes, ha="center", va="center")
        fig.suptitle(title)
        fig.tight_layout()
        fig.savefig(plot_dir / filename, dpi=160)
        plt.close(fig)

    line_plot("training_return_by_stage.png", ["Reward / Total reward (mean)"], "Method B v34 training return", "return")
    line_plot("episode_length_by_stage.png", ["Episode / Total timesteps (mean)"], "Method B v34 episode length", "control steps")
    line_plot("policy_value_loss.png", ["Loss / Policy loss", "Loss / Value loss"], "PPO losses", "loss")

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    for label, data in runs.items():
        points = data.get("Policy / Standard deviation", [])
        if points:
            axes[0].plot([p[0] for p in points], [p[1] for p in points], linewidth=1.1, label=label)
        lr = data.get("Learning / Learning rate", [])
        if lr:
            axes[1].plot([p[0] for p in lr], [p[1] for p in lr], linewidth=1.1, label=label)
    axes[0].set_title("Policy standard deviation (entropy and KL were not logged)")
    axes[1].set_title("KL-adaptive learning rate (actual KL was not logged)")
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.legend(ncol=3, fontsize=8)
        axis.set_xlabel("local control timestep")
    fig.tight_layout()
    fig.savefig(plot_dir / "entropy_kl.png", dpi=160)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(12, 5))
    axis.axis("off")
    axis.text(
        0.5,
        0.58,
        "INSTRUMENTATION GAP\nTraining TensorBoard contains no reward-component scalars.",
        ha="center",
        va="center",
        fontsize=16,
    )
    axis.text(0.5, 0.30, "Available: instantaneous/total reward, episode length, policy/value loss, policy std, learning rate.", ha="center", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(plot_dir / "reward_components.png", dpi=160)
    plt.close(fig)

    tags = sorted({tag for data in runs.values() for tag in data})
    return summaries, {"runs": len(runs), "available_tags": tags, "missing_tags": ["success rate", "reward components", "entropy", "KL", "explained variance", "clip fraction", "gradient norm", "residual norm", "saturation fraction"]}


def vector_norm(row: dict[str, str], prefix: str, count: int) -> float:
    values = [safe_float(row.get(f"{prefix}{index:02d}"), 0.0) for index in range(count)]
    return math.sqrt(sum(v * v for v in values if math.isfinite(v)))


def stream_telemetry(path: Path, episodes: list[dict[str, Any]], selected_ids: set[str]) -> tuple[dict[int, dict[str, Any]], dict[str, dict[str, list[float]]]]:
    per_env: dict[int, dict[str, Any]] = {}
    selected: dict[str, dict[str, list[float]]] = {
        scenario_id: defaultdict(list) for scenario_id in selected_ids
    }
    scenario_by_env = {index: str(row.get("scenario_id")) for index, row in enumerate(episodes)}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            env_id = safe_int(row.get("env_id"), -1)
            if env_id < 0 or env_id >= len(episodes):
                continue
            stats = per_env.setdefault(
                env_id,
                {
                    "rows": 0,
                    "first_base_x": None,
                    "last_base_x": None,
                    "last_phase": -1,
                    "max_phase": -1,
                    "executed_norm_sum": 0.0,
                    "executed_norm_max": 0.0,
                    "executed_nonzero": 0,
                    "policy_norm_sum": 0.0,
                    "policy_clip_rows": 0,
                    "phase_counts": Counter(),
                },
            )
            t = safe_float(row.get("time_s"), 0.0)
            base_x = safe_float(row.get("base_x_m"))
            phase = safe_int(safe_float(row.get("fsm_phase"), -1), -1)
            policy_norm = vector_norm(row, "policy_action_", 12)
            executed_norm = vector_norm(row, "executed_action_", 12)
            stats["rows"] += 1
            if stats["first_base_x"] is None:
                stats["first_base_x"] = base_x
            stats["last_base_x"] = base_x
            stats["last_phase"] = phase
            stats["max_phase"] = max(stats["max_phase"], phase)
            stats["executed_norm_sum"] += executed_norm
            stats["executed_norm_max"] = max(stats["executed_norm_max"], executed_norm)
            stats["executed_nonzero"] += int(executed_norm > 1.0e-8)
            stats["policy_norm_sum"] += policy_norm
            stats["policy_clip_rows"] += int(any(abs(safe_float(row.get(f"policy_action_{i:02d}"), 0.0)) >= 0.999 for i in range(12)))
            stats["phase_counts"][phase] += 1
            scenario = scenario_by_env[env_id]
            if scenario not in selected:
                continue
            record = selected[scenario]
            record["time_s"].append(t)
            record["base_x_m"].append(base_x)
            record["phase"].append(float(phase))
            record["margin_m"].append(safe_float(row.get("margin_m")))
            record["pitch_rate_rad_s"].append(safe_float(row.get("pitch_rate_rad_s")))
            record["pitch_rad"].append(safe_float(row.get("pitch_rad")))
            record["roll_rad"].append(safe_float(row.get("roll_rad")))
            record["policy_norm"].append(policy_norm)
            record["executed_norm"].append(executed_norm)
            wheel = [safe_float(row.get(f"final_wheel_target_rad_s_{i:02d}"), 0.0) for i in range(4)]
            record["wheel_speed_mean_abs"].append(mean([abs(v) for v in wheel]))
            contacts = [safe_float(row.get(f"{name}_contact_state"), 0.0) for name in ("fl", "fr", "rl", "rr")]
            record["contact_state_sum"].append(sum(contacts))
            record["all_wheels_on_top"].append(safe_float(row.get("all_wheels_on_top"), 0.0))
            record["supported_slip_speed_m_s"].append(safe_float(row.get("supported_slip_speed_m_s"), 0.0))
            record["reward"].append(safe_float(row.get("reward"), 0.0))
    for stats in per_env.values():
        n = max(1, stats["rows"])
        stats["mean_executed_norm"] = stats["executed_norm_sum"] / n
        stats["executed_nonzero_fraction"] = stats["executed_nonzero"] / n
        stats["mean_policy_norm"] = stats["policy_norm_sum"] / n
        stats["policy_clip_fraction"] = stats["policy_clip_rows"] / n
        stats["phase_counts"] = dict(stats["phase_counts"])
    return per_env, selected


def plot_episode_timeline(report: Path, controller: str, scenario: str, episode: dict[str, Any], series: dict[str, list[float]]) -> Path:
    path = report / "plots" / "episodes" / f"{controller}_{scenario}_timeline.png"
    times = series.get("time_s", [])
    if not times:
        return path
    fig, axes = plt.subplots(8, 1, figsize=(13, 18), sharex=True)
    axes[0].step(times, series["phase"], where="post")
    axes[0].set_ylabel("FSM phase")
    axes[0].set_yticks(range(13))
    axes[0].set_yticklabels([str(i) for i in range(13)])
    axes[1].plot(times, series["base_x_m"])
    axes[1].set_ylabel("base x (m)")
    axes[2].plot(times, series["margin_m"])
    axes[2].axhline(0, color="black", linewidth=0.8)
    axes[2].set_ylabel("CoM margin (m)")
    axes[3].plot(times, series["pitch_rate_rad_s"])
    axes[3].set_ylabel("pitch rate (rad/s)")
    axes[4].plot(times, series["policy_norm"], label="policy/raw")
    axes[4].plot(times, series["executed_norm"], label="executed", alpha=0.85)
    axes[4].set_ylabel("residual L2")
    axes[4].legend()
    axes[5].plot(times, series["wheel_speed_mean_abs"])
    axes[5].set_ylabel("mean |wheel cmd|\n(rad/s)")
    axes[6].step(times, series["contact_state_sum"], where="post", label="contact state sum")
    axes[6].step(times, [4.0 * value for value in series["all_wheels_on_top"]], where="post", label="all top ×4")
    axes[6].set_ylabel("contact")
    axes[6].legend()
    collision = str(episode.get("failure_reason")) == "BODY_OR_LINK_COLLISION"
    term = [0.0] * len(times)
    term[-1] = 1.0
    if collision:
        axes[7].bar([times[-1]], [1.0], width=max(0.05, (times[-1] - times[0]) / 200.0), color="red", label="collision")
    axes[7].step(times, term, where="post", color="black", label="termination")
    axes[7].set_ylim(-0.05, 1.15)
    axes[7].set_ylabel("terminal")
    axes[7].set_xlabel("simulation time (s)")
    axes[7].legend()
    for axis in axes:
        axis.grid(True, alpha=0.25)
    fig.suptitle(f"{controller} — {scenario} — {'SUCCESS' if episode.get('success') else episode.get('failure_reason')}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def select_representatives(episodes75: list[dict[str, Any]], episodes100: list[dict[str, Any]]) -> dict[int, list[str]]:
    def first(rows: list[dict[str, Any]], predicate) -> str:
        return str(next(row for row in rows if predicate(row))["scenario_id"])

    return {
        75: [
            first(episodes75, lambda row: bool(row.get("success"))),
            first(episodes75, lambda row: row.get("failure_reason") == "TIMEOUT"),
        ],
        100: [
            first(episodes100, lambda row: bool(row.get("success"))),
            first(episodes100, lambda row: row.get("failure_reason") == "BODY_OR_LINK_COLLISION"),
            first(episodes100, lambda row: row.get("failure_reason") == "TIMEOUT"),
        ],
    }


def build_episode_outputs(project: Path, report: Path, canonical: dict[tuple[int, int], tuple[Path, dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    seed = 29
    b_dirs = {height: gate_for_run(project, canonical[(seed, height)][0])[2] for height in (75, 100)}
    b_episodes = {height: read_jsonl(b_dirs[height] / "episodes.jsonl") for height in (75, 100) if b_dirs[height]}
    reps = select_representatives(b_episodes[75], b_episodes[100])
    diagnostic_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    residual_summary: dict[str, Any] = {}
    sources: list[tuple[str, int, Path, list[dict[str, Any]], str, str]] = []
    for height in (75, 100):
        gate_dir = b_dirs[height]
        result = read_json(gate_dir / "result.json")
        sources.append(("B-final", height, gate_dir, b_episodes[height], result.get("provenance", {}).get("checkpoint", ""), result.get("provenance", {}).get("checkpoint_sha256", "")))
        fsm_dir = fsm_evidence_paths(project)[height]
        fsm_eps = read_jsonl(fsm_dir / "episodes.jsonl")
        sources.append(("FSM-zero-residual", height, fsm_dir, fsm_eps, "FSM", sha256(project / "configs" / "fsm.yaml")))

    for controller, height, directory, episodes, checkpoint, checkpoint_hash in sources:
        selected_ids = set(reps[height])
        stats, selected = stream_telemetry(directory / "telemetry.csv", episodes, selected_ids)
        residual_summary[f"{controller}-{height}mm"] = {
            "mean_executed_norm": mean(item["mean_executed_norm"] for item in stats.values()),
            "max_executed_norm": max((item["executed_norm_max"] for item in stats.values()), default=0.0),
            "mean_executed_nonzero_fraction": mean(item["executed_nonzero_fraction"] for item in stats.values()),
            "mean_policy_norm": mean(item["mean_policy_norm"] for item in stats.values()),
            "mean_policy_clip_fraction": mean(item["policy_clip_fraction"] for item in stats.values()),
        }
        by_scenario = {str(row.get("scenario_id")): (index, row) for index, row in enumerate(episodes)}
        for scenario, (env_id, episode) in by_scenario.items():
            item = stats.get(env_id, {})
            diagnostic_rows.append(
                {
                    "label": "DIAGNOSTIC_ONLY_NOT_CONFIRMATORY_EXISTING_DEVELOPMENT_DATA",
                    "controller": controller,
                    "checkpoint": checkpoint,
                    "checkpoint hash": checkpoint_hash,
                    "height_mm": height,
                    "scenario": scenario,
                    "success": episode.get("success"),
                    "failure": episode.get("failure_reason"),
                    "final phase": PHASES[item.get("last_phase", -1)] if 0 <= item.get("last_phase", -1) < len(PHASES) else item.get("last_phase", ""),
                    "progress": episode.get("forward_progress_m"),
                    "episode time": episode.get("traversal_time_s"),
                    "min margin": episode.get("min_longitudinal_support_margin_m"),
                    "pitch-rate RMS": episode.get("pitch_rate_rms_rad_s"),
                    "collision": episode.get("failure_reason") == "BODY_OR_LINK_COLLISION",
                    "residual norm": item.get("mean_executed_norm", 0.0),
                    "evidence": rel(directory / "episodes.jsonl", project),
                }
            )
        for scenario in reps[height]:
            env_id, episode = by_scenario[scenario]
            item = stats.get(env_id, {})
            series = selected.get(scenario, {})
            plot_path = plot_episode_timeline(report, controller.replace("-", "_"), scenario, episode, series)
            phase_counts = item.get("phase_counts", {})
            episode_rows.append(
                {
                    "controller": controller,
                    "height_mm": height,
                    "scenario_id": scenario,
                    "seed": seed if controller.startswith("B") else "FSM",
                    "checkpoint": checkpoint,
                    "initial_distance_m": episode.get("initial_distance_m"),
                    "initial_pitch_rad": episode.get("initial_pitch_rad"),
                    "friction": episode.get("friction"),
                    "actuator_delay_steps": episode.get("actuator_delay_steps"),
                    "sensor_noise_std": episode.get("sensor_noise_std"),
                    "outcome": "SUCCESS" if episode.get("success") else episode.get("failure_reason"),
                    "final_fsm_phase": PHASES[item.get("last_phase", -1)] if 0 <= item.get("last_phase", -1) < len(PHASES) else item.get("last_phase", ""),
                    "phase_sample_counts": json.dumps(phase_counts, sort_keys=True),
                    "forward_progress_m": episode.get("forward_progress_m"),
                    "min_margin_m": episode.get("min_longitudinal_support_margin_m"),
                    "negative_margin_duration_s": episode.get("negative_margin_duration_s"),
                    "pitch_rate_rms_rad_s": episode.get("pitch_rate_rms_rad_s"),
                    "wheel_slip_distance_m": episode.get("wheel_slip_distance_m"),
                    "policy_action_mean_l2": item.get("mean_policy_norm"),
                    "executed_residual_mean_l2": item.get("mean_executed_norm"),
                    "executed_residual_max_l2": item.get("executed_norm_max"),
                    "executed_residual_nonzero_fraction": item.get("executed_nonzero_fraction"),
                    "policy_clip_fraction": item.get("policy_clip_fraction"),
                    "body_collision_time_s": episode.get("traversal_time_s") if episode.get("failure_reason") == "BODY_OR_LINK_COLLISION" else "",
                    "joint_tracking_error": "NOT_LOGGED",
                    "wheel_speed_tracking_error": "NOT_LOGGED",
                    "reward_components": "NOT_LOGGED_IN_EVALUATION_TELEMETRY",
                    "timeline_plot": rel(plot_path, project),
                    "source": rel(directory / "telemetry.csv", project),
                }
            )

    for height in (75, 100):
        run_dir, _ = canonical[(seed, height)]
        for role in ("best", "mid-agent_38400"):
            checkpoint_path = run_dir / "checkpoints" / ("best_agent.pt" if role == "best" else "agent_38400.pt")
            diagnostic_rows.append(
                {
                    "label": "DIAGNOSTIC_ONLY_NOT_CONFIRMATORY_NOT_RUN",
                    "controller": f"B-{role}",
                    "checkpoint": str(checkpoint_path),
                    "checkpoint hash": "NOT_HASHED_NOT_RUN",
                    "height_mm": height,
                    "scenario": "NOT_RUN",
                    "success": "",
                    "failure": "Initial active Isaac evaluation and supervisor transition made a new comparative campaign unsafe during the audit window",
                    "final phase": "",
                    "progress": "",
                    "episode time": "",
                    "min margin": "",
                    "pitch-rate RMS": "",
                    "collision": "",
                    "residual norm": "",
                    "evidence": "ACTIVE_PROCESS_STATUS.md",
                }
            )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    labels = [key for key in residual_summary if key.startswith("B-")]
    axes[0].bar(labels, [residual_summary[key]["mean_policy_norm"] for key in labels], color="#4C78A8", label="raw policy")
    axes[0].bar(labels, [residual_summary[key]["mean_executed_norm"] for key in labels], color="#F58518", label="executed")
    axes[0].set_title("Mean residual norm")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].legend()
    axes[1].bar(labels, [residual_summary[key]["mean_executed_nonzero_fraction"] for key in labels], color="#54A24B")
    axes[1].set_title("Executed residual nonzero fraction")
    axes[1].set_ylim(0, 1)
    axes[1].tick_params(axis="x", rotation=25)
    for axis in axes:
        axis.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(report / "plots" / "residual_action_statistics.png", dpi=160)
    plt.close(fig)
    return diagnostic_rows, episode_rows, residual_summary


def build_fsm_and_gate_plot(report: Path, fsm_rows: list[dict[str, Any]], canonical: dict[tuple[int, int], tuple[Path, dict[str, Any]]], project: Path) -> None:
    heights = [50, 75, 100]
    fsm_rate = {int(row["height_mm"]): float(row["success_rate"]) for row in fsm_rows}
    fig, axis = plt.subplots(figsize=(10, 6))
    axis.plot(heights, [fsm_rate[h] for h in heights], marker="o", linewidth=2.5, label="Frozen FSM")
    for seed in (11, 29, 47):
        rates = []
        for height in heights:
            decision, evaluation, _ = gate_for_run(project, canonical[(seed, height)][0])
            rates.append(float((evaluation or {}).get("aggregate", {}).get("success_rate", float("nan"))))
        axis.plot(heights, rates, marker="o", linestyle="--", label=f"Method B final seed {seed}")
    axis.set_xticks(heights)
    axis.set_ylim(0, 1)
    axis.set_xlabel("obstacle height (mm)")
    axis.set_ylabel("development success rate")
    axis.set_title("Existing development performance (not locked/confirmatory)")
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(report / "plots" / "checkpoint_performance.png", dpi=160)
    plt.close(fig)


def build_implementation_audit(project: Path) -> list[dict[str, Any]]:
    src = "src\\resume_validation\\"
    c_state = method_c_runtime_state(project)
    c_status = "PARTIAL" if c_state["exists"] else "IMPLEMENTED_NOT_RUN"
    c_run_evidence = c_state["evidence"]
    c_result_evidence = c_state["summary"] if c_state["exists"] else "no checkpoint/result/gate"
    c_limitation = "Training is externally owned and incomplete; no development result can be interpreted" if c_state.get("status") == "RUNNING" else "No completed Method C development gate"
    c_next = "Monitor only; do not interrupt or start a competing Isaac process" if c_state.get("status") == "RUNNING" else "Complete and gate only under the authorized pipeline"
    rows = [
        ("Robot asset discovery", "Discover canonical URDF/USD and record provenance", "COMPLETE_AND_RUN", src + "asset_discovery.py", 34, "configs\\robot.yaml", "source_manifest.csv; system_inventory.json", "configs\\robot.yaml:3-17", "Runtime asset hash is frozen", "None for audit"),
        ("URDF/USD validation", "Validate articulation and converted validation asset", "COMPLETE_AND_RUN", src + "usd_asset_audit.py", 53, "configs\\robot.yaml", "runs\\diagnostics\\residual_env_validation_003.json", "configs\\robot.yaml:17", "Validation asset changes only eight servo limits", "Preserve selected asset"),
        ("actuator limits", "Verify joint and wheel limits", "COMPLETE_AND_RUN", src + "actuator_mapping.py", 1, "configs\\actuator_limits.yaml", "tests\\test_servo_limits.py", "training preflight and zero-residual tests", "Config retains stale PENDING wording despite runtime evidence", "Reconcile wording only after experiment stops"),
        ("servo/wheel mapping", "Map eight servos and four wheel signs", "COMPLETE_AND_RUN", src + "actuator_mapping.py", 1, "configs\\actuator_limits.yaml", "tests\\test_joint_mapping.py", "configs\\actuator_limits.yaml:10-23", "Per-side wheel signs are explicit", "None"),
        ("replay 50 mm", "Replay accepted 50 mm commands", "COMPLETE_AND_RUN", src + "replay_direct_validation.py", 1, "configs\\fsm.yaml", "runs\\replay\\replay_50mm_direct_attempt005", "experiment_state.json:raw_50mm_replay=true", "Multiple preserved attempts", "Use frozen result only"),
        ("replay 100 mm", "Replay accepted 100 mm commands", "PARTIAL", src + "replay_direct_validation.py", 1, "configs\\fsm.yaml", "runs\\replay\\replay_100mm_direct_attempt001", "experiment_state.json:raw_100mm_replay_execution=true; raw_100mm_traversal=false", "Source replay is partial and does not itself traverse", "Do not claim successful raw 100 mm replay"),
        ("telemetry", "Write episode and step evidence", "COMPLETE_AND_RUN", src + "telemetry_writer.py", 11, "configs\\telemetry.yaml", "284 telemetry/episode artifacts", "development result hash chains", "Training telemetry omits many requested learning diagnostics", "Add instrumentation before retraining"),
        ("contact feedback", "Use Isaac ContactSensor and classify support/collision", "COMPLETE_AND_RUN", src + "contact_processing.py", 30, "configs\\environment.yaml", "runs\\diagnostics\\residual_env_validation_003.json", "development telemetry contact fields", "Opposing shape is inferred geometrically", "Targeted contact audit for failures"),
        ("CoM estimator", "Compute whole-body CoM", "COMPLETE_AND_RUN", src + "com_estimator.py", 15, "configs\\metrics.yaml", "tests\\test_com_estimator.py", "development margin metrics", "Actor does not receive CoM/margin", "Retain as critic/evaluation evidence"),
        ("support margin", "Compute longitudinal quasi-static support margin", "COMPLETE_AND_RUN", src + "support_margin.py", 26, "configs\\metrics.yaml", "tests\\test_support_margin.py", "FSM and B development aggregates", "Invalid margins are encoded as zero in critic", "Instrument validity rate in training"),
        ("FSM controller", "Contact-gated replay-derived FSM", "COMPLETE_AND_RUN", src + "residual_rl_env.py", 957, "configs\\fsm.yaml", "runs\\fsm\\development_* current/formal", "fsm_results.csv", "Runtime vector FSM is the authoritative implementation", "See FSM_IMPLEMENTATION.md"),
        ("frozen FSM config", "Freeze FSM and metrics after development", "COMPLETE_AND_RUN", src + "method_freeze.py", 1, "configs\\config_freeze.json", "configs\\config_freeze.json", "current hashes match formal training provenance", "Selection hash differs only by documented frozen flag", "Do not modify during audit"),
        ("FSM baseline evaluation", "Evaluate fixed development scenarios at all heights", "COMPLETE_AND_RUN", src + "evaluate_controller.py", 192, "data\\scenario_manifests\\development_v2.json", "runs\\fsm\\development_50mm_current_config_attempt043; development_75mm_formal_full_attempt042; development_100mm_current_config_attempt044", "fsm_results.csv", "Only development evidence; no validation/locked campaign", "Formal paired validation remains"),
        ("residual action", "12-D bounded residual on FSM", "COMPLETE_AND_RUN", src + "residual_rl_env.py", 1289, "configs\\ppo_common.yaml", "zero_residual_exact=true in training preflight", "Method B telemetry", "Effective v34 projection masks x and most physical actions", "Diagnose gate occupancy before retraining"),
        ("analytic IK", "Map wheel-center target to joint targets", "COMPLETE_AND_RUN", src + "residual_rl_env.py", 1251, "configs\\robot.yaml", "runtime_fk_validation_002.json; tests\\test_ik_fk_roundtrip.py", "zero fallback in canonical episode evidence", "No workspace clipping; invalid all-leg solution falls back to FSM", "Expose IK fallback rate in training"),
        ("PPO environment", "Isaac Lab DirectRLEnv residual environment", "COMPLETE_AND_RUN", src + "residual_rl_env.py", 109, "configs\\environment.yaml", "nine completed Method B v34 trainings", "training_result.json preflight", "Derived from legacy environment plumbing", "No new training in this audit"),
        ("Actor observation", "Deployment-conscious 96-D policy input", "COMPLETE_AND_RUN", src + "residual_rl_env.py", 1721, "configs\\ppo_common.yaml", "preflight actor shape [64,96]", "observation_schema.csv", "Perfect obstacle fields are currently injected", "Review real-sensor parity"),
        ("Critic privileged observation", "146-D critic state with contacts/CoM/randomization", "COMPLETE_AND_RUN", src + "residual_rl_env.py", 1798, "configs\\ppo_common.yaml", "preflight critic shape [64,146]", "observation_schema.csv", "Correctly separated from actor", "None"),
        ("Method B without CoM", "Residual PPO ablation with CoM weight 0", "COMPLETE_AND_RUN", src + "train_residual_ppo.py", 434, "configs\\ppo_without_com.yaml", "9/9 v34 seed-height training and gates complete", "all promote=false", "Cannot stand in for Method C", "Analyze as ablation only"),
        ("Method C with CoM", "Residual PPO with CoM weight 8", c_status, src + "train_residual_ppo.py", 443, "configs\\ppo_with_com.yaml", c_run_evidence, c_result_evidence, c_limitation, c_next),
        ("domain randomization", "Bounded distance/pitch/friction/delay/noise", "COMPLETE_AND_RUN", src + "training_randomization.py", 48, "configs\\obstacle_train.yaml", "training_result provenance", "full/light/full by height", "No training distribution coverage telemetry", "Instrument sampled distribution/outcomes"),
        ("curriculum", "50→75→100 warm start with per-height gate", "COMPLETE_AND_RUN", src + "curriculum_gate.py", 19, "configs\\ppo_common.yaml", "9 Method B gate_decision.json files", "all promote=false; schedule continued by explicit policy", "Cross-stage scheduler resets", "Do not describe failed gates as promotion"),
        ("multi-seed training", "Three seeds for both B and C", "PARTIAL", src + "train_residual_ppo.py", 197, "configs\\experiment_protocol.yaml", "Method B seeds 11/29/47 complete", c_result_evidence, "Method C multi-seed/multi-height coverage is incomplete", c_next),
        ("development gate", "20 fixed development episodes per height", "COMPLETE_AND_RUN", src + "curriculum_gate.py", 19, "configs\\ppo_common.yaml", "9 Method B gate decisions", "0/9 promoted", "Gate evaluates final_agent only", "Do not treat completion as passing"),
        ("validation", "Frozen validation selection", "IMPLEMENTED_NOT_RUN", src + "validation_selection.py", 125, "configs\\validation_selection_protocol.json", "scripts\\07_run_validation.ps1 exists", "runs\\validation absent", "Requires complete B and C", "Do not run until methods complete"),
        ("locked test", "Paired locked confirmatory test", "IMPLEMENTED_NOT_RUN", src + "locked_test_guard.py", 1, "configs\\experiment_protocol.yaml", "scripts\\09_run_locked_test.ps1 exists", "method_freeze.json and runs\\locked_test absent", "Locked scenarios not read in this audit", "Remain locked"),
        ("FSM vs PPO comparison", "Fair paired comparison on same scenarios", "PARTIAL", src + "evaluate_controller.py", 192, "data\\scenario_manifests\\development_v2.json", "existing FSM and B development runs use same manifest", "checkpoint_diagnostic_comparison.csv", "No completed Method C gate, validation selection, or locked test", "Formal comparison not complete"),
        ("B vs C ablation", "Only CoM reward differs", "PARTIAL" if c_state["exists"] else "IMPLEMENTED_NOT_RUN", src + "train_residual_ppo.py", 434, "configs\\ppo_without_com.yaml; ppo_with_com.yaml", "config-drift assertion and Method C training state", c_result_evidence, "No completed paired B-vs-C result", c_next),
        ("statistical analysis", "Paired/bootstrap summaries", "IMPLEMENTED_NOT_RUN", src + "statistics.py", 9, "configs\\metrics.yaml", "unit tests exist", "no formal validation/locked statistical report", "Development descriptive metrics are not confirmatory", "Run after paired formal data"),
        ("report generation", "Generate final evidence reports", "PARTIAL", src + "report_generator.py", 1, "configs\\claims_audit_protocol.json", "prelocked diagnostic reports exist", "no final_delivery_audit.json", "This handoff is an inspection report, not the experiment final report", "Use after formal data"),
        ("videos", "Select and render success/failure videos", "IMPLEMENTED_NOT_RUN", src + "video_selection.py", 132, "configs\\video_selection_protocol.json", "scripts\\10_generate_videos.ps1 exists", "no locked video campaign", "Inspection GUI wrappers are separate", "Use development GUI for inspection only"),
        ("resume wording audit", "Ensure claims match completed evidence", "PARTIAL", src + "final_audit.py", 1, "configs\\claims_audit_protocol.json", "prelocked claims audits exist", "no final audit; current resume claim unsupported for Method C", "Method B must not be called CoM-guided result", "Use HANDOFF_SUMMARY wording"),
    ]
    output = []
    for requirement, description, status, source, line, config, run_evidence, result_evidence, limitations, next_action in rows:
        path = project / source
        output.append(
            {
                "requirement": requirement,
                "description": description,
                "status": status,
                "source file": source,
                "source line": line,
                "config": config,
                "run evidence": run_evidence,
                "result evidence": result_evidence,
                "last modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else "",
                "limitations": limitations,
                "next required action": next_action,
            }
        )
    return output


def build_hypotheses(project: Path, residual_summary: dict[str, Any]) -> list[dict[str, Any]]:
    b75 = residual_summary.get("B-final-75mm", {})
    b100 = residual_summary.get("B-final-100mm", {})
    near_zero = max(safe_float(b75.get("mean_executed_nonzero_fraction"), 0.0), safe_float(b100.get("mean_executed_nonzero_fraction"), 0.0)) < 0.01
    c_state = method_c_runtime_state(project)
    c_evidence = c_state["summary"] if c_state["exists"] else "no formal Method C training result"
    c_counter = "Method C has started but is not complete" if c_state.get("status") == "RUNNING" else "Method C config and code exist"
    specs = [
        ("FSM baseline itself is unreliable", "SUPPORTED", "HIGH", "fsm_results.csv: 12/20, 7/20, 7/20", "Some fixed scenarios succeed", "B,C", "50/75/100", "paired zero-residual checkpoint test", "P0"),
        ("PPO residual is too large and destroys the FSM", "NOT_SUPPORTED", "HIGH", "final-policy executed residual is near zero; saturation 0", "Older diagnostics may contain nonzero residual", "B", "75/100", "evaluate an explicitly chosen nonzero checkpoint", "P3"),
        ("PPO residual is too small to change the FSM", "SUPPORTED" if near_zero else "PARTIALLY_SUPPORTED", "HIGH", "residual_action_statistics.png and identical final outcomes", "Raw policy outputs are nonzero before phase/state projection", "B", "75/100", "log gate occupancy and executed residual during training", "P0"),
        ("Actions are heavily clipped", "NOT_SUPPORTED", "HIGH", "episodes residual_saturation_rate=0; telemetry policy clip fraction ~0", "Phase gain has a hard clip but is rarely reached", "B", "75/100", "retain saturation instrumentation", "P3"),
        ("Workspace projection removes wheel-center residual", "NOT_SUPPORTED", "HIGH", "runtime has no workspace projection; invalid IK falls back to baseline", "The specialized action projection removes channels before IK", "B,C", "all", "separately log action projection and IK fallback", "P2"),
        ("IK branch or joint clipping breaks continuity", "NOT_SUPPORTED", "MEDIUM", "nearest-reference branch selection; canonical terminal IK invalid counts are zero", "Per-step joint target rate limiting can alter requested motion", "B", "75/100", "log requested-vs-final wheel-center displacement", "P2"),
        ("Wheel-speed residual causes slip or collision", "NOT_SUPPORTED", "HIGH", "v34 final executed wheel-speed residual is effectively zero; FSM has same collision pattern", "Earlier v31-v33 diagnostics tested wheel corrections", "B", "100", "only test under registered diagnostic label", "P3"),
        ("PPO optimizes progress while ignoring support transfer", "PARTIALLY_SUPPORTED", "MEDIUM", "progress weight 8; Method B CoM weight 0; no training component telemetry", "success, collision, phase-progress and top-contact terms exist", "B", "all", "log per-term returns by phase", "P1"),
        ("Method B has no CoM reward, so stability improvement is not expected", "SUPPORTED", "HIGH", "ppo_without_com.yaml com_margin_weight=0.0", "pitch/slip/tilt penalties still provide indirect stability incentives", "B", "all", "evaluate Method C separately", "P0"),
        ("Method C training is not complete", "SUPPORTED", "HIGH", c_evidence, c_counter, "C", "all", "monitor the externally owned run; evaluate only after a completed development gate", "P0"),
        ("Orchestration waits for Method B promote before Method C", "NOT_SUPPORTED", "HIGH", "run_until_success defaults ContinueAfterFailedDevelopmentGate=true and schedules C after B coverage", "Sequential scheduling still waits for B process completion", "B,C", "all", "fix supervisor exit-code bug", "P1"),
        ("Method B failure incorrectly blocks Method C", "NOT_SUPPORTED", "HIGH", "failed gates are explicitly continued; supervisor attempt 3 proceeded to Method C", "earlier supervisor attempts failed on an empty exit-code message", "B,C", "all", "repair supervisor exit-code handling without interrupting the live run", "P1"),
        ("Training success proxy differs from formal success", "PARTIALLY_SUPPORTED", "MEDIUM", "best_agent uses tracked total return, not development success", "environment success reward uses the same success buffer as evaluation", "B,C", "all", "evaluate checkpoint candidates on development success", "P1"),
        ("best_agent selection is not based on development success", "SUPPORTED", "HIGH", "skrl base.py selects highest Reward / Total reward (mean)", "A correlation with success is possible but unverified", "B,C", "all", "rename/document as training-return-best", "P0"),
        ("final_agent is worse than an intermediate checkpoint", "INSUFFICIENT_EVIDENCE", "LOW", "no best/mid checkpoint development evaluations", "final gates are complete", "B", "75/100", "run fixed 5-10 scenario diagnostic when no supervisor owns Isaac", "P1"),
        ("Curriculum restores only policy, not optimizer/normalizers", "NOT_SUPPORTED", "HIGH", "checkpoint keys include policy,value,optimizer,observation/state/value preprocessors", "scheduler is not checkpointed", "B,C", "75/100", "document whole-agent load semantics", "P3"),
        ("Optimizer reset causes forgetting at new heights", "NOT_SUPPORTED", "HIGH", "optimizer state is in checkpoint and agent.load loads all modules", "KLAdaptiveLR scheduler object resets", "B,C", "75/100", "log scheduler state at stage boundary", "P2"),
        ("100 mm full randomization is introduced too early", "INSUFFICIENT_EVIDENCE", "LOW", "100 mm uses full randomization despite failed 75 mm gate", "fixed schedule intentionally continues failed gates", "B,C", "100", "stratify training/eval outcomes by randomization", "P2"),
        ("100 mm collision comes from insufficient baseline lift clearance", "PARTIALLY_SUPPORTED", "MEDIUM", "FSM and B share 7 rear/body-link collisions; residual is zero", "terminal-only collision evidence cannot reconstruct clearance", "FSM,B", "100", "replay collision episodes with link clearance logging", "P1"),
        ("100 mm collision comes from negative residual z", "NOT_SUPPORTED", "HIGH", "executed residual is zero in final collision episodes", "Raw actor channels can be nonzero before gating", "B", "100", "plot executed z by collision episode", "P3"),
        ("100 mm collision comes from wheel residual advancing before placement", "NOT_SUPPORTED", "HIGH", "executed wheel residual is zero and FSM has the same failures", "FSM reference itself commands post-transfer drive", "B", "100", "separate reference and residual wheel commands", "P3"),
        ("TIMEOUTs cluster in a specific FSM phase", "SUPPORTED", "HIGH", "fsm_failure_reasons.csv and episode timelines show DRIVE_CLEAR/late-phase stalls", "Some global timeouts may have different transient histories", "FSM,B", "75/100", "add phase-at-timeout scalar to episodes.jsonl", "P0"),
        ("Timeout exposes slow behavior rather than a bad timeout setting", "PARTIALLY_SUPPORTED", "MEDIUM", "75 mm successes and failures run close to 150 s; phase gates stall on support", "The 150 s cap can still change pass/fail near the boundary", "FSM,B", "75", "measure required stable-dwell acquisition time", "P1"),
        ("PPO stalls in late phases without effective progress reward", "PARTIALLY_SUPPORTED", "MEDIUM", "late-phase timeouts and near-zero executed residual", "phase-progress and recovery rewards exist", "B", "75/100", "log phase occupancy and per-phase reward", "P1"),
        ("Success dwell and FSM completion conditions are inconsistent", "SUPPORTED", "HIGH", "phase-10 gate uses top+tilt+angular speed; success additionally requires 4-wheel upward-force support and 1.5 s dwell", "The stricter success predicate is intentional", "FSM,B,C", "all", "expose completion predicates side by side", "P1"),
        ("Contact classification confuses step top and riser", "INSUFFICIENT_EVIDENCE", "LOW", "classification has geometric disambiguation and tests", "No per-contact ground-truth opposing shape exists", "FSM,B,C", "all", "targeted contact replay with visual markers", "P2"),
        ("CoM margin is invalid or has the wrong sign", "NOT_SUPPORTED", "MEDIUM", "formula is min distance to support interval; values are plausible and validity is tracked", "many samples are invalid and encoded zero for critic", "B,C", "all", "log invalid-rate and reason", "P2"),
        ("Actor lacks key phase-completion information", "PARTIALLY_SUPPORTED", "MEDIUM", "actor lacks contact classes, forces and support margin; critic has them", "actor receives FSM phase/progress and proprioception", "B,C", "all", "ablate deployable contact proxies", "P1"),
        ("Actor observation mismatches future robot feedback", "PARTIALLY_SUPPORTED", "MEDIUM", "perfect obstacle/detection validity/age are injected in simulation", "IMU, joint and velocity terms are deployment-oriented", "B,C", "all", "write real-sensor availability table", "P1"),
        ("Domain randomization ranges are unreasonable", "INSUFFICIENT_EVIDENCE", "LOW", "bounded ranges are documented; no coverage-response analysis", "development set uses similar bounded factors", "B,C", "all", "stratify success by friction/delay/noise/distance", "P2"),
        ("Most training episodes never reach late phases", "INSUFFICIENT_EVIDENCE", "LOW", "training phase occupancy is not logged", "development telemetry reaches late phases", "B,C", "all", "log phase occupancy histogram", "P1"),
        ("Reward scales are imbalanced", "PARTIALLY_SUPPORTED", "MEDIUM", "large raw-action regularizers (-120/-180 per second) apply even when action is physically gated", "terminal success/failure weights are ±200", "B,C", "all", "log per-term returns and applied-vs-raw regularization", "P0"),
        ("Value function learning failed", "INSUFFICIENT_EVIDENCE", "LOW", "value loss exists but explained variance is not logged", "training stayed finite", "B", "all", "log explained variance and value targets", "P2"),
        ("Entropy/exploration is inappropriate", "SUPPORTED", "MEDIUM", "entropy_loss_scale=0; log_std constrained to [-5,-4], giving very small exploration", "small exploration was intentionally chosen for FSM safety", "B,C", "all", "measure executed-action exploration after gating", "P1"),
        ("Residual PPO only works by chance on one seed", "NOT_SUPPORTED", "HIGH", "all three seeds give the same final development success counts; none beats gate", "policy weights differ", "B", "all", "paired outcome difference table", "P3"),
        ("Evaluation loads the wrong checkpoint or config", "NOT_SUPPORTED", "HIGH", "gate decisions hash-match final_agent and result provenance matches current configs", "best_agent is not evaluated by the gate", "B", "all", "keep explicit checkpoint/hash output in viewer", "P3"),
    ]
    return [
        {
            "hypothesis": item[0],
            "verdict": item[1],
            "confidence": item[2],
            "evidence": item[3],
            "counter-evidence": item[4],
            "affected methods": item[5],
            "affected heights": item[6],
            "recommended diagnostic": item[7],
            "recommended fix priority": item[8],
        }
        for item in specs
    ]


def build_method_summary(project: Path, canonical: dict[tuple[int, int], tuple[Path, dict[str, Any]]], fsm_rows: list[dict[str, Any]]) -> str:
    c_state = method_c_runtime_state(project)
    if c_state["exists"]:
        c_line = f"Method C (`com_margin=8.0`) has started: seed {c_state['seed']} / {c_state['height_mm']} mm is `{c_state['status']}` and intermediate checkpoints exist. It has no completed development result at the audit cutoff, so its performance cannot yet be evaluated."
    else:
        c_line = "Method C (`com_margin=8.0`) has config and training code, but no formal training result, checkpoint, or development gate exists."
    gate_lines = []
    for (seed, height), (run_dir, result) in sorted(canonical.items()):
        decision, evaluation, _ = gate_for_run(project, run_dir)
        agg = (evaluation or {}).get("aggregate", {})
        gate_lines.append(
            f"| B | {seed} | {height} | {result.get('status')} | {agg.get('success_count')}/20 | {agg.get('success_rate')} | {(decision or {}).get('required', {}).get('minimum_development_success_rate')} | {(decision or {}).get('promote')} | final_agent.pt |"
        )
    fsm_line = ", ".join(f"{row['height_mm']} mm {row['successes']}/{row['episodes']} ({float(row['success_rate']):.0%})" for row in fsm_rows)
    return f"""# Method status and PPO failure analysis

## Bottom line

- Frozen FSM development performance: {fsm_line}.
- Method B is the **without-CoM ablation** (`com_margin=0.0`). All 9 v34 seed×height trainings completed and all 9 final checkpoints were evaluated on 20 development scenarios, but **0/9 gates promoted**.
- {c_line}
- There is no validation run, no method freeze, and no locked test. A formal FSM-vs-PPO or B-vs-C comparison therefore does not exist.
- The observed Method B final policies largely reproduce the frozen FSM outcome pattern. The principal mechanism is a narrow phase/IMU execution gate plus action projection and strong penalties on **raw** actions, which makes the executed residual effectively zero in the inspected final evaluations.

## Method B v34 completion matrix

| Method | Seed | Height mm | Training | Development | Rate | Threshold | Promote | Gate checkpoint |
|---|---:|---:|---|---:|---:|---:|---|---|
{os.linesep.join(gate_lines)}

## What “best” and “final” mean

`best_agent.pt` is selected inside installed skrl by the highest tracked `Reward / Total reward (mean)` at checkpoint intervals. It is not selected by development success, collision rate, CoM margin, or the frozen checkpoint-selection rule. `final_agent.pt` is explicitly saved after the final training update. Every development gate in the current curriculum loads `final_agent.pt`.

## Resume semantics

Cross-height warm starts call `agent.load(...)` with `resume_offset_timesteps=0`. Zero here means “start a new height-stage budget at local timestep zero,” not “load policy weights only.” Canonical checkpoint dictionaries contain policy, value, optimizer, observation preprocessor, state preprocessor, and value preprocessor. The policy state includes `log_std_parameter`. The KL-adaptive scheduler is constructed anew and is not registered in skrl’s checkpoint modules, so scheduler state resets across stages.

## Why PPO did not meet expectations

1. The reference itself is weak: FSM is only 60%/35%/35% on development at 50/75/100 mm.
2. v34 permits physical residual execution only in phases 8–10 and only after IMU hazard gates; it then projects 12 raw channels into a very constrained shared correction. All wheel-center x channels are masked.
3. Training penalizes raw action magnitude and left/right asymmetry even in steps where gating prevents any physical residual. This creates a direct incentive to output near zero.
4. Entropy bonus is zero and the Gaussian log standard deviation is constrained to [-5,-4], so exploration is deliberately narrow.
5. Method B has no CoM reward. Its result cannot answer whether the planned CoM-guided Method C improves support margin or pitch stability.
6. Training logs contain no success rate, phase occupancy, KL, entropy, explained variance, clip fraction, gradient norm, reward-component return, executed residual norm, or saturation fraction. This blocks several causal claims.

## Orchestration failure is separate from policy failure

After the final Method B gate completed, earlier `formal_training_recovery_supervisor.ps1` / `full_pipeline_supervisor.ps1` attempts recorded `FAILED` with an empty wrapper exit-code message. A later supervisor attempt proceeded to Method C. Therefore `promote=False` did not block Method C; the empty-exit-code failures were transient orchestration defects and are separate from policy quality. At this audit cutoff the live Method C process is externally owned and must not be interrupted.
"""


def build_markdown_reports(project: Path, report: Path, fsm_rows: list[dict[str, Any]], residual_summary: dict[str, Any], training_meta: dict[str, Any]) -> None:
    fsm_hash = sha256(project / "configs" / "fsm.yaml")
    asset_hash = sha256(project / "assets" / "converted" / "wlr_robot_validation.usd")
    write_text(
        report / "FSM_IMPLEMENTATION.md",
        f"""# FSM implementation audit

The authoritative runtime FSM is the vectorized implementation in `src\\resume_validation\\residual_rl_env.py`, not merely the standalone `FSMController` helper.

- Phase enum and names: `src\\resume_validation\\fsm_controller.py:10-23`.
- Height-conditioned phase boundaries: `src\\resume_validation\\fsm_phase_schedule.py:13-48` and runtime use at `src\\resume_validation\\residual_rl_env.py:1015-1047`.
- Contact-gated monotonic transitions and three-step latch: `src\\resume_validation\\residual_rl_env.py:971-1047`.
- Phase-specific fallback wheel commands: `src\\resume_validation\\residual_rl_env.py:1054-1122`.
- Baseline support geometry/load balancing: `src\\resume_validation\\residual_rl_env.py:1145-1224` and `1289-1353`.
- IK nearest-branch selection and safe limits: `src\\resume_validation\\residual_rl_env.py:1251-1287`.
- Dynamic phase timeout: `src\\resume_validation\\residual_rl_env.py:1880-1911`.
- Formal success dwell and safety termination: `src\\resume_validation\\residual_rl_env.py:1841-1943`.

The phase order is front pair first and rear pair second. Phase gates use “at least one” and then “both” contacts within each pair; this is not a strictly one-wheel-at-a-time FSM. The 50 mm replay provides the complete rear reference; the partial 100 mm replay is combined with height-conditioned rear preparation and recovery. Servo references use zero-order hold rather than geometric interpolation (`src\\resume_validation\\fsm_trajectory.py:26-47`).

There is contact debounce (3 control steps) and contact-milestone latching, but no backward transition hysteresis. Fallbacks are stop-at-gate, conservative approach/rear/post-transfer wheel commands, all-leg IK fallback to the baseline, and terminal safety predicates. Servo targets are rate limited after IK; wheel targets are acceleration limited only for nonzero PPO residual. Exact zero action bypasses both residual rate-limit paths and equals the FSM reference.

Frozen config: `configs\\fsm.yaml`; SHA-256 `{fsm_hash}`. Selected validation asset SHA-256 `{asset_hash}`. All formal Method B training/evaluation provenance records the same current FSM hash, and the config file predates the v34 formal runs; there is no evidence it changed after those runs.

75 mm uses normalized-time command interpolation between 50/100 mm replays and linearly interpolated phase/support geometry, but not every tuning parameter is a simple midpoint: support unloading, rear-transfer speeds, and post-transfer speed have explicit 75 mm anchors.

Development results are in `fsm_results.csv`. The 100 mm baseline already fails 13/20 episodes (7 body/link collisions, 6 global timeouts). Many 75/100 mm timeouts finish in late `DRIVE_CLEAR`; representative plots are under `plots\\episodes`.
""",
    )
    write_text(
        report / "residual_control_chain.md",
        """# Residual control chain

```mermaid
flowchart LR
    A["PPO Gaussian sample / deterministic mean"] --> B["sample clipping to [-1,1]"]
    B --> C["phase 8-10 + IMU hazard gate"]
    C --> D["v34 projection and channel mask"]
    D --> E["phase gain 3/4/3 + hard clip"]
    E --> F["wheel-center x/z scale"]
    F --> G["add frozen FSM wheel-center reference"]
    G --> H["analytic IK; nearest safe branch"]
    H --> I["all-leg invalid fallback to FSM"]
    I --> J["servo rate limit"]
    J --> K["joint safe-limit clamp"]
    K --> L["articulation position command"]
```

There is no explicit workspace projection/clipping step. Workspace infeasibility is detected by IK; if any leg is invalid, all residual leg targets fall back to the baseline for that environment.

```mermaid
flowchart LR
    A["PPO wheel-speed channels"] --> B["phase/IMU gate + v34 phase-9 counter-yaw projection"]
    B --> C["phase gain + hard clip"]
    C --> D["× 0.10 rad/s"]
    D --> E["add FSM wheel-speed reference"]
    E --> F["clip to ±2.094 rad/s"]
    F --> G["6 rad/s² acceleration limit"]
    G --> H["per-wheel forward-sign mapping"]
    H --> I["articulation velocity command"]
```

Exact all-zero applied action bypasses IK numerical round trips and residual wheel acceleration limiting, returning the frozen FSM commands exactly (`src\\resume_validation\\residual_rl_env.py:1647-1689`). Evaluation uses `outputs["mean_actions"]`, so PPO playback is deterministic (`src\\resume_validation\\evaluate_controller.py:728-733`).
""",
    )
    write_text(
        report / "PPO_TRAINING_ANALYSIS.md",
        f"""# PPO training-curve and learning-quality audit

TensorBoard was found for all {training_meta.get('runs', 0)} canonical Method B v34 seed×height runs. Available scalar tags are:

{os.linesep.join('- ' + tag for tag in training_meta.get('available_tags', []))}

Missing instrumentation: {', '.join(training_meta.get('missing_tags', []))}.

The curves support only statements about tracked return, episode length, policy/value loss, standard deviation, and adaptive learning rate. They do not prove task learning. In particular, a longer mean episode can be caused by more global timeouts. `best_agent.pt` is a training-return checkpoint, not a development-success checkpoint.

Observed curve patterns:

- At 50 mm, tracked total return rises from roughly -186 to +241/+244/+243 across seeds while mean episode length rises from about 6,450 to 8,058-8,086 steps. The fixed development gate still reaches only 13/20, so this return increase is not evidence of passing task learning.
- At 75 mm, episode-return samples are sparse because episodes are roughly 8,884-8,999 steps. Seed 47 regresses from about +227 to +34 while the other two seeds improve only modestly; there is no consistent cross-seed learning signal.
- At 100 mm, final tracked returns are mixed: seed 11 about -96, seed 29 about +190, and seed 47 about -214 from starts near -205/-206. All three final gates nevertheless produce the same 7/20 outcome.
- Policy standard deviation changes only slowly (approximately 0.0183 toward 0.0171-0.0180) and is already constrained by `log_std` clipping; there is no abrupt numerical collapse in the available scalar.
- Policy/value losses remain finite and value loss is modest, but explained variance is not logged. These curves cannot establish that the value function learned a useful task model.

The final development evidence is more decisive than TensorBoard: all three seeds have the same success counts at each height (13/20, 7/20, 7/20), all gates fail, and inspected final evaluations show near-zero executed residual. This is consistent with a policy that largely leaves the weak FSM unchanged, not with NaN/OOM/policy-process failure.

See `plots\\training_return_by_stage.png`, `episode_length_by_stage.png`, `policy_value_loss.png`, `entropy_kl.png`, `reward_components.png`, and `residual_action_statistics.png`. Missing charts are rendered as explicit instrumentation-gap panels rather than invented data.
""",
    )
    write_text(
        report / "GIT_STATUS.md",
        """# Git status

No `.git` directory exists at the project root, `C:\\robotics_sim\\wlr_robot`, or `C:\\robotics_sim`. Branch, commit, modified/untracked/deleted status are therefore unavailable. No commit, reset, checkout, or cleanup was performed.
""",
    )


def build_handoff_summary(project: Path, report: Path, fsm_rows: list[dict[str, Any]]) -> None:
    c_state = method_c_runtime_state(project)
    if c_state["exists"]:
        c_status = f"Method C has started (seed {c_state['seed']} / {c_state['height_mm']} mm, status `{c_state['status']}`, intermediate checkpoints exist) but has no completed development gate at the audit cutoff"
        c_created = "Method C remaining stages/gates"
        critical_wording = "目前 Method C 已启动 seed 11 / 50 mm 训练，但尚未完成且没有 development gate；因此仍不能评价计划中的 CoM-guided Residual PPO。"
        pipeline_state = "After two transient empty-exit-code supervisor failures, full-pipeline supervisor attempt 3 launched Method C. The live training process is externally owned; no GUI/evaluation was started and it must not be interrupted."
    else:
        c_status = "Method C is implemented but has not been launched"
        c_created = "Method C training path"
        critical_wording = "目前只能评价 Method B 消融组，尚不能评价简历中计划使用的 CoM-guided Residual PPO。"
        pipeline_state = "Method B coverage and gates completed, but the supervisor stopped on an empty wrapper exit-code message before Method C."
    write_text(
        report / "HANDOFF_SUMMARY.md",
        f"""# ChatGPT handoff summary

## Answers to the 11 audit questions

1. **What Codex completed:** isolated project/inventory, asset and actuator validation, 50/100 replay execution audits, contact/CoM/support-margin code and tests, a frozen replay-derived FSM, 50/75/100 FSM development evaluations, a 96-D actor/146-D critic residual environment, Method B smoke plus all 3 seeds × 3 heights of v34 training and their development gates, and extensive diagnostics.
2. **Code created but not actually run:** {c_created}, formal validation-selection campaign, method freeze, locked test, final B-vs-C/FSM statistics, and locked-test video/report pipeline. Inspection GUI wrappers were created in this audit and only dry-run/help validated.
3. **FSM actual performance:** 50 mm 12/20 (60%); 75 mm 7/20 (35%, 13 timeouts); 100 mm 7/20 (35%, 7 body/link collisions and 6 timeouts). This is development evidence, not locked-test performance.
4. **PPO actual performance:** Method B final checkpoints give 13/20 at 50 mm and 7/20 at 75/100 mm for every seed; 0/9 development gates promote. At 75/100 mm it matches the frozen FSM success counts and failure pattern. Method C has no completed result at the audit cutoff.
5. **Why PPO missed expectations:** weak FSM reference; narrow phase/IMU execution gate and projection; strong penalties on raw actions even when those actions are not executed; zero entropy bonus and tightly bounded exploration; no CoM reward in Method B; missing learning instrumentation. The inspected final policies execute almost no residual, so “training completed” did not become “controller improved.”
6. **Method status:** Method B training/gates complete but failed; {c_status}; FSM baseline development evaluation complete at all heights.
7. **Formal FSM/PPO comparison:** no. There is a fair same-manifest development comparison for FSM vs Method B final, but no completed Method C evaluation, validation, method freeze, or locked test.
8. **How to open/use the program:** use the scripts under `scripts\\inspection`; they activate the existing IsaacLab path via `conda run` and print exact commands/log paths. Do not use `run_until_success.ps1` for inspection.
9. **Watch FSM in a window:** run `show_fsm_gui.ps1 -HeightMm 75 -ScenarioMode development-success -DryRun`, inspect the command, then rerun without `-DryRun` only when `inspect_project_status.ps1` says GUI is safe.
10. **Watch PPO in a window:** run `show_ppo_gui.ps1 -Method B -Seed 29 -HeightMm 75 -Checkpoint final -ScenarioMode development-success -DryRun`, then rerun without `-DryRun` when safe. `auto` intentionally refuses because no checkpoint is promoted. Method C never falls back to B.
11. **What to send ChatGPT:** start with this report directory’s summary/audit CSVs, plots, source/config evidence list, and small episode evidence. Do not upload all 4.9 GB of telemetry or hundreds of checkpoints. See `CHATGPT_UPLOAD_MANIFEST.md` and `CHATGPT_HANDOFF_BUNDLE_FINAL.zip`.

## Critical wording

{critical_wording}

Do not write “PPO was formally better than FSM,” “CoM-guided PPO was validated,” or “locked testing completed.” A truthful current statement is: “Implemented a frozen replay-derived FSM and a residual-PPO ablation; completed three-seed development training for the no-CoM ablation, which did not pass promotion gates; CoM-guided training and confirmatory testing remain incomplete.”

## Current pipeline state

{pipeline_state} Canonical Method B training results are `COMPLETED`, gates have `passed_execution=true`, and no NaN/OOM/traceback is recorded in their training results.
""",
    )
    write_text(
        report / "CHATGPT_UPLOAD_MANIFEST.md",
        """# Files to provide to ChatGPT

## First upload (small, sufficient for planning)

- `HANDOFF_SUMMARY.md`
- `METHOD_STATUS_AND_PPO_FAILURE.md`
- `IMPLEMENTATION_AUDIT.csv`
- `EXPERIMENT_MATRIX.csv`
- `CHECKPOINT_INVENTORY.csv`
- `PPO_FAILURE_HYPOTHESES.csv`
- `FSM_IMPLEMENTATION.md`, `fsm_phase_table.csv`, `fsm_results.csv`, `fsm_failure_reasons.csv`
- `observation_schema.csv`, `action_schema.csv`, `residual_control_chain.md`
- `PPO_TRAINING_ANALYSIS.md`, `training_curve_summary.json`, and the seven top-level plots
- `episode_diagnostics.csv` plus representative timeline PNGs
- `ACTIVE_PROCESS_STATUS.md`, `active_processes.json`, `GIT_STATUS.md`, and `RUNBOOK.md`

The generated `CHATGPT_HANDOFF_BUNDLE_FINAL.zip` contains these inspection outputs plus the key source/config files below. It intentionally excludes checkpoints, full telemetry, and every locked-test scenario file. The earlier un-suffixed bundle is superseded by this final bundle.

## Key source/config evidence

- `configs/fsm.yaml`, `metrics.yaml`, `ppo_common.yaml`, `ppo_without_com.yaml`, `ppo_with_com.yaml`, `environment.yaml`, `obstacle_train.yaml`, `robot.yaml`, `config_freeze.json`, `experiment_protocol.yaml`
- `src/resume_validation/residual_rl_env.py`, `residual_safety.py`, `ppo_models.py`, `train_residual_ppo.py`, `evaluate_controller.py`, `fsm_controller.py`, `fsm_phase_schedule.py`, `fsm_trajectory.py`, `reference_tensor.py`, `reward.py`, `curriculum_gate.py`, `checkpoint_selection.py`
- `scripts/train_curriculum.ps1`, `run_until_success.ps1`, `formal_training_recovery_supervisor.ps1`, `full_pipeline_supervisor.ps1`

## Optional targeted evidence

- The selected seed-29 75/100 mm `result.json` and `episodes.jsonl` files for FSM and Method B final.
- One `best_agent.pt` and one `final_agent.pt` only if ChatGPT will inspect tensors directly. Their hashes and module keys are already in `CHECKPOINT_INVENTORY.csv`.
- Full telemetry only for a single named scenario if a new analysis specifically needs raw steps; do not upload the entire 4.9 GB corpus.

## Explicit exclusions

- Do not upload or inspect `data/locked_test/manifest_v2.json`; it has not been authorized or executed.
- Do not upload all 856 checkpoint files.
- Do not present diagnostic development plots as confirmatory evidence.
""",
    )
    write_text(
        report / "RUNBOOK.md",
        f"""# Inspection and visualization runbook

```powershell
Set-Location {project}
& .\\scripts\\inspection\\inspect_project_status.ps1
& .\\scripts\\inspection\\list_available_controllers.ps1
```

Dry-run the exact command first:

```powershell
& .\\scripts\\inspection\\show_fsm_gui.ps1 -HeightMm 75 -ScenarioMode development-success -DryRun
& .\\scripts\\inspection\\show_ppo_gui.ps1 -Method B -Seed 29 -HeightMm 75 -Checkpoint final -ScenarioMode development-success -DryRun
& .\\scripts\\inspection\\show_fsm_vs_ppo.ps1 -Method B -Seed 29 -HeightMm 75 -Checkpoint final -ScenarioMode development-success -DryRun
```

When the status script reports that GUI launch is safe, omit `-DryRun`. Add `-RecordVideo` to save a development-only replay. `show_ppo_gui.ps1 -Checkpoint auto` refuses while no promoted checkpoint exists; use explicit `best` or `final` and treat the result as diagnostic.

Training dashboard:

```powershell
& .\\scripts\\inspection\\open_training_dashboard.ps1 -DryRun
& .\\scripts\\inspection\\open_training_dashboard.ps1
```

The scripts call the existing `evaluate_controller.py` without `--headless`, force one exact development scenario, use deterministic mean actions, and never start training.
""",
    )


def main() -> int:
    args = parse_args()
    project = args.project.resolve()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=True)
    (report / "plots" / "episodes").mkdir(parents=True, exist_ok=True)

    disk_rows, recent_rows, readme_rows = build_folder_outputs(project, report)
    entry_rows, key_source_rows = build_entrypoints(project)
    experiment_rows, canonical = build_experiment_matrix(project)
    checkpoint_rows = build_checkpoint_inventory(project, canonical)
    phase_rows, fsm_rows, fsm_failure_rows = build_fsm_tables(project)
    observation_rows, action_rows = build_observation_action_tables()
    training_rows, training_meta = build_training_plots(project, report, canonical)
    diagnostic_rows, episode_rows, residual_summary = build_episode_outputs(project, report, canonical)
    build_fsm_and_gate_plot(report, fsm_rows, canonical, project)
    implementation_rows = build_implementation_audit(project)
    hypotheses_rows = build_hypotheses(project, residual_summary)

    method_text = build_method_summary(project, canonical, fsm_rows)
    write_text(report / "METHOD_STATUS_AND_PPO_FAILURE.md", method_text)
    build_markdown_reports(project, report, fsm_rows, residual_summary, training_meta)
    build_handoff_summary(project, report, fsm_rows)

    tables = {
        "disk_usage_summary.csv": disk_rows,
        "recent_artifacts.csv": recent_rows,
        "readmes.csv": readme_rows,
        "entrypoints.csv": entry_rows,
        "key_source_files.csv": key_source_rows,
        "IMPLEMENTATION_AUDIT.csv": implementation_rows,
        "fsm_phase_table.csv": phase_rows,
        "fsm_results.csv": fsm_rows,
        "fsm_failure_reasons.csv": fsm_failure_rows,
        "observation_schema.csv": observation_rows,
        "action_schema.csv": action_rows,
        "EXPERIMENT_MATRIX.csv": experiment_rows,
        "CHECKPOINT_INVENTORY.csv": checkpoint_rows,
        "training_curve_summary.csv": training_rows,
        "episode_diagnostics.csv": episode_rows,
        "PPO_FAILURE_HYPOTHESES.csv": hypotheses_rows,
        "checkpoint_diagnostic_comparison.csv": diagnostic_rows,
    }
    dump_json(report / "_tables.json", tables)
    dump_json(report / "training_curve_summary.json", {"metadata": training_meta, "rows": training_rows})
    dump_json(report / "residual_action_summary.json", residual_summary)
    dump_json(
        report / "audit_metadata.json",
        {
            "schema": "resume_validation.chatgpt_handoff_audit.v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "project": str(project),
            "report": str(report),
            "locked_test_contents_read": False,
            "new_training_started": False,
            "new_evaluation_started": False,
            "canonical_method_b_strata": len(canonical),
            "method_c_artifact_count": sum(1 for p in (project / "runs" / "ppo_with_com").rglob("*") if p.is_file()),
        },
    )
    print(json.dumps({"report": str(report), "tables": len(tables), "canonical_strata": len(canonical)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
