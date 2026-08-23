# Diagnostic 75 mm front-right extension grid 031

## Immutable result

- The exact environment process (`PID 126592`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five front-right amplitudes, five Latin replicates)
- Strict success: **0/25**
- Result SHA-256:
  `2a70e5b71590f738d4d7e6fafee8666c5d6ab4b8949855ceefe7c30b96580009`

## Results

| Front-right offset | Success | IK-invalid | Clamp | Outcomes |
| ---: | ---: | ---: | ---: | --- |
| 9.2500 mm | 0/5 | 0 | 0 | 5 collisions |
| 11.5625 mm | 0/5 | 0 | 0 | 5 collisions |
| 13.8750 mm | 0/5 | 0 | 0 | 5 collisions |
| 16.1875 mm | 0/5 | 0 | 0 | 3 collisions, 2 timeouts |
| 18.5000 mm | 0/5 | 0 | 0 | 3 collisions, 2 timeouts |

Rear-left and rear-right remained fixed at their reachable 50% values of
5.625 and 7.5 mm. Every candidate had 0/0/0/0 per-leg IK fallback and zero
clamp, proving that the complete front-right amplitude range itself is
reachable at 75 mm.

No candidate entered a force-independent complete all-wheel-top sample.
Increasing front-right amplitude after phase 9 begins can delay or avoid some
collisions, but it cannot restore geometry already lost during phase 8.

## Decision

Late front-right amplitude alone is rejected. Formal telemetry from attempt
029 shows front-right fully on top at 105 s in phase 7, then off top by 110 s
in phase 8 while rear-transfer wheel drive remains active. The next diagnostic
ramps only the front-right offset during phase 7 and holds it through phase 10;
rear-left/rear-right still begin in phase 9. A 5x5 amplitude/start-progress
grid will locate whether early reachable geometry can preserve the front
support footprint during rear transfer.
