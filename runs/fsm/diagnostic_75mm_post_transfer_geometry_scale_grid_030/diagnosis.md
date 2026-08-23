# Diagnostic 75 mm post-transfer geometry scale grid 030

## Immutable result

- The exact environment process (`PID 99576`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five scales, five Latin-rotated replicates)
- Strict success: **0/25**
- Result SHA-256:
  `bd529bbc54aa39afd1b447f17faaa268c1e3d7bb7e2121063046986cb9afb9ed`

## Scale results

| 100 mm geometry scale | Success | IK-invalid total | Clamp total | Terminal outcomes |
| ---: | ---: | ---: | ---: | --- |
| 50.0% | 0/5 | 0 | 0 | 5 collisions |
| 62.5% | 0/5 | 2,574 | 0 | 5 collisions |
| 75.0% | 0/5 | 2,756 | 0 | 5 collisions |
| 87.5% | 0/5 | 2,865 | 0 | 3 collisions, 2 timeouts |
| 100.0% | 0/5 | 2,945 | 0 | 3 collisions, 2 timeouts |

Every IK-invalid sample above 50% occurred exclusively on the rear-left leg.
Front-left, front-right, and rear-right each remained at zero invalid samples.
No scale produced a force-independent complete all-wheel-top sample, so the
best simultaneous upward-force and strict-dwell diagnostics remained null/0.

## Decision

Common amplitude scaling is rejected. The 50% geometry is fully reachable but
leaves front-right off the complete top footprint. Higher common scales cross
the rear-left reach boundary before they solve that geometry.

The next grid preserves rear-left and rear-right at their reachable 50%
offsets (5.625 and 7.5 mm), keeps the same phase-9 start, and varies only
front-right from 9.25 to 18.5 mm. Grid 030 proves that front-right itself
remains analytically reachable even at the 100% common-scale endpoint, so this
is a measured single-variable continuation rather than a new mechanism.
