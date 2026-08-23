# Diagnostic 75 mm post-transfer forward-speed grid 035

## Immutable result

- The exact environment process (`PID 110384`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five phase-9/10 speeds, five Latin replicates)
- Strict success: **0/25**
- Failure outcome: **25/25 global timeouts**
- Result SHA-256:
  `7551f8c55d4ff0f6c2b75270efd5137edd7f6a1f72321429d247852efa1fb4a6`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp.

| Phase-9/10 forward speed | Eligible samples | Best minimum upward force | Longest strict dwell |
| ---: | ---: | ---: | ---: |
| 0.0000 rad/s | 409 | 3.697 N | 0.5667 s |
| 0.0375 rad/s | 472 | 0.000 N | 0.0000 s |
| 0.0750 rad/s | 1,077 | 8.365 N | 0.4000 s |
| 0.1125 rad/s | 1,969 | 8.462 N | 0.1167 s |
| 0.1500 rad/s | 2,429 | 8.488 N | 0.0167 s |

Lower speed does not monotonically increase the number of complete-top
samples or the best simultaneous force. It does, however, produce the two
longest continuous strict windows. One 0 rad/s replicate ended at the fixed
150 s timeout while still carrying 10.565/3.720/4.374/10.119 N upward force,
after 0.5667 s of uninterrupted strict support. One 0.075 rad/s replicate
also ended while carrying 10.678/2.856/3.435/11.622 N after a 0.4 s strict
run. These are real but insufficient windows; the 1.5 s metric and 150 s
episode timeout remain unchanged.

## Decision

Use 0 rad/s as the next diagnostic post-transfer speed. Vary only when the
same reachable half-scale support geometry starts: phase 8 at progress
0.5/0.75 or phase 9 at progress 0/0.2/0.4, with five Latin replicates.
The phase-9/0.4 schedule is the exact grid-035 baseline. This tests whether
making the support target available earlier moves the late continuous window
far enough forward to satisfy 1.5 s within the immutable 150 s episode.
