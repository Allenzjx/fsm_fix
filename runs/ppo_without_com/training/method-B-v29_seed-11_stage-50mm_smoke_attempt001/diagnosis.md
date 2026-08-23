# Method-B v29 phase-selective realization smoke attempt001

## Disposition

`RUNTIME_PASS_AUDIT_COVERAGE_INCOMPLETE`.

The runtime itself passes every implemented preflight check:

- phase gains/floor provenance is `[3,4,3] / 0.1`;
- the high-drive projection is exactly 6/8/6 mm in phases 8/9/10;
- the phase-8 floor requests and physically realizes -3 mm on
  front-right and rear-left;
- all four legs are IK-valid, rollback delta is zero, and FR/RL servo
  changes are 0.01647520/0.01961753 rad.

However, the attempt001 preflight directly realizes only the phase-8
floor. It proves unequal phase gain at high drive but does not directly
realize the phase-9 and phase-10 minimum-floor targets. The v29 smoke gate
therefore remains open despite the internal `SMOKE_PASS` status.

## Corrective action

The preflight audit is extended, without changing runtime behavior or
configuration, to apply a sub-floor positive actor probe independently in
phases 8, 9, and 10 and require:

- exact applied 3/4/3 mm floor actions;
- exact requested and final wheel-center deltas;
- all-leg IK validity;
- zero IK-invalid/rollback increment.

Attempt002 is required under the amended preflight source hash.

## Artifacts

- Result:
  `ecd63bea90ce8e21b82b459b51b4c5479e46b085c50c4d262146e9477dc9f4ac`
- Stdout/stderr:
  `ec059fa9432a030233d45b61e6a4b008358601ee8e7a93357dc5df0fdb1bbbaf`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Executed preflight source:
  `c6469a6efed3116184e3ae2ee15d34bb8a1902146d45613d1bc720c3692ace47`
