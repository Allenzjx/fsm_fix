# Attempt 010 diagnosis

This run is retained as a failed FSM-development attempt.

The staged front-support extension removed the phase-6 body collision:

- it crossed every earlier collision point with no non-wheel force above the
  unchanged 5 N threshold;
- the right-rear wheel reached stable top contact and the left-rear wheel
  reached the obstacle front face;
- forward progress was +0.843341 m, minimum valid longitudinal support margin
  was +0.158809 m, and support-transfer pitch-rate RMS was 0.061832 rad/s.

The run terminated at 124.35 s with the strict `JOINT_LIMIT` predicate. The
terminal phase-8 rear reference was `[-0.7, 45.2, -35.3, -44.8]` degrees, so
two channels were at the edge of the recorded-safe command envelope. The
evaluation output available for this attempt did not retain the actual joint
position at the first violation, therefore it is not sufficient evidence for
choosing which command to alter.

The next attempt repeats the identical controller and scenario after adding
first-violation diagnostics: actual raw joint positions, raw lower/upper
limits, the unchanged 2 degree compliance tolerance, and the exact violating
joint names. No controller, safety threshold, success threshold, or scenario
is changed for that diagnostic reproduction.
