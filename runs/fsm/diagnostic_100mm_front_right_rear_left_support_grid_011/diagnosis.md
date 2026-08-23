# Front-right/rear-left support grid 011 diagnosis

- Physical candidates, scenario, controller, physics, and thresholds were
  identical to grid 010.
- Physical result: **0 / 25 strict successes**, 18 collisions, 7 timeouts.
- All 25 candidate scalar first-terminal fields compared between grids 010 and
  011 were identical.
- Result SHA256:
  `6b5889b6157a2439a5eeb91f65d8a14e4d548494c1ca3a5736d92d849c93bade`.

The corrected audit only accumulates in phases 9/10 when the environment's
formal force-independent success conditions are satisfied: all four wheels
fully inside the top footprint, support geometry valid, tilt bounded, angular
velocity bounded, and no terminal safety event.

No candidate produced even one eligible sample. Therefore every corrected
best-minimum upward force is `null` and every success-condition dwell is
0.0 s. This proves that grid 010's earlier nonzero fields came only from
initial ground support and that phase-9/10 load tuning cannot by itself satisfy
the formal metric: the force-independent full-top geometry is never present.

The next run returns to the unchanged formal controller. Attempt 021 adds only
per-wheel ordinary-top and formal-full-top flags, the aggregate formal
`all_wheels_on_top` predicate, support score, and wheel y positions to status,
CSV, and terminal evidence. Its purpose is to identify the exact geometric
subcondition that blocks success before any further physical parameter change.
