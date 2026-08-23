from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to read YAML configs") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    return data


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def config_sha256(data_or_path: Any) -> str:
    data = load_config(data_or_path) if isinstance(data_or_path, (str, Path)) else data_or_path
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def write_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def differing_leaf_paths(left: Any, right: Any, prefix: str = "") -> set[str]:
    """Return canonical dotted paths whose values or structure differ."""

    if isinstance(left, dict) and isinstance(right, dict):
        paths: set[str] = set()
        for key in set(left) | set(right):
            child = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                paths.add(child)
            else:
                paths.update(differing_leaf_paths(left[key], right[key], child))
        return paths
    if isinstance(left, list) and isinstance(right, list):
        paths = set()
        for index in range(max(len(left), len(right))):
            child = f"{prefix}[{index}]"
            if index >= len(left) or index >= len(right):
                paths.add(child)
            else:
                paths.update(differing_leaf_paths(left[index], right[index], child))
        return paths
    return set() if left == right else {prefix or "<root>"}
