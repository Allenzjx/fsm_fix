# Rear-left extension relief grid 015 diagnosis

- Fixed front-right extension: 14 mm.
- Fixed rear-right extension: 15 mm.
- Fixed phase-9 ramp start progress: 0.4.
- Varied rear-left extension: 8/9.5/11/12.5/14 mm.
- Raw result: **1 / 25 strict successes**, 12 collisions, 12 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `b4d114f9c06ffab97595d6103b3da844b940ad933f13a1ba063492f0d7ca58f7`.

The single raw success was the 14 mm control, candidate 20. It reached a best
minimum force of 6.2528 N with snapshot
6.253/8.273/7.954/6.276 N, but retained 94 rear-left IK fallback steps and is
therefore rejected.

Reducing rear-left extension isolated a narrow reachable support boundary:

- 9.5 mm was fully reachable, but the best eligible replicate reached only
  1.5584 N minimum;
- 11.0 mm was fully reachable, and candidate 19 reached a best simultaneous
  minimum of 2.0726 N with snapshot
  4.472/11.791/10.477/2.073 N;
- 12.5 mm accumulated 494 rear-left fallback steps;
- 14.0 mm accumulated fallback in the long-lived branches.

Candidate 19 is the first measured phase-9/10 state to combine all four forces
above the unchanged 2 N threshold with 0/0/0/0 per-leg fallback and zero
clamp. However, that condition lasted only one control step
(0.01667 s), far below the required 1.5 s dwell, so it is correctly not a
success.

Grid 016 holds every other command fixed and resolves the rear-left boundary
over 11.00/11.25/11.50/11.75/12.00 mm. The 11.00 mm value is an exact
control. Selection still requires strict environment success, 0/0/0/0
per-leg fallback, and zero command clamp.
