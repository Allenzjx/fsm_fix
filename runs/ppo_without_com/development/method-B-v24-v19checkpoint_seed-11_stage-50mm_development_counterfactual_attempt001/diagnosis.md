# Method-B v24/v19-checkpoint 50 mm counterfactual attempt001

## Disposition

`ACTION_LAYER_PASS`, `PHYSICAL_REALIZATION_FAIL`, `PERFORMANCE_FAIL`,
`13/20 < 16/20`.

The unchanged v19 final checkpoint completed all 20 fixed deterministic
50 mm development scenarios under v24. It retained all 12 frozen-FSM
successes and scenario `0009`, but rescued no additional scenario.

- Successes: `0000, 0001, 0002, 0004, 0007, 0009, 0010, 0011, 0012,
  0014, 0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0008, 0013, 0017`.
- FSM phase timeout: `0019`.
- The success set, failure reasons, episode records, terminal contact
  patterns, and every terminal metric are byte-identical to v23.

V24 retraining is prohibited.

## Constraint and numerical audit

- Telemetry is `51,092 x 122`.
- Only semantically undefined `margin_m` is non-finite (`5,854` rows).
  Every action, state, contact, target, and reference field is finite.
- Maximum raw policy action is `0.18966709`; maximum executed normalized
  action is `0.30000001`, or `3.00000003 mm`. Wheel-speed residual is exact
  zero.
- There are `876` nonzero rows: `235` in phase 8, `631` in phase 9, and
  `10` in phase 10. All satisfy a registered row-local enable predicate;
  nonzero rows outside phases 8--10 and unauthorized rows are zero.
- The action layer contains `13` historical phase-8 climb rows and `863`
  exact diagonal floor rows `[0,-0.3,+0.3,0]`.
- Disabled channels, the registered direction, FL/RR zeros, the FR/RL
  equal-and-opposite pair, four-wheel zero sum, climb balance, and scaling
  all pass. Scaling error is at most `9.31e-11 m`.

## Physical-realization failure

The new request never reaches the robot:

- On all `863` diagonal rows the requested targets are workspace-valid.
  Offline recomputation with the frozen geometry and safe joint limits gives
  IK-valid counts `[863,863,0,863]` for `[FL,FR,RL,RR]`.
- The rear-left primary solution exceeds its knee lower limit by at most
  `0.00195988 rad` (`0.1123 deg`). The alternate branch is also invalid.
- Runtime uses a coupled `all_legs_valid` check. One invalid rear-left leg
  replaces all four chosen targets with `baseline_raw`, canceling the valid
  front-right request too.
- All `863` diagonal rows return to the inferred baseline wheel-center
  target within `1.40e-9 m`. The 13 non-corrective climb rows do reach the
  requested targets.
- V23 and v24 have identical final wheel-center targets, final servo
  targets, and all 56 shared physical/state/contact/reference/time fields
  across all `51,092` rows. Only six requested-action columns differ.

This is why `episodes.jsonl` is byte-identical to v23 despite changing the
registered emergency vector.

## Mechanism diagnosis and next candidate

All seven failures again terminate with full-wheel-on-top pattern
`[FL=True, FR=False, RL=False, RR=True]`; all six collisions are on
`front_right_bot`.

Removing only the infeasible rear-left request from the same 863 frozen
rows yields a front-right-only target `[0,-1,0,0]`. Offline replay shows
all four IK legs valid on `863/863` rows. This is the narrowest next
candidate: it preserves the registered gates, latch, actor drive, floor,
gain, bounds, and v19 checkpoint while allowing the front-right correction
to survive the existing fail-closed safety rule.

Before a full run, v25 must be pre-registered and its real-Isaac smoke must
verify not only the executed-action tensor but also a nonzero change in the
final wheel-center and servo targets. V24 training remains prohibited.

## Artifacts

- Result:
  `e70464760abdbe2e73e22da16afab7ba11979b764aa3c86e671dae03514a0d32`
- Episodes:
  `643b8cfd66cd1dc2e0f34878863a096a806dc6821d0ca3cf8996c0bfe8cd0f9d`
- Status:
  `f9ae9fb2ada4ba7b3a2f185da6fbff57454f79ccd0e0bb4d5935fb1e97ff1068`
- Telemetry:
  `52143cb7189de1acc4bbb5f74ea428d150b26ac09685bab259f7381e3a9c0f4a`
- Stdout/stderr:
  `247f5ac7e9d621da4200eaaa2ac84bec12d0f377b33c77a19367dc511f532637`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
- Environment Python PID: `27432`; it exited naturally.

## Next action

Freeze the v25 front-right-only IK-feasibility analysis, register the
runtime before any Isaac call, and require a final-target realization smoke.
