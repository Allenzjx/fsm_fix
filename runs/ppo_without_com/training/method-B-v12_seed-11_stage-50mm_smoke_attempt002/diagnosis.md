# Method-B runtime-v12 seed-11 50 mm smoke attempt002

## Disposition

`SMOKE_PASS`. Sixteen real Isaac environments passed the registered v12
phase gate, z-only mask, signs, bilateral tie, finite-interface, tracker,
terminal-safety, and reset audits. This smoke contributes zero accepted
optimization transitions.

- Environment Python PID: `84268` (exited normally).
- Result/event SHA-256:
  `c718d00076b6cabf605a9d82eda9643ccc1e6f549401f66e41796fb6ee35b333`
  and
  `3833a6dae5dad521358c8796a30471c319e15e15e47a6718806a04d4389a1a34`.
- stdout/stderr SHA-256:
  `daaa0224d3f08552305e514069a844383c902c1d498c94ee2e9688e24c591df3`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- Phase-6/7/8/9 scaled-residual maxima were exactly
  `0 / 0.0070000002 / 0.0070000002 / 0`.
- Nonuniform raw probe
  `[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,-1.0,0.2,-0.3]`
  produced applied action
  `[0,-0.3000000119,0,-0.3000000119,0,+0.7000000477,0,+0.7000000477,0,0,0,0]`.
- Phase gate, direction, mask, and bilateral tie audits all returned `true`.
- All 22 reward terms and interfaces were finite. The isolated fall retained
  weighted term `-200`; post-terminal reset distance error was 1.327 mm.

## Next action

Run a one-scenario evaluator/provenance smoke using the existing v11 final
checkpoint under v12 semantics. Then run the full 20-scenario
development-only counterfactual. Neither artifact is promotion-eligible.
