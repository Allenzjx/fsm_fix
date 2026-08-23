# V34 formal runtime selection registration

## Status

`REGISTERED_BEFORE_V34_CODE_AND_ISAAC_EXECUTION`.

Runtime:
`runtime-v34-selected-phase9-bound-counter-yaw-skid-steer-emergency`.

## Selection rule and evidence

The original task's development figures are ideal targets, not a license to
alter definitions or suppress required training when they are missed.
V31, v32, and v33 each produce 13/20 with the same 13 success scenario IDs
and exact success trajectories. Their failure safety differs:

- v31 phase-9-only speed: 3 collisions, 4 timeouts;
- v32 phase-8/9 0.10 rad/s: 7 collisions, 0 timeouts;
- v33 phase-8 0.075 / phase-9 0.10 rad/s: 6 collisions, 1 timeout.

The registered safety constraint prohibits an obvious collision increase.
V31 therefore dominates v32/v33 and is selected. The frozen v33 post-run
analysis is
`v33_phase8_moderate_phase9_bound_counter_yaw_postrun_analysis.json`.

## V34 implementation

V34 re-expresses the selected v31 behavior through the audited phase-aligned
projection interface:

- wheel-speed phases: `[9]`;
- pre-gain floor for phase 9: `[0.25]`;
- phase-9 gain: 4;
- physical-forward residual:
  `[-0.10,+0.10,-0.10,+0.10] rad/s`;
- phase 8 and phase 10 wheel-speed residual: exact zero.

All z behavior, thresholds, latch, bounds, observations, rewards,
architecture, PPO hyperparameters, randomization, curriculum budget, seeds,
FSM, metrics, asset, and scenario manifests remain unchanged. B and C still
differ only in the CoM reward weight.

## Formal-work decision

The ideal development improvement target was not reached and must be reported
as such. This does not erase the explicit requirement to actually train B and
C, reproduce all three seeds, run validation, freeze selected checkpoints,
and execute the locked paired test. Formal training proceeds with the safer
selected runtime; no v32/v33 checkpoint may be promoted.

The locked-test manifest has not been read.

## Frozen evidence and implementation hashes

- V33 post-run analysis:
  `34aa28443fd6ac7d2c23204e8df83438aae0ebb7434fa1a758bcc5c887bbb5cf`
- Raw/canonical common config:
  `dcf500751263661930a30cffff3f029e45d081894019cdef594e3d0c01836066`,
  `00cda2749fcb006e1a843e9f30580c149e11bc62171c52cf3eea6372447c002d`
- `residual_safety.py`:
  `32d50e9b4c5487411f259b485b1afa5e9f58a9d9f76d8308ef7cd0f642cfbe02`
- `residual_rl_env.py`:
  `217f660c2d7b8ea5183edb7ab9b3bf703a1beb25dafa265b457b31e62664cc23`
- `train_residual_ppo.py`:
  `0e39b6073c5335d8948d7839291d22fe97d3b294b5b8548b17fe2e9b89a049d7`
- `evaluate_controller.py`:
  `bc6a48ab6db7747fa3cf38db41039843d1f3d0d204246d6406844272c0a939c1`

Compilation and all 166 tests pass. No v34 Isaac execution existed when
these hashes were frozen.
