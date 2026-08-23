# Method-B v17 seed-11 50 mm real-Isaac smoke attempt001

`SMOKE_PASS`.

- One full-randomization Isaac environment restored the v17 model and
  produced a finite `1 x 12` sampled action with maximum absolute value
  `0.04842373`; critic output and all 22 reward terms were finite.
- The registered probe produced exactly 2 mm balanced z residual in phases
  7 and 9 and exactly zero physical residual in phases 6 and 10.
- Direction, z-only mask, bilateral ties, four-wheel balance, and the
  reversed-action exact-off half-space all passed.
- The forced fall terminated with the exact `-200` fall term and a finite
  total reward. Partial reset and the next post-terminal step were finite
  and non-terminal.
- Provenance records common config raw/canonical SHA-256
  `820afe4fbcbf32b6f7fe000fdc24532eba25f1f3a84d0a8160bb149e4b9ce7ec`
  /
  `cdaaff91a9b21d1ad8291dafcdaee9ff2c9da9a6eb73474e74a838ccf96f2b00`,
  model source
  `97e7f1974ef79b71250d9ea5e215b0ffd86495304901da8f384ca21b36e0f14e`,
  and training source
  `6b13d231d7e33510cb841a2d7157ac8cb97b562a5e1e95a50e16de5305fb425d`.
- Environment Python PID `169236` exited normally before the launch wrapper
  could report the already-completed process.

Artifact SHA-256:

- training result:
  `52c5abe731fa9e0cf3a8f609b0cd66396d813cc84d8b37735dfa6ed824793462`
- stdout:
  `0fc5cf22e47a341b2225c6850a42060115090ca65411e746018246a1e0963ec3`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: execute the pre-registered from-scratch 64-environment Method-B
seed-11 50 mm run for exactly 76,800 local timesteps / 4,915,200
transitions.
