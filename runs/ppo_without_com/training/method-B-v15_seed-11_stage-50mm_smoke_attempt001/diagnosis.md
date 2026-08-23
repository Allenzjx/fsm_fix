# Method-B v15 seed-11 50 mm runtime smoke attempt001

`SMOKE_PASS`. The v15 phase-specific gain completed real-Isaac preflight in
16 fully randomized environments.

- Environment Python PID recorded by the result: `126268`.
- Effective phase-7/8/9 gains: `[1.0,1.0,1.5]`.
- Nonuniform probe execution at phase 7:
  `[0,-0.5,0,-0.5,0,+0.5,0,+0.5,0,0,0,0]`.
- Boundary phase-6/7/9/10 scaled maxima:
  `0/0.0049999999/0.0074999998/0`.
- Phase gate, gain, normalized hard bound, z-only mask, signs, bilateral
  ties, and exact four-wheel balance passed.
- Zero residual remains exact. Actor/critic interfaces, reward terms,
  tracker isolation, forced terminal snapshot, and post-terminal reset
  passed.
- Forced fall contributed the registered one-shot weighted `-200`.
- Post-terminal reset distance error was `0.00132722 m`.
- Common config SHA-256:
  `2cf5437c3541c21c82dc221fec77c09b3f9d4c9ad52fbaf43d9dc6dc0f74cb11`
  (canonical
  `f260aa605ec9dc229749a8c1e418333d6c1f9fbdd1f4f2a2e36b5f452db6c73c`).

Artifact SHA-256:

- `training_result.json`:
  `7e7437e2872ba355a17bf0f9a503785a731ab572471ecc361bdeba834c35b63c`
- stdout:
  `2bf31bf7a552c3fdc7394824a5b837ee2e9716c04cd5c18b3f55f84edaa12441`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: restore the exact v12 final checkpoint in the deterministic evaluator,
smoke provenance and telemetry, then run the full development counterfactual.
