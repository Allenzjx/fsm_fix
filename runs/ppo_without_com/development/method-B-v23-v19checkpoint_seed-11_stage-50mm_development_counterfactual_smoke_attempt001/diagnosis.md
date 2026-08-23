# Method-B v23/v19-checkpoint 50 mm restore smoke attempt001

## Disposition

`PASS`. The deliberate 5 s diagnostic timeout is not a traversal result.

The explicit v19 final checkpoint restored under the registered v23 runtime
with exact checkpoint, config, asset, FSM, metrics, and source provenance.
The one-scenario telemetry is `100 x 122`, every numeric value is finite,
and it is byte-identical to the v22 restore telemetry because the nominal
trajectory remains below both roll gates.

- Pitch range: `-0.02682234` to `-0.01302254 rad`.
- Roll range: `+0.00110248` to `+0.00645004 rad`.
- Maximum raw policy action: `0.06887523`.
- Executed action and scaled physical residual: exact zero.
- Restored checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.

## Artifacts

- Result:
  `9f833c535db60ba852056881f4a5162a152453f9e2e5eefca1ba1b6d06fe690d`
- Episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- Status:
  `b67ccc32198d7e2b3d4fff3d2dae6be8806113de3e6e9ab7e30f3f618f0c6a34`
- Telemetry:
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`
- Stdout/stderr:
  `75b0c275b8ddf1d9d9759087e270f002c7fc9fb5cbc2bb13aa35b9ba337c25af`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `135572`; it exited naturally.

## Next action

Run the unchanged 20-scenario 50 mm v23 counterfactual. Promotion requires
at least 16/20, retention of all 12 frozen-FSM successes plus `0009`,
exercised early/latching and phase-10 pure-roll correction, and zero
constraint violations.
