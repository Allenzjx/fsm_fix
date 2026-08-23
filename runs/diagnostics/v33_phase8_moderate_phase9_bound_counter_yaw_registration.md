# Runtime v33 phase-8 moderate / phase-9 bound counter-yaw registration

## Status

`REGISTERED_BEFORE_V33_CODE_AND_ISAAC_EXECUTION`.

Runtime name:
`runtime-v33-phase8-moderate-phase9-bound-counter-yaw-skid-steer-emergency`.

The locked-test manifest has not been read.

## Frozen evidence

V31 (phase-9-only exact-bound speed) and v32 (phase-8/9 exact-bound speed)
both finish at 13/20 with the same seven failed scenario IDs and all 13
success trajectories exact. The failure modes differ:

- v31: three `BODY_OR_LINK_COLLISION` plus four `FSM_PHASE_TIMEOUT`;
- v32: seven `BODY_OR_LINK_COLLISION`.

V32 executes only 66 recorded phase-8 speed rows across the four previous
timeout targets before all four collide with `front_right_bot`; their
durations are only 0.15, 1.25, 1.40, and 0.30 seconds. None reaches phase 9.
At matched terminal time, v32 nevertheless moves axle yaw in the registered
direction by `+0.000548` to `+0.004470 rad`. Thus the sign remains valid, but
the phase-8 exact-bound magnitude is dynamically unsafe.

The frozen source is
`v32_phase8_9_bound_counter_yaw_postrun_analysis.json`, SHA-256
`f27e9a5d568b58c9ba8b119e0d26a0650386329884d14eeb157780dd72316af7`.

## Registered v33 change

Only the phase-8 wheel-speed pre-gain floor changes from `1/3` to `1/4`.
With the unchanged phase-8 gain 3, this yields normalized magnitude 0.75 and
physical-forward residual
`[-0.075,+0.075,-0.075,+0.075] rad/s`.

The phase-9 pre-gain floor remains `1/4`; with gain 4 it retains exact
normalized magnitude 1.0 and physical-forward residual
`[-0.10,+0.10,-0.10,+0.10] rad/s`.

Everything else is frozen: phase membership `[8,9]`, signs, z commands,
state-gate thresholds and latch, phase gains, hard bounds, observations,
checkpoint, architecture, rewards, optimizer, randomization, curriculum,
budgets, development manifest, B/C distinction, and acceptance rule.

V33 therefore brackets phase-8 speed strictly between v31 zero and v32
0.10 rad/s without altering the proven phase-9 command.

## Required gates

1. Compilation and all unit tests prove phase-8 0.075, phase-9 0.10, phase-10
   zero, and phase/floor alignment.
2. Real-Isaac smoke proves physical-forward and raw-actuator realization,
   unchanged 3/4/3 mm z, all-leg IK, and zero rollback.
3. Exact v19 checkpoint restoration reproduces canonical byte-stable
   exact-zero telemetry.
4. The one fixed 20-scenario development counterfactual reaches at least
   16/20, preserves all 13 successes, and passes all authorization, bound,
   mapping, IK, numerical, and safety audits.

V33 from-scratch training is prohibited until every gate passes.

## Pre-code v32 implementation hashes

- Raw/canonical common config:
  `5c64a81a99bd7a1afce577fcc43d105bf4db7f52364dc2d3c102318fce18b518`,
  `0f341d1fe9aa8439d6be9bb2f3ba2c51999e23772debb9b071ce24ae50114a58`
- `residual_safety.py`:
  `32d50e9b4c5487411f259b485b1afa5e9f58a9d9f76d8308ef7cd0f642cfbe02`
- `residual_rl_env.py`:
  `7e4d227279d2def3c5f266dabcb7c090618cb6f78ec748ab1c7494778b97b0bc`
- `train_residual_ppo.py`:
  `cf0a63845e4d6863fb1cc7f6dc5e26144a6933517471c9ff71b598811a4e8b8c`
- `evaluate_controller.py`:
  `49f652ba17edc4b139fef3fa22dfaae264069ae79ad491836f51d06add4ef2ba`

## Frozen v33 implementation hashes

- Raw/canonical common config:
  `d7e01fae6de8abad34cb4b5afe733e1668fbf089d3a8f939b61b6aa9f23323cb`,
  `3d84a57521cb6b5721204db5a35c1541a7b9fe0910f80631cf391bba5b066280`
- `residual_safety.py`:
  `32d50e9b4c5487411f259b485b1afa5e9f58a9d9f76d8308ef7cd0f642cfbe02`
- `residual_rl_env.py`:
  `b9731f17313bafbed7064d9c09f3a596ba8e53620df572ef0f121b52317eb34a`
- `train_residual_ppo.py`:
  `b1c2ef885e7e8a4db7a9522011848a3a89f4497b32d2d6912af82da684470c7c`
- `evaluate_controller.py`:
  `407880de878b13007dea0f06261b0195ff60c84fbcd25ca5a94d56b200a3080f`

Compilation and all 166 tests pass. No v33 Isaac result existed when
these hashes were frozen.
