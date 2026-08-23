# Method-B v14 seed-11 50 mm runtime smoke attempt001

`SMOKE_PASS`. The v14 four-wheel-balanced z projection and its phase-9
extension completed the real-Isaac preflight in 16 fully randomized
environments.

- Environment Python PID recorded by the result: `145800` (exited normally
  before the external process query).
- Nonuniform probe execution:
  `[0,-0.5,0,-0.5,0,+0.5,0,+0.5,0,0,0,0]`.
- Boundary phase-6/7/9/10 scaled maxima:
  `0/0.0049999999/0.0049999999/0`.
- The inclusive phase interval and full 13-phase unit test establish phase 8
  as enabled; the unchanged projection was also physically probed in phase 8
  by the v13 real-Isaac smoke.
- Phase gate, z-only mask, signs, bilateral ties, and exact four-wheel
  balance all passed.
- Actor/critic shapes and values, contact/reward terms, tracker isolation,
  partial reset, forced terminal snapshot, and post-terminal reset passed.
- Forced fall contributed the registered one-shot weighted `-200`.
- Post-terminal randomized reset distance error was `0.00132722 m`.
- Common config SHA-256:
  `2022543c57ae20da7b62ae1874efdfcf4d06cedabc15e78a9e12692b733eff52`
  (canonical
  `4f36a5962291173fc348c331841433c54635da298527d660dfc9dd843c084f92`).
- Environment source SHA-256:
  `f9a89c28d0a2b33006bc475be1ec18abab72f8f70db4544a40f7f44cb8c60ec7`.

Artifact SHA-256:

- `training_result.json`:
  `e5d1cfa8f8c1fbb30f3ae56b02503c3ca72a062884f3dbd5802c4c1c4884408c`
- stdout:
  `caaf040156058e9a4517f73304565cfba38748a0663041387b5ba1b7e32e9b23`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: restore the v12 final checkpoint in the deterministic evaluator under
v14 semantics, smoke the action chain, then run the full 20-scenario
development-only counterfactual before deciding whether to retrain.
