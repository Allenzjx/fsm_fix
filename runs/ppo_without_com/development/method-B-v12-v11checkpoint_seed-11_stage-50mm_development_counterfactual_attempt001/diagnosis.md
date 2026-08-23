# Method-B v12 / v11-checkpoint development counterfactual attempt001

The full 20-scenario development-only counterfactual completed normally under
environment Python PID `78068`. It passed execution and achieved `9/20`
successes (`45%`), versus `6/20` for the exact same v11 checkpoint under v11
physical projection semantics. This diagnostic result is not a
promotion-eligible checkpoint evaluation.

- Retained v11 successes: `0001`, `0002`, `0012`, `0013`, `0016`.
- Newly successful: `0000`, `0011`, `0014`, `0019`.
- Lost: `0010`.
- Failures: eight `BODY_OR_LINK_COLLISION`, two `FSM_PHASE_TIMEOUT`, and one
  `TIMEOUT`. Every collision was on `front_right_bot`.
- Delay groups (success/total): delay 0 = `2/5`, delay 1 = `2/6`, delay 2 =
  `5/9`.
- The 50,719 x 122 telemetry table contains no non-finite action-chain value.
  Its 5,839 non-finite values occur only in `margin_m`, where the metric is
  undefined for invalid support configurations and is separately counted by
  each episode's valid/invalid margin samples.
- Phase gating, the z-only action mask, front-negative/rear-positive signs,
  and both left/right ties hold exactly on every telemetry row.
- Maximum absolute policy, projected action, and scaled wheel-center residual
  were `0.3372396231`, `0.1544433832`, and `0.0015444338 m`.
- Mean phase-8 scaled z residuals `[FL, FR, RL, RR]` were
  `[-0.0002937302, -0.0002937302, +0.0003183864, +0.0003183864] m`
  for successes and
  `[-0.0002592066, -0.0002592066, +0.0003679868, +0.0003679868] m`
  for collision failures.

Provenance remained exact: checkpoint
`29ac9c122b6741500d12f086f39daf768d9a88310715d1f62bdfa60acfbab418`,
v12 common config
`f171dba0270c31fb1571c9e4ff86c9524a2eb32cd4927c33f8bc6b04b9f5251a`,
FSM
`3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`,
metrics
`6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`,
asset
`98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`,
and development manifest
`f3d10d7340c06f78c200c44119bb2e17c81e587bd314b342ac90b49019ea2cdc`.

Artifact SHA-256:

- `result.json`:
  `9c0fa38490837194a6c1e69e12e65dbbacc8f75787fce61d5638132b48927efe`
- `episodes.jsonl`:
  `88f9c0562bd339ee5f3a90be113219d6df149670716a2353c18762b9c0abfb54`
- `status.json`:
  `cf239455a0fcc72fb68bb2aed5aadee3848492b91585fb0d147a5ea5480b22ce`
- `telemetry.csv`:
  `e76358c3c13943b8aa93340340f0473b55d9f683e3948e07b4a968df03cbd7df`
- stdout:
  `b99c833bc5da30b1e0bcf66b1ec66b120c16f549a53ad96cabc2cd6c38f42234`
- stderr (expected 71-byte conda wrapper message):
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

The paired +3 improvement, with exact hard constraints, justifies one new
full-budget v12 Method-B seed-11 training run from random initialization.
Eligibility still requires an independent deterministic 50 mm development
gate of at least `16/20`.
