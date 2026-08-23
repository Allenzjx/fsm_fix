# Method-B runtime-v9 seed-11 50 mm training attempt001

## Disposition

`TRAINING_INTEGRITY_PASS`. This is a new from-scratch run under the registered
v9 common protocol. It completed exactly **19,200 local timesteps** and
**1,228,800 environment transitions** in 64 real Isaac environments. This
status establishes only training and artifact integrity; checkpoint
performance remains unproven until deterministic development evaluation.

- Environment Python PID: `110716` (exited normally).
- Final checkpoint SHA-256:
  `fafc0ada9dadb12f49ebe98d7fbc258ff432d0a20d2ade3d2af6cccfb8834140`.
- `training_result.json` SHA-256:
  `e2b5d9a1924e6fc1fe75682dfd46cbd2759bf4d69e32730c0e160ae54bf7db8f`.
- TensorBoard event SHA-256:
  `c7bb10558819d08c2c01219a40b747f0c92a4b75d6e96ab86240bd01a1a6d28d`.
- stdout/stderr SHA-256:
  `7e85f31bb09e88f2c4b473486387c06f791aeb5b4e23f190f94751e6d110db63`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Integrity evidence

- Requested and completed local/cumulative timesteps and transitions agree
  exactly; `resume_offset_timesteps=0` and no checkpoint was loaded.
- The final checkpoint contains 77 tensors / 785,093 elements. Every floating
  and complex element is finite; the non-finite count is zero.
- All 11 core optimization/runtime scalar series contain exactly 300 finite
  updates from step 64 through step 19,200.
- The six repaired episode tracker series contain 36 finite windows.
  Episode-length extrema were 6,445--8,999 steps; there is no recurrence of
  the false 168-step env-0 segment.
- Instantaneous reward maxima reached `200.0108`, proving success-bonus
  transitions occurred in training; instantaneous minima reached `-200.2652`,
  proving safety-terminal transitions also occurred. These are training
  distribution signals, not evaluation outcomes.
- Policy standard deviation remained finite and ended at `0.1021474`.
- The runtime provenance records the v9 phase window `[7, 8]`, common config
  hash `52311feb...d138`, frozen FSM/metrics/asset hashes, exact source hashes,
  full randomization bounds, reward weights, versions, and GPU.

## Next action

Restore the explicit final checkpoint in the independent evaluator and run a
one-scenario, five-second diagnostic smoke. It must verify exact provenance,
finite deterministic action-chain telemetry, and zero physical residual
outside phases 7--8 before the unchanged 20-scenario 50 mm development gate.
