# Method-B v19 seed-11 50 mm real-Isaac smoke attempt001

`SMOKE_PASS`.

- One full-randomization Isaac environment produced finite policy action,
  critic value, contact force, all 22 reward terms, and post-terminal reset.
- At the real initial pitch `-0.02244199 rad`, the registered state gate
  produced exact-zero applied and physical residuals.
- A diagnostic root-orientation write produced measured pitch
  `+0.10000000 rad`, above the fixed `+0.09 rad` threshold. The same
  nonuniform action then projected to exact balanced z
  `[-0.20000002,-0.20000002,+0.20000002,+0.20000002]`.
- Under the above-hazard pose, phases 8/9 produced exactly 2 mm scaled
  wheel-center-z residual while phases 7/10 remained exactly zero. Z-only
  masking, bilateral ties, four-wheel balance, and reversed-drive exact off
  all passed.
- The forced fall retained the exact `-200` fall term; partial reset and the
  following transition were finite and non-terminal.
- Provenance records the v19 config, real-IMU gate type and threshold,
  projection, source hashes, and frozen asset/FSM/metrics. Environment Python
  PID `45208` exited naturally.

Artifact SHA-256:

- training result:
  `c02f33e4938f04009e171aac03e760dad4b9565a4021e0a45568778a86eccb55`
- stdout:
  `59c1928cd3aefd45fbc2b5f885545d9ae208cded0efb571dd42fe1d196d3a1ae`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: deterministic restore smoke of the unchanged v17 final checkpoint
under v19.
