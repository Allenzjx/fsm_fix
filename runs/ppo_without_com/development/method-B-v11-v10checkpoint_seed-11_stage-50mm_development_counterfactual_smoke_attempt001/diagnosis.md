# Method-B runtime-v11 / v10-checkpoint evaluator smoke attempt001

## Disposition

`SMOKE_PASS`. The deterministic evaluator restored the exact v10 final
checkpoint under registered v11 physical semantics and completed one
development scenario for the deliberate five-second limit. The resulting
timeout is excluded from performance evidence.

- Environment Python PID: `33092` (exited normally).
- Result SHA-256:
  `75dfcf71b3424654f1d8ce0d3ab5d3c1857f791526edddeac92d1808421a37bd`.
- Episode/status/telemetry SHA-256:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
  `5590fa9bfd6f9309724b4edc64dbf0cefc56049d1ac7eefd6533644c3b8ac3c7`,
  and
  `ac16d8b3ae6f37f85fa60bda2962c46b455843b8596e6bd0a4e4c6bbdeffb8f4`.
- stdout/stderr SHA-256:
  `d42358a64a82f2678640a5b862035db97dc2071f2c3fd5bc6fca43e0ce39441a`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- Telemetry is a uniform 100 x 122 table; all action-chain values are finite.
- In observed phases 0/1, policy max-abs was `0.1022275`, while executed
  actions, scaled wheel-center residuals, and wheel-speed residuals were all
  exactly zero.
- Provenance records checkpoint SHA-256
  `679461e49cae1c5579496da4709619ffa76cc771a15aa53fdc86398780ea3aa4`,
  common config SHA-256
  `7a37e165aa803e1c876fd3b7c30194078f4b93895f1d18430300ee4d16daafa3`,
  projection type `wheel_center_z_signed_magnitude`, and the exact
  `[0,1,0,1,0,1,0,1,0,0,0,0]` mask.
- The preceding real-Isaac training smoke independently exercised enabled
  phases 7/8 and proved the full signed-magnitude action vector.

## Next action

Run all 20 fixed 50 mm development scenarios for 150 seconds with the same
v10 checkpoint and v11 runtime semantics. This is a diagnostic
counterfactual, not a promotion-eligible trained v11 checkpoint.
