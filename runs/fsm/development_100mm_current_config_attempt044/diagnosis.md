# Current-config 100 mm development attempt 044 diagnosis

- Execution passed for all 20 scenarios under selection-time `fsm.yaml`
  SHA-256
  `1943be80e44e57ff63b479195970e0e02d0bad6f22bc4712337cec51fae243af`.
- Effective endpoint policy was recorded as rear-transfer wheel speeds
  0.3/0.3/0.3/0.3 rad/s, post-transfer speed 0.3 rad/s, full selected support
  offsets 0/18.5/11.25/15 mm, and zero support-unload maximum.
- Strict result: 7/20 successes (35%). Failures were seven
  `BODY_OR_LINK_COLLISION` events on `rear_left_bot` and six global
  `TIMEOUT` outcomes. This exactly matches formal attempt 025's result
  structure.
- All 20 scenarios had zero analytic-IK fallback on every leg, zero support
  clamp count, and zero support-unload trim. Nine of 20 terminal snapshots had
  all four wheels on top.
- Collision forces on `rear_left_bot` were 5.712--12.320 N, above the
  unchanged 5 N rejection threshold.
- Result SHA-256:
  `6a8790c641271ec46c603ba3cc7309698d22401a3d61dd6394a84edff526ee8b`.
  Episodes SHA-256:
  `1b3e1aff4f62dbc762254658d06f3dd3a2f1e192c51ae449ad6e0f0b1bc1396d`.
  Telemetry SHA-256:
  `94f1ef65fc2971661aeaf1b4c8ddf56e49b56d4541942d15982b1b56e8d34931`.

The current formal configuration preserves the 100 mm endpoint behavior.
Together with attempts 042 and 043, every target height now has nonzero
formal development success under one selection-time configuration hash.
