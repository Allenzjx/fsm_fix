# Method-B v22/v19-checkpoint restore smoke attempt001

## Disposition

`RESTORE_PASS`. The deliberate five-second timeout is performance-excluded.

- Explicit v19 final checkpoint SHA-256 is exact.
- Telemetry is `100 x 122` and fully finite.
- Pitch remains `-0.02682234` to `-0.01302254 rad`.
- Maximum raw policy action is `0.06887523`; executed and scaled residuals
  are exact zero.
- Telemetry is byte-identical to the v19/v21 restore smokes.
- V22 config/source/asset/FSM/metrics/development-manifest provenance is
  exact.

## Artifacts

- Result:
  `87f4b97e86eaf533a4b87dd34a35b33ff19dd1fe373133f55847ad589499ebef`
- Episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- Status:
  `0a923ab132351af319597bda2692c913030a4a4801fcc35162b342c9a13d57ee`
- Telemetry:
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`
- Stdout/stderr:
  `e3763b488444ebca2ac070b5510152b2978adfe72843d7fa45d00eebd80869d3`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `135924`; it exited naturally.

## Next action

Run the unchanged 20-scenario v22 counterfactual under the fixed
authorization rules.
