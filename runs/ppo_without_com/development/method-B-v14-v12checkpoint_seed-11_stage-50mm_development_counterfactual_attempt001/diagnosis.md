# Method-B v14 / v12-checkpoint 50 mm counterfactual attempt001

`EXECUTION_PASS`, `RETRAINING_EVIDENCE_FAIL`. All 20 fixed 50 mm
development scenarios completed under v14 semantics with the exact v12
Method-B seed-11 final checkpoint. The locked test manifest was not read.

- Success: `9/20`, versus `8/20` under v13 and `7/20` under v12 with the
  same checkpoint.
- Success IDs:
  `0000,0001,0002,0010,0011,0012,0013,0016,0019`.
- Failures: six `BODY_OR_LINK_COLLISION`, all with terminal
  `front_right_bot` force, and five `FSM_PHASE_TIMEOUT`.
- Delay groups (success/total): delay 0 = `2/5`, delay 1 = `2/6`, delay 2 =
  `5/9`. Only delay-2 scenario `0019` changed from v13 global timeout to
  success.

All 52,254 x 122 telemetry rows have exact phase gating, z-only masking,
signs, bilateral ties, and four-wheel balance. The action chain is finite;
5,844 undefined values occur only in `margin_m`. Maximum absolute policy,
executed, and scaled values were `0.3428333`, `0.0984901`, and
`0.000984901 m`.

V14 did not change the six collision scenarios or the five phase-timeout
scenarios from v13. In phase 9, successful episodes averaged about
`0.286 mm` shared physical magnitude, while the five timeout episodes
averaged about `0.223 mm`; all timeout episodes ended with diagonal
full-wheel flags `[true,false,false,true]`. Continuing the unchanged
projection through phase 9 therefore helped only one global-timeout case and
is insufficient evidence for a full v14 retrain.

The next bounded diagnostic is v15: retain the exact v14 projection and
window, but multiply only phase-9 applied action by `1.5` before the existing
hard action/physical bounds. This preserves zero input, signs, masks,
bilateral ties, four-wheel balance, and the 10 mm physical bound. The factor
moves the measured timeout mean to roughly `0.335 mm`, near the observed
successful range, without changing phases 7 or 8.

Artifact SHA-256:

- `result.json`:
  `537e53790ff02b2fb702d0ae351d423b23fd835cc2b0666c2218a15e07eb33ca`
- `episodes.jsonl`:
  `ce4699a07645cdacba56d0fe55d3d01f7f322c4c54d342d44944eaa948cdf707`
- `status.json`:
  `e90e19879a0d3a16023b4c7c13d0e47c60114342db5b54e80f7007ae5fb3a1ae`
- `telemetry.csv`:
  `e8a1bd25d99acdb519964bce00c1147962eb62f94123847864c8f26dcfe2c945`
- stdout:
  `54c45af8ca9e3c6a8d76f23367131040e4195054ec8712074302793077383854`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
