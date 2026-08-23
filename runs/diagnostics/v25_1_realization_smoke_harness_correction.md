# Runtime v25.1 realization-smoke harness correction

## Status

`REGISTERED_BEFORE_REPEAT_ISAAC_EXECUTION`.

This is a smoke-only diagnostic correction. The registered v25 runtime,
projection, config, gates, model, and promotion rule are unchanged.

Attempt001 established that a manually assigned phase integer does not
replace the live FSM reference posture. It also exposed action-state
contamination between two independent probes.

The corrected harness:

- moves the live 50 mm reference progress to `upper(phase 8) - 1e-6`;
- calls the real reference-bank update and requires the resulting phase to
  be 8;
- clears the phase-exit and corrective-latch state;
- processes exact zero first to establish the same-reference baseline;
- applies the registered floor probe and records the per-leg IK-valid
  vector, IK-invalid-count delta, requested and final wheel-center deltas,
  and front-right servo delta; and
- restores the original high-drive `projection_probe` before the
  independent phases 7--11 direction check.

Compilation and all 157 tests pass.

## Frozen hashes

- Unchanged raw common config:
  `ff56415597dd45fbe9c755c68c44b7332735638dab0bd27d76b7f9bd81ab8f58`
- Unchanged canonical common config:
  `261a31c92a3d8e5d39309a86a944e42de4a9a04854c200883dbe1d61cb808653`
- Corrected `train_residual_ppo.py`:
  `18f4bc0cfcd4d2d8712ffdd7afb7711511c4c3c68f462e066e31b42dde81ea51`

No repeat-smoke Isaac result exists at registration time.
