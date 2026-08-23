# Method-B runtime-v12 seed-11 50 mm full training attempt001

## Disposition

`COMPLETED_INTEGRITY_PASS`. Method B seed 11 trained from random
initialization under runtime v12 for exactly **76,800 local timesteps /
4,915,200 transitions** in 64 real Isaac environments. This integrity result
does not establish controller performance; deterministic development
evaluation is required.

- Environment Python PID: `104632` (exited normally).
- Final checkpoint SHA-256:
  `a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`.
- Training result SHA-256:
  `fdb7974e661f92a5abb1b9f5fcf28839f2f806c857adfc786c501f983d17469c`.
- Event/stdout/stderr SHA-256:
  `199819b1fb0d693bf239430e94c3123de3ac033b20ee1b337488cc3665304169`,
  `f4ae1bc9f6ed189cc4f4cba58bc616c2d22ea73aa72aead774d660139eadb49e`,
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.
- The checkpoint contains 77 tensors / 785,093 elements, all finite.
- The run produced 48 periodic checkpoints plus `best_agent.pt` and
  `final_agent.pt`.

## Budget and event audit

- Requested/completed local timesteps: `76800 / 76800`.
- Requested/completed cumulative timesteps: `76800 / 76800`.
- Requested/completed local transitions: `4915200 / 4915200`.
- Requested/completed cumulative transitions: `4915200 / 4915200`.
- TensorBoard contains 17 scalar tags and 15,510 scalar samples, all finite.
- All 1,200 core optimization samples span exact steps 64--76,800.
- The repaired episode tracker emitted 385 windows with lengths
  3,822--8,999. No false 168-step env-0 segment occurred.
- Instantaneous extrema include positive success bonuses up to `+200.0276`
  and safety terminals down to `-200.2337`.
- Policy standard deviation decreased finitely from `0.1349853` to
  `0.07029545`.

## Provenance

The run records v12 common config SHA-256
`f171dba0270c31fb1571c9e4ff86c9524a2eb32cd4927c33f8bc6b04b9f5251a`,
bilateral signed-magnitude z projection, exact z-only mask, phase-7--8
execution, full randomization, network/PPO settings, source hashes,
simulator/library versions, and frozen FSM/metrics/asset hashes. No prior
checkpoint was loaded.

## Next action

Run a one-scenario, five-second deterministic evaluator/provenance smoke with
the explicit final checkpoint. Require a uniform finite action chain, exact
phase gate, exact x/speed masking, bilateral ties, and frozen/config/source
hashes. Then run the unchanged full 20-scenario 50 mm development gate,
requiring at least 16/20 successes.
