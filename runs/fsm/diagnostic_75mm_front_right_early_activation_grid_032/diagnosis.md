# Diagnostic 75 mm early front-right activation grid 032

## Immutable result

- The exact environment process (`PID 172804`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five amplitudes by five phase-7 start progresses)
- Strict success: **0/25**
- Result SHA-256:
  `f78962e3d70b9682cde1797bdac1fb92984093b7a1f67dc06961accdcd07234b`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp. No
candidate recorded a force-independent complete all-wheel-top sample.

All 9.25, 11.5625, and 13.875 mm combinations collided at
`front_right_bot`. At 16.1875 mm, phase-7 starts 0.6 and 0.8 avoided collision
but globally timed out with front-right 0 N and rear-left about 1.04--1.08 N.
At 18.5 mm, only the 0.8 start avoided collision; it timed out with
front-right 0 N and rear-left about 0.84 N. Earlier geometry activation can
delay failure but does not preserve the declared complete footprint.

## Decision

Early front-right support geometry alone is rejected. The next single
variable is the wheel-speed split used only while the rear-transfer gate is
waiting in phases 7--8. The current controller overwrites all four wheels with
physical-forward +0.3 rad/s. Since telemetry shows front-right leaving the top
footprint while the rear wheels still need forward travel, the diagnostic
will hold both rear wheels at +0.3 and sweep the two front wheels over
-0.3/-0.15/0/0.15/0.3 rad/s. The formal 50%-scale 75 mm geometry and every
metric remain unchanged.
