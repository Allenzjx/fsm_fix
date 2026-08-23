# Method-B v26 seed-11 50 mm asymmetric realization smoke attempt001

## Disposition

`SMOKE_PASS`. This is an implementation gate only.

- The live 50 mm reference bank was sampled at FSM phase 8, normalized
  progress `0.87999898`, immediately below the held phase upper boundary.
- The exact high-drive and floor z actions were
  `[0,-0.6,+0.48,0]` and `[0,-0.3,+0.24,0]`.
- Requested wheel-center z deltas were
  `[0,-0.0029999986,+0.0024000034,0] m`.
- Per-leg IK validity was `[true,true,true,true]`; the residual IK-invalid
  counter did not increase.
- Final wheel-center z deltas were
  `[0,-0.0029999986,+0.0023999885,0] m`.
- Front-right and rear-left maximum servo-target changes were respectively
  `0.01647520 rad` and `0.01590106 rad`.
- Every inactive x/z coordinate was requested at exact zero.
- Nominal zero, slow-pitch historical climb/phase-9 zero, positive-roll and
  early roll/rate gates, latch/floor, opposite actor half-space, phase
  exclusion, phase exit, bounds, finite interfaces, terminal safety,
  partial reset, and post-terminal reset checks passed.

## Artifacts

- Result:
  `c7ba6128b005ac7ff366934756883494dfcaab20bc96e3224b8181603a65581d`
- Stdout/stderr:
  `1a0027dd0575dbfdf439bd85a3476654da86c205905a1fe70804dfb2b995d101`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `98900`; it exited naturally.

## Next action

Restore the explicit v19 final checkpoint under v26. Nominal execution must
remain exact zero and canonical 100x122 telemetry must remain byte-stable
before the full development counterfactual is authorized.
