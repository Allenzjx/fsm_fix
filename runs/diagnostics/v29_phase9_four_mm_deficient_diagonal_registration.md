# Runtime v29 phase-9 four-mm deficient-diagonal registration

## Status

`REGISTERED_BEFORE_ISAAC_EXECUTION`.

Runtime name:
`runtime-v29-phase9-four-mm-deficient-diagonal-downward-support-emergency`.

## Registered change

- Corrective signs/scales remain `[0,-1,-1,0] / [0,1,1,0]`.
- Corrective pre-gain floor returns from 0.2 to 0.1.
- Phase gains change from `[3,3,3]` to `[3,4,3]`.
- Emergency floor authority is consequently
  `[0,-3 mm,-3 mm,0]` in phase 8,
  `[0,-4 mm,-4 mm,0]` in phase 9, and
  `[0,-3 mm,-3 mm,0]` in phase 10.
- Phase 8 and phase 10 are therefore exact v27 behavior. Only phase 9
  changes, by one additional millimeter on front-right and rear-left.
- Offline reconstruction is all-leg IK-valid on all 2,524 changed v27
  phase-9 rows, with front-right/rear-left safe-joint margins of at least
  0.141975/0.068788 rad.
- The phase-9 floor retains 6 mm to the unchanged hard z bound.
- All gates, latch semantics, signs/scales, actor shared-drive
  computation, architecture, rewards, optimizer, randomization,
  curriculum, budget, action bounds, and B/C distinction remain
  unchanged.
- The locked-test manifest has not been read.

## Required gates

1. Real-Isaac smoke proves exact 3/4/3 mm phase-selective action and
   physical front-right/rear-left 3 mm phase-8 realization with all-leg
   IK.
2. The exact v19 checkpoint restores with canonical byte-stable
   exact-zero telemetry.
3. The fixed 20-scenario counterfactual reaches >=16/20, preserves every
   existing success including `0009`, and passes all constraint audits.

V29 training is prohibited until all gates pass.

## Frozen hashes

- Pre-code analysis:
  `43492c32e74d1e06ae3ee270b7218ae40c247ca5dbf1540230e758796ae25734`
- Raw/canonical common config:
  `8b312f720489b9b44f38215652235331fe77083190837225441b5f7568b18fc1`,
  `d9df8b9227762aeb7c3da169c539c9afbfc18c7f6446c984049974d8d799090c`
- `residual_safety.py`:
  `85ac601dcca69b22b780e20bc0aeb0c861962dd2adb026f2ae4e84a276c1d678`
- `residual_rl_env.py`:
  `298ce3ccd134e4358292042aa69958ad90ef1070d26ff09d0e06360909379b6b`
- `train_residual_ppo.py`:
  `c6469a6efed3116184e3ae2ee15d34bb8a1902146d45613d1bc720c3692ace47`
- `evaluate_controller.py`:
  `6bdb8dbb9d02c1e6791043c768c9eb5c4486ab9cda66b95f373659165515d372`

Compilation and all 160 tests pass. No v29 Isaac result exists at
registration time.
