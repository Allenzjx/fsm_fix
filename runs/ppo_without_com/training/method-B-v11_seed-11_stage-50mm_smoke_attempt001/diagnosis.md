# Method-B runtime-v11 seed-11 50 mm smoke attempt001

## Disposition

`SMOKE_PASS`. Sixteen real Isaac environments passed the registered v11
phase gate, z-only signed-magnitude projection, finite-interface, tracker,
terminal-safety, and reset audits. This smoke contributes zero accepted
optimization transitions and authorizes a deterministic evaluator
counterfactual. It does not authorize training promotion by itself.

- Environment Python PID: `55304` (exited normally).
- Result/event SHA-256:
  `2bede55b0090b6b62fe6c2351d24eb4564970c501c58e18340eb5c42a29321a9`
  and
  `4510f349797d078b6b4610809f90871ed2ae5c3fd63610512fc36bbfd12e7d67`.
- stdout/stderr SHA-256:
  `b43d46821bc01d22c4c5bd8ef6315b6476986f678fa2d1ff082de6c6ab8d5e67`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- Phase-6/7/8/9 scaled-residual maxima were exactly
  `0 / 0.0049999999 / 0.0049999999 / 0`.
- With every raw action dimension set to `+0.5`, the full applied action was
  exactly
  `[0,-0.5,0,-0.5,0,+0.5,0,+0.5,0,0,0,0]`.
- The eight wheel-center x and wheel-speed channels were therefore exactly
  masked, while all four z channels obeyed the registered
  front-negative/rear-positive signed-magnitude mapping.
- Actor/critic/action tensors, contact forces, and all 22 reward terms were
  finite. `AuditablePPO` preserved env 0 when other done rows were processed.
- The isolated fall retained raw/weighted terms `1/-200`. Post-terminal reset
  distance error was 1.327 mm with no immediate success or termination.
- Frozen FSM, metrics, and asset SHA-256 remained
  `3e4b65ee...e4e9`, `6a02b1c0...30ab`, and `98103315...f81dd`.

## Next action

Run a one-scenario, five-second deterministic evaluator/provenance smoke using
the existing v10 final checkpoint under v11 physical semantics. If the
telemetry records raw policy actions but exact x/speed masking and phase
gating, run the full 20-scenario development-only counterfactual.
