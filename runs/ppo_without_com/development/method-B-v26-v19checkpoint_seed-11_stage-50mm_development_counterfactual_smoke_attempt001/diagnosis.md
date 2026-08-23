# Method-B v26/v19-checkpoint restore smoke attempt001

## Disposition

`PASS`. The deliberate 5 s timeout is diagnostic only and is not a
traversal result.

The explicit v19 final checkpoint restored under the registered v26 runtime
with exact checkpoint, config, asset, FSM, metrics, and evaluation-source
provenance.

- Canonical invocation used `record_stride=3`, producing exactly `100 x
  122` telemetry cells after the header.
- Every numeric telemetry value is finite.
- Policy-action maximum absolute magnitude is `0.06887523`.
- Executed action, scaled wheel-center residual, and scaled wheel-speed
  residual maxima are all exactly zero.
- Roll remained `+0.00110248` to `+0.00645004 rad`; pitch remained
  `-0.02682234` to `-0.01302254 rad`, below every registered gate.
- Telemetry SHA-256 is
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`,
  byte-identical to canonical v25/v24/v23/v22 restores.
- Restored checkpoint SHA-256 is
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.

## Artifacts

- Result:
  `d99c5606302daeecb413005b11d46d41cef3498d1613d3343c3afb6583817c76`
- Episodes/status:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
  `e876f11c6d81ab2d3ede588c8a5bdeb98576332ebbeb3e29ae0f85ddc4bca37f`
- Stdout/stderr:
  `dc1a0bedae68dfae9f63b05e44c3ab8de28b43fd0a3023a4224931d103777e59`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `162408`; it exited naturally.

## Next action

Run the registered v26 runtime with the unchanged v19 checkpoint on all 20
fixed 50 mm development scenarios. Training remains prohibited unless the
result reaches at least 16/20, retains all frozen-FSM successes plus `0009`,
physically realizes authorized corrections, and has zero constraint
violations.
