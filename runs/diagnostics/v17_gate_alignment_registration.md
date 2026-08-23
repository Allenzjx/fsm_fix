# Runtime-v17 gate-aligned exploration registration

Registered before any v17 training or evaluation.

## Evidence

Runtime v16 and its pre-registered distinct checkpoints reached 8/20,
10/20, 10/20, and 9/20 on the fixed 50 mm development set. The final
checkpoint retained active-channel standard deviations near 0.07, so the
four-channel shared signed drive had training-time standard deviation
0.03503. Estimated stochastic gate-on probability stayed near 38--41% in
every deterministic outcome group even though the deterministic gate was
off in 71.68% of execution-window rows. The four checkpoint policies did
not learn a stable conditional gate separator.

The reward and physical projection remain unchanged. Positive gate
occupancy is not itself treated as a target because checkpoint 60800's
failure group opened more often than its success group.

## Single mechanism change

V17 introduces a deterministic-gate-aligned exploration envelope:

- initial and maximum per-action `log_std = -4.0`;
- minimum per-action `log_std = -5.0`;
- PPO entropy loss scale `0.0`.

At the maximum, independent active-channel standard deviation is
`exp(-4) = 0.0183156`. The mean of four signed channels has standard
deviation `exp(-4)/2 = 0.00915782`, corresponding to `0.0915782 mm` under
the unchanged 10 mm physical bound. At zero deterministic mean, the
expected positive noise-only residual is `0.0365328 mm`. Residuals large
enough to affect traversal must therefore be encoded in the deterministic
state-conditioned mean rather than supplied mainly by rollout noise.

The network widths, zero mean initialization, action projection and bounds,
phase window and gains, reward weights, training randomization, optimizer,
budget, curriculum gates, frozen FSM, metrics, asset, and B/C ablation
difference remain unchanged.

## Execution order and gates

1. Unit tests and CPU policy smoke must pass.
2. A one-environment real-Isaac training smoke must prove finite sampled
   actions, exact safety projection, and recorded v17 provenance.
3. Only then is one from-scratch Method-B seed-11 50 mm run authorized for
   exactly 76,800 local timesteps in 64 environments.
4. The final checkpoint must pass a deterministic restore smoke, followed
   by all 20 fixed 50 mm development scenarios with the unchanged 16/20
   promotion threshold.

An old checkpoint deterministic counterfactual is deliberately omitted:
checkpoint loading overwrites `log_std_parameter`, and deterministic
evaluation consumes `mean_actions`, so changing only the exploration
envelope cannot alter an already-trained checkpoint's deterministic
actions. Such a run would provide no evidence about the v17 mechanism.

No validation or locked-test scenario result may be used during these
steps.
