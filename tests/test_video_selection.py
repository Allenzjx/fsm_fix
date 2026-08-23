from __future__ import annotations

from resume_validation.video_selection import (
    _locked_outcome_reproduced,
    _same_scenario_parameters,
    _video_group_requirements,
    select_video_episodes,
)


def test_video_selection_includes_success_failure_and_extremes() -> None:
    rows = []
    for method in ("fsm", "B", "C"):
        seeds = (None,) if method == "fsm" else (11, 29, 47)
        for height in (50, 75, 100):
            for seed in seeds:
                for index, success in enumerate((True, False)):
                    rows.append(
                        {
                            "method": method,
                            "training_seed": seed,
                            "scenario_id": f"{method}-{seed}-{height}-{index}",
                            "obstacle_height_m": height / 1000.0,
                            "success": success,
                            "failure_reason": "" if success else "TIMEOUT",
                            "min_longitudinal_support_margin_m": (
                                0.01 if success else -0.02
                            ),
                            "pitch_rate_rms_rad_s": 0.2 + index,
                            "locked_result": "result.json",
                            "locked_result_sha256": "r",
                            "locked_episodes": "episodes.jsonl",
                            "locked_episodes_sha256": "e",
                        }
                    )
    selected = select_video_episodes(rows)
    requirements = _video_group_requirements(rows)
    assert len(requirements) == 9
    for method in ("fsm", "B", "C"):
        for height in (50, 75, 100):
            categories = {
                category
                for row in selected
                if row["method"] == method and row["height_mm"] == height
                for category in row["categories"]
            }
            assert categories == {
                "typical_success",
                "typical_failure",
                "worst_margin",
                "highest_pitch_rate",
            }
            requirement = next(
                row
                for row in requirements
                if row["method"] == method and row["height_mm"] == height
            )
            assert set(requirement["required_categories"]) == categories
            assert requirement["locked_failure_count"] > 0


def test_video_replay_requires_exact_scenario_and_failure_reason() -> None:
    locked = {
        "scenario_id": "locked-h050-0001",
        "obstacle_height_m": 0.05,
        "friction": 1.0,
        "success": False,
        "failure_reason": "TIMEOUT",
    }
    replay = dict(locked)
    selected = {
        "locked_success": False,
        "locked_failure_reason": "TIMEOUT",
    }
    assert _same_scenario_parameters(replay, locked)
    assert _locked_outcome_reproduced(replay, selected)

    replay["friction"] = 1.1
    assert not _same_scenario_parameters(replay, locked)
    replay["friction"] = 1.0
    replay["failure_reason"] = "BODY_OR_LINK_COLLISION"
    assert not _locked_outcome_reproduced(replay, selected)
