# Method-B runtime-v10 seed-11 evaluator smoke attempt001

## Disposition

`SMOKE_PASS`. The independent evaluator restored the explicit full-development
checkpoint and completed a one-scenario/five-second diagnostic. The deliberate
timeout is excluded from performance and selection.

- Environment Python PID: `129620` (exited normally).
- Checkpoint SHA-256:
  `679461e49cae1c5579496da4709619ffa76cc771a15aa53fdc86398780ea3aa4`.
- Result/episodes/status/telemetry SHA-256:
  `17772db5698d5b96bb27864e37d86c9fdcf8b3feddaf16ce3dfa7c659674d0d3`,
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
  `01b2408c2087dd0fedde8e1836d8e2c9d94eebedb272574cbc9df3f583cf5239`,
  and
  `b020cd71333153aee69a24cc9c6e986e38744a8b151ae37c2e8ad632c758f272`.
- stdout/stderr SHA-256:
  `956e136a5e81abc9a6db0b1c2758897e0b5e82f0bd6c9d7dd93b11ffeef088c7`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- Telemetry is uniformly `100 x 122`; all 64 action-chain fields are finite.
- Recorded phases were 0/1. Policy max-abs was `0.1022275`, while projected
  `executed_action_*` max-abs and scaled residual max-abs were both exactly
  zero. The revised executed-action semantics are therefore verified on a
  nonzero restored policy.
- Provenance records exact checkpoint/config/source/frozen/manifest hashes,
  direction signs `[-1,-1,+1,+1]`, window `[7,8]`, bounds, reward, and
  simulator/library versions.
- Evaluator execution passed without an internal failure.

## Next action

Run the same checkpoint and deterministic evaluator on all 20 fixed 50 mm
development scenarios with the registered 150-second limit. Promotion
requires at least 16/20.
