# Method-B v29 phase-selective realization smoke attempt002

## Disposition

`PASS`.

The amended real-Isaac preflight proves the registered phase-selective
floor end to end:

- applied normalized FR/RL actions are -0.3/-0.4/-0.3 in phases 8/9/10;
- requested physical FR/RL deltas are
  -2.999999/-4.000001/-2.999999 mm;
- final physical deltas agree within `2.24e-8 m`;
- all four legs are IK-valid in all three phases;
- every per-phase IK-invalid/rollback increment is zero.

The independent phase-8 physical-realization probe also passes with exact
FR/RL -2.999999 mm requests/final targets and servo changes of
0.01647520/0.01961753 rad.

All runtime, action-mask, phase authorization, state-gate, historical
climb, zero-preservation, reward, terminal, reset, finite, and provenance
audits pass.

## Artifacts

- Result:
  `d8be7d77dc7ddd4b112ba6d0f5b4e0cdd08411ed63bdf42dea32963625c7df85`
- Stdout/stderr:
  `a24393b7eb4f5d19d391faf1b8c48140efd2e89f78cd1ff4d4765077469dd2c7`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Executed environment Python PID `113636` exited naturally.

## Next action

Restore the exact v19 final checkpoint under v29 and require canonical
stride-3 exact-zero telemetry before the full development counterfactual.
