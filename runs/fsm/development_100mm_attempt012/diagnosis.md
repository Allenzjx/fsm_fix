# Attempt 012 diagnosis

This run is retained as a failed FSM-development attempt.

The 1 degree command-envelope margin removed the measured joint-limit failure:

- the run passed the former 124.35 s termination point with no joint-limit
  diagnostic;
- all four wheels reached top contact by 130 s;
- the FSM entered RECOVER and DRIVE_CLEAR;
- forward progress reached +1.050501 m.

At 145.5167 s, `front_right_bot` contacted the obstacle at 7.29096 N, above
the unchanged 5 N collision threshold. The post-transfer trace shows the
mechanism:

- the rear reference remained in an asymmetric lift/place posture
  `[-0.7, 44.2, -9.0, -44.8]` degrees;
- FK vertical lengths for that pose were approximately 115 mm left and
  100 mm right, whereas the physically successful 50 mm final rear posture is
  approximately symmetric at 150/149 mm;
- after both rear wheels reached the top, roll grew from 0.0124 rad at 130 s
  to about 0.078 rad, the front-right wheel lost load, and its wheel-frame
  height fell from 0.1489 m to about 0.117 m before link contact.

The next attempt smoothly blends the rear legs to the exact successful 50 mm
final rear command across phase 9, after both rear top contacts have admitted
the phase. The override is zero at 50 mm, half-strength at 75 mm, and full at
100 mm. No safety, success, force, or timeout threshold is changed.
