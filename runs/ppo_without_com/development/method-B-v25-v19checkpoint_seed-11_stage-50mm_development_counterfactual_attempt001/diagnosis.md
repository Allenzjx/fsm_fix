# Method-B v25/v19-checkpoint 50 mm counterfactual attempt001

## Disposition

`EXECUTION_PASS`, `PHYSICAL_REALIZATION_PASS`, `PERFORMANCE_FAIL`,
`13/20 < 16/20`.

The unchanged v19 final checkpoint completed all 20 fixed deterministic
50 mm development scenarios under v25. It retained all 12 frozen-FSM
successes and scenario `0009`, but rescued no additional scenario.

- Successes: `0000, 0001, 0002, 0004, 0007, 0009, 0010, 0011, 0012,
  0014, 0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0017, 0019`.
- FSM phase timeouts: `0008, 0013`.
- Relative to v24, `0008` and `0013` changed from collision to timeout,
  while `0019` changed from timeout to collision. The success set did not
  change.

V25 training is prohibited.

## Constraint and physical-realization audit

- Telemetry is `51,831 x 122`.
- Only semantically undefined `margin_m` is non-finite (`5,854` rows).
  Every action, state, contact, requested target, final target, and reference
  field is finite.
- Maximum raw policy action is `0.18966709`; maximum executed normalized
  action is `0.30000001`, or `3.00000003 mm`. Wheel-speed residual is exact
  zero.
- There are `1,615` nonzero rows: `340` in phase 8, `1,262` in phase 9,
  and `13` in phase 10. They contain `13` historical climb rows and `1,602`
  exact front-right floor rows.
- Every nonzero row satisfies the registered phase/IMU/latch authority.
  Disabled channels, front-right-only structure, climb balance, scaling,
  bounds, and finite checks pass with no violation.
- All `1,602` front-right requests are exact -3 mm. All `1,602` change the
  final target; coupled IK rollback count is zero. Final-to-request error is
  at most `4.47e-8 m`.
- All 13 success trajectories are exact across 34,800 rows and all 56
  shared physical/state/contact/reference/time fields versus v24.

## Mechanism diagnosis

Front-right-only execution is real and changes the failure dynamics, but it
cannot restore the complete deficient diagonal:

- All seven failures still end with
  `[FL=True, FR=False, RL=False, RR=True]`.
- Five collisions are still on `front_right_bot`.
- Both front-right and rear-left upward support are zero or numerical zero
  at terminal failure.
- Long front-right execution delays `0008` and `0013` into phase timeout,
  proving causal trajectory effect, but does not create rear-left support.

With the front-right -3 mm request fixed, exact IK reconstruction on the
1,602 v25 corrective baselines gives a minimum safe rear-left positive-z
limit of `2.700939 mm`; +2.7 mm is valid on 1,602/1,602 rows while +3.0 mm
is valid on 0/1,602. The same +2.7 mm test is valid on all 863 v24 source
rows.

The next isolated candidate is therefore an asymmetric corrective scale
`[0,-1,+0.8,0]`: front-right -3.0 mm plus rear-left +2.4 mm. The 0.8 scale
keeps a 0.300939 mm margin below the worst measured boundary, retains the
physically effective front-right request, and restores rear-left action.

Before any new Isaac run, the scale vector must be pre-registered and a
real-Isaac smoke must prove all-leg IK validity and both final-target/servo
changes. V25 training remains prohibited.

## Artifacts

- Result:
  `5b3ed2142b2b61dcfb8698ad6845c218df25b5a2cae6affb3f14e5159b33581c`
- Episodes:
  `5c2cf1043c8ac1354ca16649a1384cfe173980d005b911c4c512270472eba8b4`
- Status:
  `f070b82e0b965831df6991994a001d327f0b8b9d25c40a26b957412650ebc51e`
- Telemetry:
  `270a706251a02aede774334a0f5bfe9fa7f56ad823bc771215fc2f6bd83d61d8`
- Stdout/stderr:
  `e7cfc0676d3fdf09c4ac429e47dc60f39eb9947c7aa8639236edefd8a913e1f2`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
- Environment Python PID: `164680`; it exited naturally.

## Next action

Freeze and register v26 asymmetric `[0,-1,+0.8,0]`, then require action
structure and two-leg final-target realization smoke before restore/eval.
