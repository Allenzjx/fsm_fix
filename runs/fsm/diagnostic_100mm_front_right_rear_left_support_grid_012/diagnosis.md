# Front-right/rear-left support grid 012 diagnosis

- Physical candidates, scenario, controller, physics, and thresholds were
  identical to grid 011.
- Definition change: the validated attempt-022 formal full-top aggregate
  excludes the legacy link-center bounding-box proxy; actual non-wheel
  collision rejection remains ContactSensor external force above 5 N.
- Physical result: **0 / 25 strict successes**, 18 collisions, 7 timeouts.
- Result SHA256:
  `0872686a7dd8f56559e7a8d163ee5fe6eb9d874f3507de27223cc3e2a6adc670`.

Every candidate field other than the two corrected historical diagnostic
fields was identical to grid 011. This includes all 25 first-terminal times,
failure reasons, poses, forces, reference commands, IK counts, and clamp
counts. The definition correction therefore did not alter candidate physics.

Eight candidates entered at least one phase-9/10 sample satisfying the formal
force-independent full-top, support, tilt, angular-velocity, and active-state
requirements:

- 2 mm common extension: 2 of 5 replicates;
- 4 mm common extension: 2 of 5 replicates;
- 6 mm common extension: 2 of 5 replicates;
- 8 mm common extension: 2 of 5 replicates;
- 0 mm control: 0 of 5 replicates.

For every one of those eight eligible candidates, the maximum over time of
the simultaneous minimum four-wheel upward force was exactly 0 N. Every
strict success-condition dwell remained 0.0 s. The five timeout candidates
among them all ended with front-right upward force 0 N and rear-left upward
force only 0.169--0.775 N, while front-left and rear-right carried about
12.8--13.9 N and 13.7--15.0 N.

The common 2--8 mm extension was fully applied with zero IK fallback and zero
command clamp, so the negative result is not an application failure. Relative
to the no-rear-right-extension baseline, the fixed reachable 15 mm rear-right
extension moved the zero-load corner from rear-right to front-right; the
common diagonal extension up to 8 mm did not restore simultaneous four-point
support.

Grid 013 continues the same single variable at 8/11/14/17/20 mm, with the
same fixed 15 mm rear-right extension and Latin rotation. It also records
eligible sample count, per-wheel maximum upward force within eligibility, and
the full four-wheel force snapshot at the best simultaneous minimum. Those
fields are observational only and do not affect control or termination.
