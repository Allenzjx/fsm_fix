# Method-B v12 seed-11 50 mm evaluator smoke attempt001

`SMOKE_PASS`. The deterministic evaluator restored final checkpoint
`a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`
and completed the deliberate one-scenario, five-second timeout.

- Environment Python PID: `169784` (exited normally).
- The 100 x 122 telemetry table has a finite action chain.
- Policy max-abs was `0.0726394`; projected executed actions and scaled
  residuals were exactly zero throughout phases 0/1.
- Provenance records v12 common config SHA-256
  `f171dba0270c31fb1571c9e4ff86c9524a2eb32cd4927c33f8bc6b04b9f5251a`,
  projection `wheel_center_z_bilateral_signed_magnitude`, frozen FSM
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`,
  metrics
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`,
  and asset
  `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`.

Artifact SHA-256:

- `result.json`:
  `3064a9ae43c9eab432fe412b792a20bae28e36c8f68ee41a11f5e399be527288`
- `episodes.jsonl`:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- `status.json`:
  `8002bff51e4a70ef834c011db9c3c90580538e3e28e7cedd778e176cb658aed4`
- `telemetry.csv`:
  `f176aa5017745a6f1f291d7181330c80ef077c4fb944c6da1d66fc7a1c3e530c`
- stdout:
  `ded343fe0e182e6bfd5880b9cafc88334f119b873b0fd4e721a1b7ccf5246e14`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

The deliberate smoke timeout is excluded from performance. Next: evaluate
the unchanged full 20-scenario 50 mm development gate.
