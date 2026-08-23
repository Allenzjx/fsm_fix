# Runtime v26 asymmetric-diagonal IK-margin emergency registration

## Status

`REGISTERED_BEFORE_ISAAC_EXECUTION`.

Runtime name:
`runtime-v26-asymmetric-diagonal-ik-margin-emergency`.

V25 physically realized every front-right -3 mm corrective request but
rescued no scenario. Every terminal failure still lacked both front-right
and rear-left full support. Frozen pre-code reconstruction with front-right
fixed at -3 mm found that rear-left +2.7 mm is valid on every source row,
whereas +3.0 mm is invalid on every row.

## Registered change

- Corrective wheel-center-z signs change from `[0,-1,0,0]` to
  `[0,-1,+1,0]` on `[FL,FR,RL,RR]`.
- Per-leg corrective scales are newly explicit and fixed at
  `[0.0,1.0,0.8,0.0]`.
- The 0.1 pre-gain floor, gain 3, and 10 mm z bound therefore request
  `[0,-3.0 mm,+2.4 mm,0]` at the emergency floor.
- The measured worst-case rear-left IK margin is at least 0.300939 mm over
  all 1,602 v25 corrective rows and all 863 v24 source rows.
- The real-IMU gates, phase-8 latch, historical slow-pitch climb branch,
  actor drive half-space, action mask, exact-zero behavior, architecture,
  observations, rewards, optimizer, randomization, curriculum, stage
  budgets, and method-B/method-C distinction are unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Real-Isaac training-entrypoint smoke must validate exact asymmetric
   high-drive and floor tensors, state gates, latch, phase exclusion,
   bounds, finite interfaces, phase exit, and reset behavior.
2. The same smoke must prove all-leg IK validity and physical realization
   of both front-right -3.0 mm and rear-left +2.4 mm: unchanged residual
   IK-invalid count, final wheel-center movement toward both requests,
   nonzero servo-target changes for both legs, and exact-zero inactive
   coordinates.
3. The explicit v19 final checkpoint must restore with exact provenance,
   canonical 100x122 nominal telemetry, and exact-zero physical execution.
4. The fixed 20-scenario 50 mm development counterfactual must reach at
   least 16/20, retain all 12 frozen-FSM successes plus `0009`, physically
   realize registered corrections, and have zero constraint violations.

V26 training is prohibited until every gate passes.

## Frozen hashes

- Pre-code analysis:
  `fa3ebf5b1702fef2e358db3a73633a1edd9ed380b1fa7d14284c7252338a307b`
- Raw common config:
  `9b44b5bc0ad147f537f4a43f75f174bd2bfe8bd117a424270101c9b992967dde`
- Canonical common config:
  `ce653e1d195b3877f3d1beb1bcce25103961e69c8da2d9308a17248e3c84f939`
- `residual_safety.py`:
  `12af7da72f84475a32087230b19c310d7719f901f62df9581ae9fc83b02f6d4c`
- `residual_rl_env.py`:
  `7bec40132a051a02731c72bbd41cef0f66e9a06ca8f095efba4b9ad975031d4e`
- `train_residual_ppo.py`:
  `5a9f257c5a364540f0a6c7ccee03c0621c6840e5791aeb0262306966435ac7bd`
- `evaluate_controller.py`:
  `54e8d6ea8467a022fd0ab34826cf6e592f0294e1e75a80eba3494541b63b62ec`

Python compilation and all 159 tests pass. No v26 Isaac result exists at
registration time.
