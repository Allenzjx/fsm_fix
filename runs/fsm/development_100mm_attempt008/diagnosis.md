# Attempt 008 diagnosis

This run is retained as a failed FSM-development attempt.

Holding wheel speed at zero throughout phase 6 reduced, but did not eliminate,
the collision:

- phase-6 base travel fell from 70.6 mm in attempt 007 to approximately
  18.7 mm;
- terminal `base_link` contact fell from 38.5535 N to 19.0039 N;
- termination remained at approximately 78.85 s during rear preparation.

The remaining mechanism is the sequential 50 mm rear preparation. Rear-left
hip reaches its shortened-leg posture before rear-right hip, creating a
diagonal support transient while the body straddles the 100 mm edge. Wheel
speed is therefore an amplifier rather than the sole cause.

The next attempt keeps the exact recorded-safe endpoints but replaces only
phase 6 at larger heights with coordinated smooth motion: both rear hips move
together for the first 65% of phase, then the recorded rear-right knee tuck is
completed. The override is blended by obstacle height (0 at 50 mm, 0.5 at
75 mm, 1 at 100 mm), is continuous at both phase boundaries, and does not
change any command limit or safety criterion.
