"""Shared skrl model definitions for training and deterministic evaluation."""

from __future__ import annotations

import gymnasium as gym
import numpy as np
import torch
from torch import nn
from skrl.models.torch import DeterministicMixin, GaussianMixin, Model

ACTOR_HIDDEN = (256, 256, 128)
CRITIC_HIDDEN = (256, 256, 128)
INITIAL_LOG_STD = -4.0
MIN_LOG_STD = -5.0
MAX_LOG_STD = -4.0


def flat_dim(space: gym.Space) -> int:
    return int(gym.spaces.flatdim(space))


class ResidualPolicy(GaussianMixin, Model):
    def __init__(self, observation_space, action_space, device):
        action_dim = flat_dim(action_space)
        normalized_action_space = gym.spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(action_dim,),
            dtype=np.float32,
        )
        Model.__init__(
            self,
            observation_space=observation_space,
            action_space=normalized_action_space,
            device=device,
        )
        GaussianMixin.__init__(
            self,
            clip_actions=True,
            clip_log_std=True,
            min_log_std=MIN_LOG_STD,
            max_log_std=MAX_LOG_STD,
            reduction="sum",
            role="policy",
        )
        self.net = nn.Sequential(
            nn.Linear(flat_dim(observation_space), 256),
            nn.ELU(),
            nn.Linear(256, 256),
            nn.ELU(),
            nn.Linear(256, 128),
            nn.ELU(),
        )
        self.mean = nn.Linear(128, action_dim)
        nn.init.zeros_(self.mean.weight)
        nn.init.zeros_(self.mean.bias)
        self.log_std_parameter = nn.Parameter(
            torch.full((action_dim,), INITIAL_LOG_STD)
        )

    def compute(self, inputs, role):
        observations = inputs["observations"]
        observations = observations.reshape(observations.shape[0], -1).to(
            self.device
        )
        mean = torch.tanh(
            self.mean(self.net(torch.clamp(observations, -20.0, 20.0)))
        )
        return mean, {"log_std": self.log_std_parameter.expand_as(mean)}


class ResidualValue(DeterministicMixin, Model):
    def __init__(self, state_space, action_space, device):
        Model.__init__(self, observation_space=state_space, action_space=action_space, device=device)
        DeterministicMixin.__init__(self, clip_actions=False, role="value")
        self.net = nn.Sequential(
            nn.Linear(flat_dim(state_space), 256),
            nn.ELU(),
            nn.Linear(256, 256),
            nn.ELU(),
            nn.Linear(256, 128),
            nn.ELU(),
            nn.Linear(128, 1),
        )

    def compute(self, inputs, role):
        states = inputs["states"]
        states = states.reshape(states.shape[0], -1).to(self.device)
        return self.net(torch.clamp(states, -20.0, 20.0)), {}
