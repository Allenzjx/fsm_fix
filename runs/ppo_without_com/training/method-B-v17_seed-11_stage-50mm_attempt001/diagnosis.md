# Method-B runtime-v17 seed-11 50 mm full training attempt001

## Disposition

`COMPLETED_INTEGRITY_PASS`. Method B seed 11 trained from random
initialization under runtime v17 for exactly **76,800 local timesteps /
4,915,200 transitions** in 64 real Isaac environments. Performance remains
unclaimed pending deterministic development evaluation.

- Environment Python PID `148696` exited normally.
- Final checkpoint SHA-256:
  `e29c94d54a12e895c8a8e3ba1c2aea726df3b5559d5ce693dbc09ac439f5a102`.
- Training result SHA-256:
  `c48f2b852bd718356959541985a7c6f85a6b3cccdadfe52e90d2f35e5ebff165`.
- Event/stdout/stderr SHA-256:
  `1a0dfabf44a3a0c997594599265b151d330db223a52a2a3fa92cb062cbec0c19`,
  `4a72443e904c59f42d960a0081e40f5c3785d6635cc8719052518d4e434ea92d`,
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.
- The final checkpoint contains 77 tensors / 785,093 elements, all finite.
- All 77 tensors in `agent_76800.pt` and `final_agent.pt` are exactly equal.
- The run produced 48 periodic checkpoints plus `best_agent.pt` and
  `final_agent.pt`.

## Budget and event audit

- Requested/completed local timesteps: `76800 / 76800`.
- Requested/completed cumulative timesteps: `76800 / 76800`.
- Requested/completed local transitions: `4915200 / 4915200`.
- Requested/completed cumulative transitions: `4915200 / 4915200`.
- TensorBoard contains 16 scalar tags and 14,184 scalar samples, all finite.
  V17 intentionally has no entropy-loss tag because entropy scale is zero.
- All 1,200 core optimization samples span exact steps 64--76,800.
- The repaired episode tracker emitted 364 windows with mean-window lengths
  spanning 3,822--8,999 steps.
- Policy effective standard deviation remained inside the registered
  envelope, decreasing from `0.01831381` to `0.01801370`.
- Total-return windows remained highly variable: minimum `-239.6332`,
  maximum `+270.2798`, and final 25-window mean `-64.6833`. These training
  statistics are not used as a development performance claim.

## Provenance

The run records v17 common config SHA-256
`820afe4fbcbf32b6f7fe000fdc24532eba25f1f3a84d0a8160bb149e4b9ce7ec`
(canonical
`cdaaff91a9b21d1ad8291dafcdaee9ff2c9da9a6eb73474e74a838ccf96f2b00`),
model source
`97e7f1974ef79b71250d9ea5e215b0ffd86495304901da8f384ca21b36e0f14e`,
training source
`6b13d231d7e33510cb841a2d7157ac8cb97b562a5e1e95a50e16de5305fb425d`,
and frozen FSM/metrics/asset hashes. No prior checkpoint was loaded.

## Next action

Run a one-scenario five-second deterministic evaluator/provenance smoke with
the explicit final checkpoint. Require uniform finite telemetry and all
exact phase/projection constraints, then run the unchanged 20-scenario
50 mm development gate requiring at least 16/20.
