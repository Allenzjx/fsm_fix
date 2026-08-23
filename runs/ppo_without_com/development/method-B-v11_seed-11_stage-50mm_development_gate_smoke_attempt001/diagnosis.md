# Method-B runtime-v11 seed-11 50 mm evaluator smoke attempt001

## Disposition

`SMOKE_PASS`. The deterministic evaluator restored the exact v11 final
checkpoint, recorded complete v11 provenance, and completed one development
scenario for the deliberate five-second limit. The timeout is excluded from
performance evidence.

- Environment Python PID: `108892` (exited normally).
- Result SHA-256:
  `a016e4fb795e44d97b9b27d2781b688f73fb92d77b65e5464da52c45f9fc1d47`.
- Episode/status/telemetry SHA-256:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
  `d3b0641ee41897795523f22e120bd474879f63c930709334922ecb72a06cc1cc`,
  and
  `4dbfeff8a251418a53cc1e9a651c0145903e3cd488ac4a8341adf15ccf577ce0`.
- stdout/stderr SHA-256:
  `28a9dad367b8d74c6c710bcd54ca238d156d068d60d0261a2241dc95b62502da`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- Telemetry is a uniform 100 x 122 table with finite action-chain values.
- In observed phases 0/1, policy max-abs was `0.0933611`, while executed
  actions, scaled wheel-center residuals, and wheel-speed residuals were all
  exactly zero.
- Provenance records checkpoint SHA-256
  `29ac9c122b6741500d12f086f39daf768d9a88310715d1f62bdfa60acfbab418`,
  common config SHA-256
  `7a37e165aa803e1c876fd3b7c30194078f4b93895f1d18430300ee4d16daafa3`,
  projection type `wheel_center_z_signed_magnitude`, and the exact action
  mask.
- The real-Isaac training smoke separately exercised enabled phases 7/8 and
  proved the complete signed-magnitude applied vector.

## Next action

Run all 20 fixed 50 mm development scenarios for 150 seconds with this exact
checkpoint and unchanged sources/configuration. Promotion requires at least
16 successes.
