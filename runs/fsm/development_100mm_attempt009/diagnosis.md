# Attempt 009 diagnosis

This run is retained as a failed FSM-development attempt.

Synchronizing both rear hips substantially reduced the diagonal transient:

- terminal roll decreased from approximately 0.12 rad in the sequential runs
  to 0.0380 rad;
- terminal `base_link` force decreased from 19.0039 N to 9.3215 N;
- both front wheels remained geometrically on top through the terminal state.

The remaining motion was longitudinal: pitch reached -0.1239 rad while the
rear wheels stayed on the ground. FK of the active front reference showed only
58--70 mm vertical hip-to-wheel separation. The accepted 100 mm recovery pose
provides approximately 141 mm, about 70--83 mm more front support extension.

The next attempt therefore stages phase 6: first smoothly extend both front
supports to the recorded-safe 100 mm recovery pose, then move both rear hips
together, then perform the rear-right knee tuck. Wheels remain stopped. The
50 mm reference is unchanged and the override is linearly blended at 75 mm.
No safety, contact, or success threshold is changed.
