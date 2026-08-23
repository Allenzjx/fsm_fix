# Attempt 004 diagnosis

This run is retained as a failed FSM-development attempt.

The terminal reason was `BODY_OR_LINK_COLLISION` at 44.7167 s in phase 7.
The telemetry identifies a deterministic reference discontinuity at the
phase-6/phase-7 boundary:

- At 41.50 s, rear-leg servo references 04:07 were
  `[-0.7000, 0.0000, -0.7000, 0.0000]` degrees.
- At 41.60 s, the phase-7-only 50 mm substitute changed them to
  `[24.2000, 0.0000, 29.8000, -44.8000]` degrees.
- Over the same interval, pitch angular velocity changed from
  -0.0443 rad/s to -0.9248 rad/s.

The substitution did not violate the recorded scalar command envelope, but it
did violate trajectory continuity because the 50 mm rear-leg segment was
entered midway through its normalized timeline. The next attempt therefore
uses the complete 50 mm rear-leg channels from episode time zero and executes
all heights on the slower complete-source duration. No safety threshold,
contact gate, or success definition was changed.
