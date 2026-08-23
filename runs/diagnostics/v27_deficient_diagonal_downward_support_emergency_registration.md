# Runtime v27 deficient-diagonal downward-support emergency registration

## Status

`REGISTERED_BEFORE_ISAAC_EXECUTION`.

Runtime name:
`runtime-v27-deficient-diagonal-downward-support-emergency`.

V25 proves front-right -3 mm downward extension is physically realized and
delays two failures. V26 physically realizes rear-left +2.4 mm upward
retraction but makes both delayed scenarios collide again. Every failure
still lacks full front-right and rear-left support.

## Registered change

- Corrective wheel-center-z signs change from `[0,-1,+1,0]` to
  `[0,-1,-1,0]` on `[FL,FR,RL,RR]`.
- Corrective scales change from `[0,1,0.8,0]` to `[0,1,1,0]`.
- The 0.1 pre-gain floor, gain 3, and 10 mm z bound therefore request
  `[0,-3.0 mm,-3.0 mm,0]`, extending both deficient legs downward.
- Frozen calibrated-IK reconstruction is all-leg valid for 1,602/1,602
  v25 source rows and 146/146 v26 source rows at -3 mm, and remains valid
  through the full -10 mm rear-left registered bound.
- Rear-left safe-joint margin at -3 mm is at least 0.0359745 rad.
- The real-IMU gates, phase-8 latch, historical slow-pitch climb branch,
  actor half-space used to compute shared magnitude, action mask,
  exact-zero behavior, architecture, observations, rewards, optimizer,
  randomization, curriculum, stage budgets, and method-B/method-C
  distinction are unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Real-Isaac training-entrypoint smoke must validate exact
   `[0,-0.6,-0.6,0]` high-drive and `[0,-0.3,-0.3,0]` floor tensors,
   state gates, latch, phase exclusion, bounds, finite interfaces, phase
   exit, and resets.
2. The same smoke must prove all-leg IK validity and physical realization
   of front-right/rear-left -3.0 mm downward requests: unchanged residual
   IK-invalid count, final wheel-center movement toward both requests,
   nonzero servo-target changes on both legs, and exact-zero inactive
   coordinates.
3. The explicit v19 final checkpoint must restore with exact provenance,
   canonical 100x122 nominal telemetry, and exact-zero physical execution.
4. The fixed 20-scenario 50 mm development counterfactual must reach at
   least 16/20, retain all 12 frozen-FSM successes plus `0009`, physically
   realize registered corrections, and have zero constraint violations.

V27 training is prohibited until every gate passes.

## Frozen hashes

- Pre-code analysis:
  `b0e5c2ebe893ad3faec8a8fc22f410f53ec16aec94ac7bb30b6c6bcb9f7392b1`
- Raw common config:
  `676dd4a014fbf0355850fd623fdf20af144fa5c065d5cae6991e12690257a6d6`
- Canonical common config:
  `3b652b1c9e2bcb9c19e9cafdcdb8b689c546ea168200b2f92e0c57dc1154af0c`
- `residual_safety.py`:
  `85ac601dcca69b22b780e20bc0aeb0c861962dd2adb026f2ae4e84a276c1d678`
- `residual_rl_env.py`:
  `9617598a9027c5ab688794789acf3676b1c0ef99d9aa5d1196dda2ebf2480248`
- `train_residual_ppo.py`:
  `adce51260a5ac51d1e5cee83aef95a8143f73f20ffc7a6719137046bd4b202bc`
- `evaluate_controller.py`:
  `9af2fac5cd83e23a8c7ceca10b95d033056e99f022b7d9bf2fe3902abeb1be1c`

Python compilation and all 160 tests pass. No v27 Isaac result exists at
registration time.
