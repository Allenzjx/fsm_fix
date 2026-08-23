# Method-B v15 / v12 checkpoint-59200 restore smoke attempt001

`PASS`. The deterministic evaluator restored the pre-registered v12
`agent_59200.pt` candidate under fixed v15 semantics.

- Environment Python PID: `109336`.
- Checkpoint SHA-256:
  `e16f5545080b857163bd43a201be26595818cbe8e324a422675d58095e989493`.
- V15 config SHA-256:
  `2cf5437c3541c21c82dc221fec77c09b3f9d4c9ad52fbaf43d9dc6dc0f74cb11`.
- Effective window/gains: `[7,9]` / `[1.0,1.0,1.5]`.
- Telemetry: `100 x 122`, phases 0/1.
- Policy max-abs: `0.1820926`; executed and scaled residual max-abs: exact
  `0`.
- The deliberate 5 s timeout is excluded from performance evidence.

Artifact SHA-256:

- `result.json`:
  `6eec25bb233cd03480d099bde74d4187071d68fe6302898f97c75964bebe5c19`
- `episodes.jsonl`:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- `status.json`:
  `d2e2f082a447eacd47ab5b4fe5f452469147a8a8df8c8fe1c786a3d59508506e`
- `telemetry.csv`:
  `da0769b80ec9e5b722b2c369eb2a1ce755fba75f1feb9a5a9a003e49a89a6c52`
- stdout:
  `fac1ef68704737d3005d8dbe0956a7a49e43b4b5fd8323171eb6411a04031fb3`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: unchanged full 20-scenario development screen for checkpoint 59200.
