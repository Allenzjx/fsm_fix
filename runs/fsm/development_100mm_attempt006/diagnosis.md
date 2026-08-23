# Attempt 006 diagnosis

This run is retained as a failed FSM-development attempt.

The height-conditioned phase-5 boundary removed the 31.15 s gate stall and
excess travel seen in attempt 005. Terminal contact attribution also proved
that the failing body was `base_link`, with 5.1133 N external force against the
unchanged 5 N safety threshold.

The collision occurred at 69.10 s in phase 5 while the 100 mm front reference
was still completing front-leg placement. It coincided with the unwarped 50 mm
rear reference advancing rear-left hip from 7.6 to 22.8 degrees:

- roll changed from approximately -0.03 rad before that rear motion to
  -0.1230 rad at termination;
- pitch remained modest (-0.0473 rad);
- front wheels were geometrically on top and rear wheels remained on ground;
- the failure was not a phase timeout, fall, joint-limit violation, or
  numerical error.

The next attempt retains continuous rear channels but applies a continuous
height-conditioned time map. At 100 mm, rear-reference `u=0.50` is aligned with
global `u=0.574`, after the recorded 100 mm front placement. The mapping is
the identity at 50 mm and interpolated at 75 mm. No command, contact, safety,
or success limit is relaxed.
