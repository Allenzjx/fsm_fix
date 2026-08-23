# Method-B v20/v19-checkpoint 50 mm counterfactual attempt001

## Disposition

`EXECUTION_PASS`, `PERFORMANCE_FAIL`, `12/20 < 16/20`.

The explicit v19 final checkpoint completed all 20 unchanged deterministic
50 mm development scenarios under the registered v20 runtime. The run
retained every frozen-FSM success but rescued no frozen-FSM failure. In
particular, reversing the executed direction lost v19's sole additional
success, scenario `0009`.

- Successes: `0000, 0001, 0002, 0004, 0007, 0010, 0011, 0012, 0014,
  0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0008, 0009`.
- FSM phase timeouts: `0013, 0017, 0019`.
- Mean episode minimum margin: `-0.2810706794 m`.
- Mean pitch-rate RMS: `0.0614325923 rad/s`.

## Constraint and numerical audit

- Telemetry is `52,560 x 122`.
- The only non-finite field is the semantically undefined `margin_m`
  (`5,854` rows). Every action, state, contact, target, and reference value
  is finite.
- Maximum raw policy action is `0.18966709`; maximum executed normalized
  action is `0.03313052`, or `0.33130520 mm` under the fixed 10 mm bound.
- Exactly `2,386` rows execute nonzero residuals. All are among the `2,387`
  registered phase-8/9 rows at pitch at least `+0.09 rad`.
- Unauthorized nonzero rows, phase-7 nonzero rows, and below-threshold
  phase-8/9 nonzero rows are all zero.
- Masked x/wheel-speed channels, bilateral tie error, four-wheel balance,
  and the front-positive/rear-negative corrective-sign error are exactly
  zero.
- Nonzero execution occurs only in environments `5, 6, 8, 9, 13, 17, 19`.
  The 12 frozen-FSM success trajectories remain physically exact.

## Mechanism diagnosis

V20 isolates the output-direction question. Its corrective reversal is
well-formed and executes only on the intended high-positive-pitch branches,
but it is not by itself a viable recovery controller at the inherited
checkpoint's small action magnitude. It removes the climb-direction effect
that rescued scenario `0009`, while the late `+0.09 rad` gate gives the
remaining collision branches only about `0.10--0.45 s` of authority before
termination.

Frozen-FSM telemetry supports one coherent next mechanism: a phase-aware
emergency recovery state machine. Phase 8 is still rear transfer and should
retain the v19 climb direction; phases 9--10 are post-transfer and may use
the pitch-corrective direction. In phase 8, the causal IMU precursor
`pitch >= +0.04 rad` and `pitch_rate >= +0.35 rad/s` occurs only on frozen
failure trajectories `0005, 0006, 0008, 0019`, never on a frozen success,
and opens authority earlier than the existing pitch threshold. Phase 10 at
`pitch >= +0.09 rad` likewise selects only failed scenario `0003` in the
frozen trajectories.

V20 training is prohibited. Any v21 changes must be registered before an
Isaac run and must pass smoke, explicit-checkpoint restore, and the fixed
20-scenario counterfactual gate before retraining.

## Artifacts

- Result:
  `c12d03cfc91959d69ba87bf74fa69dc01f01794b6c77d32297b36057e44660c0`
- Episodes:
  `4705caf2fa92686147f2a759224899dedf6b86f40cc544c1b6d4b53d17486906`
- Status:
  `2c9326563d50acf4f3d1c389329251718a148d125beaf876c01d12f78cef819e`
- Telemetry:
  `aa6e05854900cd1169a1defa16add8a506d7d5f951823ae603f2ee290d998c5d`
- Stdout/stderr:
  `be4fb238bfbe741e987c77952f4978d4dd1af3230d769e6553b985be0a14927f`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

## Next action

Register v21 from frozen-trajectory evidence, including its exact phase
logic, IMU thresholds, gain, signs, and retraining authorization rule before
running Isaac.
