from __future__ import annotations

import pytest
import torch

from resume_validation.episode_tracking import advance_episode_accumulators


def test_only_finished_environment_rows_are_reset() -> None:
    previous_rewards = torch.arange(8, dtype=torch.float32).reshape(8, 1)
    previous_timesteps = torch.arange(10, 18, dtype=torch.int32).reshape(8, 1)
    rewards = torch.ones((8, 1), dtype=torch.float32)
    terminated = torch.zeros((8, 1), dtype=torch.bool)
    truncated = torch.zeros_like(terminated)
    terminated[5] = True
    truncated[7] = True

    cumulative_rewards, cumulative_timesteps = advance_episode_accumulators(
        previous_rewards,
        previous_timesteps,
        rewards,
        terminated,
        truncated,
    )

    assert cumulative_rewards[0].item() == pytest.approx(1.0)
    assert cumulative_timesteps[0].item() == 11
    assert cumulative_rewards[5].item() == pytest.approx(0.0)
    assert cumulative_timesteps[5].item() == 0
    assert cumulative_rewards[7].item() == pytest.approx(0.0)
    assert cumulative_timesteps[7].item() == 0
    assert cumulative_rewards[6].item() == pytest.approx(7.0)
    assert cumulative_timesteps[6].item() == 17


def test_initial_accumulators_and_shape_validation() -> None:
    rewards = torch.tensor([[1.5], [-2.0]], dtype=torch.float32)
    done = torch.tensor([[False], [True]])
    cumulative_rewards, cumulative_timesteps = advance_episode_accumulators(
        None,
        None,
        rewards,
        done,
        torch.zeros_like(done),
    )
    torch.testing.assert_close(cumulative_rewards, torch.tensor([[1.5], [0.0]]))
    torch.testing.assert_close(
        cumulative_timesteps,
        torch.tensor([[1], [0]], dtype=torch.int32),
    )

    with pytest.raises(ValueError, match="shapes must match"):
        advance_episode_accumulators(
            None,
            None,
            rewards,
            done.reshape(2),
            torch.zeros_like(done),
        )
