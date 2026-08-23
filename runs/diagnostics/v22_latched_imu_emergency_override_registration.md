# Runtime v22 latched IMU emergency override registration

Registered before any v22 Isaac execution.

## Frozen mechanism

Runtime identifier: `runtime-v22-latched-imu-emergency-override`.

V22 retains v21's deployable real-IMU thresholds, phase window, actor
half-space, phase-dependent directions, and 3x gain. It changes the
rapid-rise correction into one coherent emergency override:

- In phase 8, observing `pitch >= +0.04 rad` and
  `pitch_rate >= +0.35 rad/s` latches corrective mode through the remainder
  of phase 8. The latch clears on phase exit and every episode reset.
- While latched, a positive actor shared drive executes at least `0.1`
  normalized before the fixed 3x phase gain: `0.3` normalized / `3 mm`
  physical wheel-center-z correction.
- Phase-9/10 high-pitch corrective rows use the same positive-drive floor.
- A non-latched phase-8 `pitch >= +0.09 rad` row retains the actor-scaled
  historical climb direction with no floor, preserving the mechanism that
  rescued scenario `0009`.
- Exact actor zero and the opposite actor half-space remain exact physical
  zero. Wheel-center x and wheel-speed channels remain disabled. The
  unchanged hard wheel-center-z bound is `10 mm`.

No contact truth, scenario identity, obstacle identity, environment index,
or locked-test result enters the controller.

## Development evidence and fixed authority

V21 reached the same 13/20 success set as v19. Its corrective branch
executed, but failed rapid-rise trajectories reverted to climb as soon as
pitch rate crossed back below `+0.35 rad/s`:

- `0008`: 3 phase-8 corrective rows, then 22 climb rows.
- `0019`: 4 phase-8 corrective rows, then 160 climb rows.

V21's strongest inherited-checkpoint action was `1.082152 mm` and rescued
no new scenario. The v22 emergency floor is fixed at `3 mm`, approximately
2.77x that observed maximum and 30% of the unchanged 10 mm hard bound.
It is required because `0005` and `0006` terminate only 3--4 recorded rows
after their first rapid-rise trigger, leaving no time for a weak
actor-scaled response. Latching alone could change at most the longer
`0008`/`0019` branches and therefore could not reach the 16/20 gate.

## Unchanged invariants

Frozen FSM, metrics, asset, observations/states, network, stochastic
bounds, PPO optimizer, rewards, randomization, curriculum, total training
budget, hard bounds, and Method-B/Method-C distinction remain unchanged.

## Pre-registered decision gates

1. Real-Isaac training-entrypoint smoke must prove exact nominal zero;
   phase-8 slow/high-pitch climb; phase-8 rapid-rise correction; correction
   persistence after pitch rate falls; exact 3 mm positive-drive floor;
   latch clear on phase exit/reset; phase-9/10 correction; phase-7/11
   exclusion; zero/opposite-drive shutoff; masks, ties, balance, bounds,
   finite interfaces, terminal safety, and reset behavior.
2. Explicit v19 final checkpoint
   `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
   must pass one-scenario deterministic restore smoke with exact provenance.
3. The same checkpoint must run all 20 unchanged 50 mm development
   scenarios. Retraining requires at least `16/20`, all 12 frozen-FSM
   successes plus `0009`, nonzero latched phase-8 floor execution,
   nonzero phase-10 corrective execution, zero unauthorized actions, and
   exact structural constraints.
4. Any failure prohibits v22 retraining. Passing authorizes exactly one
   from-scratch Method-B seed-11 50 mm run for `76,800` local timesteps /
   `4,915,200` transitions.

## Frozen implementation hashes

- Common config raw:
  `39927e1e21f8bdfc364cc2d81bef9e617911fa4acaa31e241de0f02159b43b74`
- Common config canonical:
  `180d8d52c8f12f1d74316708e865a4bd699984ae093b568842697b8fe670e05a`
- `residual_safety.py`:
  `f82040465935e19763ab62cc23f352c3088694f344899d72f4af67e13c3cef4f`
- `residual_rl_env.py`:
  `d3cd1f808804fbf559430ccdead5416010f8901563a6e9361a5c6d72663e2ae2`
- `train_residual_ppo.py`:
  `d9edde392ba5c8396783cf66ec11d5743d98bdf973434dcc17989e7ef7479fd9`
- `evaluate_controller.py`:
  `db6a6b08648bf24cb040b2bc0f0a00df89afc68c123ceff8c300db8f1847ddfe`
- Frozen FSM:
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
- Frozen metrics:
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`
- Frozen asset:
  `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`

Python compilation and all `152` unit tests pass. No v22 Isaac result
existed when this registration was written.
