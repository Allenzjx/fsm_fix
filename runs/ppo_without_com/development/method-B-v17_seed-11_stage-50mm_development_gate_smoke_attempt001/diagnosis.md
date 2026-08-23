# Method-B v17 seed-11 final-checkpoint development smoke attempt001

`RESTORE_PASS`, `CONSTRAINT_PASS`, `PERFORMANCE_EXCLUDED`.

- The explicit final checkpoint restored with SHA-256
  `e29c94d54a12e895c8a8e3ba1c2aea726df3b5559d5ce693dbc09ac439f5a102`.
- The deliberate one-scenario five-second timeout produced exactly
  `100 x 122` fully finite telemetry.
- Maximum absolute deterministic policy action was `0.08164108`.
- Phases 0/1 produced exact zero executed and scaled residuals. Disabled
  dimensions, paired z values, and four-wheel balance all have zero error.
- Common config SHA-256
  `820afe4fbcbf32b6f7fe000fdc24532eba25f1f3a84d0a8160bb149e4b9ce7ec`
  and model source SHA-256
  `97e7f1974ef79b71250d9ea5e215b0ffd86495304901da8f384ca21b36e0f14e`
  match training provenance.
- Environment Python PID `89436` exited normally.

Artifact SHA-256: result
`dca94929f5087bb72dbf92556df4a8d67570f4ffdd3e019c1980fc334d2c9c5b`,
episodes
`3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
status
`9d7e52dc0d38406c6d029975cb8fdbb93b9fa95b24f7c35f94b7d92b222b5b0a`,
telemetry
`cff4b69b6653858982baa724a0b00c59c7b853d0d85dc96e52b96c8de012cea7`,
stdout
`220f975dad1ab3140a493eab88de95633423113f15c264fa38e0c46f432794b3`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: run all 20 fixed 50 mm development scenarios with the unchanged
150-second limit and require at least 16 successes.
