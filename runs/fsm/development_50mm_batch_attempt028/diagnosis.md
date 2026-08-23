# Development 50 mm batch attempt 028 diagnosis

## Immutable result

- The exact environment process (`PID 121372`) exited naturally.
- Evaluator execution passed for all 20 development scenarios.
- Strict success: **12/20 (60%)**.
- Failures:
  - `BODY_OR_LINK_COLLISION`: 7
  - `FSM_PHASE_TIMEOUT`: 1
- FSM config SHA-256:
  `25563d73eb883f7514a2458387b8c99279f3af394a90508ffa021a04d7ee914c`
- Result SHA-256:
  `7fb3bea395971f31c2489a65faaa6bd3c9566768399b3f01069dc6341fdfd0e7`
- Episodes SHA-256:
  `45ab81f4158210b160b7f12016c88a618a525cf5df1ba74618114475ea3141a6`
- Telemetry SHA-256:
  `2bb4b5f39a0375c58347eba9fca7b480faa4a1ddc86d6894b67fd00b0b9a0b6a`

## Engineering-admissibility audit

The result provenance records the effective 50 mm formal wheel-center offsets
as exactly zero for all four legs. Across all 20 episodes:

- baseline analytic-IK invalid count: **0**
- per-leg analytic-IK invalid counts: **0/0/0/0**
- formal/diagnostic geometry clamp count: **0**

The 12 strict successes therefore do not depend on an unreachable IK target or
silent clamp.

## Failure audit

The seven collision failures were scenarios 0003, 0005, 0006, 0008, 0009,
0017, and 0019. Every collision was `front_right_bot` above the unchanged
5 N ContactSensor threshold. Scenarios 0005, 0006, 0008, 0009, 0017, and
0019 reproduced the phase-8 collision branches from attempt 026. Scenario
0003 failed later after entering the post-transfer stage.

Scenario 0013 was the only `FSM_PHASE_TIMEOUT`. It ended with
`full_wheel_on_top=[true,false,false,true]`; its diagnostic
`front_right_bot` force was 2.058 N, below the formal collision threshold.

No global `TIMEOUT` remained. In attempt 026, the same 12 scenarios that now
succeeded had each timed out after accumulating rear-left IK fallbacks from
the unscaled 100 mm geometry.

## Decision

Attempt 028 establishes a real, nonzero, engineering-admissible 50 mm FSM
baseline on the complete development split. The 60% rate is not represented
as robust or production-ready. The seven collision branches and one phase
timeout remain valid baseline failures for the later paired PPO comparison.

The next required measurement is the complete 75 mm development split under
the same immutable FSM config, using 50% of the selected 100 mm support
offsets as declared in provenance.
