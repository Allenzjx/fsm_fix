# V32 smoke attempt001 diagnosis

## Disposition

`FAILED_PREFLIGHT_RETAINED_AND_SUPERSEDED`.

This real-Isaac smoke was stopped by the mandatory runtime audit before
training or evaluation. The directory and its evidence are retained without
reuse. The next execution must use a new `attempt002` directory.

## What the run proved

- Isaac Lab constructed the environment and realized the registered
  3/4/3 mm phase-8/9/10 deficient-diagonal wheel-center-z targets.
- All four legs were IK-valid in every probed phase, with zero IK-invalid
  increments and no rollback.
- Phase 10 wheel-speed residual stayed exactly zero.
- Phase 9 realized the intended physical-forward residual
  `[-0.10,+0.10,-0.10,+0.10] rad/s`.
- Phase 8 realized only
  `[-0.075,+0.075,-0.075,+0.075] rad/s`.
- The phase-selective realization audit passed. The later rapid-rise latch
  audit failed because its independently constructed expected tensor omitted
  the now-authorized phase-8 wheel-speed channels.

## Root cause

The initial v32 registration retained one pre-gain speed floor of 0.25 while
also retaining phase gains `[3,4,3]`. Therefore phase 8 produced normalized
speed 0.75 and physical speed 0.075 rad/s, while phase 9 produced normalized
speed 1.0 and physical speed 0.10 rad/s. The registration's statement that
both phases would realize the exact hard-bound speed was arithmetically
inconsistent.

The separate rapid-rise audit omission was a test-oracle defect: the runtime
correctly applied the phase-8 speed authorized by the implemented projection,
but `expected_floor_action_tensor` contained only wheel-center-z values.

## Corrective action

The superseding correction is registered in
`runs/diagnostics/v32_phase8_9_bound_counter_yaw_smoke_correction.md`.
It uses phase-aligned pre-gain floors `[1/3,1/4]`, so the unchanged gains
`[3,4]` produce the same normalized hard-bound speed in phases 8 and 9. The
rapid-rise expected tensor now includes phase-8 wheel speed. No threshold,
gate, z command, physical bound, checkpoint, scenario, or evaluation rule
changes.

## Frozen failed-attempt evidence

- `training_result.json`:
  `bede9f9a04e5c3834428337d5073be548fa0beb8b26799e9bb34f3438399ba2`
- stdout:
  `24166680318cb896727d0d6b8a43b1632b596b8c51b20a0994d6272a08fd8758`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

