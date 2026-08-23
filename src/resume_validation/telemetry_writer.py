from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .telemetry_schema import REQUIRED_STEP_FIELDS, SCHEMA_VERSION, UNITS


class TelemetryWriter:
    def __init__(self, path: str | Path, metadata: dict[str, Any], *, chunk_rows: int = 1000):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.path.with_suffix(self.path.suffix + ".metadata.json")
        self.metadata_path.write_text(
            json.dumps({"schema_version": SCHEMA_VERSION, "units": UNITS, **metadata}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.chunk_rows = max(1, int(chunk_rows))
        self._rows: list[dict[str, Any]] = []
        self._fieldnames: list[str] | None = None
        self.rows_written = 0

    def append(self, row: dict[str, Any]) -> None:
        missing = [name for name in REQUIRED_STEP_FIELDS if name not in row]
        if missing:
            raise ValueError(f"Telemetry row missing fields: {missing}")
        if self._fieldnames is None:
            self._fieldnames = list(row)
        elif set(row) != set(self._fieldnames):
            raise ValueError("Telemetry schema changed within a file")
        self._rows.append(dict(row))
        if len(self._rows) >= self.chunk_rows:
            self.flush()

    def extend(self, rows: Iterable[dict[str, Any]]) -> None:
        for row in rows:
            self.append(row)

    def flush(self) -> None:
        if not self._rows:
            return
        exists = self.path.exists()
        with self.path.open("a", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=self._fieldnames)
            if not exists:
                writer.writeheader()
            writer.writerows(self._rows)
        self.rows_written += len(self._rows)
        self._rows.clear()

    def close(self) -> None:
        self.flush()

    def __enter__(self) -> "TelemetryWriter":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
