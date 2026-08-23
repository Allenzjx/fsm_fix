# Method-B v23/v19-checkpoint 50 mm counterfactual attempt001

## Disposition

`EXECUTION_PASS`, `PERFORMANCE_FAIL`, `13/20 < 16/20`.

The unchanged v19 final checkpoint completed all 20 fixed deterministic
50 mm development scenarios under v23. It retained all 12 frozen-FSM
successes and scenario `0009`, but rescued no additional scenario.

- Successes: `0000, 0001, 0002, 0004, 0007, 0009, 0010, 0011, 0012,
  0014, 0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0008, 0013, 0017`.
- FSM phase timeout: `0019`.
- Relative to v22, `0013` worsened from timeout to collision while `0019`
  improved from collision to timeout. The success set did not change.

V23 retraining is prohibited.

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
- The executed directions are `13` historical phase-8 climb rows and `863`
  pure-roll rows. All 863 pure-roll rows use the exact 0.1 pre-gain /
  0.3 normalized / 3 mm floor.
- Disabled channels, registered signs, pure-roll pairing, four-wheel zero
  sum, zero front/rear pitch moment, climb balance, and physical scaling are
  exact. Scaling error is at most `9.31e-11 m`.
- The 12 frozen-FSM success trajectories are exactly equal across all 56
  shared physical/state/contact/reference/time fields. Scenario `0009`
  remains successful and its maximum roll stays below the +0.10-rad gate.

## Mechanism diagnosis

The new channel executes, but pure roll is still the wrong physical
subspace for the complete contact defect:

- Every one of the seven failed scenarios terminates with full-wheel-on-top
  pattern `[FL=True, FR=False, RL=False, RR=True]`.
- All six collisions are on `front_right_bot`; front-right upward support is
  zero or numerical zero at collision.
- Pure roll `[+1,-1,+1,-1]` moves all four wheel centers. It targets the
  failing front-right/rear-left diagonal, but also moves the already-good
  front-left/rear-right diagonal.
- Short failures `0005` and `0006` still collide after four and three
  pure-roll rows. `0008` lasts 25 corrective rows, but still collides.
- In matched trajectory time, v23 increases positive roll by about
  `0.00693` and `0.00747 rad` at the `0005/0006` terminal samples; `0008`
  decreases roll by about `0.01917 rad` and survives longer, showing that
  response depends on the current contact topology rather than roll angle
  alone.

The observed diagonal defect gives a more specific action:
`[0,-1,+1,0]` on `[FL,FR,RL,RR]` wheel-center z. It extends/raises the
front-right body support and retracts/lowers rear-left while leaving the
already-supported front-left and rear-right unchanged. Algebraically it is
the sum of climb `[-1,-1,+1,+1]` and pure roll `[+1,-1,+1,-1]`.

Before any new Isaac run, that diagonal direction must be pre-registered
under the same success-inactive roll gates, actor half-space, 3 mm floor,
gain, bounds, and promotion rule. V23 training remains prohibited.

## Artifacts

- Result:
  `3e360e5acc0c8ae990a22728be14e1b8263d962ae097982240a10718b03436a4`
- Episodes:
  `643b8cfd66cd1dc2e0f34878863a096a806dc6821d0ca3cf8996c0bfe8cd0f9d`
- Status:
  `ece68649c7d48206f2eeeedded1e49ac145066c173870939bf3f84c9736aa073`
- Telemetry:
  `70d990948beec72c092476ae3f5dfb360e20ee6338351bfc66dcb494a073fff9`
- Stdout/stderr:
  `2826a478cd319e11411e11408331506d4be706c8837abc3d2bec889e7d33e007`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
- Environment Python PID: `135720`; it exited naturally.

## Next action

Pre-register a v24 phase-8--10 diagonal front-right/rear-left emergency
projection `[0,-1,+1,0]` under the unchanged v23 IMU gates. Do not train
v23.
