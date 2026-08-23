# Diagnostic 75 mm rear-transfer front-speed grid 033

## Immutable result

- The exact environment process (`PID 173436`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five front-wheel speeds, five Latin replicates)
- Strict success: **0/25**
- Result SHA-256:
  `adccfc8840de359ebbe43f13848f12ef0749532f96e381411aa7bc4e4eaf2228`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp.

| Front speed in phases 7--8 | Outcome summary | Complete-top samples | Best minimum upward force | Longest strict dwell |
| ---: | --- | ---: | ---: | ---: |
| -0.30 rad/s | 5 timeouts in phase 7 | 0 | n/a | 0 s |
| -0.15 rad/s | 3 rear-left collisions, 2 phase-8 timeouts | 0 | n/a | 0 s |
| 0.00 rad/s | 5 phase-10 timeouts | 2,599 | 8.365 N | 0.2833 s |
| +0.15 rad/s | 4 front-right collisions, 1 timeout | 0 | n/a | 0 s |
| +0.30 rad/s | 5 front-right collisions | 0 | n/a | 0 s |

Zero front-wheel speed is the only tested value that repeatedly preserves
force-independent complete all-wheel-top geometry. All five replicates also
crossed the unchanged 2 N threshold on all four wheels at least briefly. The
best replicate sustained the full strict condition for 0.2833 s, which is
real progress but still below the unchanged 1.5 s requirement.

## Decision

The rear-transfer front speed is fixed at 0 rad/s for the next diagnostic;
both rear wheels remain +0.3 rad/s. With phase-8 geometry now preserved, vary
only the phase-9 front-right support offset over the same reachable
9.25--18.5 mm range. Rear-left/rear-right remain fixed at their reachable
5.625/7.5 mm offsets. This tests whether additional front-right load can turn
the observed 0.2833 s window into the required 1.5 s dwell.
