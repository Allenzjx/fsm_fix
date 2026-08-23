# Method-B v15 / v12-checkpoint evaluator smoke attempt001

`PASS`. The deterministic evaluator restored the exact v12 Method-B seed-11
final checkpoint under v15 semantics and completed its deliberate 5 s
development-only timeout.

- Environment Python PID: `109028`.
- Checkpoint SHA-256:
  `a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`.
- V15 common config SHA-256:
  `2cf5437c3541c21c82dc221fec77c09b3f9d4c9ad52fbaf43d9dc6dc0f74cb11`.
- Effective phase window/gains: `[7,9]` / `[1.0,1.0,1.5]`.
- Telemetry shape: `100 x 122`; its SHA-256 exactly matches the independently
  audited v14 smoke because both observe only phases 0 and 1.
- Maximum absolute policy action: `0.0726393983`.
- Maximum absolute executed and physically scaled residual: exact `0`.

The timeout is diagnostic only and excluded from performance evidence.

Artifact SHA-256:

- `result.json`:
  `a1aa61dd30d9f3c4a2aaef6dda2a2d44a290ede423331e3e62c4677d9c07bd51`
- `episodes.jsonl`:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- `status.json`:
  `b0a83c9ae52f10dd1474c75e8e8d2c6cde848d1c66f75727d35cc8bc7274f10c`
- `telemetry.csv`:
  `f176aa5017745a6f1f291d7181330c80ef077c4fb944c6da1d66fc7a1c3e530c`
- stdout:
  `d83a3381b68a7e0461ec93790561ae93f4208618ca2bd033b8e9f7ac36cc8015`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: run all 20 fixed 50 mm development scenarios with the same checkpoint
and v15 runtime.
