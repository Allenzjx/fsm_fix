# Attempt 014 diagnosis

This run is retained as a failed FSM-development attempt.

Capping rear recovery at 10% did not produce a static four-wheel equilibrium.
The balanced forces observed in attempt 013 at 132 s were a transient while
the reference was still moving. After the capped reference became constant,
the front-right wheel unloaded; at 140 s forces were approximately
11.79/0.00/2.82/14.35 N. The run terminated at 145.55 s when
`front_right_bot` contact reached 26.8161 N.

The persistent pattern is a rigid diagonal load split (front-left/rear-right)
rather than a missing geometric traversal: all four wheels have already
reached the platform. The next attempt adds a bounded contact-feedback trim
only in RECOVER and DRIVE_CLEAR. Each underloaded front wheel extends its
reference wheel center through the already validated planar IK at 2.5 mm/s,
with 2/4 N hysteresis and a 10 mm maximum. All resulting servo targets remain
inside the recorded-safe envelope. No success, force, collision, timeout, or
joint-limit threshold is changed.
