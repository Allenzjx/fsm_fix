# Runtime v32 phase-8--9 bound counter-yaw registration

## Status

`REGISTERED_BEFORE_CODE_AND_ISAAC_EXECUTION`.

Runtime name:
`runtime-v32-phase8-9-bound-counter-yaw-skid-steer-emergency`.

## Evidence fixed before implementation

- V31 finished at 13/20 with the exact v30 failure set.
- Exactly 2,524 v31 rows execute the registered
  `[-0.10,+0.10,-0.10,+0.10] rad/s` physical-forward residual; every
  such row belongs to timeout environments 5/8/13/17 in phase 9.
- Relative to v30, every target moves farther in the correct direction:
  terminal axle-midpoint yaw improves toward zero by
  `0.006950--0.011244 rad` and front-right lateral position improves by
  `0.002419--0.003397 m`.
- The hard speed bound is therefore directionally valid but insufficient
  after the robot has become statically stuck in phase 9. All four
  terminal contact states remain `[TOP,TOP,AIR,TOP]`.
- The unchanged actor-observable roll-IMU corrective gate selects exactly
  636 phase-8 rows, all in failed environments 5/6/8/13/17/19 and none in
  any of the 13 current successes.
- Timeout environments receive 145--166 authorized phase-8 rows, or
  7.25--8.30 seconds of additional dynamic-transfer opportunity before
  phase 9. Collision environments 6/19 receive only 3/4 rows.

The frozen evidence source is
`v31_phase9_bound_counter_yaw_postrun_analysis.json`.

## Registered v32 change

- Replace the scalar `corrective_wheel_speed_phase: 9` with the explicit
  ordered phase list `corrective_wheel_speed_phases: [8,9]`.
- On corrective rows in either registered phase, retain the exact v31
  independent 0.25 speed floor, post-gain hard clip, physical-forward
  signs `[-1,+1,-1,+1]`, and physical residual hard bound
  `[-0.10,+0.10,-0.10,+0.10] rad/s`.
- Phase 10, non-corrective rows, exact-zero input, and the opposite actor
  half-space retain exact-zero wheel-speed residual.
- Retain the exact wheel-center z floor/gains and physical realization:
  3/4/3 mm deficient-diagonal downward support in phases 8/9/10.
- Retain the exact state-gate thresholds and latch; v32 adds no simulator
  contact truth, scenario identity, or new observation.
- Architecture, checkpoint, rewards, optimizer, randomization,
  curriculum, training budget, development manifest, hard action bounds,
  and the B/C distinction remain unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Compilation and unit tests prove exact `[8,9]` phase membership,
   phase-10 zero preservation, independent floors, and hard bounds.
2. Real-Isaac smoke proves exact phase-8/9 physical-forward speed,
   phase-10 zero, raw actuator mapping, unchanged 3/4/3 mm z, all-leg IK,
   and zero rollback.
3. The exact v19 checkpoint restores with canonical byte-stable
   exact-zero telemetry.
4. The fixed 20-scenario development counterfactual reaches at least
   16/20, preserves all 13 existing successes, and passes authorization,
   bound, mapping, IK, numerical, and safety audits.

V32 from-scratch training is prohibited until all gates pass.

## Frozen implementation hashes

- V31 post-run analysis:
  `5707549bd63742aa01f557bf9545dba98c9142341240787a0c709e95b6483025`
- Raw/canonical common config:
  `900983f5b6ad177fbcc0f9db382e9fb49c63fceaf4daae1d20be3f2f4097f3bb`,
  `cbc9d8a1ad464fa4683feb2cb923ce5286b6bf002acb5be8b0e90773b8cdc313`
- `residual_safety.py`:
  `8d148396d94d7a16053b2c8da16e4e0dfe3feb94b30545bc095d6b297323f861`
- `residual_rl_env.py`:
  `2fc9dd2712aeeef586a839cee0fcd50656b4f15d3d63c784a754262a5527e492`
- `train_residual_ppo.py`:
  `65f509d1791792fe5a32ca6bffcbd0a3526abac7670c3c40d32b513ca0a3fb23`
- `evaluate_controller.py`:
  `272f15070bb10cee4f4c7fe0bdd00b8d511be01c908e89fee98b54571d83b290`

Compilation and all 165 tests pass. No v32 Isaac result existed when
these hashes were frozen.
