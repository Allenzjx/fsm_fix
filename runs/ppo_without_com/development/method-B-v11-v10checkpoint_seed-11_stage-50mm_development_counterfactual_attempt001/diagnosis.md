# Method-B runtime-v11 / v10-checkpoint 50 mm counterfactual attempt001

## Disposition

`DIAGNOSTIC_PASS_NOT_PROMOTABLE`. Execution, provenance, action semantics, and
artifact integrity passed. The existing v10 checkpoint achieved **7/20
(35%)** under v11 physical semantics, below the registered **16/20 (80%)**
gate. Because this checkpoint was not trained under v11 semantics, it is not
promotion- or validation-eligible regardless of score. The result establishes
causal development evidence for a new from-scratch v11 run.

- V10 checkpoint SHA-256:
  `679461e49cae1c5579496da4709619ffa76cc771a15aa53fdc86398780ea3aa4`.
- Result SHA-256:
  `d55bb2c787de9deaf86c8e4dca7e481ffd7ce621ee1d5db7155cf41331c9a41c`.
- Episode/status/telemetry SHA-256:
  `3a9da156c6c3eb1aeb8144c680a5802a7d775c0a72cee20f190d184cb1288e35`,
  `305d46fbffbb6786d094e86b4c9afe5dc1f710c3ac9fcb5702428f4f0b4843af`,
  and
  `d772382263a0bc31d7a99ab8f87b3962811dacf4fe3c2065596f039c1315c993`.
- stdout/stderr SHA-256:
  `464b1e6ad79983b7c3b05cbc2ce962c673fcfa3a47d1291d8b8359af32c3c7b8`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.
- Successes were 0000, 0001, 0002, 0011, 0012, 0013, and 0014.
- Failures were six `BODY_OR_LINK_COLLISION`, five `FSM_PHASE_TIMEOUT`,
  and two global `TIMEOUT`.
- Delay subgroups were 2/5, 2/6, and 3/9 for delays 0, 1, and 2.

## Paired effect

Changing only runtime physical authority raised the same checkpoint from
v10's 2/20 to 7/20. It retained frozen-FSM successes 0000, 0001, 0002, 0011,
0012, and 0014, rescued baseline failure 0013, and lost baseline successes
0004, 0007, 0010, 0015, 0016, and 0018. Relative to v10, it retained 0013,
restored 0000, 0001, 0002, 0011, 0012, and 0014, and lost 0010.

All six collisions were phase-8 `front_right_bot` events. The five phase
timeouts ended in phase 9; four had sub-threshold front-right contact forces
of 1.7--2.0 N. The two global timeouts ended in phase 10 with strict full-top
flags `1110`.

## Action-chain evidence

Across the complete 88 MB telemetry table:

- the maximum absolute applied value in all eight masked x/speed channels was
  exactly `0`;
- all front z applied actions were non-positive and all rear z applied
  actions were non-negative;
- phase-8 successful applied z means were approximately
  `[-0.0407, -0.0872, +0.0800, +0.0799]`, corresponding to
  `[-0.407, -0.872, +0.800, +0.799] mm`;
- phase-8 collision means were approximately
  `[-0.0424, -0.0718, +0.0912, +0.0768]`, corresponding to
  `[-0.424, -0.718, +0.912, +0.768] mm`.

The exact mask removed four of v10's ten collisions and restored five net
successes without changing checkpoint parameters. Remaining outcome
separation is not a single scalar action-magnitude threshold: collision and
success action ranges overlap. A state-conditioned policy must learn z
magnitudes under the restricted authority.

## Registered next action

Train Method B seed 11 at 50 mm from random initialization for exactly 76,800
local timesteps / 4,915,200 transitions in 64 environments under unchanged
v11 semantics. No prior checkpoint is reused. The completed training artifact
must pass finite checkpoint/event/tracker audits and a deterministic evaluator
smoke before its full 20-scenario gate.
