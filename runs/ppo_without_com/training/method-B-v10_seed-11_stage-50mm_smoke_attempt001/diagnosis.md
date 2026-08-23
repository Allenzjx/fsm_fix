# Method-B runtime-v10 seed-11 50 mm smoke attempt001

## Disposition

`SMOKE_PASS`. Sixteen real Isaac environments passed the registered v10
phase-gate, vertical-direction projection, finite-interface, tracker,
terminal-safety, and reset audits. This smoke contributes zero accepted
optimization transitions and authorizes from-scratch full development.

- Environment Python PID: `85220` (exited normally).
- Result/event SHA-256:
  `4f6d0e81ddca690e258ab756c219f773579e57bbb4f617d19de8ed2b9f1a89af`
  and
  `f08b443388301c8c25707cb27019dcd63456ba1f1c2936e1078cbd17e5ab12b9`.
- stdout/stderr SHA-256:
  `f3db1cbf27afd01b75376df173dd57143e7802fe5880665a495c4abc42ca7794`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Runtime evidence

- Phase-6/7/8/9 scaled-residual maxima were exactly
  `0 / 0.0500000007 / 0.0500000007 / 0`.
- With every raw action dimension set to `+0.5`, the applied front-left,
  front-right, rear-left, and rear-right z actions were exactly
  `[0, 0, 0.5, 0.5]`. The real environment therefore enforced the registered
  front-non-positive/rear-non-negative direction cone.
- Actor/critic/action tensors, contact forces, and all 22 reward terms were
  finite. `AuditablePPO` preserved env 0 when other done rows were processed.
- The isolated fall retained raw/weighted terms `1/-200` and finite total
  reward. Post-terminal reset distance error was 1.327 mm with no immediate
  success or termination.
- Provenance records the 76,800-step registered budget, exact direction
  signs, config/source/frozen hashes, physical bounds, reward, randomization,
  simulator/library versions, and GPU.

## Next action

Train Method B seed 11 at 50 mm from random initialization for exactly 76,800
local timesteps / 4,915,200 transitions in 64 environments. No previous
checkpoint is reused.
