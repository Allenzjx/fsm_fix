# Method-B v22 seed-11 50 mm runtime smoke attempt001

## Disposition

`SMOKE_PASS`. This is an implementation gate only.

The real-Isaac training entrypoint verified the registered v22 latch and
emergency-floor semantics:

- Nominal pitch `-0.02244199 rad` produced exact-zero physical residual.
- A slow `+0.10 rad` probe produced phase-8 climb and phase-9/10
  correction, with phase-7/11 exact exclusion.
- A `+0.05 rad`, `+0.40 rad/s` rapid-rise probe triggered phase-8
  correction.
- After setting pitch rate back to zero and reducing positive shared drive
  from `0.2` to `0.05`, phase-8 correction remained latched and executed
  exactly `0.1` pre-gain / `0.3` normalized / `3 mm`.
- Entering phase 9 below `+0.09 rad` cleared the phase-8 latch and executed
  exact zero.
- Opposite actor drive remained exact zero. Masks, bilateral ties,
  four-wheel balance, hard bounds, finite interfaces, one-shot terminal
  safety, partial reset, and post-terminal reset all passed.

## Artifacts

- Result:
  `d965b9f20fc4afd64d02d6aeb277a008e1a61cb2c8a311fa079f2f4617a1d59a`
- Stdout/stderr:
  `5805f8aafed101a4002ec86d398214e78428638e5e4581f23dd725faa7bfd94f`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `38728`; it exited naturally.

## Next action

Restore the explicit v19 final checkpoint under v22 in a deterministic
one-scenario development smoke, then run the unchanged counterfactual only
if restore provenance and numerical checks pass.
