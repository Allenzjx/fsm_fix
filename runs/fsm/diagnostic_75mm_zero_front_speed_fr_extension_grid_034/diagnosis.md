# Diagnostic 75 mm zero-front-speed front-right grid 034

## Immutable result

- The exact environment process (`PID 125592`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five front-right amplitudes, five Latin replicates)
- Strict success: **0/25**
- Failure outcome: **25/25 global timeouts**
- Result SHA-256:
  `f71e7de0ac4f81d83d65563bb02fed67494e5de4f9bbe5aeaae601c981ea4d4b`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp.
Unlike grids 030--032, all 25 candidates entered force-independent complete
all-wheel-top geometry.

| Front-right offset | Eligible samples | Best minimum upward force | Longest strict dwell |
| ---: | ---: | ---: | ---: |
| 9.2500 mm | 2,293 | 8.359 N | 0.0167 s |
| 11.5625 mm | 2,360 | 7.625 N | 0.0500 s |
| 13.8750 mm | 2,610 | 7.705 N | 0.0167 s |
| 16.1875 mm | 2,469 | 6.848 N | 0.0333 s |
| 18.5000 mm | 2,449 | 10.333 N | 0.0167 s |

The amplitude response is not monotonic. Higher front-right extension can
produce a larger single-frame minimum force, but no amplitude preserves all
four upward forces above the unchanged 2 N threshold. The best dwell is only
0.05 s versus the required 1.5 s, and is shorter than grid 033's 0.2833 s.

## Decision

Reject front-right amplitude as the missing mechanism at 75 mm. Keep the
grid-033 phase-7/8 split (front 0, rear +0.3 rad/s) and the reachable
half-scale support geometry. The next grid varies only the exact phase-9/10
forward speed over 0/0.0375/0.075/0.1125/0.15 rad/s. This tests whether the
formal 0.15 rad/s capture/resume cycle is repeatedly breaking an otherwise
valid top-and-force state.
