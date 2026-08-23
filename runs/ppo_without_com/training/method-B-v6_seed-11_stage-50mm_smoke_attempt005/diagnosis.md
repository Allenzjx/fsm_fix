# Method-B reward-v6 seed-11 50 mm smoke attempt005 diagnosis

## Disposition

`PASS`. This smoke authorizes a new Method-B seed-11 50 mm reward-v6
from-scratch full-budget training attempt.

## Real-Isaac evidence

- 16 parallel environments; actor 16x96; critic 16x146; action 16x12.
- Finite observations, critic values, policy actions, contacts, rewards, and
  two-environment partial reset.
- Exact zero-residual equivalence passed.
- All 22 registered runtime raw reward terms were present and finite at control
  `step_dt=0.016666666666666666` s.
- The isolated 1.4 rad tilt stimulus produced `terminated=true`, terminal fall
  snapshot `true`, raw fall term `1.0`, weighted fall term `-200.0`, and finite
  total reward `-200.19393920898438`.
- Direct full-randomization provenance records distance ±0.025 m, pitch
  ±0.020 rad, friction 0.90--1.20, delay 0--2 control steps, and sensor noise
  0--0.005.
- Frozen FSM SHA-256 remains
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`;
  frozen metrics SHA-256 remains
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`;
  reward-v6 common config SHA-256 is
  `c416ea5ad8dc4836f5f97d3e9da95869baea5cc25a6008edfa1c233f972c2a32`.

Exact executed source hashes:

- `reward.py`:
  `b50f0cde377bb4aa75f509e8bc7b4fcae9199e60f6df6a9d9276212659480000`
- `residual_rl_env.py`:
  `6389bfadfa04d664f2619cbde9cd95768fbf2506819b05974ab8d4235702a8cb`
- `ppo_models.py`:
  `33eb36ba2f7cbbf9f5a18e7197c26addc518e18f80f2d91f6c5bc733256f4b34`
- `train_residual_ppo.py`:
  `1839fae91ac4e172c8c5befac6ec59c19f64c850dcd4a3f59ce21aeb14a8577d`

The immutable `training_result.json` SHA-256 is
`40b68763b12034f7da7feb1eec39b2e5187f4d0461e61c6fbc511f91d69cc2f5`;
its no-optimization TensorBoard event SHA-256 is
`797c8cd24732390eeadbb178e8a6cd19840c8ad60d1ce4eb0222556350724f6c`.

## Authorized next action

Train from random initialization for exactly 300 iterations x 64 rollouts =
19,200 local timesteps and 1,228,800 transitions using 64 environments and
the registered full randomization. No v5 checkpoint may be loaded.
