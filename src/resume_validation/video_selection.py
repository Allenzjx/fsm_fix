"""Deterministic, non-cherry-picked locked-episode video selection and audit."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from .config_io import write_json
from .locked_test_guard import SCENARIO_FIELDS, audit_locked_campaign
from .method_freeze import verify_method_freeze
from .source_audit import sha256_file

HEIGHTS = (50, 75, 100)
SEEDS = (11, 29, 47)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _load_rows(result_path: Path, method: str, seed: int | None) -> list[dict[str, Any]]:
    result = _load_json(result_path)
    episodes = Path(result["artifacts"]["episodes"])
    if sha256_file(episodes) != result["artifacts"]["episodes_sha256"]:
        raise ValueError(f"Locked episode hash mismatch: {episodes}")
    return [
        {
            **json.loads(line),
            "method": method,
            "training_seed": seed,
            "locked_result": str(result_path.resolve()),
            "locked_result_sha256": sha256_file(result_path),
            "locked_episodes": str(episodes.resolve()),
            "locked_episodes_sha256": sha256_file(episodes),
        }
        for line in episodes.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _metric(row: dict[str, Any], name: str, default: float) -> float:
    value = row.get(name)
    if value is None:
        return default
    numeric = float(value)
    return numeric if math.isfinite(numeric) else default


def _tie(row: dict[str, Any]) -> tuple[int, str]:
    seed = row.get("training_seed")
    return (int(seed) if seed is not None else -1, str(row["scenario_id"]))


def _same_scenario_parameters(
    replay: dict[str, Any],
    locked: dict[str, Any],
) -> bool:
    return all(
        replay.get(field) == locked.get(field)
        for field in SCENARIO_FIELDS
    )


def _locked_outcome_reproduced(
    replay: dict[str, Any],
    selected: dict[str, Any],
) -> bool:
    replay_success = bool(replay["success"])
    if replay_success != bool(selected["locked_success"]):
        return False
    return replay_success or (
        str(replay.get("failure_reason", ""))
        == str(selected.get("locked_failure_reason", ""))
    )


def _decode_video_probe(video: Path) -> dict[str, Any]:
    import imageio.v2 as imageio

    reader = imageio.get_reader(video)
    try:
        metadata = reader.get_meta_data()
        first = reader.get_data(0)
        frame_count = int(reader.count_frames())
    finally:
        reader.close()
    return {
        "decoded": True,
        "width": int(first.shape[1]),
        "height": int(first.shape[0]),
        "fps": float(metadata["fps"]),
        "codec": str(metadata.get("codec", "")),
        "decoded_frame_count": frame_count,
    }


def _typical(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid_margins = [
        float(row["min_longitudinal_support_margin_m"])
        for row in rows
        if row.get("min_longitudinal_support_margin_m") is not None
    ]
    pitch_values = [float(row["pitch_rate_rms_rad_s"]) for row in rows]
    median_margin = median(valid_margins) if valid_margins else None
    median_pitch = median(pitch_values)
    return min(
        rows,
        key=lambda row: (
            (
                abs(
                    float(row["min_longitudinal_support_margin_m"])
                    - median_margin
                )
                if median_margin is not None
                and row.get("min_longitudinal_support_margin_m") is not None
                else math.inf
            ),
            abs(float(row["pitch_rate_rms_rad_s"]) - median_pitch),
            *_tie(row),
        ),
    )


def select_video_episodes(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        height = int(round(float(row["obstacle_height_m"]) * 1000.0))
        groups[(str(row["method"]), height)].append(row)
    if set(groups) != {
        (method, height)
        for method in ("fsm", "B", "C")
        for height in HEIGHTS
    }:
        raise ValueError("Video selection requires every method-height group")
    selections: list[dict[str, Any]] = []
    for method in ("fsm", "B", "C"):
        for height in HEIGHTS:
            group = groups[(method, height)]
            category_rows: list[tuple[str, dict[str, Any]]] = []
            successes = [row for row in group if bool(row["success"])]
            failures = [row for row in group if not bool(row["success"])]
            if successes:
                category_rows.append(("typical_success", _typical(successes)))
            if failures:
                category_rows.append(("typical_failure", _typical(failures)))
            valid_margin = [
                row
                for row in group
                if row.get("min_longitudinal_support_margin_m") is not None
            ]
            if valid_margin:
                worst_margin = min(
                    valid_margin,
                    key=lambda row: (
                        float(row["min_longitudinal_support_margin_m"]),
                        -float(row["pitch_rate_rms_rad_s"]),
                        *_tie(row),
                    ),
                )
                worst_margin_valid = True
            else:
                worst_margin = min(group, key=_tie)
                worst_margin_valid = False
            category_rows.append(("worst_margin", worst_margin))
            highest_pitch = min(
                group,
                key=lambda row: (
                    -float(row["pitch_rate_rms_rad_s"]),
                    _metric(
                        row,
                        "min_longitudinal_support_margin_m",
                        math.inf,
                    ),
                    _tie(row)[0],
                    str(row["scenario_id"]),
                ),
            )
            category_rows.append(("highest_pitch_rate", highest_pitch))

            deduplicated: dict[tuple[int | None, str], dict[str, Any]] = {}
            for category, row in category_rows:
                key = (row.get("training_seed"), str(row["scenario_id"]))
                if key not in deduplicated:
                    deduplicated[key] = {
                        "method": method,
                        "height_mm": height,
                        "training_seed": row.get("training_seed"),
                        "scenario_id": str(row["scenario_id"]),
                        "locked_success": bool(row["success"]),
                        "locked_failure_reason": str(
                            row.get("failure_reason", "")
                        ),
                        "min_longitudinal_support_margin_m": row.get(
                            "min_longitudinal_support_margin_m"
                        ),
                        "pitch_rate_rms_rad_s": row.get(
                            "pitch_rate_rms_rad_s"
                        ),
                        "categories": [],
                        "locked_result": row["locked_result"],
                        "locked_result_sha256": row["locked_result_sha256"],
                        "locked_episodes": row["locked_episodes"],
                        "locked_episodes_sha256": row[
                            "locked_episodes_sha256"
                        ],
                    }
                deduplicated[key]["categories"].append(category)
                if category == "worst_margin":
                    deduplicated[key]["worst_margin_metric_valid"] = (
                        worst_margin_valid
                    )
            selections.extend(deduplicated.values())
    return sorted(
        selections,
        key=lambda row: (
            ("fsm", "B", "C").index(row["method"]),
            row["height_mm"],
            row["training_seed"] if row["training_seed"] is not None else -1,
            row["scenario_id"],
        ),
    )


def _video_group_requirements(
    rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        height = int(round(float(row["obstacle_height_m"]) * 1000.0))
        groups[(str(row["method"]), height)].append(row)
    requirements: list[dict[str, Any]] = []
    for method in ("fsm", "B", "C"):
        for height in HEIGHTS:
            group = groups[(method, height)]
            success_count = sum(bool(row["success"]) for row in group)
            failure_count = len(group) - success_count
            required = ["worst_margin", "highest_pitch_rate"]
            if success_count:
                required.append("typical_success")
            if failure_count:
                required.append("typical_failure")
            requirements.append(
                {
                    "method": method,
                    "height_mm": height,
                    "locked_episode_count": len(group),
                    "locked_success_count": success_count,
                    "locked_failure_count": failure_count,
                    "required_categories": sorted(required),
                }
            )
    return requirements


def build_video_selection(
    *,
    project_root: Path,
    freeze_path: Path,
    authorization_path: Path,
    locked_run_root: Path,
    audit_path: Path,
) -> dict[str, Any]:
    freeze = _load_json(freeze_path)
    failures = verify_method_freeze(freeze)
    if failures:
        raise RuntimeError("Method freeze drift: " + " | ".join(failures))
    fresh_audit = audit_locked_campaign(
        freeze_path=freeze_path,
        authorization_path=authorization_path,
        run_root=locked_run_root,
    )
    recorded_audit = _load_json(audit_path)
    if (
        not fresh_audit["paired_scenario_coverage_complete"]
        or fresh_audit["episode_count"] != recorded_audit["episode_count"]
        or fresh_audit["locked_manifest_sha256"]
        != recorded_audit["locked_manifest_sha256"]
    ):
        raise ValueError("Locked audit does not reproduce before video selection")
    protocol_path = project_root / "configs" / "video_selection_protocol.json"
    protocol = _load_json(protocol_path)
    if not protocol.get("frozen_before_locked_test", False):
        raise ValueError("Video selection protocol is not frozen")
    rows: list[dict[str, Any]] = []
    for height in HEIGHTS:
        rows.extend(
            _load_rows(
                locked_run_root / "fsm" / f"height-{height}mm" / "result.json",
                "fsm",
                None,
            )
        )
    for method in ("B", "C"):
        for seed in SEEDS:
            for height in HEIGHTS:
                rows.extend(
                    _load_rows(
                        locked_run_root
                        / f"method-{method}"
                        / f"seed-{seed}"
                        / f"height-{height}mm"
                        / "result.json",
                        method,
                        seed,
                    )
                )
    selections = select_video_episodes(rows)
    selection_by_method_seed = {
        (str(row["method"]), int(row["seed"])): row
        for row in freeze["selections"]
    }
    for row in selections:
        if row["method"] == "fsm":
            row["checkpoint"] = None
            row["checkpoint_sha256"] = None
        else:
            selection = selection_by_method_seed[
                (row["method"], int(row["training_seed"]))
            ]
            row["checkpoint"] = selection["selected_checkpoint"]
            row["checkpoint_sha256"] = selection[
                "selected_checkpoint_sha256"
            ]
    return {
        "schema": "resume_validation.video_selection.v1",
        "method_freeze": str(freeze_path.resolve()),
        "method_freeze_sha256": sha256_file(freeze_path),
        "locked_audit": str(audit_path.resolve()),
        "locked_audit_sha256": sha256_file(audit_path),
        "locked_manifest": fresh_audit["locked_manifest"],
        "locked_manifest_sha256": fresh_audit["locked_manifest_sha256"],
        "selection_protocol": str(protocol_path.resolve()),
        "selection_protocol_sha256": sha256_file(protocol_path),
        "locked_episode_count_considered": len(rows),
        "selection_count_after_deduplication": len(selections),
        "group_category_requirements": _video_group_requirements(rows),
        "selections": selections,
    }


def build_video_inventory(
    *,
    selection_path: Path,
    videos_root: Path,
) -> dict[str, Any]:
    selection = _load_json(selection_path)
    inventory_rows: list[dict[str, Any]] = []
    categories_seen: dict[tuple[str, int], set[str]] = defaultdict(set)
    for index, selected in enumerate(selection["selections"]):
        replay_dir = videos_root / f"replay-{index:03d}"
        result_path = replay_dir / "result.json"
        result = _load_json(result_path)
        locked_result = Path(selected["locked_result"])
        locked_episodes = Path(selected["locked_episodes"])
        if (
            sha256_file(locked_result) != selected["locked_result_sha256"]
            or sha256_file(locked_episodes)
            != selected["locked_episodes_sha256"]
        ):
            raise ValueError(
                f"Selected locked source evidence drifted: {locked_result}"
            )
        checkpoint = selected.get("checkpoint")
        if (
            checkpoint is not None
            and sha256_file(Path(checkpoint))
            != selected["checkpoint_sha256"]
        ):
            raise ValueError(f"Video checkpoint hash mismatch: {checkpoint}")
        if (
            not result.get("passed_execution", False)
            or result.get("controller") != selected["method"]
            or int(result.get("height_mm", -1)) != int(selected["height_mm"])
            or result["provenance"].get("checkpoint_sha256")
            != selected["checkpoint_sha256"]
            or result["provenance"].get("manifest_sha256")
            != selection["locked_manifest_sha256"]
            or result.get("video_replay", {}).get("scenario_id")
            != selected["scenario_id"]
            or result.get("video_replay", {}).get("locked_outcome_label")
            != ("success" if selected["locked_success"] else "failure")
        ):
            raise ValueError(f"Video replay provenance mismatch: {result_path}")
        episodes = Path(result["artifacts"]["episodes"])
        if sha256_file(episodes) != result["artifacts"]["episodes_sha256"]:
            raise ValueError(f"Video replay episode hash mismatch: {episodes}")
        rows = [
            json.loads(line)
            for line in episodes.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(rows) != 1 or str(rows[0]["scenario_id"]) != selected["scenario_id"]:
            raise ValueError(f"Video replay scenario mismatch: {result_path}")
        locked_rows = [
            json.loads(line)
            for line in locked_episodes.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        locked_matches = [
            row
            for row in locked_rows
            if str(row["scenario_id"]) == selected["scenario_id"]
        ]
        if (
            len(locked_matches) != 1
            or not _same_scenario_parameters(rows[0], locked_matches[0])
        ):
            raise ValueError(
                f"Video replay scenario parameters differ from locked source: "
                f"{result_path}"
            )
        video = Path(result["artifacts"]["video"])
        if sha256_file(video) != result["artifacts"]["video_sha256"]:
            raise ValueError(f"Video hash mismatch: {video}")
        video_probe = _decode_video_probe(video)
        if (
            video_probe["width"] != 960
            or video_probe["height"] != 540
            or not math.isclose(
                video_probe["fps"],
                20.0,
                abs_tol=0.05,
            )
            or video_probe["decoded_frame_count"]
            != int(result["video_replay"]["frame_count"])
        ):
            raise ValueError(f"Video decode probe mismatch: {video}")
        replay_success = bool(rows[0]["success"])
        replay_failure_reason = str(rows[0].get("failure_reason", ""))
        failure_reason_reproduced = replay_success or (
            replay_failure_reason
            == str(selected.get("locked_failure_reason", ""))
        )
        for category in selected["categories"]:
            categories_seen[(selected["method"], int(selected["height_mm"]))].add(
                category
            )
        inventory_rows.append(
            {
                **selected,
                "replay_result": str(result_path.resolve()),
                "replay_result_sha256": sha256_file(result_path),
                "video": str(video.resolve()),
                "video_sha256": sha256_file(video),
                "video_frame_count": result["video_replay"]["frame_count"],
                "video_duration_s": result["video_replay"]["duration_s"],
                "video_decode_probe": video_probe,
                "replay_success": replay_success,
                "replay_failure_reason": replay_failure_reason,
                "failure_reason_reproduced": failure_reason_reproduced,
                "locked_outcome_reproduced": _locked_outcome_reproduced(
                    rows[0],
                    selected,
                ),
            }
        )
    requirements = selection.get("group_category_requirements")
    if not isinstance(requirements, list) or len(requirements) != 9:
        raise ValueError("Video selection lacks complete group requirements")
    for requirement in requirements:
        key = (
            str(requirement["method"]),
            int(requirement["height_mm"]),
        )
        categories = categories_seen[key]
        required = set(requirement["required_categories"])
        if not required <= categories:
            raise ValueError(
                f"Video categories incomplete: {key} required={required} "
                f"actual={categories}"
            )
    return {
        "schema": "resume_validation.video_inventory.v1",
        "selection": str(selection_path.resolve()),
        "selection_sha256": sha256_file(selection_path),
        "video_count": len(inventory_rows),
        "all_replay_outcomes_reproduced": all(
            row["locked_outcome_reproduced"] for row in inventory_rows
        ),
        "videos": inventory_rows,
    }


def _main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    select = subparsers.add_parser("select")
    select.add_argument("--project_root", type=Path, required=True)
    select.add_argument("--freeze", type=Path, required=True)
    select.add_argument("--authorization", type=Path, required=True)
    select.add_argument("--locked_run_root", type=Path, required=True)
    select.add_argument("--audit", type=Path, required=True)
    select.add_argument("--output", type=Path, required=True)
    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--selection", type=Path, required=True)
    inventory.add_argument("--videos_root", type=Path, required=True)
    inventory.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite video evidence: {args.output}")
    if args.command == "select":
        payload = build_video_selection(
            project_root=args.project_root,
            freeze_path=args.freeze,
            authorization_path=args.authorization,
            locked_run_root=args.locked_run_root,
            audit_path=args.audit,
        )
    else:
        payload = build_video_inventory(
            selection_path=args.selection,
            videos_root=args.videos_root,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "schema": payload["schema"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
