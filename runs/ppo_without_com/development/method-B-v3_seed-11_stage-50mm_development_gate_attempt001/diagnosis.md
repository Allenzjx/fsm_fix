# Method B reward-v3 seed-11 50 mm development gate attempt001

- Status: execution `PASS`; curriculum promotion `FAIL`.
- Deterministic final checkpoint:
  `d3509ab1dbebc658cefdbf00aef77766e4ec574263c5c8c99ca3dfef1ad62a2e`.
- Outcome: `2/20` success (10%) versus the registered `16/20` minimum.
- Failures: 12 `BODY_OR_LINK_COLLISION`, two `FSM_PHASE_TIMEOUT`, and four
  global `TIMEOUT`.
- All 12 collisions were `front_right_bot`; mean/max terminal force was
  10.15/18.15 N.
- Successful scenarios: `development-h050-0001` and
  `development-h050-0018`.
- Episode end time: mean 122.76 s, range 107.50--149.95 s.
- Mean episode-minimum quasi-static margin was -0.12932 m and mean
  support-transfer pitch-rate RMS was 0.06297 rad/s. The margin aggregate
  includes all failed episodes and is not an improvement claim.
- Phase-8 mean deterministic action L2 fell from reward-v2's 0.667 to 0.289.
  Mean absolute normalized left/right differences were 0.106/0.022 for front
  dx/dz, 0.115/0.050 for rear dx/dz, and 0.045/0.032 for front/rear wheel
  residuals. The v3 regularizer materially reduced but did not eliminate
  asymmetric correction.
- Telemetry contains 49,124 finite data rows and 122 columns.
- Artifact SHA-256 values:
  - `episodes.jsonl`:
    `52658935a99ac504501c8135113a70ed03580cba1f28c6ea1fbd83d3c84ad451`
  - `result.json`:
    `65b2c74e68765ef08a00b0160c62f784e24a058417fa4d855814f0cb96a3f78c`
  - `status.json`:
    `ff636d3f28137ead8146368d4e1ae97f7e507974057b07956d469514c99b7045`
  - `telemetry.csv`:
    `8d64c4722ad23e0c9f7420423fe0e2815ed64789b2c547b276ade397f27eefe1`

Reward v3 is a real improvement over v2's 0/20 and 20 collisions, but it
remains substantially worse than the frozen FSM's 12/20 result and cannot be
promoted. Reward v4 will preserve the v3 terminal/time scale while increasing
normalized residual anchoring from -0.5 to -2.0, increasing left/right
asymmetry regularization from -1.0 to -3.0, and halving all three physical
residual bounds to 7.5 mm x, 10 mm z and 0.10 rad/s wheel speed. It must
retrain from random initialization.
