# Method-B runtime-v7 seed-11 50 mm training attempt001

## Disposition

`PASS_TRAINING_INTEGRITY`. This is a completed training artifact, not
curriculum promotion.

- Exact budget: 19,200/19,200 timesteps and 1,228,800/1,228,800 transitions.
- Final checkpoint SHA-256:
  `0f00a8207fff1fb096f9124f4e9b0df47cae9d9d579914913f47ef5f90ab704d`.
- 77 checkpoint tensors, 785,093 elements, all finite.
- All 17 TensorBoard scalar series are finite. The 11 optimization/runtime
  series each contain exactly 300 updates through timestep 19,200.
- `training_result.json` SHA-256:
  `5a374faf6d600382ffa7241ec813a50bb595bc1bdd0038224044d4ef865f54fa`.
- TensorBoard event SHA-256:
  `39f58af1216e3b467d8395bb55a6845effdb05bd7d5775bfd75fa9d6f863f53b`.

## Tracker limitation

skrl 2.0's display-only episode tracker uses the full two-column output of
`[N,1].nonzero()` to reset `[N,1]` cumulative arrays. The constant column
index zero therefore also clears environment 0 whenever any environment
ends. This corrupts the six rolling `Reward / Total reward` and
`Episode / Total timesteps` series, including the apparent 168-step segment.
It does not alter environment rewards, PPO memory, GAE, losses, parameter
updates, or the explicit final checkpoint.

Performance eligibility must therefore come only from the independent
development evaluator's per-scenario results and terminal snapshots. The
skrl “best” checkpoint is ignored. The next training revision will repair the
local tracker without modifying the installed package.

## Next action

Restore the exact final checkpoint in a one-scenario, five-second development
evaluator smoke. Verify checkpoint/config/source hashes and complete action
telemetry, then run the unchanged 20-scenario 150-second development gate.
