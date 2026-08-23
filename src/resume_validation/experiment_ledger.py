from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FIELDS = (
    "timestamp_utc", "experiment_id", "parent_experiment_id", "stage", "method", "seed",
    "hypothesis", "changed_parameters", "unchanged_controls", "expected_effect",
    "actual_effect", "result", "next_action", "artifact_path",
)


def append_ledger(path: str | Path, row: dict[str, Any]) -> None:
    path = Path(path)
    payload = {name: row.get(name, "") for name in FIELDS}
    payload["timestamp_utc"] = payload["timestamp_utc"] or datetime.now(timezone.utc).isoformat()
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(payload)
