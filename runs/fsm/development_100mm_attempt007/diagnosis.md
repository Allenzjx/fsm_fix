# Attempt 007 diagnosis

This run is retained as a failed FSM-development attempt.

The continuous height-conditioned rear time map removed attempt 006's
premature phase-5 collision. The run safely crossed 69.10 s and entered phase
6 after the recorded 100 mm front placement.

The phase-6 source wheel command remained 0.3 rad/s while rear preparation
advanced. From phase-6 entry at 75.40 s to the 78.833 s terminal state:

- base x advanced from 0.684783 m to 0.755388 m;
- rear wheels remained on the ground behind the obstacle edge;
- rear-right hip advanced to 29.8 degrees;
- pitch reached -0.1441 rad;
- `base_link` external contact reached 38.5535 N.

The next attempt holds all wheel speeds at zero during BODY_TRANSFER (phase 6)
and retains the phase-7/8 contact-gated 0.3 rad/s recovery. This lets the
continuous rear preparation complete before the base is pushed farther across
the edge. No safety, contact, command, or success threshold is changed.
