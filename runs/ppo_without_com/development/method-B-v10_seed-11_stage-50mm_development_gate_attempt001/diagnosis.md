# Method-B runtime-v10 seed-11 50 mm development gate attempt001

## Disposition

`FAIL_PROMOTION`. Execution and artifact integrity passed, but the frozen
development result was **2/20 (10%)**, below the registered **16/20 (80%)**
50 mm curriculum gate. This checkpoint is not eligible for validation,
curriculum promotion, warm start, or locked-test evaluation.

- Final checkpoint SHA-256:
  `679461e49cae1c5579496da4709619ffa76cc771a15aa53fdc86398780ea3aa4`.
- Result SHA-256:
  `a7c68a6563b5d2e204bae0a5a61b1e2f5a2ed52a81e499ad2d086024df453cd4`.
- Episode/status/telemetry SHA-256:
  `f1f6fca2128fb3c27069f6256e4d4421c65604295b85c6293472c8f722183eb0`,
  `03291b70acedefa8034cf50eaba2df92f05e580c75c85397fd3280f612f6d165`,
  and
  `623e66682e38acd3e8e350ce6dfb439c99b8d91a34b5c7ecaf9c9500c49ef29f`.
- Successes were 0010 and 0013.
- Failures were ten `BODY_OR_LINK_COLLISION`, five `FSM_PHASE_TIMEOUT`,
  and three global `TIMEOUT`.
- Delay subgroups were 0/5, 1/6, and 1/9 for delays 0, 1, and 2.

## Paired effect

V10 retained only one of the frozen FSM's 12 successes (0010), rescued
baseline failure 0013, and lost eleven baseline successes. Relative to v8,
it retained two of ten successes and lost 0001, 0004, 0007, 0008, 0011,
0014, 0015, and 0018. Extending training exposure and projecting only the
vertical directions therefore did not preserve the baseline.

Nine phase-8 collisions terminated at 107.60--108.50 seconds and reported
`front_right_bot` force above the 5 N collision threshold. Scenario 0003
terminated later in phase 10 with `rear_right_bot` collision. The five phase
timeouts ended in phase 9, while the three global timeouts ended in phase 10
with strict full-top flags `1110`.

## Applied-action diagnosis

The physical direction projection exposed a dead-action region. In phase 8,
the v10 policy means were front z positive and rear z negative:

`policy z = [+0.031, +0.071, -0.090, -0.076]` for collision rows.

The registered clamp rejected these signs, yielding approximately zero
physical vertical correction:

`executed z = [-0.006, 0.000, 0.000, 0.000]`.

The rejected half-space maps many distinct actions to the same physical
outcome, weakening exploration and credit assignment in this model-free PPO
setting. The policy instead used the still-unrestricted x and wheel-speed
channels.
Collision rows had mean executed front-left/front-right x actions
`-0.027/-0.036` and wheel-speed actions
`-0.038/+0.041/+0.029/-0.001`. With the registered 0.01 m center bound,
front-right x was approximately `-0.36 mm`. By contrast, v8 successful
phase-8 rows used approximately `+0.2 mm` front-right x together with the
safer front-down/rear-up vertical pattern. Nine of ten v10 collisions on the
front-right lower link are consistent with this compensating channel shift.

The v10 terminal checkpoint is not merely a large-residual failure: its
phase-8 center residuals were generally smaller than v8's. The failure is a
credit-assignment and authority-allocation problem. A one-sided clamp creates
a flat action-to-outcome region, while unrestricted lateral channels remain
available to PPO. PPO does not backpropagate through the simulator; this is
not claimed to be an environment-gradient failure.

## Training-time checkpoint evidence

All 1,200 core scalar updates are finite, but training performance is
non-monotonic. At registered checkpoint steps 16,000, 32,000, 64,000, and
76,800, the nearest reported total-reward means were approximately
`-529`, `-325`, `-343`, and `-494`. The terminal checkpoint is therefore not
assumed to be the best checkpoint. These tracker values are diagnostic only
and cannot select a formal checkpoint; independent evaluation remains
required.

## Registered next action

Create runtime v11 as a development-only physical-authority correction:

1. retain the frozen phase window 7--8;
2. execute only the four wheel-center z residual channels, masking all
   wheel-center x and wheel-speed residuals to exact zero;
3. map each raw z action to a differentiable-almost-everywhere signed
   magnitude (`front = -abs(raw)`, `rear = +abs(raw)`) instead of a
   rejected half-space with identical physical outcomes;
4. retain all 12 raw policy outputs and their regularization/telemetry, so the
   ablation architecture and audit chain remain unchanged;
5. first run a real-Isaac smoke and a frozen-development counterfactual with
   the existing v10 checkpoint. Retrain v11 from scratch only if the new
   physical semantics restore material baseline behavior.

Frozen FSM, metrics, asset, success definition, network, PPO
hyperparameters, randomization, seeds, and B/C-only CoM difference remain
unchanged. The locked test manifest remains unopened.
