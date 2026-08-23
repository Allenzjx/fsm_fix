# Formal 100 mm development batch attempt 025

- Controller/config hash:
  `809577abdddcd229071edf0f406f07ecbfdf20464089da3674f9245542bbcf16`.
- Scenarios: all 20 development 100 mm scenarios.
- Result: **7 / 20 strict successes (35%)**.
- Failures: 7 `BODY_OR_LINK_COLLISION`, 6 `TIMEOUT`.
- Result SHA256:
  `0724ed582e4c130afbc32685b28eec820781c955792fc098d215e01bf7e51c65`.
- Episodes SHA256:
  `1b3e1aff4f62dbc762254658d06f3dd3a2f1e192c51ae449ad6e0f0b1bc1396d`.
- Telemetry SHA256:
  `94f1ef65fc2971661aeaf1b4c8ddf56e49b56d4541942d15982b1b56e8d34931`.

Reachability and safety audit:

- all 20 episodes had total baseline IK fallback zero;
- all 20 had per-leg counts 0/0/0/0;
- all 20 had formal clamp count zero;
- every success used the unchanged complete-top, stability, 2 N, and 1.5 s
  predicates.

All seven collision failures were `rear_left_bot` contacts above the formal
5 N threshold. They occurred in phase 8 before the selected phase-9 support
geometry activates, so they are retained as baseline failures rather than
attributed to the new support offsets.

Six scenarios timed out. Four ended with front-right outside the complete-top
footprint; two retained complete all-wheel geometry but did not develop
four-wheel load. These failures show that the FSM is not robust enough to
claim general 100 mm success. The defensible result is exactly 35% on this
development set.

The FSM now has real, strict, reachable development successes at 100 mm.
Before any freeze, attempts 026 and 027 will measure the same controller on
the 50 and 75 mm development splits.
