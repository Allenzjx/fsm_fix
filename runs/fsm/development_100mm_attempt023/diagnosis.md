# Formal 100 mm attempt 023 diagnosis

- Controller: formal FSM loaded from `configs/fsm.yaml`.
- Scenario: `development-h100-0000`.
- Candidate geometry: FR/RL/RR 18.5/11.25/15 mm, common start 0.4.
- Result: **0 / 1**, `TIMEOUT`.
- Baseline IK fallback: **0**.
- Result SHA256:
  `f19a654ef775031d120c013cca852879b469f37ba72f48e982719a5ef9420f41`.
- Telemetry SHA256:
  `3c7b821f96550c20db847c25e7298a647a0194bb10111c6a2d51d44a2ad97eff`.

The formal single environment did not reproduce grid 022 candidate 19. The
failure was a temporal mismatch between geometry capture and force capture,
not an unreachable command:

- all four wheels satisfied the formal complete-top geometry from 129.2 to
  131.6 s;
- all four upward forces reached at least 2 N only from 133.6 s onward;
- front-right wheel y moved from -0.4182 m at 130 s to approximately
  -0.4312 m by 140 s while the post-transfer drive continued;
- at 135 s the four upward forces were
  4.291/11.544/10.373/2.303 N, but front-right complete-top geometry was
  already false;
- terminal full-top flags were true/false/true/true.

Thus the controller achieved each half of the unchanged success predicate in
separate windows. Attempt 024 changes only the post-transfer capture trigger:
wheel drive stops when complete all-wheel geometry is captured OR when all
four forces are supported. The success predicate, thresholds, geometry,
physics, and scenario remain unchanged.
