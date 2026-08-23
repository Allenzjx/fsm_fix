# Method-B v21/v19-checkpoint 50 mm counterfactual attempt001

## Disposition

`EXECUTION_PASS`, `PERFORMANCE_FAIL`, `13/20 < 16/20`.

The unchanged v19 final checkpoint completed all 20 fixed deterministic
50 mm development scenarios under v21. It retained all 12 frozen-FSM
successes and scenario `0009`, but rescued no additional scenario.

- Successes: `0000, 0001, 0002, 0004, 0007, 0009, 0010, 0011, 0012,
  0014, 0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0008, 0017`.
- FSM phase timeouts: `0013, 0019`.
- Scenario `0017` worsened from a v19 phase timeout to a collision.

The success set is exactly v19's. V21 retraining is prohibited.

## Constraint and numerical audit

- Telemetry is `51,949 x 122`.
- Only the semantically undefined `margin_m` is non-finite (`5,854` rows).
  All action, state, contact, target, and reference fields are finite.
- Maximum raw policy action is `0.18966709`; maximum executed normalized
  action is `0.10821524`, or `1.08215236 mm` under the unchanged 10 mm
  wheel-center-z bound. Wheel-speed residual is exact zero.
- There are `1,744` nonzero rows: `362` in phase 8, `1,262` in phase 9,
  and `120` in phase 10. Post-step telemetry places all within a registered
  gate; unauthorized nonzero rows are zero.
- Actual directions are `348` phase-8 climb rows, `14` phase-8 corrective
  rows, `1,262` phase-9 corrective rows, and `120` phase-10 corrective
  rows. Every nonzero row exactly matches one registered sign vector.
- Disabled channels, bilateral ties, four-wheel balance, and physical
  scaling are exact; scaled-residual numerical error is at most
  `7.45e-11 m`.
- The 12 frozen-FSM success trajectories have exact equality across all 56
  shared physical, state, contact, reference, and time fields.

Actor-action telemetry is intentionally undelayed, whereas physical
execution uses the scenario's registered 0--2-step action delay; state is
recorded after the physics step. Consequently, exact gain and threshold
transition semantics are established by the frozen source hash and direct
Isaac smoke, not by incorrectly pairing a delayed action with the same CSV
row's undelayed policy output.

## Mechanism diagnosis

The v21 rapid-rise correction is too brief because it has no memory. Once
pitch rate drops below `+0.35 rad/s` while phase-8 pitch remains high, the
controller switches back to the climb direction:

- Failed `0008`: 3 corrective rows followed by 22 climb rows.
- Failed `0019`: 4 early corrective rows followed by 160 phase-8 climb
  rows, then phase-9 correction.

The short correction does not rescue `0005`, `0006`, `0008`, or `0019`.
The phase-10 correction executes for 120 rows on `0003` but also does not
rescue it. The next mechanism should make the rapid-rise decision
hysteretic: once observed in phase 8, latch corrective mode through the
remainder of that phase. The latch remains based only on deployable IMU
history and naturally resets at episode reset/phase exit, while the
non-rapid phase-8 path can continue retaining `0009`.

## Artifacts

- Result:
  `4926c3a4628f486deea7f59e86904ee0f3e994b9fdb81ae0a003f1d7afb47642`
- Episodes:
  `a3f99e4c18a5ddf15e7904a44f6ca9bc762677edf4a89748a0e4c820ecde8418`
- Status:
  `c7ebdbbe23f6b8056391fb87e15acf7df57ac83a2d52b75722add236c633495c`
- Telemetry:
  `5f964adf061435942108f5f81a32fce8b578a3c79d97d672bdbd93af15927fb1`
- Stdout/stderr:
  `e78fab809e92f9093ca354488bfb24fea432e1379440265b0cd7628c040fe975`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
- Environment Python PID: `109092`; it exited naturally.

## Next action

Register a v22 hysteretic phase-8 emergency latch before any v22 Isaac
execution. Do not train v21.
