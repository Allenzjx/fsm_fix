# Method B reward-v4 seed-11 50 mm development gate attempt001

- Status: execution `PASS`, curriculum promotion `FAIL`.
- Deterministic final checkpoint:
  `e23b091a4a3f05b2092963a3960df7b1a2539a3e62072cb095b375e8587b87f0`.
- Frozen development manifest: `development_v2.json`, SHA-256
  `f3d10d7340c06f78c200c44119bb2e17c81e587bd314b342ac90b49019ea2cdc`.
- Result: 5/20 successes (25%), below the registered 16/20 threshold.
- Failures: eight `BODY_OR_LINK_COLLISION`, three `FSM_PHASE_TIMEOUT`,
  and four global `TIMEOUT`.
- All eight collisions were on `front_right_bot`; collision-force mean/min/max
  were 16.42 / 6.48 / 22.34 N.
- Successful scenario IDs were 0001, 0002, 0013, 0015, and 0018.
  Four were also frozen-FSM successes; v4 rescued 0013 but caused eight
  frozen-FSM successes to fail.
- Every delay-2 scenario failed (five collisions, two phase timeouts, two
  global timeouts). The five successes all had delay 0 or 1. Training
  attempt001 used only nominal delay 0, friction 1.0, zero observation noise,
  and a single initial distance.
- Late residuals were physically small but systematic. Phase-8 collision
  endpoints showed positive rear-left x residuals and differential wheel
  speeds; phase-10 success and timeout actions were nearly identical, so the
  policy did not learn disturbance-conditioned corrections.
- Telemetry contains 52,130 rows and 122 columns with uniform row width.
  The complete 64-field action-to-actuator chain is finite. The only
  non-finite telemetry values are 5,643 intentional `margin_m` NaNs where the
  support interval is invalid; episode records separately count these invalid
  samples.
- Artifact SHA-256 values:
  - `episodes.jsonl`:
    `78a00452a257ade3127a3dffef5caa763bdc579e34108af189086948a473db1e`
  - `status.json`:
    `bc3d861eee0c6d5f9854e1036f8789a4dfa1f8a9d23b75984eafc1a219b62f75`
  - `telemetry.csv`:
    `b9f76b13b8fbed1cd666c31bb176c117b9aa8602b0e12d3912c988e567190486`
  - `result.json`:
    `e392711cb0ed936c8b6c957de5e51b55aac032cc0920687e83d6a3bc7f0d9b13`

Two common training defects are now directly evidenced. First, `stuck=-6`
was charged once per 60 Hz control step: one second of stuck occupancy cost
-360, making a one-time -200 collision termination preferable to continued
recovery. Second, phase-local progress fell from approximately one to zero at
each phase transition, cancelling the intended dense phase-advancement
reward. Reward v5 will integrate stuck occupancy in seconds and use monotonic
global FSM progress. Its 50 mm training distribution will also cover bounded
initial-pose, friction, delay, and sensor-noise variation rather than the
single nominal point. Frozen FSM, metrics, success rules, action semantics,
and B/C-only CoM difference remain unchanged.
