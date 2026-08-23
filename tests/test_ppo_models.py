"""Initialization regressions for the shared B/C model architecture."""

from __future__ import annotations


def test_actor_starts_with_zero_deterministic_residual_and_recorded_std() -> None:
    import gymnasium as gym
    import numpy as np
    import torch

    from resume_validation.ppo_models import (
        INITIAL_LOG_STD,
        MAX_LOG_STD,
        MIN_LOG_STD,
        ResidualPolicy,
    )

    observation_space = gym.spaces.Box(-1.0, 1.0, shape=(96,), dtype=np.float32)
    action_space = gym.spaces.Box(-1.0, 1.0, shape=(12,), dtype=np.float32)
    policy = ResidualPolicy(observation_space, action_space, torch.device("cpu"))
    observations = torch.randn(7, 96)
    mean, metadata = policy.compute(
        {"observations": observations},
        role="policy",
    )
    assert torch.equal(mean, torch.zeros_like(mean))
    assert torch.equal(
        metadata["log_std"],
        torch.full_like(metadata["log_std"], INITIAL_LOG_STD),
    )
    assert policy._g_clip_log_std is True
    assert policy._g_min_log_std == MIN_LOG_STD == -5.0
    assert policy._g_max_log_std == MAX_LOG_STD == INITIAL_LOG_STD == -4.0


def test_actor_uses_observations_and_ignores_privileged_critic_state() -> None:
    import gymnasium as gym
    import numpy as np
    import torch

    from resume_validation.ppo_models import ResidualPolicy

    observation_space = gym.spaces.Box(-1.0, 1.0, shape=(96,), dtype=np.float32)
    action_space = gym.spaces.Box(-1.0, 1.0, shape=(12,), dtype=np.float32)
    policy = ResidualPolicy(observation_space, action_space, torch.device("cpu"))
    with torch.no_grad():
        policy.mean.weight.fill_(0.01)
    observations = torch.randn(5, 96)
    first, _ = policy.compute(
        {
            "observations": observations,
            "states": torch.randn(5, 146),
        },
        role="policy",
    )
    second, _ = policy.compute(
        {
            "observations": observations,
            "states": torch.randn(5, 146),
        },
        role="policy",
    )
    torch.testing.assert_close(first, second)


def test_actor_normalizes_unbounded_environment_action_space() -> None:
    import gymnasium as gym
    import numpy as np
    import torch

    from resume_validation.ppo_models import ResidualPolicy

    observation_space = gym.spaces.Box(-np.inf, np.inf, shape=(96,), dtype=np.float32)
    unbounded_action_space = gym.spaces.Box(
        -np.inf,
        np.inf,
        shape=(12,),
        dtype=np.float32,
    )
    policy = ResidualPolicy(
        observation_space,
        unbounded_action_space,
        torch.device("cpu"),
    )

    np.testing.assert_array_equal(policy.action_space.low, -np.ones(12))
    np.testing.assert_array_equal(policy.action_space.high, np.ones(12))
    actions = policy.act(
        {"observations": torch.randn(32, 96)},
        role="policy",
    )[0]
    assert torch.isfinite(actions).all()
    assert torch.all(actions >= -1.0)
    assert torch.all(actions <= 1.0)


def test_evaluator_restores_training_preprocessors_and_uses_mean_action() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "resume_validation"
        / "evaluate_controller.py"
    ).read_text(encoding="utf-8")
    make_agent = source.split("def _make_agent(env, checkpoint: Path):", 1)[1].split(
        "\n\ndef ", 1
    )[0]
    assert '"value_preprocessor": RunningStandardScaler' in make_agent
    assert '"value_preprocessor_kwargs": {"size": 1, "device": device}' in make_agent
    assert "agent.enable_training_mode(False, apply_to_models=True)" in make_agent
    assert 'actions = outputs["mean_actions"]' in source
