# Method B seed-11 50 mm training attempt002 diagnosis

- Status: `FAILED` after the 6,400-timestep checkpoint and before the next
  rollout boundary.
- Last durable checkpoint:
  `checkpoints/agent_6400.pt`, SHA-256
  `e1779b119ac64879ffe87ac4bba6130a55345695bbcb7cc8fdd7a3f598e9e4a8`.
  Its 77 stored tensors are all finite.
- Training-result SHA-256:
  `e41fbd10c9c371a8dcf93896f2ea61e5e0f4af6663c276d6e917b53571839a4f`.
- At the 6,400-step boundary TensorBoard recorded finite optimization values:
  mean instantaneous reward `0.693764925`, policy loss `0.010073660`,
  value loss `0.0000940221`, policy standard deviation `0.134198368`, and
  adaptive learning rate `0.0000592593`.
- Failure: two environments terminated together. The partial-reset path
  combined two selected root heights with the complete 64-element
  `_estimated_wheel_radius` tensor, causing a `2` versus `64` shape mismatch.
  The initial all-environment reset had hidden the error because both shapes
  were 64.
- Fix: index the per-environment wheel radius with the same `env_ids`. The
  smoke path now forcibly exercises a two-environment partial reset and checks
  the resulting root poses for finite values. A regression brings the suite to
  113 passing tests.
- Recovery rule: only the durable 6,400 timesteps count. Approximately 45
  later, uncheckpointed steps are discarded. A successful retry must load the
  exact hashed checkpoint and execute the remaining 12,800 timesteps, yielding
  the original registered total of 19,200 timesteps and 1,228,800 parallel
  transitions.

No incomplete or failed artifact was deleted.
