# Runtime-v20 pitch-corrective projection registration

Registered before any v20 Isaac training or evaluation.

## Evidence available at registration

The explicit v19 final checkpoint completed its fixed 50 mm development
gate at 13/20, below the pre-registered 16/20 promotion threshold. Its
success set was exactly the same as the v19/v17-checkpoint counterfactual:
all 12 frozen-FSM successes plus rescue `0009`.

V19's state selection was exact. All 2,386 nonzero executed rows were in
phase 8/9 at real-IMU pitch at least `+0.09 rad`; all unauthorized, masked,
bilateral, and balance errors were zero. The newly trained checkpoint used
roughly 3--5x larger mean executed-action L2 on long phase-9 timeout
branches than the old checkpoint, but rescued no additional scenario.

The remaining mismatch is physical direction. With wheel contacts
approximately fixed, front-negative wheel-center z raises the front of the
body, while rear-positive wheel-center z lowers the rear. V19's executed
front-negative/rear-positive output therefore creates a positive-pitch
moment aligned with the positive-pitch hazard that opens the gate.

## Single runtime mechanism change

V20 preserves v19's historical actor-drive half-space but reverses only the
executed physical direction:

- shared-drive alignment signs remain `[-1, -1, +1, +1]`;
- a positive shared drive executes wheel-center z signs
  `[+1, +1, -1, -1]`;
- a zero or non-positive shared drive remains exactly off.

This separation makes the already-frozen v19 checkpoint a meaningful
counterfactual: its learned positive drive is retained rather than erased
by redefining the input half-space.

The phase window remains exactly 8--9 and the actor-observable real-IMU gate
remains exactly `pitch >= +0.09 rad`. Wheel-center x and wheel-speed
authority remain zero. The network, v17 exploration envelope, action
bounds, rewards, optimizer, randomization, budget, curriculum, frozen FSM,
metrics, asset, and B/C ablation distinction are unchanged.

## Fixed execution order and decision rules

1. Python compilation and all unit tests must pass.
2. A one-environment real-Isaac training-entrypoint smoke must prove exact
   below-gate FSM preservation, above-gate front-positive/rear-negative
   output, phase exclusion, zero preservation, finite interfaces/rewards,
   terminal safety, reset, and v20 provenance.
3. The explicit v19 final checkpoint
   `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
   must pass a deterministic one-scenario restore smoke under v20.
4. That fixed checkpoint is evaluated on all 20 unchanged 50 mm development
   scenarios. No validation or locked-test scenario may be read.
5. Exactly one from-scratch Method-B seed-11 50 mm v20 run at 76,800 local
   timesteps is authorized only if the counterfactual:
   - reaches at least 16/20;
   - loses none of the frozen FSM's 12 successful scenario pairs;
   - records at least one nonzero front-positive/rear-negative residual row;
   - records zero unauthorized nonzero rows.
6. A newly trained checkpoint still requires the unchanged 16/20 curriculum
   threshold.

The counterfactual is mechanism-authorization evidence, not a selectable
locked-test result. No per-scenario exception or result-dependent direction
is permitted.

## Frozen v20 implementation hashes

- `configs/ppo_common.yaml` raw SHA-256:
  `5494a5b575445d05fe2ea45ed9fd5fe351d08b94c4bd5fb3a74ad16c21a671be`
- canonical common-config SHA-256:
  `51bae0d8d66105104a2126843d49f35405163ad0543bd785fea9fe7e34943111`
- `residual_safety.py`:
  `bfee2da059a5004e5edc31d99e8097d8f40c659a7d0e06563d021f974b8df6a1`
- `residual_rl_env.py`:
  `536b1c8074aac0cf8c209f9ea83668a7f83dad217158a03957186a1f3ddec0ce`
- `train_residual_ppo.py`:
  `3463b93accbcf28d156113e5e60f38a462ae92260be4c395320e3d6b854ec25a`
- `evaluate_controller.py`:
  `240f6a0d92b27ef5fbbbda2b564ccb347d003f1b1ab0545e3569c4062523e7e9`

Python compilation and all 146 tests passed before this registration and
before any v20 Isaac launch.
