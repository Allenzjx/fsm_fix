# Method-B runtime-v16 seed-11 50 mm full training attempt001

## Disposition

`COMPLETED_INTEGRITY_PASS`. Method B seed 11 trained from random
initialization under runtime v16 for exactly **76,800 local timesteps /
4,915,200 transitions** in 64 real Isaac environments. This integrity result
does not establish controller performance; deterministic development
evaluation is required.

- Environment Python PID: `140908` (exited normally).
- Final checkpoint SHA-256:
  `c835b6fc5a9e72557de12232aa8f2f86c4850e7ee7c9820ca25c9d2a4123b75e`.
- Training result SHA-256:
  `05262a3915a9a9ee858e12366099d03dd6d8360c7292f2f547cc46263a7ce951`.
- Event/stdout/stderr SHA-256:
  `637492a66f7b3d88c77c3b3329c84c66bfa90bef0f321f5ae810b8bad8e73d52`,
  `72b969ee32a0ff7a67bbd2faa4d5753cfedd87441794fe8103a9ee0f5515bc56`,
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
- TensorBoard contains 17 scalar tags and 17,964 scalar samples, all finite.
- All 1,200 core optimization samples span exact steps 64--76,800.
- The repaired episode tracker emitted 388 windows with lengths
  3,822--8,999. No false 168-step env-0 segment occurred.
- Instantaneous extrema include positive success bonuses up to `+200.0236`
  and safety terminals down to `-200.2395`.
- Policy standard deviation decreased finitely from `0.1349853` to
  `0.07000092`.

## Provenance

The run records v16 common config SHA-256
`8dc33c824c1b3576012dc5437db764df04fb8e47ea48c6af9a6a325a0494b193`
(canonical
`0cea2d98a2ab17b82cdca9dedd2051d799fbe059ed99a4e85172db14b538c71d`),
the zero-preserving one-sided balanced z gate, exact z-only mask,
phase-7--9 execution, full randomization, network/PPO settings, source
hashes, simulator/library versions, and frozen FSM/metrics/asset hashes. No
prior checkpoint was loaded.

## Next action

Run a one-scenario, five-second deterministic evaluator/provenance smoke with
the explicit final checkpoint. Require a uniform finite action chain, exact
phase gate, exact x/speed masking, four-wheel balance, zero-preserving gate,
and frozen/config/source hashes. Then run the unchanged full 20-scenario
50 mm development gate, requiring at least 16/20 successes.
