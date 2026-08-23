# Method-B v22/v19-checkpoint 50 mm counterfactual attempt001

## Disposition

`EXECUTION_PASS`, `PERFORMANCE_FAIL`, `13/20 < 16/20`.

The unchanged v19 final checkpoint completed all 20 fixed deterministic
50 mm development scenarios under v22. It retained all 12 frozen-FSM
successes and scenario `0009`, but rescued no additional scenario.

- Successes: `0000, 0001, 0002, 0004, 0007, 0009, 0010, 0011, 0012,
  0014, 0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0017, 0019`.
- FSM phase timeouts: `0008, 0013`.
- Relative to v21, `0008` improved from collision to timeout while `0019`
  worsened from timeout to collision. The success set did not change.

V22 retraining is prohibited.

## Constraint and numerical audit

- Telemetry is `51,926 x 122`.
- Only the semantically undefined `margin_m` is non-finite (`5,854` rows).
  All action, state, contact, target, and reference fields are finite.
- Maximum raw policy action is `0.18966709`; maximum executed normalized
  action is `0.30000001`, or `3.00000003 mm` under the unchanged 10 mm
  wheel-center-z bound. Wheel-speed residual is exact zero.
- There are `1,721` nonzero rows: `339` in phase 8, `1,262` in phase 9,
  and `120` in phase 10. Post-step telemetry places all within a registered
  gate; unauthorized nonzero rows are zero.
- Actual directions are `166` phase-8 climb rows, `173` phase-8
  corrective rows, `1,262` phase-9 corrective rows, and `120` phase-10
  corrective rows. The registered corrective floor is active for `1,555`
  rows. Every nonzero row exactly matches one registered sign vector.
- Disabled channels, bilateral ties, four-wheel balance, and physical
  scaling are exact; scaled-residual numerical error is at most
  `9.31e-11 m`.
- The 12 frozen-FSM success trajectories have exact equality across all 56
  shared physical, state, contact, reference, and time fields.

Actor-action telemetry is intentionally undelayed, whereas physical
execution uses the scenario's registered 0--2-step action delay; state is
recorded after the physics step. Consequently, exact floor/gain/latch
semantics are established by frozen source provenance and the direct Isaac
smoke, not by incorrectly pairing a delayed action with the same CSV row's
undelayed policy output.

## Mechanism diagnosis

The v22 latch and 3 mm floor execute as registered, so lack of authority is
not the explanation. The surviving failure branch is laterally asymmetric:

- Every terminal collision across the frozen FSM and v19--v22 involves
  `front_right_bot`.
- At collision the robot has positive roll and the front-right wheel has
  zero upward support.
- In frozen-FSM phases 8--10, successful trajectories remain below
  `+0.09077 rad` roll, while failed trajectories reach as high as
  `+0.14237 rad`.
- The v19--v22 residual signs are bilaterally tied. They generate a pitch
  moment but cannot generate a roll moment, regardless of the 3x gain or
  floor.

With the project wheel-center-z convention, positive roll lowers the right
side. A pure corrective roll pattern is left-positive/right-negative
`[+1,-1,+1,-1]`, which has zero sum and zero pitch moment. That direction
is outside the current bilateral subspace and directly targets the observed
front-right collapse.

Before any new Isaac run, the next development step must quantify a
positive-roll gate using only frozen development telemetry, require zero
activation on all frozen-FSM success trajectories, and pre-register the
resulting phase-8--10 pure-roll emergency override. V22 training remains
prohibited.

## Artifacts

- Result:
  `9252d07295c46c93aed32d041f95bffd6e01c54254a6cf15e075884e5bacb9f9`
- Episodes:
  `f92eaeb67c0d596a8de8d0ea4d477c2abe65610456b1f6d24b55bb72b0256f0d`
- Status:
  `51c3c0f83f7164b150cf97c3a607c48d17998a5039ad605bb71926fc0743532c`
- Telemetry:
  `7dfbcdf34ca2595ac165a067a66cbd45d4ab756d90339642db7bc60a8b4af039`
- Stdout/stderr:
  `9b7bfefdd2e62cece3a68d05cd63f8d2497cc15f640bb8ab8d09b9c287039dbe`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
- Environment Python PID: `139276`; it exited naturally.

## Next action

Derive and pre-register a positive-roll phase-8--10 corrective override
with zero frozen-FSM-success activation before any v23 Isaac execution.
Do not train v22.
