# Front-right extension balance grid 019 diagnosis

- Fixed rear-left extension: 11.25 mm, its zero-fallback upper bound.
- Fixed rear-right extension: 15 mm, its zero-fallback upper bound.
- Varied front-right extension: 10/11/12/13/14 mm.
- Fixed common phase-9 ramp start: 0.4.
- Result: **0 / 25 strict successes**, 12 collisions, 13 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `4d407840667c67f9af16ffc10badf96582e349ec49cae893ed0cf5eec40ef0d4`.

All 25 candidates finished with 0/0/0/0 per-leg analytic-IK fallback and
zero diagnostic clamp. The 12 collisions occurred in phase 8 before the
varied phase-9 offsets became active, matching the prior grid's common early
branch and providing no evidence against a particular front-right value.

The proposed downward load redistribution was falsified:

- 10 mm produced no formally eligible sample in its sole timeout;
- 11 mm produced two eligible timeout branches but a 0 N best simultaneous
  minimum;
- 12 mm peaked at 0.9566 N;
- 13 mm peaked at 0 N;
- 14 mm produced the grid maximum of 1.6522 N.

No candidate accumulated even one sample of the full success condition, so
the maximum strict-condition dwell was 0 s. In the best 14 mm snapshot at
131.45 s, the ordered FL/FR/RL/RR upward forces were
3.968/12.265/10.891/1.652 N. The limiting rear-right force increased rather
than decreased at the upper end of this sweep.

Grid 020 therefore keeps rear-left/rear-right at 11.25/15 mm and resolves the
adjacent front-right upper boundary at 14.00/14.25/14.50/14.75/15.00 mm.
Selection still requires environment strict success, 0/0/0/0 fallback, and
zero clamp; any front-right fallback invalidates that value.
