# Diagnostic 75 mm support-unload grid 037

## Immutable result

- The exact environment process (`PID 167064`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five shortening limits, five Latin replicates)
- Strict success: **0/25**
- Failure outcome: **25/25 global timeouts**
- Result SHA-256:
  `3498c572a0b378a946dbd35946555cf6bb5e721dc9ab3496e2c7388f6f0a1e02`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp. The
terminal trim confirms that the controller selected only the measured
high-load diagonal: front-left and rear-right reached the configured bound,
while front-right and rear-left remained at zero shortening.

| Maximum shortening | Best minimum upward force | Longest strict dwell | Mean strict dwell |
| ---: | ---: | ---: | ---: |
| 0.0 mm | 3.697 N | 0.5667 s | 0.1233 s |
| 0.5 mm | 4.094 N | 0.7167 s | 0.2533 s |
| 1.0 mm | 4.768 N | 1.3500 s | 0.4533 s |
| 1.5 mm | 5.340 N | 1.0333 s | 0.3467 s |
| 2.0 mm | 6.769 N | 1.2500 s | 0.6667 s |

The load-transfer mechanism is validated even though no candidate reaches
the unchanged 1.5 s requirement. The 2 mm group has the strongest group-level
trend: three of five replicates sustain 0.8667--1.25 s and one ends at the
150 s cutoff with balanced 7.729/6.589/7.131/7.211 N upward forces. The
fixed 0.5 mm/s rate needs four seconds to reach the 2 mm bound, leaving the
balanced state late in the episode.

## Decision

Fix maximum shortening at 2 mm and vary only the rate over
0.25/0.5/0.75/1.0/1.5 mm/s with five Latin replicates. The 0.5 mm/s value is
an exact grid-037 comparison. A successful candidate must still have zero
fallback/clamp and satisfy the full 1.5 s strict predicate before the fixed
150 s timeout.
