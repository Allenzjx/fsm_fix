from __future__ import annotations

import json
from pathlib import Path

from resume_validation.report_generator import (
    _claims,
    _resume_interpretation,
)


def test_registered_numeric_claim_rules_verify_only_exact_supported_values() -> None:
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads(
        (root / "configs" / "claims_audit_protocol.json").read_text(
            encoding="utf-8"
        )
    )
    method_summaries = {
        "fsm": {
            "success_rate": 0.84,
            "pitch_rate_rms_all": {"equal_height_mean": 1.0},
        },
        "C": {
            "success_rate": 0.91,
            "pitch_rate_rms_all": {"equal_height_mean": 0.69},
        },
    }
    comparison = {
        "metrics": {
            "success": {
                "equal_height_mean_delta": 0.07,
                "stratified_bootstrap_95_ci": [0.02, 0.12],
            },
            "min_longitudinal_support_margin_m": {
                "equal_height_mean_delta": 0.01,
                "stratified_bootstrap_95_ci": [0.005, 0.015],
                "missing_pair_count": 0,
            },
            "pitch_rate_rms_rad_s": {
                "equal_height_mean_delta": -0.31,
                "stratified_bootstrap_95_ci": [-0.4, -0.2],
            },
        }
    }
    claims = _claims(protocol, method_summaries, comparison)
    assert {detail["status"] for detail in claims.values()} == {"VERIFIED"}


def test_numeric_mismatch_is_only_partial_when_direction_is_supported() -> None:
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads(
        (root / "configs" / "claims_audit_protocol.json").read_text(
            encoding="utf-8"
        )
    )
    method_summaries = {
        "fsm": {
            "success_rate": 0.5,
            "pitch_rate_rms_all": {"equal_height_mean": 1.0},
        },
        "C": {
            "success_rate": 0.6,
            "pitch_rate_rms_all": {"equal_height_mean": 0.9},
        },
    }
    comparison = {
        "metrics": {
            "success": {
                "equal_height_mean_delta": 0.1,
                "stratified_bootstrap_95_ci": [0.01, 0.2],
            },
            "min_longitudinal_support_margin_m": {
                "equal_height_mean_delta": 0.002,
                "stratified_bootstrap_95_ci": [0.001, 0.003],
                "missing_pair_count": 0,
            },
            "pitch_rate_rms_rad_s": {
                "equal_height_mean_delta": -0.1,
                "stratified_bootstrap_95_ci": [-0.2, -0.01],
            },
        }
    }
    claims = _claims(protocol, method_summaries, comparison)
    assert {detail["status"] for detail in claims.values()} == {
        "PARTIALLY_VERIFIED"
    }


def test_missing_continuous_metrics_are_disclosed_without_crashing() -> None:
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads(
        (root / "configs" / "claims_audit_protocol.json").read_text(
            encoding="utf-8"
        )
    )
    method_summaries = {
        "fsm": {
            "success_rate": 0.5,
            "pitch_rate_rms_all": {"equal_height_mean": None},
        },
        "C": {
            "success_rate": 0.5,
            "pitch_rate_rms_all": {"equal_height_mean": None},
        },
    }
    comparison = {
        "metrics": {
            "success": {
                "equal_height_mean_delta": 0.0,
                "stratified_bootstrap_95_ci": [-0.1, 0.1],
            },
            "min_longitudinal_support_margin_m": {
                "equal_height_mean_delta": None,
                "stratified_bootstrap_95_ci": None,
                "missing_pair_count": 900,
            },
            "pitch_rate_rms_rad_s": {
                "equal_height_mean_delta": None,
                "stratified_bootstrap_95_ci": None,
            },
        }
    }
    claims = _claims(protocol, method_summaries, comparison)
    assert claims["margin_plus_10mm"]["actual_paired_improvement_mm"] is None
    assert claims["pitch_rate_minus_31pct"]["actual_reduction_percent"] is None
    assert {detail["status"] for detail in claims.values()} == {
        "NOT_VERIFIED"
    }


def test_resume_interpretation_explicitly_labels_tradeoff() -> None:
    code, text = _resume_interpretation(
        success_delta_pp=-3.0,
        success_direction_supported=False,
        margin_direction_supported=True,
        pitch_direction_supported=True,
    )
    assert code == "SUCCESS_STABILITY_TRADEOFF"
    assert "权衡" in text


def test_resume_interpretation_does_not_overclaim_nonsignificant_success() -> None:
    code, text = _resume_interpretation(
        success_delta_pp=4.0,
        success_direction_supported=False,
        margin_direction_supported=True,
        pitch_direction_supported=True,
    )
    assert code == "SUCCESS_POINT_ESTIMATE_UP_STABILITY_SUPPORTED"
    assert "未排除零" in text
