# Diagnostic 75 mm support-activation grid 036

## Immutable result

- The exact environment process (`PID 155560`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five activation schedules, five Latin replicates)
- Strict success: **0/25**
- Failure outcome: **25/25 global timeouts**
- Result SHA-256:
  `962539dcabf5db173fc04bf07a5028b618da8b8400df8d955aa52b8d6975aa4d`

| Start phase/progress | Eligible samples | Best minimum upward force | Longest strict dwell | IK-invalid |
| ---: | ---: | ---: | ---: | ---: |
| 8 / 0.50 | 742 | 2.072 N | 0.0500 s | 5,444 |
| 8 / 0.75 | 845 | 2.225 N | 0.0667 s | 4,809 |
| 9 / 0.00 | 482 | 2.039 N | 0.0167 s | 0 |
| 9 / 0.20 | 367 | 3.309 N | 0.3333 s | 0 |
| 9 / 0.40 | 390 | 2.211 N | 0.1000 s | 0 |

Every clamp count was zero. Both phase-8 schedules are engineering-rejected
because the half-scale targets become unreachable during the phase-8
reference posture, causing thousands of baseline IK fallbacks. The three
phase-9 schedules are reachable, but none improves on grid 035's 0.5667 s
maximum and no activation timing produces a repeatable dwell trend.

## Decision

Stop timing-only searches. Return to the reachable phase-9/0.4 geometry,
phase-7/8 front/rear speed split 0/+0.3 rad/s, and zero phase-9/10 drive.
The next grid varies only a bounded high-load radial-shortening controller
over 0/0.5/1.0/1.5/2.0 mm at a fixed 0.5 mm/s rate. This directly targets
the measured diagonal rocking: front-left/rear-right carry roughly 10--14 N
while front-right/rear-left repeatedly cross the unchanged 2 N threshold.
The 0 mm branch is an exact disabled-controller baseline.
