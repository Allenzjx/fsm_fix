# Attempt 015 diagnosis

This run is retained as a failed FSM-development attempt.

The contact-driven front load trim activated only in phase 9 and its terminal
state was captured before reset. The direction initially improved load
sharing, but the 10 mm bound allowed over-extension:

- at 133.0 s and 3.583 mm front-right trim, forces were
  9.80/2.32/4.56/12.02 N, all above the unchanged 2 N requirement;
- front-right trim then continued to 6.083 mm by 134.0 s after force dipped
  below the hysteresis threshold;
- the run terminated at 134.3167 s with 6.875 mm trim and
  `front_right_bot` contact of 5.07742 N.

The next attempt retains the measured direction, rate, hysteresis, and IK
constraints but caps extension at 3.5 mm, just below the measured all-wheel
support point. No safety or success threshold is changed.
