# Method B reward-v3 evaluator smoke attempt002

- Status: execution `PASS`.
- Scope: one fixed development scenario deliberately truncated at 5 seconds;
  its `0/1` timeout is excluded from performance evidence.
- Checkpoint SHA-256:
  `d3509ab1dbebc658cefdbf00aef77766e4ec574263c5c8c99ca3dfef1ad62a2e`.
- Direct effective residual bounds: 0.015 m x, 0.020 m z, 0.20 rad/s wheel
  speed.
- Telemetry: 100 data rows, 122 columns, uniform row width, no non-finite
  numeric values, and all 64 policy-to-actuator chain columns.
- Artifact SHA-256 values:
  - `episodes.jsonl`:
    `794deccef6207171ef10c9227ea3770ef1ce7b4d1eaccfbf6b46c571c985f121`
  - `result.json`:
    `e24d7a9ddcedae3f4d27e1d0d3e83889220892c264fd727ac88abfd880578fcc`
  - `status.json`:
    `ed5b4a2a4f30991e80b661f8658c998d637ca684f098d6a8f538e459210d07cc`
  - `telemetry.csv`:
    `baabf63c2d75ba7f898125fa0180c9dc2754cc2f8d304251f8faa00ec034e5b1`

This smoke authorizes the unchanged 20-scenario, 150-second development gate.
It is not policy-performance evidence.
