# Method-B runtime-v8 seed-11 50 mm training attempt001

## Disposition

`PASS_TRAINING_INTEGRITY`. This is a completed training artifact, not
curriculum promotion.

- Exact budget: 19,200/19,200 local timesteps and
  1,228,800/1,228,800 transitions across 64 environments.
- Explicit final checkpoint SHA-256:
  `8a5b9520dad5ecc928623da2d52e5bf08b44611db6fd985bed93f949fb243ae2`.
- The final checkpoint contains 77 tensors and 785,093 elements; every
  element is finite.
- `training_result.json` SHA-256:
  `69fbbcb6efc63b67ee4837813baee7b3a55d6a997bf7e689eb912112899dc243`.
- TensorBoard event SHA-256:
  `2a9491b4d4317c2065363db4e9fb06943b08dc2e3d43965d03a84d885f79efd0`.
- Environment Python PID `92964` exited normally.

## Training evidence

All 11 optimization/runtime scalar series contain exactly 300 finite updates
from timestep 64 through 19,200. All six locally repaired episode series are
finite and contain 40 update windows. Recorded episode lengths range from
3,814 to 8,999 steps; the prior false 168-step env-0 display segment did not
recur.

The run observed both sides of the registered objective:

- 15 logging windows contained a real approximately +200 success term;
- 24 logging windows contained a real approximately -200 safety termination
  term;
- policy standard deviation fell from at most 0.13499 to 0.09774;
- the best observed completed-episode return window improved to about
  -446.39 while all values remained finite.

These rolling training signals do not establish development performance and
are not used for checkpoint selection. The skrl-generated `best_agent.pt` is
ignored. Eligibility uses only the explicit final checkpoint in the
independent deterministic evaluator.

## Provenance

The run directly recorded the common phase window `[2, 9]`, integrated
residual weights `-120/-180`, full 50 mm randomization, exact source hashes,
and the unchanged frozen FSM/metrics/asset hashes. It started from random
initialization and reused no v7 checkpoint.

## Next action

Restore the explicit final checkpoint in a one-scenario, five-second
development evaluator smoke. Verify checkpoint/config/source hashes, phase
gate provenance, and the complete action-to-actuator telemetry before the
unchanged 20-scenario 150-second development gate.
