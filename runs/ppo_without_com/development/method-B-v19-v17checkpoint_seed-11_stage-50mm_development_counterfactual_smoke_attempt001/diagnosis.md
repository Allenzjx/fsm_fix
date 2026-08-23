# Method-B v19 / v17-checkpoint deterministic restore smoke attempt001

`RESTORE_PASS`, `CONSTRAINT_PASS`, `PERFORMANCE_EXCLUDED`.

- The unchanged v17 final checkpoint restored with SHA-256
  `e29c94d54a12e895c8a8e3ba1c2aea726df3b5559d5ce693dbc09ac439f5a102`.
- The deliberate one-scenario five-second timeout produced exactly
  `100 x 122` fully finite telemetry.
- Maximum deterministic policy action was `0.08164108`; maximum observed
  pitch was `-0.01302254 rad`, below the hazard threshold, so all executed
  and scaled physical residuals were exactly zero.
- The telemetry is byte-identical to the v17/v18 restore smokes, confirming
  deterministic checkpoint restoration and exact nominal-state FSM
  preservation.
- Provenance records v19 config/source hashes, zero-preserving projection,
  real-IMU gate and `+0.09 rad` threshold, and frozen artifacts.

Artifact SHA-256: result
`eb66def5509e9534f023df4b9864286f22f871b49baab6c1cbd8f01e2da22b84`,
episodes
`3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
status
`d6ea58ea755a5287c141a72564e8369f82a483a0f529b885304f82b120b466ea`,
telemetry
`cff4b69b6653858982baa724a0b00c59c7b853d0d85dc96e52b96c8de012cea7`,
stdout
`56599bd0efd435288b8d1328f170d6644c1ae868660ecab274755d6b125fd6b4`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: execute all 20 fixed 50 mm development scenarios under v19.
