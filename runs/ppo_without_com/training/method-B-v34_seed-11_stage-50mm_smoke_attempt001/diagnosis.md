# V34 selected-runtime real-Isaac smoke

`SMOKE_PASS`.

- phase 8 wheel-speed residual: exact zero;
- phase 9 physical-forward residual:
  `[-0.100000001,+0.100000001,-0.100000001,+0.100000001] rad/s`;
- phase 10 wheel-speed residual: exact zero;
- z realization remains 3/4/3 mm in phases 8/9/10;
- all-leg IK, zero invalid increments, zero rollback, raw actuator mapping,
  rapid-rise latch, zero preservation, and final-target audits pass.

No optimization or development evaluation occurred.

SHA-256:

- result:
  `fac67f9fe971eca797b4f6a389f5c94b5428a15a2825cb8b146fc6882de056f0`
- stdout:
  `cb836374b050343c599a6f4c6717639cb5af22d8b5dea00913ac77efe4174055`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

