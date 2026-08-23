# Method B reward-v4 seed-11 50 mm evaluator smoke attempt001

- Status: execution `PASS`.
- Scope: the first fixed development scenario only, deliberately truncated at
  5 seconds. Its `0/1` timeout is diagnostic and is excluded from performance
  evidence.
- Deterministic final checkpoint:
  `e23b091a4a3f05b2092963a3960df7b1a2539a3e62072cb095b375e8587b87f0`.
- The evaluator restored the complete checkpoint and ran 298 control steps.
- Frozen FSM and metrics hashes are
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
  and
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`.
- Reward-v4 common config SHA-256 is
  `b3417383ecb3ab22436764a33c57adb5a374897f87ae680f38bbe64c2275699a`.
  Direct provenance records x/z/wheel bounds of
  0.0075 m / 0.010 m / 0.10 rad/s and regularization weights -2 / -3.
- Telemetry has 100 rows and 122 columns with uniform row width and no
  missing or non-finite numeric values. Columns 46 through 109 are the full
  64-field policy-action, executed-action, scaled-residual, requested-target,
  final-target, servo-target, and wheel-target chain.
- Maximum observed absolute scaled center residual was 0.001324816 m and
  maximum wheel-speed residual was 0.012575802 rad/s, both within the direct
  registered bounds.
- Artifact SHA-256 values:
  - `episodes.jsonl`:
    `8498006424af833b8a293c21aa940c3dafcaf5ab14dab1cf6773e2f444707b1d`
  - `status.json`:
    `f8898faf2cfb15100ed946f0ac3ced9f2e1884b28fce5040815f95e39a9fba44`
  - `telemetry.csv`:
    `091106dcad91fe190a510e31f0ed5c23b9f1a2797350b7d1e33ed8e706e3d33d`
  - `result.json`:
    `4f6e435215d2092768ea51a367f0c8e14bab87c93d4ecf8ce0f44d8fbfa32954`

This smoke authorizes the unchanged full 20-scenario, 150-second development
gate. It does not authorize curriculum promotion by itself.
