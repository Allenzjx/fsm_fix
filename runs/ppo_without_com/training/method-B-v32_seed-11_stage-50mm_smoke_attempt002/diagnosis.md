# V32 corrected smoke attempt002 audit

## Disposition

`SMOKE_PASS`.

The corrected v32 runtime passed the complete real-Isaac preflight:

- physical-forward wheel-speed residual is exactly
  `[-0.100000001,+0.100000001,-0.100000001,+0.100000001] rad/s`
  in both phases 8 and 9;
- physical wheel-command deltas are
  `[-0.099999994,+0.099999994,-0.099999994,+0.099999994] rad/s`;
- raw joint-target deltas are all `+0.099999994 rad/s`, confirming the
  actuator sign mapping;
- phase 10 wheel-speed residual is exact zero;
- phases 8/9/10 retain 3/4/3 mm deficient-diagonal downward support;
- all four legs are IK-valid in every probed phase, with zero IK-invalid
  increments and no rollback;
- phase-selective realization, rapid-rise latch, zero-preservation, and
  final-target realization audits all pass.

The smoke performed no PPO optimization and does not count as evaluation.

## Frozen evidence

- `training_result.json`:
  `1e65fd9c5152f3f9a8439afefc4822738406a7f2475cfaa24cacad205e9c568d`
- stdout:
  `a01fce8e1616d6bb21298849439f61c802fc41a01110f5e949bea903ca969c75`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

The next mandatory gate is exact v19 checkpoint restoration with canonical
exact-zero telemetry.

