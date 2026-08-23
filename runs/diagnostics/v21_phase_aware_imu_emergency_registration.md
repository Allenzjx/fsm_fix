# Runtime v21 phase-aware IMU emergency recovery registration

Registered before any v21 Isaac execution.

## Frozen mechanism

Runtime identifier:
`runtime-v21-phase-aware-imu-emergency-recovery`.

The actor input and shared-drive half-space remain unchanged. Only the
physical gate, phase-dependent output direction, and a fixed emergency
authority gain change:

- Physical authority exists only in FSM phases 8--10.
- In phase 8, authority opens when pitch is at least `+0.09 rad`, or when
  the early rapid-rise conjunction is true: pitch at least `+0.04 rad` and
  pitch rate at least `+0.35 rad/s`.
- A phase-8 rapid-rise row executes the front-positive/rear-negative
  pitch-corrective direction.
- A phase-8 high-pitch row below the rapid-rise rate threshold executes the
  historical front-negative/rear-positive climb direction.
- In phases 9--10, authority opens only at pitch at least `+0.09 rad` and
  executes the pitch-corrective direction.
- Phase gains are fixed at `[3.0, 3.0, 3.0]`. The inherited checkpoint's
  v20 maximum physical action was `0.331305 mm`, so the intended emergency
  scale is approximately `0.994 mm`, still below the unchanged `10 mm`
  hard wheel-center-z residual bound.
- Policy zero and the opposite actor half-space remain exact physical zero.
  Wheel-center x and wheel-speed residual channels remain exactly disabled.

No contact truth, scenario identity, obstacle identity, environment index,
or locked-test result enters the controller.

## Frozen-development evidence

This mechanism was derived only from the frozen FSM 50 mm development
trajectories and completed v19/v20 development runs:

- Frozen-FSM successful phase-8 pitch never exceeded `+0.08677 rad`;
  phase-9 never exceeded `+0.07910 rad`; phase-10 never exceeded
  `+0.07852 rad`.
- The phase-8 conjunction `pitch >= +0.04 rad` and
  `pitch_rate >= +0.35 rad/s` selects only frozen failures `0005`, `0006`,
  `0008`, and `0019`. It selects no frozen-FSM success. The closest
  successful phase-8 pitch-rate maximum is `+0.33046 rad/s`.
- The conjunction opens authority `0.05--0.15 s` earlier than the old
  `+0.09 rad` gate on those branches.
- The frozen v19 checkpoint has positive shared drive at every selected
  precursor row: ranges are `0.01447--0.03087` (`0005`),
  `0.01313--0.03220` (`0006`), `0.01735--0.02998` (`0008`), and
  `0.01619--0.02428` (`0019`).
- Frozen scenario `0003` is the only failed trajectory entering phase 10
  above `+0.09 rad`; its inherited-checkpoint shared drive is
  `0.0312--0.0366`.
- V19's climb direction rescued `0009`; v20's unconditional reversal lost
  it. The phase-8 slow/high-pitch branch therefore retains the climb
  direction.

## Invariants

The frozen FSM, metrics, asset, actor/critic architecture, observation and
privileged-state definitions, stochastic bounds, PPO optimizer, reward
weights, randomization, curriculum, training budget, hard action bounds,
and Method-B/Method-C distinction are unchanged.

## Pre-registered decision gates

1. A real-Isaac training-entrypoint smoke must prove:
   nominal exact zero; phase-8 slow/high-pitch climb direction; phase-8
   early rapid-rise corrective direction; phase-9/10 high-pitch corrective
   direction; exact phase-7/11 exclusion; fixed gain; masking, bilateral
   ties, four-wheel balance, zero preservation, finite interfaces, terminal
   safety, and reset behavior.
2. The explicit v19 final checkpoint
   `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
   must restore under v21 in a one-scenario deterministic smoke with exact
   provenance.
3. The same checkpoint must then run all 20 unchanged 50 mm development
   scenarios. V21 retraining is authorized only if all conditions hold:
   at least `16/20` successes; all 12 frozen-FSM successes retained;
   scenario `0009` retained; nonzero phase-8 rapid-rise corrective
   execution; nonzero phase-10 corrective execution; zero unauthorized
   nonzero rows; exact masks, ties, balance, direction, gain, and bounds.
4. Failure of any gate prohibits v21 retraining. Passing authorizes exactly
   one from-scratch Method-B seed-11, 50 mm run for `76,800` local
   timesteps / `4,915,200` environment transitions.

## Frozen implementation hashes

- `configs/ppo_common.yaml` raw:
  `96d11bc49cc06a0af4248673b59d25117464aa3638c8964b32c844ab25abdb1b`
- `configs/ppo_common.yaml` canonical:
  `1db52003b9a2b78ed670702334611a1f3cb132bddbcfb630764977586678b9ba`
- `residual_safety.py`:
  `717025e5c5be2857adaaf61b6d40735751ed739d30a49f59a9ee3a353444da92`
- `residual_rl_env.py`:
  `5788cd87f5d978b5976245cd42f1b98053c7bbdb44379eebed42a85932c9f689`
- `train_residual_ppo.py`:
  `017ae7bb9f67ca3c1f74a80d7e6225e82a65998f8627754abd575593d86011be`
- `evaluate_controller.py`:
  `01438601dd3c42520fc20c149b4db0c5f3d80111692aa323610c82fddea6c7f0`
- Frozen FSM:
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
- Frozen metrics:
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`
- Frozen asset:
  `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`

Python compilation passes and all `149` unit tests pass. No v21 Isaac
result existed when this registration was written.
