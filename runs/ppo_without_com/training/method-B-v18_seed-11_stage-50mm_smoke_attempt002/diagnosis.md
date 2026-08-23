# Method-B v18.1 seed-11 50 mm real-Isaac smoke attempt002

`SMOKE_PASS`.

- The corrected entrypoint constructed one full-randomization Isaac
  environment and produced finite policy action, critic value, contact force,
  reward terms, and post-terminal reset state.
- The registered `0.2` shared-drive probe executed
  `0.1816843748` normalized after subtracting
  `exp(-4) = 0.01831563888873418`, or `1.81684375 mm` under the 10 mm
  wheel-center-z bound.
- Phases 7 and 9 enabled that exact residual; phases 6 and 10 were exactly
  zero. Direction, z-only mask, bilateral ties, four-wheel balance, and the
  reversed-action exact-off case all passed.
- All 22 reward terms were finite. The forced fall terminated with the exact
  `-200` fall term; partial reset and the following step were finite and
  non-terminal.
- Provenance records the v18 common-config raw/canonical hashes, confidence
  projection type and threshold, corrected training source hash, and the
  frozen asset/FSM/metrics hashes. Environment Python PID `73196` exited
  naturally.

Artifact SHA-256:

- training result:
  `63e5458a9c533fbf1993e198dd8ded4cffcd29667e8fe8e19cd4009e0fd34c2c`
- stdout:
  `4025c8ef5c9c956d4b6b1595dcecaee83d124f4ff781b7927a2c66638c3ebfc5`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: restore the unchanged v17 final checkpoint under v18 in a
one-scenario, five-second deterministic evaluator smoke.
