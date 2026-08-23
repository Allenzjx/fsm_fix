from __future__ import annotations

import torch


def advance_episode_accumulators(
    previous_rewards: torch.Tensor | None,
    previous_timesteps: torch.Tensor | None,
    rewards: torch.Tensor,
    terminated: torch.Tensor,
    truncated: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Advance display accumulators and reset only finished environment rows.

    skrl 2.0 uses the complete two-column result of ``[N, 1].nonzero()`` as
    an index into another ``[N, 1]`` tensor. The constant column index zero
    consequently resets environment 0 whenever any environment finishes.
    This helper retains the intended first-axis semantics. It is deliberately
    display-only and does not touch rollout memory.
    """

    if rewards.ndim == 0:
        raise ValueError("rewards must have an environment dimension")
    if terminated.shape != rewards.shape or truncated.shape != rewards.shape:
        raise ValueError("reward, terminated, and truncated shapes must match")
    if (previous_rewards is None) != (previous_timesteps is None):
        raise ValueError(
            "previous reward and timestep accumulators must both exist or both be None"
        )

    if previous_rewards is None:
        cumulative_rewards = torch.zeros_like(rewards, dtype=torch.float32)
        cumulative_timesteps = torch.zeros_like(rewards, dtype=torch.int32)
    else:
        if (
            previous_rewards.shape != rewards.shape
            or previous_timesteps.shape != rewards.shape
        ):
            raise ValueError("previous accumulator shapes must match rewards")
        cumulative_rewards = previous_rewards.clone()
        cumulative_timesteps = previous_timesteps.clone()

    cumulative_rewards.add_(rewards)
    cumulative_timesteps.add_(1)
    done_rows = torch.logical_or(terminated.bool(), truncated.bool()).reshape(
        rewards.shape[0], -1
    ).any(dim=1)
    cumulative_rewards[done_rows] = 0
    cumulative_timesteps[done_rows] = 0
    return cumulative_rewards, cumulative_timesteps
