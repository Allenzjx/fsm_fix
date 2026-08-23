# Method-B runtime-v11 seed-11 50 mm full training attempt001

## Disposition

`COMPLETED_INTEGRITY_PASS`. Method B seed 11 trained from random
initialization under runtime v11 for exactly **76,800 local timesteps /
4,915,200 transitions** in 64 real Isaac environments. This integrity result
does not establish controller performance; deterministic development
evaluation is required.

- Environment Python PID: `125240` (exited normally).
- Final checkpoint SHA-256:
  `29ac9c122b6741500d12f086f39daf768d9a88310715d1f62bdfa60acfbab418`.
- Training result SHA-256:
  `ac93642540d6387a272f746465161253930ba4028e5edf0c2b9dc640aa76c4df`.
- Event/stdout/stderr SHA-256:
  `1fc0f77f7a06f4227a10d4f3175afe1d29fc38edcff9455672b0eb17a0fd3572`,
  `6b3d3d5a1d66300bf5bb417a30709b0d11528460c8924f8af75273bc06192f6f`,
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
- TensorBoard contains 17 scalar tags and 15,534 scalar samples, all finite.
- All 1,200 core optimization samples span exact steps 64--76,800.
- The repaired episode tracker emitted 389 windows with lengths
  3,822--8,999. No false 168-step env-0 segment occurred.
- Instantaneous extrema include positive success bonuses up to `+200.0301`
  and safety terminals down to `-200.2396`.
- Policy standard deviation decreased finitely from `0.134985` to
  `0.0741615`.

## Provenance

The run records common config SHA-256
`7a37e165aa803e1c876fd3b7c30194078f4b93895f1d18430300ee4d16daafa3`,
the exact z-only mask/projection, full randomization, network/PPO settings,
source hashes, simulator/library versions, and frozen FSM/metrics/asset
hashes. No prior checkpoint was loaded.

## Next action

Run a one-scenario, five-second deterministic evaluator/provenance smoke with
the explicit final checkpoint. Require a uniform finite action chain, exact
phase gate, exact x/speed masking, and frozen/config/source hashes. Then run
the unchanged full 20-scenario 50 mm development gate, requiring at least
16/20 successes.
