# Method-B v24 seed-11 50 mm runtime smoke attempt001

## Disposition

`SMOKE_PASS`. This is an implementation gate only.

- Nominal state produced exact-zero physical residual.
- Slow +0.10-rad pitch retained phase-8 historical climb and phase-9 zero.
- +0.11-rad roll produced exact `[0,-0.6,+0.6,0]` z action in phases
  8--10 and exact zero in phases 7/11.
- The early roll/rate probe selected the same diagonal and remained latched
  after rate decay.
- A 0.05 positive shared drive executed the exact 0.1 pre-gain /
  `[0,-0.3,+0.3,0]` normalized / 3 mm diagonal floor.
- FL/RR corrective channels, all x channels, and all wheel-speed channels
  were exact zero. FR/RL were equal and opposite; four-wheel sum was zero.
- Bounds, finite observations/actions/values/rewards/contacts, one-shot
  terminal safety, partial reset, and post-terminal reset passed.

## Artifacts

- Result:
  `96476d592d1c97667d3dab67f50379bba21be9d365b5a6e9b97d90498b879c03`
- Stdout/stderr:
  `6b6a5c61f3de4d204456fd5187a179507bf6c96e235f020f6aaa3c30304dde48`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `160884`; it exited naturally.

## Next action

Restore the explicit v19 final checkpoint under v24, then run the fixed
20-scenario counterfactual only after exact provenance and nominal-zero
checks pass.
