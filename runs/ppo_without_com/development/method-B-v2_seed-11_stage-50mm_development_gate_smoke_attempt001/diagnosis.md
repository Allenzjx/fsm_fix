# Method B reward-v2 seed-11 50 mm development-gate smoke attempt001

- Status: execution `PASS`.
- Scope: the first registered 50 mm development scenario, deliberately
  truncated at 5 seconds; the resulting `0/1` timeout is excluded from all
  performance claims.
- Deterministic checkpoint:
  `c02026df0f913c6761e1354f6026928421896d5e570dd1e1c848ce13852d8706`.
- PPO common config:
  `034019e479cbe64fd5b1b8d5207a55920a72cadb094f394dcbbffcdd9e5d127e`.
- Method-B config:
  `d27d84488d692a4af2764859ae55cf913803b0e9645a4abf2796a2cd65a2e8b1`.
- The evaluator restored the complete checkpoint and executed deterministic
  mean actions through the real Isaac articulation.
- Telemetry contains 100 data rows and 122 columns. Every row has exactly 122
  fields, all numeric values are finite, and all 64 expanded action-chain
  fields are present (policy action, delayed/executed action, scaled
  residuals, requested/final wheel-center targets, and final servo/wheel
  targets).
- Artifact SHA-256 values:
  - `episodes.jsonl`:
    `2e1d1b4eb165fc494d4f43e07649abdc59a7eb3bae91637afbd6325cf51e779e`
  - `result.json`:
    `ae838366679ac42b7b7c99e1e8f49d14ad3e3de5c22bf48f7eec18fcd936fda2`
  - `status.json`:
    `6576834d53b3ff9a364e5edf2da9d94d32e4581091ce716fca980dc0d412832b`
  - `telemetry.csv`:
    `2f8029598f1fb99d1f3c9d58931a74d462cb2dd15880f1f6b4081ab337e9bf81`

This integration smoke authorizes the unchanged 20-scenario, 150-second
development gate. It is not evidence of policy performance.
