# Front-right/rear-left support grid 010 diagnosis

- Scenario: `development-h100-0000`.
- Fixed geometry: rear-right extension 15 mm.
- Single varied parameter: common front-right/rear-left extension
  (`0/2/4/6/8 mm`), five Latin-rotated candidates per value.
- Physical result: **0 / 25 strict successes**.
- Outcomes: 18 body/link collisions and 7 global timeouts.
- Terminal phases: 12 in phase 8 and 13 in phase 10.
- Collision bodies: 12 `rear_left_bot` contacts before intervention and 6
  late `front_right_bot` contacts.
- All 25 candidates had zero baseline-IK fallback.
- Result SHA256:
  `236764a7c09710f221fafdc26571b91f0e6f177796f129b14df1858c4910c4cc`.

The same 12 environment IDs as grids 008/009 collided in phase 8 before the
varied phase-9/10 geometry. Among the remaining candidates, collision-free
global timeouts occurred at 2 mm (two), 4 mm (one), 6 mm (two), and 8 mm
(two). The 0 mm control had no timeout. These are valid physical first-terminal
and IK observations, but none met the unchanged success predicate.

## Secondary audit-field invalidation

Grid 010 introduced trajectory-wide fields intended to measure recovery
support quality. Their accumulator was not restricted to phase 9/10 and
therefore counted the robot's initial four-wheel ground support. Values such
as 2.5--7.1 s and 6.94--10.89 N do **not** describe top capture and must not be
used to rank candidates. The 0/25 success count and physical terminal
snapshots remain valid because the environment's formal success implementation
was unchanged.

Grid 011 repeats the identical 25 candidates, scenario, controller, physics,
and thresholds after changing only the diagnostic accumulator. The corrected
scope requires phase 9/10, the formal full-top geometry/support predicate,
bounded tilt and angular velocity, and an active non-terminal environment
before measuring minimum upward force or continuous success-condition dwell.
