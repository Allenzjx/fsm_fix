# Method-B runtime-v19 seed-11 50 mm full training attempt001

## Disposition

`COMPLETED_INTEGRITY_PASS`. Method B seed 11 trained from random
initialization under the pre-registered runtime v19 for exactly **76,800
local timesteps / 4,915,200 transitions** in 64 real Isaac environments.
This completion is not a performance claim; the independent deterministic
development gate remains required.

- Environment Python PID `51172` and conda wrapper PID `98620` exited
  normally.
- Final checkpoint SHA-256:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.
- Training result SHA-256:
  `a801dbd03f37686b6d31e6092f2bc139f89087c376f72cd78f707bc9f26f14fc`.
- Event/stdout/stderr SHA-256:
  `33f0ade0b2f531e83400d119ba96b8db37f7523e38bbdc5822266305510804fa`,
  `04527f94b056159d1d52f00c3f7c95e884eb00cf06aebe017f9713086ab6d89d`,
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Budget and numerical audit

- Requested/completed local timesteps: `76800 / 76800`.
- Requested/completed cumulative timesteps: `76800 / 76800`.
- Requested/completed local transitions: `4915200 / 4915200`.
- Requested/completed cumulative transitions: `4915200 / 4915200`.
- The run produced 48 periodic checkpoints plus `best_agent.pt` and
  `final_agent.pt`.
- Across all 50 files, 3,850 floating tensors / 39,254,650 values are
  finite. The 77 tensors in `final_agent.pt` and `agent_76800.pt` are
  exactly equal.
- TensorBoard contains 16 scalar streams and 14,232 scalar samples, all
  finite. All 1,200 core optimization samples span exact steps
  64--76,800.
- The repaired episode tracker emitted 372 windows with window lengths
  spanning 3,822--8,999 steps.
- Policy standard deviation decreased from `0.0183138102` to
  `0.0179480314` and stayed within those finite bounds.
- Training total returns span `-221.4726` to `+273.2784`; these noisy
  training aggregates are not used to claim development performance.

## Checkpoint selection rule

The next smoke and development gate use the explicit final checkpoint,
`final_agent.pt`. Although the trainer also wrote `best_agent.pt` at the
8,000-step state, it is not eligible for retrospective result-driven
selection. Its 77 tensors exactly equal those in `agent_8000.pt`.

## Provenance

The frozen v19 raw/canonical common-config hashes remain
`f115a3a4e435c70721ffdc44468e0352e71ca66f8187610f6ecd3cda112a8f93`
and
`3ffba6ff7e809a4244ebcee93e38b359a080ab7f594c87c73bd6e22f39ea31bf`.
The safety/environment/training/evaluator source hashes remain
`8209dec556979c0e6db32b3c5825262672ad57aac4896e95bf65882c7302ddc5`,
`fcadaca601955127673c3b44bd5d4f841f1003e37a77f4c5fafc95031ceef572`,
`bd3282ec2431a4d775bc400fa56ddb9e73575c33d695229e62f461fea79de73d`,
and
`c87a4ed88420bf1d12a474f51bb6509cc30db0f2e23ff1503b587c578974ca64`.
The frozen FSM, metrics, and robot asset hashes are unchanged.

## Next action

Run a one-scenario five-second deterministic evaluator/provenance smoke
with the explicit final checkpoint. Require a complete restore, finite
telemetry, and exact phase/pitch/projection constraints. If it passes, run
the unchanged 20-scenario 50 mm development gate and require at least
16/20.
