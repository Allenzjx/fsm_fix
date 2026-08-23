# Runtime v30 phase-9 counter-yaw skid-steer registration

## Status

`REGISTERED_BEFORE_ISAAC_EXECUTION`.

Runtime name:
`runtime-v30-phase9-counter-yaw-skid-steer-emergency`.

## Registered change

- V29 deficient-diagonal wheel-center floors remain exactly 3/4/3 mm in
  phases 8/9/10.
- The checkpoint-compatible shared magnitude remains derived exclusively
  from the historical z-action half-space.
- On corrective phase-9 rows only, that magnitude also produces
  physical-forward wheel-speed signs `[-1,+1,-1,+1]`.
- At the 0.1 floor and phase-9 gain 4, physical residuals are
  `[-0.04,+0.04,-0.04,+0.04] rad/s`.
- Phase 8, phase 10, non-corrective rows, exact-zero input, and the
  opposite actor half-space retain exact-zero wheel-speed residual.
- The candidate retains 0.06 rad/s to the 0.1 rad/s residual bound.
- The direction is positive counter-clockwise skid-steer yaw in the
  registered +x-forward/+y-left frame, directly opposing the measured
  negative-yaw failure geometry.
- Wheel-speed authority does not change wheel-center IK targets. The
  existing v29 phase-9 target reconstruction remains 2,524/2,524
  all-leg valid.
- All IMU thresholds, latch semantics, z signs/scales/floor/gains,
  architecture, rewards, optimizer, randomization, curriculum, budget,
  hard action bounds, and B/C distinction remain unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Real-Isaac smoke proves phase-9-only applied action, exact physical
   wheel-speed residual, physical-forward command delta, raw actuator
   mapping, unchanged 3/4/3 mm wheel-center realization, all-leg IK, and
   zero rollback.
2. The exact v19 checkpoint restores with canonical byte-stable
   exact-zero telemetry.
3. The fixed 20-scenario counterfactual reaches >=16/20, preserves every
   existing success including `0009`, and passes all authorization,
   bounds, mapping, IK, numerical, and safety audits.

V30 training is prohibited until all gates pass.

## Frozen hashes

- Pre-code analysis:
  `11894db1ad878a168eb651daefbfe14c1d3c5ebf8ea4df3b21c8455d697c846c`
- Raw/canonical common config:
  `0b69563697b9d4b3962d0ee74ccb5536be11f324375349f25bacbc2888aa938b`,
  `628d74b0eb679665240cfdf6fb2944cb8f35077655ada46329a9e208e118214e`
- `residual_safety.py`:
  `067b5273590e939d01f6ba8a823314a72b37331d82eb7ba6c0aa217982b52152`
- `residual_rl_env.py`:
  `d72b6977922c2511eb9fdddcdc83879f6e477ae43ba97104bc88733ac03d280a`
- `train_residual_ppo.py`:
  `cf22dd2ffe7ee61fc5bc06758c8ca502abbc26e353690511bcd94a7c089e9645`
- `evaluate_controller.py`:
  `b4d7c7822282f2bb1a57b16afeb8f218b55dea03e7dbb5f216e4bd1b08e1c6d1`

Compilation and all 162 tests pass. No v30 Isaac result exists at
registration time.
