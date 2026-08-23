from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .paths import (
    CANONICAL_URDF,
    CANONICAL_USD,
    ISAACLAB_LAUNCHER,
    PROJECT_ROOT,
    REFERENCE_REPLAY_ROOT,
    VALIDATION_ROOT,
    WORKSPACE_ROOT,
    ensure_output_dirs,
)

AUDITED_SUFFIXES = {".urdf", ".usd", ".usda", ".yaml", ".yml", ".json", ".jsonl", ".py"}
IGNORED_PARTS = {"__pycache__", ".git"}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(command: list[str], timeout: float = 30.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "command": command,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"command": command, "error": f"{type(exc).__name__}: {exc}"}


def _package_versions(names: Iterable[str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name in names:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def system_inventory() -> dict[str, Any]:
    conda_exe = shutil.which("conda")
    nvidia_smi = shutil.which("nvidia-smi")
    ps = shutil.which("powershell") or shutil.which("pwsh")
    inventory: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "windows_version": platform.version(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "active_conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "conda_prefix": os.environ.get("CONDA_PREFIX"),
        "isaaclab_launcher": str(ISAACLAB_LAUNCHER.resolve()) if ISAACLAB_LAUNCHER.exists() else None,
        "isaaclab_launcher_exists": ISAACLAB_LAUNCHER.exists(),
        "packages_current_python": _package_versions(
            ["isaaclab", "isaacsim", "skrl", "torch", "numpy", "scipy", "pandas", "matplotlib", "gymnasium", "pyarrow"]
        ),
        "disk": {},
        "git": {},
    }
    for root in {PROJECT_ROOT.anchor, VALIDATION_ROOT.anchor}:
        usage = shutil.disk_usage(root)
        inventory["disk"][root] = {"total": usage.total, "used": usage.used, "free": usage.free}
    if ps:
        inventory["powershell"] = _run([ps, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"])
        inventory["windows_cim"] = _run(
            [
                ps,
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber,OSArchitecture | ConvertTo-Json -Compress",
            ]
        )
    if conda_exe:
        inventory["conda_info"] = _run([conda_exe, "info", "--json"])
        inventory["conda_envs"] = _run([conda_exe, "env", "list", "--json"])
    if nvidia_smi:
        inventory["gpu"] = _run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total,memory.free,driver_version",
                "--format=csv,noheader,nounits",
            ]
        )
    inventory["git"]["project"] = _run(["git", "-C", str(PROJECT_ROOT), "status", "--short", "--branch"])
    inventory["known_isaac_versions_from_verified_local_artifacts"] = {
        "isaaclab": "0.54.3",
        "isaacsim": "5.1.0.0",
        "source": str(
            REFERENCE_REPLAY_ROOT
            / "artifacts"
            / "e2e"
            / "vision_round2_final.json"
        ),
        "requires_current_run_confirmation": True,
    }
    return inventory


def discover_sources() -> list[Path]:
    files: list[Path] = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDITED_SUFFIXES:
            continue
        rel = path.relative_to(PROJECT_ROOT)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] == VALIDATION_ROOT.name:
            continue
        files.append(path.resolve())
    return sorted(files, key=lambda item: str(item).lower())


def selection_reason(path: Path) -> tuple[bool, str]:
    selected: dict[Path, str] = {
        CANONICAL_USD.resolve(): "height replay default robot asset and prior physical validation asset",
        CANONICAL_URDF.resolve(): "SolidWorks-exported URDF corresponding to the canonical USD",
        (REFERENCE_REPLAY_ROOT / "command_model.py").resolve(): "authoritative replay command limits and sign mapping",
        (REFERENCE_REPLAY_ROOT / "sim_robot_adapter.py").resolve(): "authoritative command-space to Isaac target adapter",
        (REFERENCE_REPLAY_ROOT / "sim_obstacle_scene.py").resolve(): "authoritative replay obstacle and physics setup",
        (REFERENCE_REPLAY_ROOT / "playback.py").resolve(): "authoritative playback timing semantics",
        (REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl").resolve():
            "recorded 50 mm reference sequence",
        (REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_10cm" / "accepted_steps.jsonl").resolve():
            "recorded 100 mm reference sequence",
    }
    resolved = path.resolve()
    return (resolved in selected, selected.get(resolved, "candidate or supporting source; not frozen as primary reference"))


def write_source_manifest() -> dict[str, str]:
    ensure_output_dirs()
    rows: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for path in discover_sources():
        digest = sha256_file(path)
        selected, reason = selection_reason(path)
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        stat = path.stat()
        rows.append(
            {
                "absolute_path": str(path),
                "relative_path": relative,
                "file_type": path.suffix.lower().lstrip("."),
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": digest,
                "selected_as_reference": str(selected).lower(),
                "selection_reason": reason,
            }
        )
        hashes[relative] = digest
    manifest = VALIDATION_ROOT / "source_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    hash_path = VALIDATION_ROOT / "source_hashes.json"
    hash_path.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": str(manifest), "hashes": str(hash_path), "file_count": str(len(rows))}


def run_inventory() -> dict[str, Any]:
    ensure_output_dirs()
    inventory = system_inventory()
    inventory_path = VALIDATION_ROOT / "system_inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    outputs = write_source_manifest()
    return {"system_inventory": str(inventory_path), **outputs}
