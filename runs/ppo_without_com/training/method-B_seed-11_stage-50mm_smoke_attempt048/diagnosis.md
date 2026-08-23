# Method B seed-11 50 mm smoke attempt 048 diagnosis

- Status: `FAILED` during the post-Trainer `agent.act` preflight.
- Failure: IsaacLab's integer `action_space` declaration produced an unbounded
  `Box(-inf, inf, (12,))`. Local skrl 2.0 correctly initialized that as an
  unbounded model action space, so `GaussianMixin` retained `None` clip bounds
  and PyTorch rejected `torch.clamp`.
- The residual environment's actual command contract is normalized: it
  clamps all 12 residual actions to `[-1, 1]` before scaling and records
  saturation against those exact bounds. Leaving PPO sampling unbounded would
  also make stored log-probabilities disagree with the executed environment
  action whenever a sample exceeded the contract.
- Fix: `ResidualPolicy` now exposes an internal finite
  `Box(-1, 1, (12,))` to `GaussianMixin`, preserving the environment's true
  residual semantics while leaving the public Isaac action tensor shape
  unchanged. A regression constructs the policy from an unbounded
  environment action space and verifies finite, bounded samples.
- Training-result SHA-256:
  `f67fccdefa5f44998bdfb18fa53444ee799393c55001233ccbcee1494f70fb66`.
- Post-fix unit suite: 112 passing tests.

No checkpoint exists and this run contributes zero training transitions.
Retry uses smoke attempt 049.
