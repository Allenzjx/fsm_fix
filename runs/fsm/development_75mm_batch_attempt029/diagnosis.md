# Development 75 mm batch attempt 029 diagnosis

## Immutable result

- The exact environment process (`PID 104216`) exited naturally.
- Evaluator execution passed for all 20 development scenarios.
- Strict success: **0/20**.
- Failure count: `BODY_OR_LINK_COLLISION` 20/20.
- All 20 collisions were `front_right_bot` contacts above the unchanged
  5 N ContactSensor threshold.
- FSM config SHA-256:
  `25563d73eb883f7514a2458387b8c99279f3af394a90508ffa021a04d7ee914c`
- Result SHA-256:
  `ac87e628c3af051c9e800d6006d590eb55a570183291cf2da08f9f42a49b680f`
- Episodes SHA-256:
  `2ece8c63e947b08d1b056840f751986dfe864aeb42e799155d94ce432322232b`
- Telemetry SHA-256:
  `0e5bcdb236393c61fdd5066f6bf66a6214910130e5b38aba86a73b586aa2fd09`

## Geometry and reachability audit

The result provenance records the effective 75 mm formal offsets as:

- front-left: 0 mm
- front-right: 9.25 mm
- rear-left: 5.625 mm
- rear-right: 7.5 mm

These are exactly 50% of the selected 100 mm target. Across all episodes:

- baseline analytic-IK invalid count: **0**
- per-leg analytic-IK invalid counts: **0/0/0/0**
- formal/diagnostic geometry clamp count: **0**

Thus the failure is not caused by an unreachable target or silent clamp.

No scenario ever recorded even one `all_wheels_on_top` telemetry sample.
Nineteen scenarios reached phase 10 and ended with front-right as the only
wheel not fully on top; its upward force was 0 N. Their terminal front-right
wheel y positions clustered near -0.46 to -0.48 m. The phase-9/10 wheel
command remained the declared 0.15 rad/s because the capture predicate never
became true.

Scenario 0011 was the sole earlier branch. It collided in phase 7 near
100.65 s. The other 19 collided in phase 10 near 137--138 s.

## Decision

Attempt 029 is retained as a formal negative result. Linear 50% scaling is
reachable but insufficient to bring the front-right wheel into the complete
top footprint before continued post-transfer rolling produces link contact.

The next diagnostic holds every metric, phase, speed, source trajectory, and
scenario fixed, and varies only the common scale applied to the already
selected 100 mm offsets over 50/62.5/75/87.5/100%. Five Latin-rotated
replicates per scale will distinguish an amplitude threshold from
environment-index contact-solver sensitivity. Any candidate with IK fallback
or clamp remains ineligible.
