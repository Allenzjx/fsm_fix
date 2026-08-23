# Method-B v13 / v12-checkpoint evaluator smoke attempt001

`SMOKE_PASS`. The deterministic evaluator restored v12 final checkpoint
`a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`
under v13 four-wheel balanced semantics and completed the deliberate
five-second timeout.

- Environment Python PID: `163452` (exited normally).
- The 100 x 122 telemetry table has a finite action chain.
- Policy max-abs was `0.0726394`; executed actions and scaled residuals were
  exactly zero throughout phases 0/1.
- Common config SHA-256:
  `0c06cd2d2ea208461233074062285ec42cf14f92809036c2e164a27a6b2aec17`.
- Projection:
  `wheel_center_z_four_wheel_balanced_signed_magnitude`.
- Frozen FSM/metrics/asset hashes all match.

Artifact SHA-256:

- `result.json`:
  `c9aba73d4f399895f012515a9455f587335c2d006a529e2a734ff7ba486dc9fd`
- `episodes.jsonl`:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- `status.json`:
  `360df6caf6ec5d50f1e4c95f07ae425186a0f24c744de39dab1d50cc6d1824bb`
- `telemetry.csv`:
  `f176aa5017745a6f1f291d7181330c80ef077c4fb944c6da1d66fc7a1c3e530c`
- stdout:
  `8cb06cf39efeeb5238e263954ec1657e7e9d9e6906beb5b3ad47d5083d81ddb1`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: run the full 20-scenario development-only counterfactual.
