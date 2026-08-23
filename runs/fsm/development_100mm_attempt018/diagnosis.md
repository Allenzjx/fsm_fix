# FSM 100 mm development attempt 018 diagnosis

- Scenario: `development-h100-0000`.
- Result: **FAIL**, `BODY_OR_LINK_COLLISION`.
- First terminal event: `front_right_bot` at 10.064577 N and 142.0333 s.
- Forward progress: 1.113575 m.
- Terminal wheel-center z: front-right 0.113373 m; the other three wheels
  remained near the 0.15 m top plane.
- Terminal controller audit: all wheels commanded physical-forward at
  0.300000 rad/s, baseline IK fallback count 0, all rejected load trims 0.
- Result SHA256:
  `fde6c05c0ef03a3d68d5a654392999d0686447ad3abf10dcbd3e97223b3cb082`.

The height-conditioned all-wheel drive removed the grid-007
`-1.32/-1.31/0/0` front-reversal split and increased traversal, but continuous
driving did not hold the front-right wheel on the top.

The telemetry contains a low-roll contact transition at 138.05 s: all four
contact states were top and the **contact-force magnitudes** were
6.86/9.67/6.75/10.86 N, with roll/pitch 0.04583/-0.04722 rad. A later audit
found that the evaluator had logged magnitudes while the success predicate
uses world-Z upward components. This row therefore does **not** prove that the
unchanged all-wheel upward >=2 N predicate was satisfied.

Attempt 019 kept all attempt-018 geometry and thresholds and attempted to stop
on the actual upward-force predicate. Its later bit-identical telemetry showed
that the magnitude-based hypothesis did not activate a sustained capture.
