"""Canonical config hashing regressions."""

from __future__ import annotations

from resume_validation.config_io import canonical_json, config_sha256


def test_canonical_config_hash_is_key_order_independent() -> None:
    left = {"b": [2, 3], "a": {"y": False, "x": 1}}
    right = {"a": {"x": 1, "y": False}, "b": [2, 3]}
    assert canonical_json(left) == canonical_json(right)
    assert config_sha256(left) == config_sha256(right)


def test_canonical_config_hash_changes_with_a_value() -> None:
    assert config_sha256({"value": 1}) != config_sha256({"value": 2})
