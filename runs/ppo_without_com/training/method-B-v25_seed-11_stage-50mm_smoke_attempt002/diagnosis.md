# Method-B v25 seed-11 50 mm realization smoke attempt002

## Disposition

`SMOKE_PASS`. This is an implementation gate only.

- The live 50 mm reference bank was sampled at FSM phase 8, normalized
  progress `0.87999898`, immediately below the held phase upper boundary.
- The exact floor action was `[0,-0.3,0,0]`; all x and wheel-speed channels
  and every non-front-right z channel were exact zero.
- Requested front-right wheel-center z changed by
  `-0.0029999986 m`.
- Per-leg IK validity was `[True,True,True,True]`; the residual IK-invalid
  counter did not increase.
- Final front-right wheel-center z changed by the same
  `-0.0029999986 m`, and the front-right servo target changed by
  `0.01647520 rad`.
- The independent high-drive probe produced exact
  `[0,-0.6,0,0]` in phases 8--10 and exact zero in phases 7/11.
- Nominal zero, slow-pitch historical climb/phase-9 zero, early gate,
  latch/floor, opposite actor half-space, phase exit, bounds, finite
  interfaces, terminal safety, partial reset, and post-terminal reset
  checks passed.

## Artifacts

- Result:
  `93d939290c18b77240a9f31221bde0a5ddcd84c9b2025178f1691de104ecce07`
- Stdout/stderr:
  `2d492952959c6f6ff294fccc47cf3f2bf0b973551f9bcb5af8d225ff187335eb`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `125708`; it exited naturally.

## Next action

Restore the explicit v19 final checkpoint under v25. The nominal restore
must remain exact-zero and byte-stable before a full counterfactual is
authorized.
