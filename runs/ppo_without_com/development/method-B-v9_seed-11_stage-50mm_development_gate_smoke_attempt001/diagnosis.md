# Method-B runtime-v9 seed-11 evaluator smoke attempt001

## Disposition

`SMOKE_PASS`. The independent evaluator restored the explicit final
checkpoint and completed one development scenario under a deliberate
five-second diagnostic time limit. Its 0/1 timeout is excluded from
performance claims and checkpoint selection.

- Environment Python PID: `102036` (exited normally).
- Checkpoint SHA-256:
  `fafc0ada9dadb12f49ebe98d7fbc258ff432d0a20d2ade3d2af6cccfb8834140`.
- Result/episodes/status/telemetry SHA-256:
  `8084b8ab43d4526811c18533eb96b07279335a2e104c842b6c3f66cfacf022c5`,
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
  `55c2341f5729b8a7b25857812a87b0201b4070495a0c440cb3e81c916308e02e`,
  and
  `809c3f701f6b848bdfdf6319a45e40f4e9fb014371c948d9adacf1ca9df51a09`.
- stdout/stderr SHA-256:
  `c8b65552f5099aeb3a4164814a05082646ce8160780f5904637ae70de01fe095`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- The telemetry table is uniformly `100 x 122`.
- All 64 policy/executed/scaled/requested/final action-chain fields are
  present and finite on every row.
- Recorded phases were 0 and 1. Policy action max-abs was `0.0774652`, while
  physical scaled-residual max-abs was exactly `0`, directly verifying the
  v9 phase gate on a restored nonzero deterministic policy.
- Result provenance records the exact checkpoint, common config, frozen
  FSM/metrics/asset, development manifest, source files, simulator/library
  versions, action bounds, reward weights, and execution window `[7, 8]`.
- Evaluator execution passed with no internal failure.

## Next action

Run the same restored checkpoint, source, configuration, and deterministic
mean-action evaluator on all 20 fixed 50 mm development scenarios with the
registered 150-second episode limit. Promotion requires at least 16/20.
