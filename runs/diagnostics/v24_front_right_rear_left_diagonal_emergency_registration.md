# Runtime v24 front-right/rear-left diagonal emergency registration

Registered before any v24 Isaac execution.

## Frozen mechanism

Runtime identifier:
`runtime-v24-front-right-rear-left-diagonal-emergency`.

V24 changes only the v23 emergency output vector:

- The high-roll and early roll/rate gates, phase-8 latch, historical
  phase-8 climb branch, actor positive half-space, 0.1 corrective floor,
  gain3, phase window 8--10, and hard bounds are unchanged.
- A roll emergency executes wheel-center-z
  `[FL=0, FR=-1, RL=+1, RR=0]`.
- The vector extends the front-right leg/body support, retracts rear-left,
  and leaves front-left/rear-right exactly unchanged.
- It has zero four-wheel sum and is algebraically the sum of historical
  climb `[-1,-1,+1,+1]` and v23 pure roll `[+1,-1,+1,-1]`, up to a common
  factor of two.
- Exact actor zero and opposite actor drive remain exact physical zero.
  Wheel-center x and wheel-speed channels remain disabled.

No contact truth, scenario identity, obstacle identity, environment index,
or locked-test result enters the runtime controller.

## Development evidence

V23 executed 863 exact 3 mm pure-roll rows but remained 13/20. All seven
failures, including the one timeout, ended with the same full-wheel-on-top
pattern:

`[FL=True, FR=False, RL=False, RR=True]`.

All six collisions were on `front_right_bot`. Thus the support defect is
diagonal rather than a generic bilateral roll defect. The v24 fixed output
targets only the two deficient wheel supports and does not perturb the two
supports already fully on top.

The v23 success-inactive gate evidence remains frozen:

- High gate: `roll >= +0.10 rad` in phases 8--10.
- Early phase-8 gate:
  `roll >= +0.06 rad` and `pitch_rate >= +0.35 rad/s`.
- Neither gate activates on any frozen-FSM, v19, v22, or v23 success
  trajectory, including `0009`.

## Unchanged invariants

Frozen FSM, metrics, asset, observations/states, network, stochastic bounds,
PPO optimizer, rewards, randomization, curriculum, total training budget,
hard bounds, and Method-B/Method-C distinction remain unchanged.

## Pre-registered decision gates

1. Real-Isaac training-entrypoint smoke must prove nominal exact zero;
   phase-8 slow/high-pitch climb and phase-9 zero; high-roll diagonal output
   in phases 8--10; early-gate output and latch; exact 3 mm floor;
   phase-7/11 exclusion; opposite-drive shutoff; FR/RL equal-and-opposite,
   FL/RR exact zero, four-wheel zero sum, masks, scaling, bounds, finite
   interfaces, terminal safety, and resets.
2. The v19 final checkpoint
   `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
   must pass deterministic one-scenario restore smoke with exact provenance.
3. The same checkpoint must run all 20 fixed 50 mm development scenarios.
   Retraining requires at least `16/20`, all 12 frozen-FSM successes plus
   `0009`, exercised early/latching and phase-10 diagonal correction, and
   zero structural/authorization violations.
4. Any failure prohibits v24 retraining. Passing authorizes exactly one
   from-scratch Method-B seed-11 50 mm run for `76,800` local timesteps /
   `4,915,200` transitions.

## Frozen implementation hashes

- Common config raw:
  `1a2116bceca376f03f3532047609d01ff15beb96f5e0742104015bd98ff7f07a`
- Common config canonical:
  `2619274f812fe3e658d7765cc0b9728c87acd90fcdeb32901db7744dc7f8756d`
- `residual_safety.py`:
  `1be56308f1dc7d11231e9b63e99e4214820dcf476afdb74493081640a42c406e`
- `residual_rl_env.py`:
  `7e18172da171fe422bbc79c3d2094c929461bc27afa64cf457841ec2f388ef66`
- `train_residual_ppo.py`:
  `a7e37045b9a035e97348e7946b623734d6f442c0be53625392122e853bcd19b3`
- `evaluate_controller.py`:
  `7e2483752494936c30550bacb52bb5a05fb8e055793e5ef1e57f3db5e246f924`
- Frozen FSM:
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
- Frozen metrics:
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`
- Frozen asset:
  `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`

Python compilation and all `156` tests pass. No v24 Isaac result existed
when this registration was written.
