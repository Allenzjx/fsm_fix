# V33 real-Isaac smoke audit

`SMOKE_PASS`.

- phase 8 physical-forward wheel-speed residual:
  `[-0.075000003,+0.075000003,-0.075000003,+0.075000003] rad/s`;
- phase 9:
  `[-0.100000001,+0.100000001,-0.100000001,+0.100000001] rad/s`;
- phase 10: exact zero;
- raw joint-target signs and physical command mapping pass;
- phase-8/9/10 z realization remains 3/4/3 mm;
- all four legs are IK-valid in every phase, with zero invalid increments
  and no rollback;
- phase-selective, rapid-rise latch, zero-preserving, and final-target
  audits pass.

No optimization or development evaluation occurred.

Evidence SHA-256:

- result:
  `157cb0e98f9892bf5efb0265e5f963252b32f182caa85c520f1e6b97b2f20138`
- stdout:
  `28819edbe4199c5e1c54de963f1b8876d5206fdae59f47eb0b45bd9f07831bf0`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

