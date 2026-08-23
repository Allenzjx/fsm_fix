# Runtime v31 phase-9 bound counter-yaw registration

## Status

`REGISTERED_BEFORE_CODE_AND_ISAAC_EXECUTION`.

Runtime name:
`runtime-v31-phase9-bound-counter-yaw-skid-steer-emergency`.

## Evidence fixed before implementation

- V30 finished at 13/20 with the unchanged failure set: collisions
  `0003/0006/0019` and phase-9 timeouts `0005/0008/0013/0017`.
- All 45,944 common pre-phase-9 state rows were exactly equal to v29.
- The 13 existing-success state trajectories were exactly equal to v29.
- Exactly 2,524 v30 rows had nonzero wheel-speed residual, all belonging
  to the four timeout environments and all in phase 9.
- V30 applied exactly
  `[-0.04,+0.04,-0.04,+0.04] rad/s` in physical-forward wheel order.
- Relative to v29, all four target trajectories moved in the registered
  positive counter-yaw direction: terminal axle-midpoint yaw improved
  toward zero by `0.001719--0.009877 rad`, and front-right lateral
  position moved toward support by `0.001127--0.001865 m`.
- The authority was insufficient: all four terminal contact states
  remained `[TOP,TOP,AIR,TOP]` and all four timed out in phase 9.

The frozen evidence source is
`v30_phase9_counter_yaw_postrun_analysis.json`.

## Registered v31 change

- Retain the v30 state gate, phase-9-only authorization, positive
  counter-yaw signs `[-1,+1,-1,+1]`, and 3/4/3 mm deficient-diagonal
  wheel-center support without modification.
- Add an independent corrective wheel-speed shared-magnitude floor of
  `0.25` before the phase-9 gain of `4`.
- This yields normalized applied wheel-speed action
  `[-1,+1,-1,+1]` and physical-forward residual
  `[-0.10,+0.10,-0.10,+0.10] rad/s`, exactly at but never beyond the
  existing registered residual bound.
- Explicitly clip every post-phase-gain normalized applied action to
  `[-1,+1]`. This makes all configured wheel-center and wheel-speed
  residual bounds hard for both checkpoint replay and future training.
- The wheel-speed floor is independent of the `0.1` wheel-center shared
  floor. V31 therefore must preserve the exact v29/v30 3/4/3 mm
  wheel-center targets and IK behavior.
- Phase 8, phase 10, non-corrective rows, exact-zero input, and the
  opposite actor half-space retain exact-zero wheel-speed residual.
- Architecture, checkpoint, rewards, optimizer, randomization,
  curriculum, training budget, development manifest, and the B/C
  distinction remain unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Compilation and unit tests prove the independent floors and hard
   post-gain clip.
2. Real-Isaac smoke proves exact phase isolation, physical-forward
   signs, `0.10 rad/s` bound execution, raw actuator mapping, unchanged
   3/4/3 mm wheel-center realization, all-leg IK, and zero rollback.
3. The exact v19 checkpoint restores with canonical byte-stable
   exact-zero telemetry.
4. The fixed 20-scenario development counterfactual reaches at least
   16/20, preserves all 13 existing successes, and passes authorization,
   bound, mapping, IK, numerical, and safety audits.

V31 from-scratch training is prohibited until all gates pass.

## Frozen implementation hashes

- V30 post-run analysis:
  `7149b4bdd57edcc507da1d87efe747a961012ae97f07b3ca25e6c1a0194ff400`
- Raw/canonical common config:
  `8b27e86cca58471424eb08e85d9d337b33ef588f779e68c4446e8bd98594638e`,
  `855356646b94cbe31c4a709e7acfd3362e73df56d4db15ea4a19a0558840d557`
- `residual_safety.py`:
  `b1e544e39164e0a85693f13412050be90986355ba7f7342c120a0354f891dc41`
- `residual_rl_env.py`:
  `c2bc8594a75f9f7b291f59b69133b20820e02cb898f5b149f34b5c4ff3fe9d38`
- `train_residual_ppo.py`:
  `387d0813baa3878407059eb8fa93f01649112ca0140fc23591a34524f98f6cca`
- `evaluate_controller.py`:
  `94840256e634728830474495d01a8eb34b0768e6be4c80b066a946baaeb35bed`

Compilation and all 164 tests pass. No v31 Isaac result existed when
these hashes were frozen.
