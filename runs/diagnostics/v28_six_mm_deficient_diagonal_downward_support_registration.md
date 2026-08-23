# Runtime v28 six-mm deficient-diagonal downward-support registration

## Status

`REGISTERED_BEFORE_ISAAC_EXECUTION`.

Runtime name:
`runtime-v28-six-mm-deficient-diagonal-downward-support-emergency`.

## Registered change

- Corrective signs/scales remain `[0,-1,-1,0] / [0,1,1,0]`.
- Corrective pre-gain floor changes from 0.1 to 0.2.
- With unchanged gain 3 and 10 mm z bound, emergency authority changes
  from `[0,-3 mm,-3 mm,0]` to `[0,-6 mm,-6 mm,0]`.
- The candidate remains 4 mm inside the hard physical bound.
- Offline reconstruction is valid on 1,602/1,602 v25 rows, 146/146 v26
  rows, and 3,280/3,282 v27 rows. The only two invalid rows are the same
  late, already invalid scenario-0003 rows that v27 rolls back.
- Valid-row front-right/rear-left safe-joint margins are at least
  0.15512/0.053832 rad.
- All gates, latch semantics, signs/scales, actor shared-drive computation,
  architecture, rewards, optimizer, randomization, curriculum, budget,
  action bounds, and B/C distinction remain unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Real-Isaac smoke proves exact `[0,-0.6,-0.6,0]` floor and physical
   front-right/rear-left -6 mm realization with all-leg IK.
2. The exact v19 checkpoint restores with canonical byte-stable exact-zero
   telemetry.
3. The fixed 20-scenario counterfactual reaches >=16/20, preserves every
   existing success including `0009`, and passes all constraint audits.

V28 training is prohibited until all gates pass.

## Frozen hashes

- Pre-code analysis:
  `394d86982970f11ce82f8f2d359991d2b8f2b1f5a78b8677e2813363e3ca9139`
- Raw/canonical common config:
  `71edd8326fbe9507dc6c34cc35abd1a3058a067d183b981a465a31483c44de5c`,
  `c9193a5a1bf795a49dc26bacf31acfe316461c0406a12d652c6b634788832f1e`
- `residual_safety.py`:
  `85ac601dcca69b22b780e20bc0aeb0c861962dd2adb026f2ae4e84a276c1d678`
- `residual_rl_env.py`:
  `8565c7d2707f2da6e3f858d45453a2d0af49b6ccbdef8296ab8b85f30fee6971`
- `train_residual_ppo.py`:
  `ac50706d989e39aed99ac6d55d889ef9b58aa68891a9c03bcadef9c8e3273d6b`
- `evaluate_controller.py`:
  `97d5f79a84a3dad61901fbbf265f821717bd79b0a43456b9ed404d678a740720`

Compilation and all 160 tests pass. No v28 Isaac result exists at
registration time.
