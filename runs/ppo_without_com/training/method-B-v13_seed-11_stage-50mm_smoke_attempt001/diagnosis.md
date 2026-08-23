# Method-B v13 seed-11 50 mm runtime smoke attempt001

`SMOKE_PASS`. The v13 four-wheel balanced z projection completed all
real-Isaac preflight checks in 16 fully randomized environments.

- Environment Python PID recorded by the result: `45596` (exited normally
  before the external process query).
- Nonuniform probe execution:
  `[0,-0.5,0,-0.5,0,+0.5,0,+0.5,0,0,0,0]`.
- Phase-6/7/8/9 scaled maxima:
  `0/0.0049999999/0.0049999999/0`.
- Phase gate, z-only mask, signs, bilateral ties, and exact four-wheel
  balance all passed.
- Actor/critic shapes and values, contact/reward terms, tracker isolation,
  partial reset, forced terminal snapshot, and post-terminal reset passed.
- Forced fall contributed the registered one-shot weighted `-200`.
- Post-terminal randomized reset distance error was `0.00132722 m`.
- Common config SHA-256:
  `0c06cd2d2ea208461233074062285ec42cf14f92809036c2e164a27a6b2aec17`.
- Projection:
  `wheel_center_z_four_wheel_balanced_signed_magnitude`.

Artifact SHA-256:

- `training_result.json`:
  `2f2eb1f2ed31a6d4b3f935bc66708e65ab18b705898757019fcb2e344732040a`
- stdout:
  `83c3a6a78245ebf828c6a30705715fca3eeb667474656f9304a7fcf301701b6d`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: restore the v12 final checkpoint in the deterministic evaluator under
v13 semantics, smoke the action chain, then run the full 20-scenario
development-only counterfactual before deciding whether to retrain.
