# Method-B v14 / v12-checkpoint evaluator smoke attempt001

`PASS`. The deterministic evaluator restored the exact v12 Method-B seed-11
final checkpoint under v14 semantics and completed its deliberate 5 s
development-only timeout.

- Checkpoint SHA-256:
  `a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`.
- V14 common config SHA-256:
  `2022543c57ae20da7b62ae1874efdfcf4d06cedabc15e78a9e12692b733eff52`.
- Effective execution phase window: `[7,9]`.
- Telemetry shape: `100 x 122`; every field is finite.
- Observed phases: 0 and 1.
- Maximum absolute policy action: `0.0726393983`.
- Maximum absolute executed and physically scaled residual: exact `0`.
- Frozen FSM, metrics, asset, development manifest, evaluator, environment,
  and projection-source hashes match the registered provenance.
- Environment Python PID tracked externally: `147172`.

The deliberate timeout is not a performance observation. It only establishes
checkpoint restoration and truthful action-chain telemetry before the full
20-scenario counterfactual.

Artifact SHA-256:

- `result.json`:
  `4c46f23a9c58dd4c1a6bc4d5df6b31162e29997669906d5b21d38f827a9a33df`
- `episodes.jsonl`:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- `status.json`:
  `64f25e225945021a9df0ba6018d42f34289db2fb37fdd2b5c1a260332e8be3a2`
- `telemetry.csv`:
  `f176aa5017745a6f1f291d7181330c80ef077c4fb944c6da1d66fc7a1c3e530c`
- stdout:
  `b767c20348036dfbfdfd6e1744058481d380acf118591ed7ab7db799235db6a2`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: run all 20 fixed 50 mm development scenarios with the same checkpoint
and v14 runtime semantics.
