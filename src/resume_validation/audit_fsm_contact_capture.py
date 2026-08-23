"""Audit FSM post-transfer contact capture from evaluator telemetry.

The evaluator historically named contact-force magnitudes ``*_contact_force_n``.
Formal support and success, however, use the world-Z component recorded in the
new ``*_contact_upward_force_n`` columns.  This tool keeps those semantics
explicit and can prove that an instrumentation-only replay preserved every
pre-existing telemetry column.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

WHEELS = ("fl", "fr", "rl", "rr")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"Telemetry has no header: {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Telemetry has no data rows: {path}")
    if any(None in row for row in rows):
        raise ValueError(f"Telemetry contains a row wider than its header: {path}")
    if any(value is None for row in rows for value in row.values()):
        raise ValueError(f"Telemetry contains a row shorter than its header: {path}")
    return list(reader.fieldnames), rows


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _longest_true_run(
    samples: list[tuple[float, bool]], nominal_dt_s: float
) -> dict[str, float | int | None]:
    best_start: float | None = None
    best_end: float | None = None
    best_count = 0
    run_start: float | None = None
    run_end: float | None = None
    run_count = 0
    previous_time: float | None = None
    max_gap_s = nominal_dt_s * 1.5
    for time_s, condition in samples:
        contiguous = previous_time is not None and time_s - previous_time <= max_gap_s
        if condition:
            if run_count == 0 or not contiguous:
                run_start = time_s
                run_count = 1
            else:
                run_count += 1
            run_end = time_s
            if run_count > best_count:
                best_start = run_start
                best_end = run_end
                best_count = run_count
        else:
            run_start = None
            run_end = None
            run_count = 0
        previous_time = time_s
    return {
        "sample_count": best_count,
        "start_time_s": best_start,
        "end_time_s": best_end,
        "duration_s": best_count * nominal_dt_s,
    }


def _compare_shared_columns(
    headers: list[str],
    rows: list[dict[str, str]],
    comparison_path: Path,
) -> dict[str, Any]:
    comparison_headers, comparison_rows = _read_csv(comparison_path)
    shared = [name for name in comparison_headers if name in headers]
    mismatch_count = 0
    first_mismatch: dict[str, Any] | None = None
    for index in range(min(len(rows), len(comparison_rows))):
        for name in shared:
            if rows[index][name] != comparison_rows[index][name]:
                mismatch_count += 1
                if first_mismatch is None:
                    first_mismatch = {
                        "row_index_zero_based": index,
                        "column": name,
                        "current": rows[index][name],
                        "comparison": comparison_rows[index][name],
                    }
                break
    mismatch_count += abs(len(rows) - len(comparison_rows))
    return {
        "path": str(comparison_path),
        "sha256": _sha256(comparison_path),
        "row_count": len(comparison_rows),
        "shared_column_count": len(shared),
        "shared_columns": shared,
        "mismatched_row_count": mismatch_count,
        "first_mismatch": first_mismatch,
        "all_shared_values_identical": (
            len(rows) == len(comparison_rows) and mismatch_count == 0
        ),
    }


def audit(
    telemetry_path: Path,
    *,
    upward_threshold_n: float,
    required_top_state: int,
    dwell_s: float,
    compare_telemetry_path: Path | None = None,
) -> dict[str, Any]:
    headers, rows = _read_csv(telemetry_path)
    required = {
        "time_s",
        "env_id",
        "fsm_phase",
        *(f"{wheel}_contact_state" for wheel in WHEELS),
        *(f"{wheel}_contact_force_n" for wheel in WHEELS),
        *(f"{wheel}_contact_upward_force_n" for wheel in WHEELS),
    }
    missing = sorted(required - set(headers))
    if missing:
        raise ValueError(f"Telemetry is missing required columns: {missing}")
    full_top_columns = [
        f"{wheel}_full_wheel_on_top" for wheel in WHEELS
    ]
    has_formal_full_top = all(name in headers for name in full_top_columns)

    env_ids = sorted({int(row["env_id"]) for row in rows})
    if env_ids != [0]:
        raise ValueError(f"Single-scenario audit requires only env_id 0, got {env_ids}")
    times = [float(row["time_s"]) for row in rows]
    positive_deltas = [
        later - earlier
        for earlier, later in zip(times, times[1:])
        if later > earlier
    ]
    if not positive_deltas:
        raise ValueError("Telemetry timestamps do not advance")
    nominal_dt_s = _median(positive_deltas)

    post_rows = [
        row for row in rows if int(float(row["fsm_phase"])) in (9, 10)
    ]
    if not post_rows:
        raise ValueError("Telemetry contains no FSM phase 9 or 10 samples")

    condition_samples: list[tuple[float, bool]] = []
    all_top_samples: list[tuple[float, bool]] = []
    all_upward_samples: list[tuple[float, bool]] = []
    best_min_upward: tuple[float, float] | None = None
    per_wheel: dict[str, dict[str, Any]] = {}
    for wheel in WHEELS:
        values = [float(row[f"{wheel}_contact_upward_force_n"]) for row in post_rows]
        magnitudes = [float(row[f"{wheel}_contact_force_n"]) for row in post_rows]
        per_wheel[wheel] = {
            "minimum_upward_force_n": min(values),
            "maximum_upward_force_n": max(values),
            "maximum_contact_force_magnitude_n": max(magnitudes),
            "samples_at_or_above_upward_threshold": sum(
                value >= upward_threshold_n for value in values
            ),
        }

    for row in post_rows:
        time_s = float(row["time_s"])
        if has_formal_full_top:
            all_top = all(
                int(float(row[name])) == 1 for name in full_top_columns
            )
        else:
            all_top = all(
                int(float(row[f"{wheel}_contact_state"])) == required_top_state
                for wheel in WHEELS
            )
        minimum_upward = min(
            float(row[f"{wheel}_contact_upward_force_n"]) for wheel in WHEELS
        )
        all_upward = minimum_upward >= upward_threshold_n
        supported_top = all_top and all_upward
        all_top_samples.append((time_s, all_top))
        all_upward_samples.append((time_s, all_upward))
        condition_samples.append((time_s, supported_top))
        if best_min_upward is None or minimum_upward > best_min_upward[1]:
            best_min_upward = (time_s, minimum_upward)

    supported_run = _longest_true_run(condition_samples, nominal_dt_s)
    result: dict[str, Any] = {
        "schema": "resume_validation.fsm_contact_capture_audit.v1",
        "telemetry": {
            "path": str(telemetry_path),
            "sha256": _sha256(telemetry_path),
            "row_count": len(rows),
            "column_count": len(headers),
            "columns": headers,
            "csv_rows_match_header": True,
            "nominal_dt_s": nominal_dt_s,
        },
        "criteria": {
            "phases": [9, 10],
            "required_top_state": required_top_state,
            "top_geometry_source": (
                "formal_full_wheel_on_top"
                if has_formal_full_top
                else "legacy_contact_state_fallback"
            ),
            "minimum_each_wheel_upward_force_n": upward_threshold_n,
            "required_stable_dwell_s": dwell_s,
        },
        "post_transfer": {
            "sample_count": len(post_rows),
            "start_time_s": float(post_rows[0]["time_s"]),
            "end_time_s": float(post_rows[-1]["time_s"]),
            "all_top_sample_count": sum(value for _, value in all_top_samples),
            "all_upward_sample_count": sum(value for _, value in all_upward_samples),
            "supported_top_sample_count": sum(value for _, value in condition_samples),
            "longest_all_top_run": _longest_true_run(all_top_samples, nominal_dt_s),
            "longest_all_upward_run": _longest_true_run(
                all_upward_samples, nominal_dt_s
            ),
            "longest_supported_top_run": supported_run,
            "required_dwell_met": float(supported_run["duration_s"]) >= dwell_s,
            "best_minimum_wheel_upward_force": {
                "time_s": best_min_upward[0],
                "force_n": best_min_upward[1],
            },
            "per_wheel": per_wheel,
        },
    }
    if compare_telemetry_path is not None:
        result["comparison"] = _compare_shared_columns(
            headers, rows, compare_telemetry_path
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("telemetry", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare-telemetry", type=Path)
    parser.add_argument("--upward-threshold-n", type=float, default=2.0)
    parser.add_argument("--required-top-state", type=int, default=3)
    parser.add_argument("--dwell-s", type=float, default=1.5)
    args = parser.parse_args()
    report = audit(
        args.telemetry.resolve(),
        upward_threshold_n=args.upward_threshold_n,
        required_top_state=args.required_top_state,
        dwell_s=args.dwell_s,
        compare_telemetry_path=(
            args.compare_telemetry.resolve() if args.compare_telemetry else None
        ),
    )
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        output = args.output.resolve()
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite audit output: {output}")
        output.write_text(payload, encoding="utf-8")
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
