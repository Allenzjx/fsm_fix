# Method-B v25 seed-11 50 mm realization smoke attempt001

## Disposition

`SMOKE_FAIL`. No training, restore, or counterfactual is authorized.

The new physical-realization gate correctly rejected the probe:

- The action layer produced exact `[0,-0.3,0,0]` at the corrective floor.
- The front-right requested z delta was `-0.0030000061 m`; all other-leg
  requested deltas were exact zero.
- The residual IK-invalid counter increased by one.
- Final wheel-center delta and front-right servo-target delta were exact
  zero, proving coupled baseline rollback.

The new probe used the environment's initial standing reference while
manually changing only the phase integer. That is not the phase-8 reference
bank posture used by the 863 frozen development correction rows. Therefore
this failure proves the smoke probe is not representative; it does not
contradict the frozen actual-reference IK reconstruction.

The realization probe also left `small_positive_probe` in
`_raw_actions` before the existing phase-direction loop. The loop produced
`[0,-0.3,0,0]` while its registered high-drive expectation was
`[0,-0.6,0,0]`, so `residual_direction_projection_passed` correctly failed
too.

Before another Isaac call, the smoke harness must:

1. sample the real 50 mm reference bank at the held end of phase 8;
2. run zero action at that same reference to establish its baseline;
3. apply the exact floor action and record per-leg IK validity, final
   wheel-center movement, and servo movement; and
4. restore `projection_probe` before the independent direction loop.

The v25 runtime projection and config remain unchanged. This is a
smoke-harness correction only and must be re-registered with a new training
source hash.

## Artifacts

- Result:
  `45ddc0b79ed69876663e2797fedb3e16f258eb004ee9f3befcfc502153ce827d`
- Stdout/stderr:
  `5f0c2b3a15aa62b3b5f8918ac7f73625cbccbdebd559e60f6b94823a025756ad`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `106012`; it exited naturally.
