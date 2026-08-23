# Method-B v24/v19-checkpoint 50 mm restore smoke attempt001

## Disposition

`PASS`. The deliberate 5 s diagnostic timeout is not a traversal result.

The explicit v19 final checkpoint restored under the registered v24 runtime
with exact checkpoint, config, asset, FSM, metrics, and source provenance.
The one-scenario telemetry is `100 x 122`, every numeric value is finite,
and it is byte-identical to the v23 and v22 restore telemetry because the
nominal trajectory remains below both registered IMU gates.

- Pitch range: `-0.02682234` to `-0.01302254 rad`.
- Roll range: `+0.00110248` to `+0.00645004 rad`.
- Maximum raw policy action: `0.06887523`.
- Executed action and scaled physical residual: exact zero.
- Restored checkpoint:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.

## Artifacts

- Result:
  `3d3dc9cf6913f5ea3ff7a9009ddc0a3ffec7dd9fff676b1565f4aadba192009b`
- Episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- Status:
  `88d73f8612c060021de736b776128d87f8a1b2096e0e19f79847fbe62c46c9be`
- Telemetry:
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`
- Stdout/stderr:
  `e263dda09ac60509152599e625d66b126b7bbb1080382407078b4f2502ad7eab`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `92144`; it exited naturally.

## Next action

Run the unchanged 20-scenario 50 mm v24 counterfactual. Promotion requires
at least 16/20, retention of all 12 frozen-FSM successes plus `0009`,
exercised early/latching and phase-10 diagonal correction, and zero
constraint violations.
