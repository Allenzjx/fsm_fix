# Method-B v19 seed-11 50 mm development gate attempt001

## Disposition

`EXECUTION_PASS`, `PERFORMANCE_FAIL`, `13/20 < 16/20`.

The explicit v19 final checkpoint completed all 20 unchanged deterministic
50 mm development scenarios. It retained every one of the frozen FSM's 12
successes and rescued scenario `0009`, but it added no rescue beyond the
pre-training v19/v17-checkpoint counterfactual.

- Successes: `0000, 0001, 0002, 0004, 0007, 0009, 0010, 0011, 0012,
  0014, 0015, 0016, 0018`.
- Collisions: `0003, 0005, 0006, 0008`.
- FSM phase timeouts: `0013, 0017, 0019`.
- Mean episode minimum margin: `-0.2810706794 m`.
- Mean pitch-rate RMS: `0.0615251936 rad/s`.

## Constraint and numerical audit

- Telemetry is `52,618 x 122`.
- The only non-finite field is the semantically undefined `margin_m`
  (`5,854` rows). Every action, state, contact, target, and reference value
  is finite.
- Maximum raw policy action is `0.18966709`; maximum executed normalized
  action is `0.03354103`, or `0.33541027 mm` under the fixed 10 mm bound.
- Exactly `2,386` rows execute nonzero residuals. All are among the `2,387`
  registered phase-8/9 rows at pitch at least `+0.09 rad`.
- Unauthorized nonzero rows, phase-7 nonzero rows, and below-threshold
  phase-8/9 nonzero rows are all zero.
- Masked x/wheel-speed channels, bilateral tie error, and four-wheel
  balance error are exactly zero.
- Nonzero execution occurs only in environments `5, 6, 8, 9, 13, 17, 19`.
  The 12 frozen-FSM success trajectories remain physically exact.

## Mechanism diagnosis

The v19 state gate selected the intended hazardous branches. The trained
policy actually drove them more strongly than the old-checkpoint
counterfactual: the long phase-9 timeout branches increased mean executed
action L2 by roughly 3--5x. Nevertheless, the success set remained exactly
the same.

The physical direction is the mismatch. With wheels approximately fixed at
ground contact, decreasing front wheel-center z raises the front of the
body, while increasing rear wheel-center z lowers the rear. V19's fixed
front-negative/rear-positive residual therefore creates a positive-pitch
moment, aligned with the already excessive positive IMU pitch that opens
the hazard gate. Increasing its magnitude cannot provide corrective
feedback.

This diagnosis is also consistent with the paired trajectories: action-free
environments are byte-exact, while the stronger residual changes hazardous
branch pitch and position but produces no additional successful outcome.

## Artifacts

- Result:
  `2dadb76b978753b903146160cb301ce2cd3018ca6b595652e1c12604118f1f0e`
- Episodes:
  `888e37b49e884f07d26baaa8a8f8f3fde76026200fcf21e45f0d801a72e599c6`
- Status:
  `68ac8d63588074bc80ac3810cad4eeedd21fc97eac98c7fb68563cca1006120a`
- Telemetry:
  `eef4e209511f4646cbca6054b181087d834aef9583d81127ce7828eb7fa090d4`
- Stdout/stderr:
  `14a7c1cc5443b05812205717f75896cc66c8d62b4e40f3dfcc23b1d2f870a0aa`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

## Next action

Register a v20 pitch-corrective projection that preserves v19's phase
window, `+0.09 rad` real-IMU gate, raw shared-drive alignment, zero action,
mask, bounds, learning setup, and budget, while reversing only the executed
balanced-z physical direction. Before any retraining, require the explicit
v19 final checkpoint to pass a smoke and all 20 scenarios under v20.
