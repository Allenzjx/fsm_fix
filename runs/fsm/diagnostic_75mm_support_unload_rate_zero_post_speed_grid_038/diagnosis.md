# Diagnostic 75 mm support-unload rate grid 038

## Immutable result

- The exact environment process (`PID 86084`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five shortening rates, five Latin replicates)
- Strict success: **1/25**
- Other outcomes: **24/25 global timeouts**
- Result SHA-256:
  `cdbf788713344787fe89824b8faad83e997f1d8627a6e3533393b91745ce7f0c`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp. All
nonzero branches reached the fixed 2 mm front-left/rear-right shortening
bound without shortening front-right or rear-left.

| Shortening rate | Success | Longest diagnostic dwell | Mean diagnostic dwell |
| ---: | ---: | ---: | ---: |
| 0.25 mm/s | 0/5 | 1.1833 s | 0.6833 s |
| 0.50 mm/s | 0/5 | 1.2333 s | 0.8800 s |
| 0.75 mm/s | **1/5** | 1.4833 s | 0.8700 s |
| 1.00 mm/s | 0/5 | 1.2167 s | 0.5600 s |
| 1.50 mm/s | 0/5 | 1.2333 s | 0.6600 s |

The successful 0.75 mm/s candidate terminated naturally at 149.8333 s with
front-left/rear-right trim 2/2 mm, terminal upward forces
7.999/5.954/6.692/7.957 N, 0.2857 m longitudinal margin, and zero non-wheel
contact. The grid-side diagnostic loop reports 1.4833 s because it excludes
the step on which the environment terminates; the environment's authoritative
internal counter included that 90th step and satisfied the unchanged 1.5 s
predicate.

## Decision

One success in five repetitions is evidence of a valid mechanism, not enough
robustness for formal promotion. Fix the successful 2 mm / 0.75 mm/s load
controller and repeat the five post-transfer forward speeds
0/0.0375/0.075/0.1125/0.15 rad/s. Earlier grids showed that moderate drive
creates complete-top geometry sooner, while the new load controller can now
hold balanced force. The combined grid tests whether both conditions can
overlap repeatably before the fixed 150 s timeout.
