# Method-B runtime-v11 seed-11 50 mm development gate attempt001

## Disposition

`FAIL_PROMOTION`. Execution and artifact integrity passed, but the frozen
development result was **6/20 (30%)**, below the registered **16/20 (80%)**
50 mm gate. This checkpoint is not eligible for validation, curriculum
promotion, warm start, or locked-test evaluation.

- Final checkpoint SHA-256:
  `29ac9c122b6741500d12f086f39daf768d9a88310715d1f62bdfa60acfbab418`.
- Result SHA-256:
  `8602f69a1691858c55c14792a64f7a42aab63947b609d739677976aea795fded`.
- Episode/status/telemetry SHA-256:
  `2e151471759824751acbac838ea8711f9e5cbe21b0566abe9deb68d81a5664de`,
  `5279ba62f614c0df48ee94f292a2f464117455797a2a6d00cf677b1c9863d3f2`,
  and
  `d50a6b3c4049591f573468b14b721d6c9204938f8b43c4ca5ff2d16ff2994d86`.
- stdout/stderr SHA-256:
  `b0e917d64d6da580fe0619870d20090b7e5aa45de7cb982f2f94fd0571d8269f`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.
- Successes were 0001, 0002, 0010, 0012, 0013, and 0016.
- Failures were ten `BODY_OR_LINK_COLLISION`, one `FSM_PHASE_TIMEOUT`,
  and three global `TIMEOUT`.
- Delay subgroups were 2/5, 2/6, and 2/9 for delays 0, 1, and 2.

## Paired effect

V11 retained five of the frozen FSM's 12 successes (0001, 0002, 0010, 0012,
0016), rescued baseline failure 0013, and lost seven baseline successes.
Relative to the 7/20 v11/v10-checkpoint counterfactual, it retained 0001,
0002, 0012, and 0013; gained 0010/0016; and lost 0000/0011/0014.

All ten collisions were phase-8 `front_right_bot` events. The phase timeout
ended in phase 9 with a 1.9 N sub-threshold front-right contact. The three
global timeouts ended in phase 10 with strict full-top flags `1110`.

## Physical-action diagnosis

The complete telemetry proves the action mask and signs were exact:

- maximum absolute applied x/speed action: `0`;
- front z was always non-positive and rear z always non-negative.

Training reduced overall z magnitude relative to the v10-checkpoint
counterfactual, but learned a systematic rear left/right imbalance. In phase
8:

- successful applied z means were
  `[-0.0318, -0.0261, +0.0184, +0.0454]`;
- collision applied z means were
  `[-0.0279, -0.0220, +0.0221, +0.0518]`;
- mean rear physical magnitude mismatch was about `0.0313` for successes and
  `0.0358` for collisions.

At the 0.01 m z bound, collision rows lifted the rear-right wheel center by
about 0.52 mm but the rear-left by only 0.22 mm. This roll-inducing twist is
consistent with all ten contacts occurring on the front-right lower link.
The soft raw-action asymmetry reward did not enforce physical symmetry after
the absolute-value map.

## Registered next action

Create runtime v12 with the same z-only phase-7--8 authority, but hard-tie
left/right physical magnitudes:

1. front-left/front-right both execute the negative mean absolute front z
   magnitude;
2. rear-left/rear-right both execute the positive mean absolute rear z
   magnitude;
3. x and wheel-speed residuals remain exactly zero;
4. all 12 raw outputs remain observable and regularized.

Run unit tests and a real-Isaac sign/mask/tie smoke, then a full
development-only counterfactual using the existing v11 checkpoint. Retrain
from scratch only if bilateral tying materially improves paired behavior.
Frozen FSM, metrics, asset, success definition, network/PPO, randomization,
seeds, and B/C-only CoM difference remain unchanged. The locked manifest
remains unopened.
