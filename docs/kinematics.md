# Planar wheel-center kinematics

Each leg is represented by a two-revolute planar chain in its hip-joint plane.
Lengths and fixed angular offsets are read from the canonical URDF:

- upper link: approximately 0.1478 m;
- projected knee-to-wheel vector:
  `sqrt(0.1559^2 + 0.0200^2) = 0.157177... m`;
- per-leg knee-zero offsets combine the knee child-frame yaw and the
  knee-to-wheel vector angle.

For raw articulation coordinates `q1`, `q2`:

```text
x = l1 cos(q1) + l2 cos(q1 + q2 + q0)
z = l1 sin(q1) + l2 sin(q1 + q2 + q0)
```

The analytic inverse uses the law of cosines, constructs both elbow branches,
rejects candidates outside the per-joint recorded-safe envelope, and selects
the candidate nearest the previous/reference coordinates. Unreachable targets
are explicit failures; the controller falls back to the FSM reference and
increments an IK-invalid counter.

The local unit test samples at least 1,000 safe configurations and checks
FK→IK→FK reconstruction. Formal runtime FK calibration against Isaac body
poses remains a freeze gate; the configuration therefore must not claim a
validated analytic IK until that test artifact exists.
