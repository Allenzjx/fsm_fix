# Current-config 50 mm development attempt 043 diagnosis

- Execution passed for all 20 scenarios under `fsm.yaml` SHA-256
  `1943be80e44e57ff63b479195970e0e02d0bad6f22bc4712337cec51fae243af`.
- Effective endpoint policy was recorded as rear-transfer wheel speeds
  0.3/0.3/0.3/0.3 rad/s, post-transfer speed 0 rad/s, zero support-geometry
  offset, and zero support-unload maximum.
- Strict result: 12/20 successes (60%). Failures were seven
  `BODY_OR_LINK_COLLISION` events on `front_right_bot` and one
  `FSM_PHASE_TIMEOUT`. This exactly matches formal attempt 028's result
  structure.
- All 20 scenarios had zero analytic-IK fallback on every leg, zero support
  clamp count, and zero support-unload trim.
- The phase-timeout branch had only a sub-threshold 2.058 N
  `front_right_bot` terminal diagnostic; the seven collision branches measured
  8.399--21.692 N and therefore exceeded the unchanged 5 N rejection
  threshold.
- Result SHA-256:
  `778ee3de28b15e48d05667d10f1939d2fef1bef176325555d463207b01208adc`.
  Episodes SHA-256:
  `45ab81f4158210b160b7f12016c88a618a525cf5df1ba74618114475ea3141a6`.
  Telemetry SHA-256:
  `2bb4b5f39a0375c58347eba9fca7b480faa4a1ddc86d6894b67fd00b0b9a0b6a`.

The current formal configuration preserves the 50 mm endpoint behavior.
The 100 mm endpoint still requires the same-hash rerun before FSM freezing.
