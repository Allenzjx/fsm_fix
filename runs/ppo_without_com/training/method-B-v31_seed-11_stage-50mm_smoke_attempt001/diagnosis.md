# Method-B v31 bound counter-yaw smoke attempt001

## Disposition

`PASS`.

The complete real-Isaac probe verifies:

- wheel-center FR/RL floor actions remain -0.3/-0.4/-0.3 in phases
  8/9/10 and physically realize -3/-4/-3 mm;
- physical-forward wheel-speed residual is exact zero in phases 8/10;
- phase-9 physical-forward residual is
  `[-0.100000001,+0.100000001,-0.100000001,+0.100000001] rad/s`;
- the realized physical command delta is
  `[-0.099999994,+0.099999994,-0.099999994,+0.099999994] rad/s`;
- after the registered wheel-joint sign mapping, all four raw actuator
  target deltas are `+0.099999994 rad/s`;
- normalized post-gain wheel-speed actions are exactly
  `[-1,+1,-1,+1]`, at but not beyond the configured hard bound;
- all four legs are IK-valid in all three phases and every rollback
  increment is zero.

All phase authorization, independent z/speed floor, action-mask, bound,
direction, historical climb, exact-zero, reward, finite, terminal,
reset, and provenance audits pass.

## Artifacts

- Result:
  `db0f2004065d94a2df3c30c45638b1429aaf9f30976b5e006b8558adf1479ad2`
- Stdout/stderr:
  `e483cd3475f3dcca6dd98535f5d5dafd44b7022c722bc16717d006e01afd55c4`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Executed environment Python PID `170064` exited naturally.

## Next action

Restore the exact v19 final checkpoint under v31 and require canonical
stride-3 exact-zero telemetry before the full development
counterfactual.
