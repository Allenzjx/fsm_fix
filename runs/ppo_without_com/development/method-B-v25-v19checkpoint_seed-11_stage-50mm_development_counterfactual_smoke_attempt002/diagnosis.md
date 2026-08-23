# Method-B v25/v19-checkpoint restore smoke attempt002

## Disposition

`PASS`. The deliberate 5 s diagnostic timeout is not a traversal result.

The explicit v19 final checkpoint restored under the registered v25 runtime
with exact checkpoint, config, asset, FSM, metrics, and evaluation-source
provenance.

- Telemetry is `100 x 122`; every numeric value is finite.
- Pitch range: `-0.02682234` to `-0.01302254 rad`.
- Roll range: `+0.00110248` to `+0.00645004 rad`.
- Maximum raw policy action: `0.06887523`.
- Executed action, scaled physical residual, and wheel-speed residual are
  exact zero.
- Telemetry is byte-identical to the v24/v23/v22 restore artifact.
- Restored checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.

## Artifacts

- Result:
  `004bd2c82235b22e33e273fcd924a198190351856e47ea209f0169a164c2f85e`
- Episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- Status:
  `6b9132af95b00be8740dac07989bb0cc743e8aea0a3b2afd7d7b9aecf20169d7`
- Telemetry:
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`
- Stdout/stderr:
  `013601d688e06ad4845c921580e7ae5982fbcdeca972ab84f3b6ea8a5f7b572e`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `161808`; it exited naturally.

## Next action

Run the unchanged fixed 20-scenario 50 mm v25 counterfactual. Promotion
requires at least 16/20, retention of all 12 frozen-FSM successes plus
`0009`, physically realized front-right correction, and zero constraint
violations.
