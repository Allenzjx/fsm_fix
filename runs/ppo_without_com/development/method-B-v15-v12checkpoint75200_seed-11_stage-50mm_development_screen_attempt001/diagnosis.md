# Method-B v15 / v12 checkpoint-75200 development screen attempt001

`EXECUTION_PASS`, `CURRENT_DEVELOPMENT_BEST`, `CHECKPOINT_INELIGIBLE`.

- Success: `10/20`
  (`0001,0002,0004,0010,0011,0012,0013,0014,0016,0019`).
- Failures: five `BODY_OR_LINK_COLLISION`, four `FSM_PHASE_TIMEOUT`, and one
  global `TIMEOUT`.
- All 52,818 x 122 telemetry rows have uniform width and preserve exact v15
  phase gating, action masking, four-wheel balanced signed projection, and
  physical scaling (maximum float32 roundoff `7.92e-11 m`).
- The 5,844 non-finite values occur only in geometrically undefined
  `margin_m`; the complete action chain is finite.
- Maximum absolute policy/executed/scaled values:
  `0.2861260` / `0.1186086` / `0.001186086 m`.

Checkpoint 75200 is the current best development candidate, improving over
the v12 final checkpoint under v15 semantics (`9/20`), but it does not meet
the pre-registered `16/20` eligibility threshold. The final pre-registered
candidate, skrl `best_agent` (tensor-identical to checkpoint 70400), remains
to be evaluated.

Artifact SHA-256:

- result:
  `c94db7224e3bf7ede0decc9d59c7cf099eb870ab4a7364bd9be49b8d72995bb9`
- episodes:
  `622b5e316cbdad9aa2c85a18026bfe67c4691477de2e0bcc97982077ac9cfe11`
- status:
  `a450d9b5c40c3f3284bbe36fb4134ecb913f4f27b54cb38b5d1a484614b4f67d`
- telemetry:
  `b3206276e64794cd76bb4b2e51b8af526e45c1423c029d785cd5696b9fa6d321`
- stdout:
  `004fb68fd9c821ec1c079e2ad99436ae82df475f114f4051a10f5377c32930f9`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
