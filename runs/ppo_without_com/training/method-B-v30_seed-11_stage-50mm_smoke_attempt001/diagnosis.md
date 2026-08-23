# Method-B v30 composite realization smoke attempt001

## Disposition

`PASS`.

The complete real-Isaac probe verifies:

- wheel-center FR/RL floor actions remain -0.3/-0.4/-0.3 in phases
  8/9/10 and physically realize -3/-4/-3 mm;
- physical-forward wheel-speed residual is exact zero in phases 8/10;
- phase-9 physical-forward residual is
  `[-0.040000003,+0.040000003,-0.040000003,+0.040000003] rad/s`;
- the realized physical command delta is
  `[-0.039999992,+0.039999992,-0.039999992,+0.039999992] rad/s`;
- after the registered wheel-joint sign mapping, all four raw actuator
  target deltas are `+0.039999992 rad/s`;
- all four legs are IK-valid in all three phases and every rollback
  increment is zero.

All phase authorization, action-mask, bounds, direction, historical
climb, exact-zero, reward, finite, terminal, reset, and provenance audits
pass.

## Artifacts

- Result:
  `2ae156db7ddcbe620f9c3ac70ac337cd37ae50de03e259a019778397a2c4c941`
- Stdout/stderr:
  `e1ba78dfb776c976e37eaf727cbc26a501b55029381de4ac8b5f2fe33f3e1672`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Executed environment Python PID `143984` exited naturally.

## Next action

Restore the exact v19 final checkpoint under v30 and require canonical
stride-3 exact-zero telemetry before the full counterfactual.
