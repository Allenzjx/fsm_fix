# Method-B runtime-v20 real-Isaac training-entrypoint smoke attempt001

`SMOKE_PASS`.

- One real Isaac environment constructed with full training randomization.
- The measured nominal pitch was `-0.02244199 rad`; physical residuals were
  exactly zero below the `+0.09 rad` gate.
- An explicit `+0.1000000015 rad` pose probe produced exact normalized
  wheel-center-z output `[+0.20000002, +0.20000002, -0.20000002,
  -0.20000002]`, or 2 mm under the fixed bound, in phases 8/9.
- Phases 7/10, masked x/wheel-speed channels, and the opposite drive
  half-space were exactly zero.
- Actor, critic, contact, 22 reward terms, forced one-shot `-200` fall
  safety, partial reset, and post-terminal reset checks were finite and
  passed.
- Provenance records the frozen v20 config and source hashes.

Artifact SHA-256: result
`790eec73ff0c938205e820182f8c060a2164d1782d72f689a642532da891f9d4`,
stdout
`27139fe6ea23decbb4e4a73387100be58f81232c07778cc6cf3a4127b0bc1915`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: restore the explicit v19 final checkpoint under v20 in a one-scenario
deterministic evaluator smoke before the 20-scenario counterfactual.
